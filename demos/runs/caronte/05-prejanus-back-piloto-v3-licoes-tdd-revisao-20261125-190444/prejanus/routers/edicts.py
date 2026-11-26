from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import forms_db, mapping
from prejanus.db import get_db, get_forms_db
from prejanus.deps import get_current_user, require_admin
from prejanus.models import Edict, EdictFormMapping, EdictPhase, Submission, User, UserEdictSlots
from prejanus.submissions_service import get_mappings

router = APIRouter(tags=["edicts"])

PHASE_DATE_ASSOCIATION = {
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


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictDateSchema(BaseModel):
    closed_date: str


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: str
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


def _check_dates(app, verif, eval_, closed):
    if not (app < verif < eval_ < closed):
        raise HTTPException(status_code=400, detail="Datas fora de ordem cronológica")


async def _get_edict(db: AsyncSession, edict_id: int) -> Edict:
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


def _edict_list_item(e: Edict) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "year": e.year,
        "semester": e.semester,
        "edict_type": e.type,
        "is_open": e.is_open,
    }


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Edict).order_by(Edict.closed_date.desc(), Edict.id.desc())
    if type is not None:
        q = q.where(Edict.type == type)
    if is_open is not None:
        q = q.where(Edict.is_open == is_open)
    edicts = (await db.execute(q)).scalars().all()
    return [_edict_list_item(e) for e in edicts]


