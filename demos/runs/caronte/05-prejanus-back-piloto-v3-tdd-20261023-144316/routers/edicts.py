import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

import services.forms_db as forms_db
import services.reports as reports
from auth import get_current_user, require_admin
from database import SessionLocal
from services.mappings import validate_mapping

router = APIRouter(tags=["edicts"])

PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}

# Associação vigente entre as datas recebidas e as fases.
DATE_PHASE_ASSOCIATION = [
    ("date_application", "inscricoes"),
    ("date_evaluation", "homologacao"),
    ("date_verification", "avaliacao"),
    ("date_closed", "encerrado"),
]


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
    closed_date: date


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


def _validate_dates(payload) -> None:
    ordered = [
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    ]
    for a, b in zip(ordered, ordered[1:]):
        if not a < b:
            raise HTTPException(
                status_code=400, detail="Datas fora de ordem cronológica"
            )


async def _get_edict(edict_id: int) -> dict:
    async with SessionLocal() as s:
        rows = await s.execute(
            text("select * from edict where id = :id"), {"id": edict_id}
        )
        r = rows.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        return dict(r._mapping)


def _edict_list_item(e: dict) -> dict:
    return {
        "id": e["id"],
        "title": e["title"],
        "year": e["year"],
        "semester": e["semester"],
        "edict_type": e["type"],
        "is_open": e["is_open"],
    }


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user: dict = Depends(get_current_user),
):
    async with SessionLocal() as s:
        sql = "select * from edict where 1=1"
        params: dict = {}
        if type is not None:
            sql += " and type = :type"
            params["type"] = type
        if is_open is not None:
            sql += " and is_open = :is_open"
            params["is_open"] = is_open
        sql += " order by closed_date desc, id desc"
        rows = await s.execute(text(sql), params)
        return [_edict_list_item(dict(r._mapping)) for r in rows.fetchall()]


@router.get("/edicts/{edict_id}")
async def get_edict(edict_id: int, user: dict = Depends(get_current_user)):
    e = await _get_edict(edict_id)
    async with SessionLocal() as s:
        phases = await s.execute(
            text(
                "select id, closed_date, phase from edict_phase where edict_id = :e"
                " order by id"
            ),
            {"e": edict_id},
        )
        phase_rows = [
            {
                "id": r.id,
                "closed_date": r.closed_date.isoformat() if r.closed_date else None,
                "phase": r.phase,
            }
            for r in phases.fetchall()
        ]
        slots = await s.execute(
            text(
                "select slots from user_edict_slots where user_id = :u and edict_id = :e"
            ),
            {"u": user["id"], "e": edict_id},
        )
        slot_row = slots.fetchone()
    return {
        "id": e["id"],
        "title": e["title"],
        "candidate_form_id": str(e["candidate_forms"]),
        "recommender_form_id": str(e["recommenders_forms"]),
        "description": e["description"] or "",
        "closed_date": e["closed_date"].isoformat() if e["closed_date"] else None,
        "created_at": e["created_at"].isoformat() if e["created_at"] else None,
        "year": e["year"],
        "semester": e["semester"],
        "type": e["type"],
        "is_open": e["is_open"],
        "updated_at": e["updated_at"].isoformat() if e["updated_at"] else None,
        "phase": e["phase"],
        "phases": phase_rows,
        "slots": str(slot_row.slots) if slot_row and slot_row.slots is not None else "0",
    }


@router.post("/edicts")
async def create_edict(
    payload: InsertEdictSchema, user: dict = Depends(get_current_user)
):
    require_admin(user)
    _validate_dates(payload)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "insert into edict (title, description, candidate_forms,"
                " recommenders_forms, closed_date, year, semester, type, phase,"
                " is_open, created_at, updated_at, user_id)"
                " values (:title, :description, :cf, :rf, :closed, :year, :semester,"
                " :type, 'inscricoes', :is_open, now(), now(), :uid) returning id"
            ),
            {
                "title": payload.title,
                "description": payload.description,
                "cf": payload.candidate_forms,
                "rf": payload.recommenders_forms,
                "closed": payload.date_closed.date(),
                "year": payload.year,
                "semester": payload.semester,
                "type": payload.edict_type,
                "is_open": payload.is_open,
                "uid": user["id"],
            },
        )
        edict_id = rows.fetchone().id
        for date_attr, phase in DATE_PHASE_ASSOCIATION:
            await s.execute(
                text(
                    "insert into edict_phase (edict_id, closed_date, phase)"
                    " values (:e, :d, :p)"
                ),
                {"e": edict_id, "d": getattr(payload, date_attr).date(), "p": phase},
            )
        await s.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application.isoformat(),
        "date_verification": payload.date_verification.isoformat(),
        "date_evaluation": payload.date_evaluation.isoformat(),
        "date_closed": payload.date_closed.isoformat(),
        "id": edict_id,
        "closed_date": payload.date_closed.date().isoformat(),
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int, payload: EditEdictSchema, user: dict = Depends(get_current_user)
):
    require_admin(user)
    await _get_edict(edict_id)
    _validate_dates(payload)
    async with SessionLocal() as s:
        await s.execute(
            text(
                "update edict set title = :title, description = :description,"
                " year = :year, semester = :semester, type = :type, closed_date = :closed,"
                " updated_at = now() where id = :id"
            ),
            {
                "title": payload.title,
                "description": payload.description,
                "year": int(payload.year),
                "semester": int(payload.semester),
                "type": payload.edict_type,
                "closed": payload.date_closed.date(),
                "id": edict_id,
            },
        )
        for date_attr, phase in DATE_PHASE_ASSOCIATION:
            await s.execute(
                text(
                    "update edict_phase set closed_date = :d"
                    " where edict_id = :e and phase = :p"
                ),
                {"d": getattr(payload, date_attr).date(), "e": edict_id, "p": phase},
            )
        await s.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": payload.date_application.isoformat(),
        "date_verification": payload.date_verification.isoformat(),
        "date_evaluation": payload.date_evaluation.isoformat(),
        "date_closed": payload.date_closed.isoformat(),
    }


