import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from auth import get_current_user, require_admin
from database import get_db
from models import Edict, EdictFormMapping, EdictPhase, Submission, User, UserEdictSlot
from schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    MappingTree,
    SectionsDocument,
    SlotsSchema,
)
import services.forms_service as forms_service
import services.reports as reports
import services.submissions_service as submissions_service
from services.mapping import validate_tree

router = APIRouter(tags=["edicts"])

PHASE_ORDER = ["inscricoes", "homologacao", "avaliacao", "encerrado"]


def _validate_chronology(date_application, date_evaluation, date_verification, date_closed):
    dates = [date_application, date_evaluation, date_verification, date_closed]
    for earlier, later in zip(dates, dates[1:]):
        if later <= earlier:
            raise HTTPException(
                status_code=422, detail="Dates must be in strict chronological order"
            )


def _phase_dates(payload) -> dict:
    # Original association: application->inscricoes, evaluation->homologacao,
    # verification->avaliacao, closed->encerrado.
    return {
        "inscricoes": payload.date_application.date(),
        "homologacao": payload.date_evaluation.date(),
        "avaliacao": payload.date_verification.date(),
        "encerrado": payload.date_closed.date(),
    }


async def _get_edict(db: AsyncSession, edict_id: int) -> Edict:
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Edict).order_by(Edict.closed_date.desc(), Edict.id.desc())
    if type is not None:
        stmt = stmt.where(Edict.edict_type == type)
    if is_open is not None:
        stmt = stmt.where(Edict.is_open.is_(is_open))
    edicts = (await db.execute(stmt)).scalars().all()
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
async def create_edict(
    payload: InsertEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    _validate_chronology(
        payload.date_application, payload.date_evaluation, payload.date_verification, payload.date_closed
    )
    edict = Edict(
        title=payload.title,
        description=payload.description,
        candidate_forms=str(payload.candidate_forms),
        recommenders_forms=str(payload.recommenders_forms),
        closed_date=payload.date_closed.date(),
        year=payload.year,
        semester=payload.semester,
        edict_type=payload.edict_type,
        phase="inscricoes",
        is_open=payload.is_open,
        user_id=user.id,
    )
    db.add(edict)
    await db.flush()
    for phase, closed in _phase_dates(payload).items():
        db.add(EdictPhase(edict_id=edict.id, phase=phase, closed_date=closed))
    await db.commit()
    await db.refresh(edict)
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
async def get_edict(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    edict = await _get_edict(db, edict_id)
    slot = (
        await db.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.edict_id == edict.id, UserEdictSlot.user_id == user.id
            )
        )
    ).scalars().first()
    return {
        "id": edict.id,
        "title": edict.title,
        "candidate_form_id": str(edict.candidate_forms or ""),
        "recommender_form_id": str(edict.recommenders_forms or ""),
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
            for p in (
                await db.execute(
                    select(EdictPhase).where(EdictPhase.edict_id == edict.id).order_by(EdictPhase.id)
                )
            ).scalars().all()
        ],
        "slots": str(slot.slots) if slot and slot.slots is not None else "0",
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    _validate_chronology(
        payload.date_application, payload.date_evaluation, payload.date_verification, payload.date_closed
    )
    edict.title = payload.title
    edict.description = payload.description
    edict.year = int(payload.year)
    edict.semester = int(payload.semester)
    edict.edict_type = payload.edict_type
    edict.closed_date = payload.date_closed.date()
    phase_dates = _phase_dates(payload)
    phases = (
        await db.execute(select(EdictPhase).where(EdictPhase.edict_id == edict.id))
    ).scalars().all()
    for phase in phases:
        if phase.phase in phase_dates:
            phase.closed_date = phase_dates[phase.phase]
    await db.commit()
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
async def edit_edict_date_only(
    edict_id: int,
    payload: EditEdictDateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    edict.closed_date = payload.closed_date
    phases = (
        await db.execute(
            select(EdictPhase).where(EdictPhase.edict_id == edict.id, EdictPhase.phase == "encerrado")
        )
    ).scalars().all()
    for phase in phases:
        phase.closed_date = payload.closed_date
    await db.commit()
    return {"closed_date": payload.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    phase = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.id == payload.id, EdictPhase.edict_id == edict.id
            )
        )
    ).scalars().first()
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    edict.phase = phase.phase
    await db.commit()
    try:
        form_id = int(edict.candidate_forms)
        await forms_service.change_form_phase(form_id, forms_service.FORM_PHASE_MAP[phase.phase])
    except (TypeError, ValueError):
        pass
    return {"id": phase.id, "label": phase.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict already closed")
    edict.is_open = False
    await db.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    await db.delete(edict)
    await db.commit()
    return {"message": "Edict removed successfully"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_edict(db, edict_id)
    amount = payload.amount.strip()
    if amount == "":
        amount = "0"
    try:
        value = int(amount)
    except ValueError:
        raise HTTPException(status_code=422, detail="Amount must be an integer")
    if value < 0:
        value = 0
    slot = (
        await db.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.edict_id == edict_id, UserEdictSlot.user_id == user.id
            )
        )
    ).scalars().first()
    if slot is None:
        slot = UserEdictSlot(edict_id=edict_id, user_id=user.id, slots=value)
        db.add(slot)
    else:
        slot.slots = value
    await db.commit()
    return {"amount": str(value)}


async def _valid_pairs(form_id: int, version: int) -> set[tuple[int, int]]:
    pairs = set()
    for section in await forms_service.get_sections(form_id, version):
        for field in await forms_service.get_fields(section["id"], version):
            pairs.add((section["id"], field["id"]))
    return pairs