@router.post("/edicts")
async def create_edict(
    body: InsertEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _check_dates(
        body.date_application, body.date_verification, body.date_evaluation, body.date_closed
    )
    edict = Edict(
        title=body.title,
        description=body.description,
        candidate_forms=str(body.candidate_forms),
        recommenders_forms=str(body.recommenders_forms),
        closed_date=body.date_closed.date(),
        year=body.year,
        semester=body.semester,
        type=body.edict_type,
        phase="inscricoes",
        is_open=body.is_open,
        user_id=user.id,
    )
    db.add(edict)
    await db.flush()
    for phase_name, date_attr in PHASE_DATE_ASSOCIATION.items():
        db.add(
            EdictPhase(
                edict_id=edict.id,
                phase=phase_name,
                closed_date=getattr(body, date_attr).date(),
            )
        )
    await db.commit()
    return {
        "title": body.title,
        "description": body.description,
        "year": body.year,
        "semester": body.semester,
        "edict_type": body.edict_type,
        "is_open": body.is_open,
        "candidate_forms": body.candidate_forms,
        "recommenders_forms": body.recommenders_forms,
        "date_application": body.date_application,
        "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation,
        "date_closed": body.date_closed,
        "id": edict.id,
        "closed_date": body.date_closed,
    }


@router.get("/edicts/{edict_id}")
async def get_edict(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    e = await _get_edict(db, edict_id)
    phases = (
        await db.execute(
            select(EdictPhase).where(EdictPhase.edict_id == edict_id).order_by(EdictPhase.id)
        )
    ).scalars().all()
    slots_row = (
        await db.execute(
            select(UserEdictSlots).where(
                UserEdictSlots.edict_id == edict_id, UserEdictSlots.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    return {
        "id": e.id,
        "title": e.title,
        "candidate_form_id": e.candidate_forms or "",
        "recommender_form_id": e.recommenders_forms or "",
        "description": e.description or "",
        "closed_date": e.closed_date,
        "created_at": e.created_at,
        "year": e.year,
        "semester": e.semester,
        "type": e.type,
        "is_open": e.is_open,
        "updated_at": e.updated_at,
        "phase": e.phase,
        "phases": [
            {"id": p.id, "closed_date": p.closed_date, "phase": p.phase} for p in phases
        ],
        "slots": str(slots_row.slots) if slots_row and slots_row.slots is not None else "0",
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    body: EditEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _check_dates(
        body.date_application, body.date_verification, body.date_evaluation, body.date_closed
    )
    e = await _get_edict(db, edict_id)
    e.title = body.title
    e.description = body.description
    e.year = int(body.year)
    e.semester = int(body.semester)
    e.type = body.edict_type
    e.closed_date = body.date_closed.date()
    phases = (
        await db.execute(select(EdictPhase).where(EdictPhase.edict_id == edict_id))
    ).scalars().all()
    for p in phases:
        date_attr = PHASE_DATE_ASSOCIATION.get(p.phase)
        if date_attr:
            p.closed_date = getattr(body, date_attr).date()
    await db.commit()
    return {
        "title": body.title,
        "description": body.description,
        "year": body.year,
        "semester": body.semester,
        "edict_type": body.edict_type,
        "date_application": body.date_application,
        "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation,
        "date_closed": body.date_closed,
    }


@router.post("/edicts/{edict_id}/edit-date")
async def edit_edict_date_only(
    edict_id: int,
    body: EditEdictDateSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    e = await _get_edict(db, edict_id)
    from datetime import date

    new_date = date.fromisoformat(body.closed_date)
    e.closed_date = new_date
    phases = (
        await db.execute(
            select(EdictPhase).where(EdictPhase.edict_id == edict_id, EdictPhase.phase == "encerrado")
        )
    ).scalars().all()
    for p in phases:
        p.closed_date = new_date
    await db.commit()
    return {"closed_date": body.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int,
    body: AdvancePhaseEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    e = await _get_edict(db, edict_id)
    phase_row = (
        await db.execute(
            select(EdictPhase).where(
                EdictPhase.id == body.id, EdictPhase.edict_id == edict_id
            )
        )
    ).scalar_one_or_none()
    if phase_row is None:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    e.phase = phase_row.phase
    await db.commit()

    cand_form = None
    try:
        cand_form = int(str(e.candidate_forms))
    except (TypeError, ValueError):
        cand_form = None
    if cand_form is not None:
        await forms_db.change_form_phase(fdb, cand_form, FORMS_PHASE[phase_row.phase])
    return {"id": phase_row.id, "label": phase_row.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    body: CloseEdictSchema,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    e = await _get_edict(db, edict_id)
    if not e.is_open:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    e.is_open = False
    await db.commit()
    return {"message": "Edital encerrado"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    e = await _get_edict(db, edict_id)
    await db.delete(e)
    await db.commit()
    return {"message": "Edital removido"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    body: SlotsSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict(db, edict_id)
    amount = (body.amount or "").strip()
    if amount == "":
        value = 0
    else:
        try:
            value = int(amount)
        except ValueError:
            raise HTTPException(status_code=400, detail="Quantidade inválida")
        if value < 0:
            value = 0
    row = (
        await db.execute(
            select(UserEdictSlots).where(
                UserEdictSlots.edict_id == edict_id, UserEdictSlots.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        db.add(UserEdictSlots(edict_id=edict_id, user_id=user.id, slots=value))
    else:
        row.slots = value
    await db.commit()
    return {"amount": str(value)}


# ---------------------------------------------------------------------------
# Mapeamentos de formulários


async def _validate_mapping_tree(fdb: AsyncSession, form_id: int, version: int, tree: dict):
    sections = await forms_db.get_sections(fdb, form_id, version)
    sec_ids = [s["id"] for s in sections]
    fields = await forms_db.get_fields(fdb, form_id, sec_ids, version)
    valid = {(f["section_id"], f["id"]) for f in fields}
    if not valid:
        valid = {(f["section_id"], f["id"]) for f in await forms_db.get_all_fields(fdb, form_id)}
    for leaf in mapping.leaves(tree):
        if (leaf["section"], leaf["field"]) not in valid:
            raise HTTPException(status_code=422, detail="Referência seção/campo inválida")


def _mapping_dict(m: EdictFormMapping) -> dict:
    return {
        "id": m.id,
        "edict_id": m.edict_id,
        "form_type": m.form_type,
        "user_id": m.user_id,
        "form_version": m.form_version,
        "mapping": m.mapping,
        "is_active": m.is_active,
    }


async def _create_mapping(db, fdb, edict_id, form_type, version, tree, user):
    e = await _get_edict(db, edict_id)
    form_attr = "candidate_forms" if form_type == "candidate" else "recommenders_forms"
    try:
        form_id = int(str(getattr(e, form_attr)))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Edital sem formulário associado")
    await _validate_mapping_tree(fdb, form_id, version, tree)
    existing = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Mapeamento já existe para esta versão")
    import json as _json

    row = (
        await db.execute(
            text(
                "insert into edict_form_mappings"
                " (edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version)"
                " values (:e, cast(:ft as form_type_enum), cast(:m as jsonb), :a, now(), :f, :u, :v)"
                " returning id"
            ),
            {
                "e": edict_id,
                "ft": form_type,
                "m": _json.dumps(tree),
                "a": True,
                "f": str(form_id),
                "u": user.id,
                "v": version,
            },
        )
    ).mappings().first()
    await db.commit()
    return {
        "id": row["id"],
        "edict_id": edict_id,
        "form_type": form_type,
        "user_id": user.id,
        "form_version": version,
        "mapping": tree,
        "is_active": True,
    }


async def _list_mappings(db, edict_id, form_type):
    await _get_edict(db, edict_id)
    rows = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
            ).order_by(EdictFormMapping.id)
        )
    ).scalars().all()
    return [_mapping_dict(m) for m in rows]


async def _update_mapping(db, fdb, edict_id, form_type, version, mapping_id, tree):
    e = await _get_edict(db, edict_id)
    m = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    form_attr = "candidate_forms" if form_type == "candidate" else "recommenders_forms"
    try:
        form_id = int(str(getattr(e, form_attr)))
    except (TypeError, ValueError):
        form_id = None
    if form_id is not None:
        await _validate_mapping_tree(fdb, form_id, version, tree)
    m.mapping = tree
    await db.commit()
    return _mapping_dict(m)


async def _delete_mapping(db, edict_id, form_type, version, mapping_id):
    await _get_edict(db, edict_id)
    m = (
        await db.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    await db.delete(m)
    await db.commit()
    return {"message": "Mapping deleted successfully"}


async def _unmapped_versions(db, edict_id, form_type):
    await _get_edict(db, edict_id)
    column = (
        Submission.candidate_form_version
        if form_type == "candidate"
        else Submission.recommender_form_version
    )
    rows = await db.execute(
        select(column).where(Submission.edict_id == edict_id).distinct()
    )
    versions = {r[0] for r in rows.all()}
    mappings = await get_mappings(db, edict_id, form_type)
    return sorted(versions - set(mappings.keys()))


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
async def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "candidate", version, tree, user)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
async def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "recommender", version, tree, user)


@router.get("/edicts/{edict_id}/candidates/mappings")
async def get_candidate_mappings(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_mappings(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/mappings")
async def get_recommender_mappings(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _list_mappings(db, edict_id, "recommender")


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _update_mapping(db, fdb, edict_id, "candidate", version, mapping_id, tree)


@router.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def update_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    tree: dict,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _update_mapping(db, fdb, edict_id, "recommender", version, mapping_id, tree)


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _delete_mapping(db, edict_id, "candidate", version, mapping_id)


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _delete_mapping(db, edict_id, "recommender", version, mapping_id)


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _unmapped_versions(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _unmapped_versions(db, edict_id, "recommender")
