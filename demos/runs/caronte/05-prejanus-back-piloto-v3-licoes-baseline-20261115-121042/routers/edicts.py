import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user, get_db, get_forms_db, require_admin
from schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)
from services import forms_service, reports, submission_service
from services.mapping_service import collect_leaf_refs

router = APIRouter(tags=["edicts"])

PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


def _validate_dates(date_application, date_verification, date_evaluation, date_closed):
    dates = [date_application, date_verification, date_evaluation, date_closed]
    for previous, current in zip(dates, dates[1:]):
        if not previous < current:
            raise HTTPException(status_code=400, detail="Dates must be in strict chronological order")


async def _get_edict_or_404(db: AsyncSession, edict_id: int) -> dict:
    edict = await submission_service.get_edict(db, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


async def _get_user_slots(db: AsyncSession, edict_id: int, user_id: int) -> str:
    result = await db.execute(
        text("select slots from user_edict_slots where edict_id = :eid and user_id = :uid"),
        {"eid": edict_id, "uid": user_id},
    )
    row = result.first()
    return str(row[0]) if row and row[0] is not None else "0"


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del user
    query = "select id, title, year, semester, type, is_open from edict where true"
    params: dict = {}
    if type is not None:
        query += " and type = :type"
        params["type"] = type
    if is_open is not None:
        query += " and is_open = :is_open"
        params["is_open"] = is_open
    query += " order by closed_date desc, id desc"
    result = await db.execute(text(query), params)
    return [
        {
            "id": r.id,
            "title": r.title,
            "year": r.year,
            "semester": r.semester,
            "edict_type": r.type,
            "is_open": r.is_open,
        }
        for r in result.mappings()
    ]


@router.post("/edicts")
async def create_edict(
    payload: InsertEdictSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _validate_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    now = datetime.now(timezone.utc)
    result = await db.execute(
        text(
            "insert into edict (title, description, candidate_forms, recommenders_forms, closed_date, "
            "year, semester, type, phase, is_open, created_at, updated_at, user_id) "
            "values (:title, :description, :candidate_forms, :recommenders_forms, :closed_date, "
            ":year, :semester, :type, 'inscricoes', :is_open, :now, :now, :user_id) returning id"
        ),
        {
            "title": payload.title,
            "description": payload.description,
            "candidate_forms": str(payload.candidate_forms),
            "recommenders_forms": str(payload.recommenders_forms),
            "closed_date": payload.date_closed.date(),
            "year": payload.year,
            "semester": payload.semester,
            "type": payload.edict_type,
            "is_open": payload.is_open,
            "now": now,
            "user_id": user["id"],
        },
    )
    edict_id = result.scalar_one()
    for phase, phase_date in (
        ("inscricoes", payload.date_application),
        ("homologacao", payload.date_evaluation),
        ("avaliacao", payload.date_verification),
        ("encerrado", payload.date_closed),
    ):
        await db.execute(
            text(
                "insert into edict_phase (edict_id, closed_date, phase) values (:eid, :cdate, :phase)"
            ),
            {"eid": edict_id, "cdate": phase_date.date(), "phase": phase},
        )
    await db.commit()
    return {
        "id": edict_id,
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application,
        "date_verification": payload.date_verification,
        "date_evaluation": payload.date_evaluation,
        "date_closed": payload.date_closed,
        "closed_date": payload.date_closed,
    }


@router.get("/edicts/{edict_id}")
async def get_edict(
    edict_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    result = await db.execute(
        text("select id, closed_date, phase from edict_phase where edict_id = :eid order by id"),
        {"eid": edict_id},
    )
    phases = [dict(r) for r in result.mappings()]
    slots = await _get_user_slots(db, edict_id, user["id"])
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": edict["candidate_forms"],
        "recommender_form_id": edict["recommenders_forms"],
        "description": edict["description"],
        "closed_date": edict["closed_date"],
        "created_at": edict["created_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": phases,
        "slots": slots,
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    _validate_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    now = datetime.now(timezone.utc)
    await db.execute(
        text(
            "update edict set title = :title, description = :description, year = :year, "
            "semester = :semester, type = :type, closed_date = :closed_date, updated_at = :now "
            "where id = :id"
        ),
        {
            "title": payload.title,
            "description": payload.description,
            "year": int(payload.year),
            "semester": int(payload.semester),
            "type": payload.edict_type,
            "closed_date": payload.date_closed.date(),
            "now": now,
            "id": edict_id,
        },
    )
    for phase, phase_date in (
        ("inscricoes", payload.date_application),
        ("homologacao", payload.date_evaluation),
        ("avaliacao", payload.date_verification),
        ("encerrado", payload.date_closed),
    ):
        await db.execute(
            text("update edict_phase set closed_date = :cdate where edict_id = :eid and phase = :phase"),
            {"cdate": phase_date.date(), "eid": edict_id, "phase": phase},
        )
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
async def edit_edict_date(
    edict_id: int,
    payload: EditEdictDateSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    await db.execute(
        text("update edict set closed_date = :cdate, updated_at = :now where id = :id"),
        {"cdate": payload.closed_date, "now": datetime.now(timezone.utc), "id": edict_id},
    )
    await db.execute(
        text("update edict_phase set closed_date = :cdate where edict_id = :eid and phase = 'encerrado'"),
        {"cdate": payload.closed_date, "eid": edict_id},
    )
    await db.commit()
    return {"closed_date": payload.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    result = await db.execute(
        text("select id, phase from edict_phase where id = :id and edict_id = :eid"),
        {"id": payload.id, "eid": edict_id},
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    await db.execute(
        text("update edict set phase = :phase, updated_at = :now where id = :id"),
        {"phase": row["phase"], "now": datetime.now(timezone.utc), "id": edict_id},
    )
    await db.commit()
    forms_phase = PHASE_TO_FORMS.get(row["phase"])
    if forms_phase:
        for form_id in submission_service.parse_form_ids(
            (await submission_service.get_edict(db, edict_id)).get("candidate_forms")
        ):
            await forms_service.change_form_phase(fs, form_id, forms_phase)
    return {"id": row["id"], "label": row["phase"]}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del user
    edict = await _get_edict_or_404(db, edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict already closed")
    await db.execute(
        text("update edict set is_open = false, updated_at = :now where id = :id"),
        {"now": datetime.now(timezone.utc), "id": edict_id},
    )
    await db.execute(
        text("update edict_phase set closed_date = :cdate where edict_id = :eid and phase = 'encerrado'"),
        {"cdate": payload.confirmation_deadline, "eid": edict_id},
    )
    await db.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    await db.execute(text("delete from edict where id = :id"), {"id": edict_id})
    await db.commit()
    return {"message": "Edict deleted successfully"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    raw = (payload.amount or "").strip()
    if raw == "":
        amount = 0
    else:
        try:
            amount = int(raw)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid amount")
        if amount < 0:
            amount = 0
    existing = await db.execute(
        text("select id from user_edict_slots where edict_id = :eid and user_id = :uid"),
        {"eid": edict_id, "uid": user["id"]},
    )
    row = existing.first()
    if row:
        await db.execute(
            text("update user_edict_slots set slots = :slots where id = :id"),
            {"slots": amount, "id": row[0]},
        )
    else:
        await db.execute(
            text(
                "insert into user_edict_slots (user_id, edict_id, slots) values (:uid, :eid, :slots)"
            ),
            {"uid": user["id"], "eid": edict_id, "slots": amount},
        )
    await db.commit()
    return {"amount": str(amount)}


async def _validate_mapping_tree(fs: AsyncSession, form_id: int, version: int, tree) -> None:
    sections = await forms_service.select_sections(fs, form_id, version)
    section_ids = {s["id"] for s in sections}
    valid: set[tuple] = set()
    for section in sections:
        fields = await forms_service.select_fields(fs, section["id"], version)
        for field in fields:
            valid.add((section["id"], field["id"]))
    for section_id, field_id in collect_leaf_refs(tree):
        if section_id not in section_ids or (section_id, field_id) not in valid:
            raise HTTPException(status_code=422, detail="Invalid mapping reference")


def _form_type(tipo: str) -> str:
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(status_code=404, detail="Unknown mapping type")


def _edict_form_id(edict: dict, form_type: str) -> int | None:
    raw = edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"]
    ids = submission_service.parse_form_ids(raw)
    return ids[0] if ids else None


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    payload: dict,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    form_type = _form_type(tipo)
    form_id = _edict_form_id(edict, form_type)
    if form_id is None:
        raise HTTPException(status_code=404, detail="No form configured for this edict")
    await _validate_mapping_tree(fs, form_id, version, payload)
    existing = await db.execute(
        text(
            "select id from edict_form_mappings where edict_id = :eid "
            "and form_type = :ftype::form_type_enum and form_version = :v"
        ),
        {"eid": edict_id, "ftype": form_type, "v": version},
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="Mapping already exists for this version")
    result = await db.execute(
        text(
            "insert into edict_form_mappings (edict_id, form_type, mapping, is_active, form_id, "
            "user_id, form_version) values (:eid, :ftype::form_type_enum, :mapping::jsonb, true, "
            ":form_id, :uid, :v) returning id"
        ),
        {
            "eid": edict_id,
            "ftype": form_type,
            "mapping": _dump(payload),
            "form_id": str(form_id),
            "uid": user["id"],
            "v": version,
        },
    )
    mapping_id = result.scalar_one()
    await db.commit()
    return {
        "id": mapping_id,
        "edict_id": edict_id,
        "form_type": form_type,
        "user_id": user["id"],
        "form_version": version,
        "form_id": str(form_id),
        "mapping": payload,
        "is_active": True,
    }


def _dump(tree) -> str:
    import json

    return json.dumps(tree)


@router.get("/edicts/{edict_id}/{tipo}/mappings")
async def get_mappings(
    edict_id: int,
    tipo: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    form_type = _form_type(tipo)
    result = await db.execute(
        text(
            "select * from edict_form_mappings where edict_id = :eid "
            "and form_type = :ftype::form_type_enum order by id"
        ),
        {"eid": edict_id, "ftype": form_type},
    )
    return [dict(r) for r in result.mappings()]


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    payload: dict,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    del user
    edict = await _get_edict_or_404(db, edict_id)
    form_type = _form_type(tipo)
    result = await db.execute(
        text(
            "select id from edict_form_mappings where id = :id and edict_id = :eid "
            "and form_type = :ftype::form_type_enum and form_version = :v"
        ),
        {"id": mapping_id, "eid": edict_id, "ftype": form_type, "v": version},
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    form_id = _edict_form_id(edict, form_type)
    if form_id is not None:
        await _validate_mapping_tree(fs, form_id, version, payload)
    await db.execute(
        text("update edict_form_mappings set mapping = :mapping::jsonb where id = :id"),
        {"mapping": _dump(payload), "id": mapping_id},
    )
    await db.commit()
    return {"message": "Mapping updated successfully"}


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del user
    form_type = _form_type(tipo)
    result = await db.execute(
        text(
            "select id from edict_form_mappings where id = :id and edict_id = :eid "
            "and form_type = :ftype::form_type_enum and form_version = :v"
        ),
        {"id": mapping_id, "eid": edict_id, "ftype": form_type, "v": version},
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    await db.execute(text("delete from edict_form_mappings where id = :id"), {"id": mapping_id})
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def get_unmapped_versions(
    edict_id: int,
    tipo: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    form_type = _form_type(tipo)
    column = "candidate_form_version" if form_type == "candidate" else "recommender_form_version"
    sql = (
        f"select distinct {column} as version from submission where edict_id = :eid "
        f"and {column} not in (select form_version from edict_form_mappings "
        "where edict_id = :eid and form_type = :ftype::form_type_enum and is_active = true) "
        "order by version"
    )
    result = await db.execute(text(sql), {"eid": edict_id, "ftype": form_type})
    return [r.version for r in result.mappings()]


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    await submission_service.ensure_submissions(db, fs, edict)
    result = await db.execute(
        text("select * from submission where edict_id = :eid order by id"),
        {"eid": edict_id},
    )
    submissions = []
    for row in [dict(r) for r in result.mappings()]:
        if stats is not None and row["stats"] != stats:
            continue
        if only_favorites and not await submission_service.is_favorite(db, row["id"], user["id"]):
            continue
        submissions.append(await submission_service.build_summary(db, fs, edict, row, user))
    return {"submissions": submissions}


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    payload: SectionsDocument | None = None,
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    if mode == "pdf":
        options = payload or SectionsDocument()
        job_id, _ = reports.new_job("pdf")

        async def run():
            async with _admin_session() as session:
                async with _forms_session() as forms_session:
                    edict = await submission_service.get_edict(session, edict_id)
                    await reports.generate_pdf(session, forms_session, edict, options)

        background_tasks.add_task(run)
        return {"job_id": job_id, "status": "processing"}
    result = await db.execute(
        text(
            'select distinct u.id, u.name, u.email from "user" u where u.id in ('
            "select user_id from comment where submission_id in (select id from submission where edict_id = :eid) "
            "union select user_id from favorites where submission_id in (select id from submission where edict_id = :eid) "
            "union select user_id from labels where submission_id in (select id from submission where edict_id = :eid) "
            "union select user_id from private_note where submission_id in (select id from submission where edict_id = :eid)"
            ") order by u.id"
        ),
        {"eid": edict_id},
    )
    return [dict(r) for r in result.mappings()]


def _admin_session():
    from db import SessionLocal

    return SessionLocal()


def _forms_session():
    from db import FormsSessionLocal

    return FormsSessionLocal()


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    del user
    await _get_edict_or_404(db, edict_id)
    job_id, _ = reports.new_job("csv")

    async def run():
        async with _admin_session() as session:
            async with _forms_session() as forms_session:
                edict = await submission_service.get_edict(session, edict_id)
                await reports.generate_csv(session, forms_session, edict)

    background_tasks.add_task(run)
    return {"job_id": job_id, "status": "processing"}


def _serve_job(job_id: str, media_type: str):
    path = reports.JOBS.get(job_id)
    if path is None or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path, "rb") as f:
        content = f.read()
    os.remove(path)
    del reports.JOBS[job_id]
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{os.path.basename(path)}"'},
    )


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _serve_job(job_id, "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _serve_job(job_id, "text/csv")
