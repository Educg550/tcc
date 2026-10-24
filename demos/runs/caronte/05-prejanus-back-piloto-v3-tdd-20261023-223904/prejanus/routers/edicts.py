import json
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import formsdb, reports, subservice
from prejanus.auth import get_current_user, require_admin
from prejanus.db import get_db
from prejanus.models import (
    Comment,
    Edict,
    EdictFormMapping,
    EdictPhase,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlots,
)
from prejanus.schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)

router = APIRouter(tags=["edicts"])

PHASE_DATES = {
    "inscricoes": "date_application",
    "homologacao": "date_evaluation",
    "avaliacao": "date_verification",
    "encerrado": "date_closed",
}
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
TYPE_MAP = {"candidates": "candidate", "recommenders": "recommender"}


async def _get_edict(db: AsyncSession, edict_id: int) -> Edict:
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(404, "edict not found")
    return edict


def _check_dates(payload) -> None:
    dates = [
        payload.date_application,
        payload.date_evaluation,
        payload.date_verification,
        payload.date_closed,
    ]
    if not all(dates[i] < dates[i + 1] for i in range(3)):
        raise HTTPException(400, "dates must be in strict chronological order")


def _edict_list_item(edict: Edict) -> dict:
    return {
        "id": edict.id,
        "title": edict.title,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.type,
        "is_open": edict.is_open,
    }


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Edict).order_by(Edict.closed_date.desc(), Edict.id.desc())
    if type is not None:
        query = query.where(Edict.type == type)
    if is_open is not None:
        query = query.where(Edict.is_open == is_open)
    edicts = (await db.execute(query)).scalars().all()
    return [_edict_list_item(e) for e in edicts]


@router.post("/edicts")
async def create_edict(
    payload: InsertEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _check_dates(payload)
    edict = Edict(
        title=payload.title,
        description=payload.description,
        candidate_forms=str(payload.candidate_forms),
        recommenders_forms=str(payload.recommenders_forms),
        closed_date=payload.date_closed.date(),
        year=payload.year,
        semester=payload.semester,
        type=payload.edict_type,
        phase="inscricoes",
        is_open=payload.is_open,
        user_id=user.id,
    )
    db.add(edict)
    await db.flush()
    for phase, attr in PHASE_DATES.items():
        db.add(
            EdictPhase(
                edict_id=edict.id,
                phase=phase,
                closed_date=getattr(payload, attr).date(),
            )
        )
    await db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application,
        "date_evaluation": payload.date_evaluation,
        "date_verification": payload.date_verification,
        "date_closed": payload.date_closed,
        "id": edict.id,
        "closed_date": payload.date_closed,
    }