@router.post("/edicts/{edict_id}/edit-date")
async def edit_edict_date(
    edict_id: int, payload: EditEdictDateSchema, user: dict = Depends(get_current_user)
):
    require_admin(user)
    await _get_edict(edict_id)
    async with SessionLocal() as s:
        await s.execute(
            text("update edict set closed_date = :d, updated_at = now() where id = :id"),
            {"d": payload.closed_date, "id": edict_id},
        )
        await s.execute(
            text(
                "update edict_phase set closed_date = :d"
                " where edict_id = :e and phase = 'encerrado'"
            ),
            {"d": payload.closed_date, "e": edict_id},
        )
        await s.commit()
    return {"closed_date": payload.closed_date.isoformat()}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: int, payload: AdvancePhaseEdictSchema, user: dict = Depends(get_current_user)
):
    require_admin(user)
    e = await _get_edict(edict_id)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select id, phase from edict_phase where id = :id and edict_id = :e"
            ),
            {"id": payload.id, "e": edict_id},
        )
        r = rows.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Fase não encontrada")
        await s.execute(
            text("update edict set phase = :p, updated_at = now() where id = :id"),
            {"p": r.phase, "id": edict_id},
        )
        await s.commit()
    if e["candidate_forms"] is not None:
        await forms_db.change_form_phase(
            int(e["candidate_forms"]), PHASE_TO_FORMS[r.phase]
        )
    return {"id": r.id, "label": r.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int, payload: CloseEdictSchema, user: dict = Depends(get_current_user)
):
    require_admin(user)
    e = await _get_edict(edict_id)
    if not e["is_open"]:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    async with SessionLocal() as s:
        await s.execute(
            text("update edict set is_open = false, updated_at = now() where id = :id"),
            {"id": edict_id},
        )
        await s.commit()
    return {"message": "Edital encerrado com sucesso"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(edict_id: int, user: dict = Depends(get_current_user)):
    require_admin(user)
    await _get_edict(edict_id)
    async with SessionLocal() as s:
        await s.execute(text("delete from edict where id = :id"), {"id": edict_id})
        await s.commit()
    return {"message": "Edital removido com sucesso"}


def _form_type(tipo: str) -> str:
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(status_code=422, detail="Tipo de mapeamento inválido")


def _mapping_response(m: dict) -> dict:
    return {
        "id": m["id"],
        "edict_id": m["edict_id"],
        "form_type": m["form_type"],
        "user_id": m["user_id"],
        "form_id": m["form_id"],
        "form_version": m["form_version"],
        "mapping": m["mapping"],
        "is_active": m["is_active"],
    }


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    payload: dict,
    user: dict = Depends(get_current_user),
):
    require_admin(user)
    e = await _get_edict(edict_id)
    form_type = _form_type(tipo)
    form_id = int(e["candidate_forms"] if form_type == "candidate" else e["recommenders_forms"])
    await validate_mapping(form_id, version, payload)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select id from edict_form_mappings where edict_id = :e"
                " and form_type = :t and form_version = :v"
            ),
            {"e": edict_id, "t": form_type, "v": version},
        )
        if rows.fetchone():
            raise HTTPException(
                status_code=409, detail="Mapeamento já existe para esta versão"
            )
        rows = await s.execute(
            text(
                "insert into edict_form_mappings (edict_id, form_type, mapping,"
                " is_active, form_id, user_id, form_version)"
                " values (:e, :t, :m::jsonb, true, :f, :u, :v) returning *"
            ),
            {
                "e": edict_id,
                "t": form_type,
                "m": _mapping_json(payload),
                "f": str(form_id),
                "u": user["id"],
                "v": version,
            },
        )
        await s.commit()
        return _mapping_response(dict(rows.fetchone()._mapping))