def _mapping_payload(mapping: EdictFormMapping) -> dict:
    return {
        "id": mapping.id,
        "edict_id": mapping.edict_id,
        "form_type": mapping.form_type,
        "user_id": mapping.user_id,
        "form_id": mapping.form_id,
        "form_version": mapping.form_version,
        "mapping": mapping.mapping,
        "is_active": mapping.is_active,
    }


async def _create_mapping(db, edict, form_type, version, tree, user):
    form_id = edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms
    try:
        numeric_form_id = int(form_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Form not configured for this edict")
    if not validate_tree(tree, await _valid_pairs(numeric_form_id, version)):
        raise HTTPException(status_code=422, detail="Invalid section/field reference")
    existing = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mapping already exists for this version")
    mapping = EdictFormMapping(
        edict_id=edict.id,
        form_type=form_type,
        mapping=tree,
        is_active=True,
        form_id=str(form_id),
        user_id=user.id,
        form_version=version,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return _mapping_payload(mapping)


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}")
async def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    payload: MappingTree,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    return await _create_mapping(db, edict, "candidate", version, payload, user)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}")
async def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    payload: MappingTree,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    edict = await _get_edict(db, edict_id)
    return await _create_mapping(db, edict, "recommender", version, payload, user)


async def _list_mappings(db, edict_id, form_type):
    await _get_edict(db, edict_id)
    mappings = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
            ).order_by(EdictFormMapping.id)
        )
    ).scalars().all()
    return [_mapping_payload(m) for m in mappings]


@router.get("/edicts/{edict_id}/candidates/mappings")
async def get_candidate_mappings(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _list_mappings(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/mappings")
async def get_recommender_mappings(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _list_mappings(db, edict_id, "recommender")


async def _find_mapping(db, edict_id, form_type, version, mapping_id):
    mapping = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalars().first()
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping


async def _update_mapping(db, edict_id, form_type, version, mapping_id, tree):
    edict = await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    form_id = edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms
    try:
        numeric_form_id = int(form_id)
    except (TypeError, ValueError):
        numeric_form_id = None
    if numeric_form_id is not None and not validate_tree(
        tree, await _valid_pairs(numeric_form_id, version)
    ):
        raise HTTPException(status_code=422, detail="Invalid section/field reference")
    mapping.mapping = tree
    await db.commit()
    return _mapping_payload(mapping)


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: MappingTree,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    return await _update_mapping(db, edict_id, "candidate", version, mapping_id, payload)


@router.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def update_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    payload: MappingTree,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    return await _update_mapping(db, edict_id, "recommender", version, mapping_id, payload)


async def _delete_mapping(db, edict_id, form_type, version, mapping_id):
    await _get_edict(db, edict_id)
    mapping = await _find_mapping(db, edict_id, form_type, version, mapping_id)
    await db.delete(mapping)
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    return await _delete_mapping(db, edict_id, "candidate", version, mapping_id)


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    return await _delete_mapping(db, edict_id, "recommender", version, mapping_id)


async def _unmapped_versions(db, edict_id, form_type):
    await _get_edict(db, edict_id)
    versions = (
        await db.execute(
            select(
                Submission.candidate_form_version
                if form_type == "candidate"
                else Submission.recommender_form_version
            ).where(Submission.edict_id == edict_id)
        )
    ).scalars().all()
    mapped = set(
        (
            await db.execute(
                select(EdictFormMapping.form_version).where(
                    EdictFormMapping.edict_id == edict_id,
                    EdictFormMapping.form_type == form_type,
                )
            )
        ).scalars().all()
    )
    return sorted({v for v in versions if v not in mapped})


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _unmapped_versions(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _unmapped_versions(db, edict_id, "recommender")


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    mode: str = "plain_text",
    payload: SectionsDocument | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    await _get_edict(db, edict_id)
    options = payload.model_dump() if payload else {}
    if mode == "pdf":
        job_id = reports.new_job("pdf")
        background_tasks.add_task(reports.generate_pdf, job_id, edict_id, options)
        return {"job_id": job_id, "status": "processing"}
    return await reports.get_interactors(edict_id)


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    await _get_edict(db, edict_id)
    job_id = reports.new_job("csv")
    background_tasks.add_task(reports.generate_csv, job_id, edict_id)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, media_type: str):
    job = reports.JOBS.get(job_id)
    if not job or not job.get("ready") or not job.get("path") or not os.path.exists(job["path"]):
        raise HTTPException(status_code=404, detail="Report not found")
    path = job["path"]
    reports.JOBS.pop(job_id, None)
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
        background=BackgroundTask(os.remove, path),
    )


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str, user: User = Depends(get_current_user)):
    return _download(job_id, "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str, user: User = Depends(get_current_user)):
    return _download(job_id, "text/csv")


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    edict = await _get_edict(db, edict_id)
    subs = await submissions_service.sync_edict_submissions(db, edict)
    if stats is not None:
        subs = [s for s in subs if s.stats == stats]
    if only_favorites:
        from models import Favorite

        fav_ids = set(
            (
                await db.execute(
                    select(Favorite.submission_id).where(Favorite.user_id == user.id)
                )
            ).scalars().all()
        )
        subs = [s for s in subs if s.id in fav_ids]
    items = []
    for sub in subs:
        context = await submissions_service.load_submission_context(db, edict, sub)
        items.append(
            await submissions_service.build_submission_item(db, edict, sub, user, context)
        )
    return {"submissions": items}