@router.get("/edicts/{edict_id}")
async def get_edict(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    phases = (
        await db.execute(
            select(EdictPhase).where(EdictPhase.edict_id == edict.id).order_by(EdictPhase.id)
        )
    ).scalars().all()
    slot_row = (
        await db.execute(
            select(UserEdictSlots).where(
                UserEdictSlots.user_id == user.id, UserEdictSlots.edict_id == edict.id
            )
        )
    ).scalar_one_or_none()
    slots = str(slot_row.slots) if slot_row and slot_row.slots is not None else "0"
    return {
        "id": edict.id,
        "title": edict.title,
        "candidate_form_id": edict.candidate_forms or "",
        "recommender_form_id": edict.recommenders_forms or "",
        "description": edict.description or "",
        "closed_date": edict.closed_date,
        "created_at": edict.created_at,
        "year": edict.year,
        "semester": edict.semester,
        "type": edict.type,
        "is_open": edict.is_open,
        "updated_at": edict.updated_at,
        "phase": edict.phase,
        "phases": [
            {"id": p.id, "closed_date": p.closed_date, "phase": p.phase} for p in phases
        ],
        "slots": slots,
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    _check_dates(payload)
    edict.title = payload.title
    edict.description = payload.description
    edict.year = int(payload.year)
    edict.semester = int(payload.semester)
    edict.type = payload.edict_type
    edict.closed_date = payload.date_closed.date()
    phases = (
        await db.execute(
            select(EdictPhase).where(EdictPhase.edict_id == edict.id)
        )
    ).scalars().all()
    for phase in phases:
        phase.closed_date = getattr(payload, PHASE_DATES[phase.phase]).date()
    await db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": payload.date_application,
        "date_evaluation": payload.date_evaluation,
        "date_verification": payload.date_verification,
        "date_closed": payload.date_closed,
    }


@router.post("/edicts/{edict_id}/edit-date")
async def edit_edict_date_only(
    edict_id: int,
    payload: EditEdictDateSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    edict.closed_date = payload.closed_date
    phases = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.edict_id == edict.id, EdictPhase.phase == "encerrado"
            )
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
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    phase = await db.get(EdictPhase, payload.id)
    if phase is None or phase.edict_id != edict.id:
        raise HTTPException(404, "phase not found")
    edict.phase = phase.phase
    await db.commit()
    try:
        form_id = int(edict.candidate_forms)
        await formsdb.change_form_phase(form_id, FORMS_PHASE[phase.phase])
    except (TypeError, ValueError):
        pass
    return {"id": phase.id, "label": phase.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    if not edict.is_open:
        raise HTTPException(409, "edict is already closed")
    edict.is_open = False
    await db.commit()
    return {"message": "edict closed"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    await db.delete(edict)
    await db.commit()
    return {"message": "edict removed"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict(db, edict_id)
    amount = (payload.amount or "").strip()
    if amount == "":
        value = 0
    else:
        try:
            parsed = int(amount)
        except ValueError:
            raise HTTPException(422, "amount must be an integer")
        value = parsed if parsed > 0 else 0
    slot_row = (
        await db.execute(
            select(UserEdictSlots).where(
                UserEdictSlots.user_id == user.id, UserEdictSlots.edict_id == edict_id
            )
        )
    ).scalar_one_or_none()
    if slot_row is None:
        db.add(UserEdictSlots(user_id=user.id, edict_id=edict_id, slots=value))
    else:
        slot_row.slots = value
    await db.commit()
    return {"amount": str(value)}


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    submissions = await subservice.list_submissions(db, edict, user.id, stats, only_favorites)
    return {"submissions": submissions}


# --- mappings ---


async def _validate_mapping_tree(form_id: int, version: int, tree: dict) -> None:
    sections = await formsdb.get_sections(form_id, version)
    valid_sections = {s["id"] for s in sections}
    if version == 1:
        active = await formsdb.get_sections(form_id, None)
        valid_sections.update(s["id"] for s in active)
    valid_fields: set[int] = set()
    for section_id in valid_sections:
        fields = await formsdb.get_fields_for_version(section_id, version)
        valid_fields.update(f["id"] for f in fields)
        active_fields = await formsdb.get_fields(section_id)
        valid_fields.update(f["id"] for f in active_fields)

    def walk(node):
        if not isinstance(node, dict):
            return
        for value in node.values():
            if value is None:
                continue
            if isinstance(value, dict) and set(value.keys()) == {"section", "field"}:
                if value["section"] not in valid_sections or value["field"] not in valid_fields:
                    raise HTTPException(422, "invalid section/field reference in mapping")
            elif isinstance(value, dict):
                walk(value)

    walk(tree)


def _mapping_dict(mapping: EdictFormMapping, user: User | None) -> dict:
    return {
        "id": mapping.id,
        "edict_id": mapping.edict_id,
        "form_type": mapping.form_type,
        "user": {"id": user.id, "name": user.name} if user else None,
        "form_id": mapping.form_id,
        "form_version": mapping.form_version,
        "mapping": mapping.mapping,
        "is_active": mapping.is_active,
        "created_at": mapping.created_at,
    }


async def _get_form_id_for_type(db: AsyncSession, edict: Edict, tipo: str) -> int:
    column = edict.candidate_forms if tipo == "candidates" else edict.recommenders_forms
    try:
        return int(column)
    except (TypeError, ValueError):
        raise HTTPException(404, "edict has no form configured for this type")


async def _create_mapping(db: AsyncSession, edict: Edict, tipo: str, version: int, tree: dict, user: User):
    form_type = TYPE_MAP[tipo]
    form_id = await _get_form_id_for_type(db, edict, tipo)
    await _validate_mapping_tree(form_id, version, tree)
    existing = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "mapping already exists for this version")
    result = await db.execute(
        text(
            "insert into edict_form_mappings "
            "(edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
            "values (:e, cast(:ft as form_type_enum), cast(:m as jsonb), true, :f, :u, :v) "
            "returning id"
        ),
        {
            "e": edict.id,
            "ft": form_type,
            "m": json.dumps(tree),
            "f": str(form_id),
            "u": user.id,
            "v": version,
        },
    )
    new_id = result.scalar_one()
    await db.commit()
    mapping = await db.get(EdictFormMapping, new_id)
    return _mapping_dict(mapping, user)


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
async def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _create_mapping(db, edict, "candidates", version, tree, user)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
async def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _create_mapping(db, edict, "recommenders", version, tree, user)


async def _list_mappings(db: AsyncSession, edict: Edict, tipo: str) -> list[dict]:
    result = await db.execute(
        select(EdictFormMapping, User)
        .join(User, User.id == EdictFormMapping.user_id, isouter=True)
        .where(
            EdictFormMapping.edict_id == edict.id,
            EdictFormMapping.form_type == TYPE_MAP[tipo],
        )
        .order_by(EdictFormMapping.id)
    )
    return [_mapping_dict(m, u) for m, u in result]


@router.get("/edicts/{edict_id}/candidates/mappings")
async def get_candidate_mappings(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _list_mappings(db, edict, "candidates")


@router.get("/edicts/{edict_id}/recommenders/mappings")
async def get_recommender_mappings(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _list_mappings(db, edict, "recommenders")


async def _find_mapping(db: AsyncSession, edict: Edict, tipo: str, version: int, mapping_id: int):
    mapping = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == TYPE_MAP[tipo],
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if mapping is None:
        raise HTTPException(404, "mapping not found")
    return mapping


async def _update_mapping(db: AsyncSession, edict: Edict, tipo: str, version: int, mapping_id: int, tree: dict, user: User):
    mapping = await _find_mapping(db, edict, tipo, version, mapping_id)
    form_id = await _get_form_id_for_type(db, edict, tipo)
    await _validate_mapping_tree(form_id, version, tree)
    await db.execute(
        text("update edict_form_mappings set mapping = cast(:m as jsonb) where id = :i"),
        {"m": json.dumps(tree), "i": mapping_id},
    )
    await db.commit()
    await db.refresh(mapping)
    return _mapping_dict(mapping, user)


async def _delete_mapping(db: AsyncSession, edict: Edict, tipo: str, version: int, mapping_id: int):
    mapping = await _find_mapping(db, edict, tipo, version, mapping_id)
    await db.delete(mapping)
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _update_mapping(db, edict, "candidates", version, mapping_id, tree, user)


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _delete_mapping(db, edict, "candidates", version, mapping_id)


@router.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def update_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _update_mapping(db, edict, "recommenders", version, mapping_id, tree, user)


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _delete_mapping(db, edict, "recommenders", version, mapping_id)


async def _unmapped_versions(db: AsyncSession, edict: Edict, tipo: str) -> list[int]:
    form_type = TYPE_MAP[tipo]
    column = (
        Submission.candidate_form_version
        if tipo == "candidates"
        else Submission.recommender_form_version
    )
    versions = {
        v[0]
        for v in await db.execute(
            select(column).where(Submission.edict_id == edict.id)
        )
    }
    mapped = {
        m[0]
        for m in await db.execute(
            select(EdictFormMapping.form_version).where(
                EdictFormMapping.edict_id == edict.id,
                EdictFormMapping.form_type == form_type,
            )
        )
    }
    return sorted(versions - mapped)


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _unmapped_versions(db, edict, "candidates")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    return await _unmapped_versions(db, edict, "recommenders")


# --- reports ---


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    mode: str = "plain_text",
    options: SectionsDocument | None = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    options = options or SectionsDocument()
    if mode == "pdf":
        job_id = reports.start_pdf_job(background_tasks, edict, options)
        return {"job_id": job_id, "status": "processing"}
    return await reports._interactors(db, edict.id)


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict(db, edict_id)
    job_id = reports.start_csv_job(background_tasks, edict)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, media_type: str, filename: str) -> Response:
    job = reports.JOBS.get(job_id)
    if not job or not job.get("path"):
        raise HTTPException(404, "report not found")
    try:
        with open(job["path"], "rb") as f:
            data = f.read()
    except OSError:
        raise HTTPException(404, "report not found")
    try:
        os.remove(job["path"])
    except OSError:
        pass
    reports.JOBS.pop(job_id, None)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str, user: User = Depends(get_current_user)):
    return _download(job_id, "application/pdf", "report.pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str, user: User = Depends(get_current_user)):
    return _download(job_id, "text/csv", "report.csv")
