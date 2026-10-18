"""Edict routes: CRUD, phases, mappings, slots, reports and downloads."""
import os
from datetime import datetime

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .. import formsdb
from ..db import get_db
from ..models import Edict, EdictPhase, FormMapping, Slot, Submission, User
from ..reports import JOBS, start_csv_job, start_pdf_job
from ..schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    MappingNode,
    SectionsDocument,
    SlotsSchema,
)
from ..security import require_admin, require_user
from ..summary import build_item

router = APIRouter(tags=["edicts"])

# Original association between edict dates and phases:
# inscricoes -> date_application, homologacao -> date_evaluation,
# avaliacao -> date_verification, encerrado -> date_closed.
PHASE_ORDER = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
PHASES_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


def get_edict_or_404(db, edict_id: int) -> Edict:
    edict = db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def user_slots(db, edict_id: int, user_id: int) -> str:
    slot = (
        db.query(Slot)
        .filter(Slot.edict_id == edict_id, Slot.user_id == user_id)
        .first()
    )
    return slot.amount if slot else "0"


def _check_dates(application, verification, evaluation, closed):
    if not (application < verification < evaluation < closed):
        raise HTTPException(
            status_code=400,
            detail="Dates must be in strict chronological order",
        )


def _edict_by_id(db, edict: Edict, user: User) -> dict:
    return {
        "id": edict.id,
        "title": edict.title,
        "candidate_form_id": str(edict.candidate_form_id),
        "recommender_form_id": str(edict.recommender_form_id),
        "description": edict.description or "",
        "closed_date": edict.closed_date,
        "created_at": edict.created_at,
        "year": edict.year,
        "semester": edict.semester,
        "type": edict.edict_type,
        "is_open": edict.is_open,
        "updated_at": edict.updated_at,
        "phase": edict.phase,
        "phases": [
            {"id": p.id, "closed_date": p.closed_date, "phase": p.phase}
            for p in edict.phases
        ],
        "slots": user_slots(db, edict.id, user.id),
    }


@router.get("/edicts")
def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(require_user),
    db=Depends(get_db),
):
    query = db.query(Edict)
    if type is not None:
        query = query.filter(Edict.edict_type == type)
    if is_open is not None:
        query = query.filter(Edict.is_open.is_(is_open))
    edicts = query.order_by(Edict.closed_date.desc().nulls_last(), Edict.id).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "year": e.year,
            "semester": e.semester,
            "edict_type": e.edict_type,
            "is_open": e.is_open,
        }
        for e in edicts
    ]