def _mapping_json(payload) -> str:
    import json

    return json.dumps(payload)


@router.get("/edicts/{edict_id}/{tipo}/mappings")
async def list_mappings(edict_id: int, tipo: str, user: dict = Depends(get_current_user)):
    form_type = _form_type(tipo)
    await _get_edict(edict_id)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select * from edict_form_mappings where edict_id = :e"
                " and form_type = :t order by id"
            ),
            {"e": edict_id, "t": form_type},
        )
        return [_mapping_response(dict(r._mapping)) for r in rows.fetchall()]


async def _find_mapping(edict_id, form_type, version, mapping_id) -> dict:
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select * from edict_form_mappings where id = :id and edict_id = :e"
                " and form_type = :t and form_version = :v"
            ),
            {"id": mapping_id, "e": edict_id, "t": form_type, "v": version},
        )
        r = rows.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
        return dict(r._mapping)


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    payload: dict,
    user: dict = Depends(get_current_user),
):
    require_admin(user)
    e = await _get_edict(edict_id)
    form_type = _form_type(tipo)
    await _find_mapping(edict_id, form_type, version, mapping_id)
    form_id = int(e["candidate_forms"] if form_type == "candidate" else e["recommenders_forms"])
    await validate_mapping(form_id, version, payload)
    async with SessionLocal() as s:
        await s.execute(
            text(
                "update edict_form_mappings set mapping = :m::jsonb where id = :id"
            ),
            {"m": _mapping_json(payload), "id": mapping_id},
        )
        await s.commit()
    return {"message": "Mapeamento atualizado com sucesso"}


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    user: dict = Depends(get_current_user),
):
    require_admin(user)
    form_type = _form_type(tipo)
    await _find_mapping(edict_id, form_type, version, mapping_id)
    async with SessionLocal() as s:
        await s.execute(
            text("delete from edict_form_mappings where id = :id"), {"id": mapping_id}
        )
        await s.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def unmapped_versions(edict_id: int, tipo: str, user: dict = Depends(get_current_user)):
    form_type = _form_type(tipo)
    await _get_edict(edict_id)
    column = (
        "candidate_form_version" if form_type == "candidate" else "recommender_form_version"
    )
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                f"select distinct {column} as v from submission where edict_id = :e"
                f" and {column} not in (select form_version from edict_form_mappings"
                f" where edict_id = :e and form_type = :t)"
            ),
            {"e": edict_id, "t": form_type},
        )
        return [r.v for r in rows.fetchall()]


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int, payload: SlotsSchema, user: dict = Depends(get_current_user)
):
    await _get_edict(edict_id)
    raw = (payload.amount or "").strip()
    if raw == "":
        amount = 0
    else:
        try:
            amount = int(raw)
        except ValueError:
            raise HTTPException(status_code=422, detail="Quantidade inválida")
        if amount < 0:
            amount = 0
    async with SessionLocal() as s:
        await s.execute(
            text(
                "insert into user_edict_slots (user_id, edict_id, slots)"
                " values (:u, :e, :s)"
                " on conflict (user_id, edict_id) do update set slots = :s"
            ),
            {"u": user["id"], "e": edict_id, "s": amount},
        )
        await s.commit()
    return {"amount": str(amount)}


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    payload: dict | None = None,
    user: dict = Depends(get_current_user),
):
    require_admin(user)
    await _get_edict(edict_id)
    options = payload or {}
    if mode == "pdf":
        job_id = uuid.uuid4().hex
        reports.schedule_pdf(job_id, edict_id, options)
        return {"job_id": job_id, "status": "processing"}
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                'select distinct u.id, u.name, u.email from "user" u where u.id in ('
                " select user_id from comment where submission_id in"
                " (select id from submission where edict_id = :e)"
                " union select user_id from favorites where submission_id in"
                " (select id from submission where edict_id = :e)"
                " union select user_id from labels where submission_id in"
                " (select id from submission where edict_id = :e)"
                " union select user_id from private_note where submission_id in"
                " (select id from submission where edict_id = :e))"
                " order by u.id"
            ),
            {"e": edict_id},
        )
        return [
            {"id": r.id, "name": r.name, "email": r.email} for r in rows.fetchall()
        ]


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(edict_id: int, user: dict = Depends(get_current_user)):
    require_admin(user)
    await _get_edict(edict_id)
    job_id = uuid.uuid4().hex
    reports.schedule_csv(job_id, edict_id)
    return {"job_id": job_id, "status": "processing"}


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return reports.serve_report(job_id, "pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return reports.serve_report(job_id, "csv")