@router.post("/edicts")
def create_edict(
    payload: InsertEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    now = datetime.utcnow()
    edict = Edict(
        title=payload.title,
        description=payload.description,
        year=payload.year,
        semester=payload.semester,
        edict_type=payload.edict_type,
        is_open=payload.is_open,
        candidate_form_id=str(payload.candidate_forms),
        recommender_form_id=str(payload.recommenders_forms),
        created_by=user.id,
        phase="inscricoes",
        closed_date=payload.date_closed.date(),
        created_at=now,
        updated_at=now,
    )
    db.add(edict)
    db.flush()
    dates = {
        "inscricoes": payload.date_application.date(),
        "homologacao": payload.date_evaluation.date(),
        "avaliacao": payload.date_verification.date(),
        "encerrado": payload.date_closed.date(),
    }
    for phase in PHASE_ORDER:
        db.add(EdictPhase(edict_id=edict.id, phase=phase,
                          closed_date=dates[phase]))
    db.commit()
    return {
        "title": edict.title,
        "description": edict.description,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.edict_type,
        "is_open": edict.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
        "id": edict.id,
        "closed_date": payload.date_closed,
    }


@router.get("/edicts/{edict_id}")
def get_edict(
    edict_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    return _edict_by_id(db, edict, user)


@router.post("/edicts/{edict_id}/edit")
def edit_date_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    try:
        year = int(payload.year)
        semester = int(payload.semester)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid year/semester")
    edict.title = payload.title
    edict.description = payload.description
    edict.year = year
    edict.semester = semester
    edict.edict_type = payload.edict_type
    edict.closed_date = payload.date_closed.date()
    edict.updated_at = datetime.utcnow()
    dates = {
        "inscricoes": payload.date_application.date(),
        "homologacao": payload.date_evaluation.date(),
        "avaliacao": payload.date_verification.date(),
        "encerrado": payload.date_closed.date(),
    }
    for phase in edict.phases:
        phase.closed_date = dates.get(phase.phase, phase.closed_date)
    db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
    }


@router.post("/edicts/{edict_id}/edit-date")
def edit_edict_date_only(
    edict_id: int,
    payload: EditEdictDateSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    edict.closed_date = payload.closed_date
    edict.updated_at = datetime.utcnow()
    for phase in edict.phases:
        if phase.phase == "encerrado":
            phase.closed_date = payload.closed_date
    db.commit()
    return {"closed_date": payload.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
def advance_edict(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    phase = (
        db.query(EdictPhase)
        .filter(
            EdictPhase.id == payload.id,
            EdictPhase.edict_id == edict_id,
        )
        .first()
    )
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    edict.phase = phase.phase
    edict.updated_at = datetime.utcnow()
    db.commit()
    # Propagate the phase to the candidate form in the Forms database.
    forms_phase = PHASES_FORMS.get(phase.phase)
    if forms_phase:
        formsdb.set_form_phase(int(edict.candidate_form_id), forms_phase)
    return {"id": phase.id, "label": phase.phase}


@router.patch("/edicts/{edict_id}/close")
def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict already closed")
    edict.is_open = False
    edict.closed_date = payload.confirmation_deadline
    edict.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
def remove_edict(
    edict_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    db.delete(edict)
    db.commit()
    return {"message": "Edict removed successfully"}


@router.post("/edicts/{edict_id}/slots")
def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user=Depends(require_user),
    db=Depends(get_db),
):
    get_edict_or_404(db, edict_id)
    amount = (payload.amount or "").strip()
    if amount == "":
        amount = "0"
    else:
        try:
            value = int(amount)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid amount")
        if value < 0:
            amount = "0"
    slot = (
        db.query(Slot)
        .filter(Slot.edict_id == edict_id, Slot.user_id == user.id)
        .first()
    )
    if slot is None:
        slot = Slot(edict_id=edict_id, user_id=user.id, amount=amount)
        db.add(slot)
    else:
        slot.amount = amount
    db.commit()
    return {"amount": amount}


# --- mappings ---------------------------------------------------------------

def _form_id_for_type(edict: Edict, form_type: str) -> int:
    if form_type == "candidates":
        return int(edict.candidate_form_id)
    return int(edict.recommender_form_id)


def _validate_tree(form_id: int, version: int, tree: dict) -> None:
    """Validate every leaf reference against the requested form version."""
    from ..summary import flatten_tree

    sections = {s.get("id"): s for s in formsdb.get_sections(form_id, version)}
    for leaf in flatten_tree(tree).values():
        if leaf is None:
            continue
        if leaf.get("section") not in sections:
            raise HTTPException(status_code=422, detail="Invalid section reference")
        if not formsdb.field_exists(leaf.get("section"), leaf.get("field")):
            raise HTTPException(status_code=422, detail="Invalid field reference")


def _mapping_payload(db, mapping: FormMapping) -> dict:
    author = db.get(User, mapping.user_id) if mapping.user_id else None
    return {
        "id": mapping.id,
        "edict_id": mapping.edict_id,
        "form_type": mapping.form_type,
        "user": {"id": author.id, "name": author.name} if author else None,
        "version": mapping.version,
        "tree": mapping.tree,
        "active": mapping.active,
    }


def _get_mapping(db, edict_id: int, form_type: str, version: int,
                 mapping_id: int) -> FormMapping:
    mapping = db.get(FormMapping, mapping_id)
    if (
        mapping is None
        or mapping.edict_id != edict_id
        or mapping.form_type != form_type
        or mapping.version != version
    ):
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping


def _create_mapping(db, user, edict_id: int, form_type: str, version: int,
                    tree: dict) -> dict:
    edict = get_edict_or_404(db, edict_id)
    existing = (
        db.query(FormMapping)
        .filter(
            FormMapping.edict_id == edict_id,
            FormMapping.form_type == form_type,
            FormMapping.version == version,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mapping already exists")
    _validate_tree(_form_id_for_type(edict, form_type), version, tree)
    mapping = FormMapping(
        edict_id=edict_id,
        form_type=form_type,
        version=version,
        tree=tree,
        user_id=user.id,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.add(mapping)
    db.commit()
    return _mapping_payload(db, mapping)


def _list_mappings(db, edict_id: int, form_type: str) -> list[dict]:
    get_edict_or_404(db, edict_id)
    mappings = (
        db.query(FormMapping)
        .filter(
            FormMapping.edict_id == edict_id,
            FormMapping.form_type == form_type,
        )
        .order_by(FormMapping.id)
        .all()
    )
    return [_mapping_payload(db, m) for m in mappings]


def _update_mapping(db, edict_id: int, form_type: str, version: int,
                    mapping_id: int, tree: dict) -> dict:
    edict = get_edict_or_404(db, edict_id)
    mapping = _get_mapping(db, edict_id, form_type, version, mapping_id)
    _validate_tree(_form_id_for_type(edict, form_type), version, tree)
    mapping.tree = tree
    db.commit()
    return _mapping_payload(db, mapping)


def _delete_mapping(db, edict_id: int, form_type: str, version: int,
                    mapping_id: int) -> dict:
    get_edict_or_404(db, edict_id)
    mapping = _get_mapping(db, edict_id, form_type, version, mapping_id)
    db.delete(mapping)
    db.commit()
    return {"message": "Mapping deleted successfully"}


def _unmapped_versions(db, edict_id: int, form_type: str) -> list[int]:
    edict = get_edict_or_404(db, edict_id)
    mapped = {
        m.version
        for m in db.query(FormMapping)
        .filter(
            FormMapping.edict_id == edict_id,
            FormMapping.form_type == form_type,
        )
        .all()
    }
    if form_type == "candidates":
        versions = {
            s.version
            for s in db.query(Submission)
            .filter(Submission.edict_id == edict_id)
            .all()
        }
    else:
        emails = {
            s.email
            for s in db.query(Submission)
            .filter(Submission.edict_id == edict_id)
            .all()
        }
        versions = set()
        for answer in formsdb.get_answers(int(edict.recommender_form_id)):
            if answer.get("email") in emails:
                versions.add(answer.get("version") or 1)
    return sorted(v for v in versions if v not in mapped)


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    payload: MappingNode,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _create_mapping(
        db, user, edict_id, "candidates", version, payload.model_dump()
    )


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    payload: MappingNode,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _create_mapping(
        db, user, edict_id, "recommenders", version, payload.model_dump()
    )


@router.get("/edicts/{edict_id}/candidates/mappings")
def get_candidate_mappings(
    edict_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    return _list_mappings(db, edict_id, "candidates")


@router.get("/edicts/{edict_id}/recommenders/mappings")
def get_recommender_mappings(
    edict_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    return _list_mappings(db, edict_id, "recommenders")


@router.put(
    "/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}"
)
def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _update_mapping(
        db, edict_id, "candidates", version, mapping_id, payload
    )


@router.put(
    "/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}"
)
def update_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _update_mapping(
        db, edict_id, "recommenders", version, mapping_id, payload
    )


@router.delete(
    "/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}"
)
def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _delete_mapping(db, edict_id, "candidates", version, mapping_id)


@router.delete(
    "/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}"
)
def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    return _delete_mapping(db, edict_id, "recommenders", version, mapping_id)


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
def get_candidates_unmapped_versions(
    edict_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    return _unmapped_versions(db, edict_id, "candidates")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
def get_recommenders_unmapped_versions(
    edict_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    return _unmapped_versions(db, edict_id, "recommenders")


# --- reports ----------------------------------------------------------------

@router.post("/edicts/{edict_id}/interactors_list")
def interactors_list(
    edict_id: int,
    mode: str = Query(default="plain_text"),
    options: SectionsDocument = SectionsDocument(),
    user=Depends(require_admin),
    db=Depends(get_db),
):
    get_edict_or_404(db, edict_id)
    if mode == "pdf":
        job_id = start_pdf_job(edict_id, options.model_dump())
        return {"job_id": job_id, "status": "processing"}
    from ..reports import _interactors

    return [
        {"id": u.id, "name": u.name, "email": u.email}
        for u in _interactors(db, edict_id)
    ]


@router.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(
    edict_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    get_edict_or_404(db, edict_id)
    job_id = start_csv_job(edict_id)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, kind: str, media_type: str):
    job = JOBS.get(job_id)
    if job is None or job.get("kind") != kind or not job.get("path"):
        raise HTTPException(status_code=404, detail="Report not found")
    if not os.path.exists(job["path"]):
        raise HTTPException(status_code=404, detail="Report not found")

    def cleanup(path: str) -> None:
        try:
            os.remove(path)
        except OSError:
            pass
        JOBS.pop(job_id, None)

    return FileResponse(
        job["path"],
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
        background=BackgroundTask(cleanup, job["path"]),
    )


@router.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    return _download(job_id, "pdf", "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    return _download(job_id, "csv", "text/csv")


# --- submissions listing ----------------------------------------------------

@router.get("/edicts/{edict_id}/submissions")
def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(require_user),
    db=Depends(get_db),
):
    edict = get_edict_or_404(db, edict_id)
    query = db.query(Submission).filter(Submission.edict_id == edict_id)
    if stats is not None:
        query = query.filter(Submission.stats == stats)
    submissions = query.order_by(Submission.id).all()
    if only_favorites:
        from ..models import Favorite

        favorites = {
            f.submission_id
            for f in db.query(Favorite).filter(Favorite.user_id == user.id).all()
        }
        submissions = [s for s in submissions if s.id in favorites]
    return {"submissions": [build_item(db, edict, s, user) for s in submissions]}