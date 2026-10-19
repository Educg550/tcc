import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user, require_admin
from database import get_db, get_forms_db
from services import forms_service, reports
from services import submission_builder as sb

router = APIRouter(tags=["edicts"])

PHASES = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
# associação vigente no original: fase -> data recebida na criação/edição
PHASE_DATE_KEYS = {
    "inscricoes": "date_application",
    "homologacao": "date_evaluation",
    "avaliacao": "date_verification",
    "encerrado": "date_closed",
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


class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


def _validate_dates(payload: dict):
    ordered = [
        payload["date_application"],
        payload["date_evaluation"],
        payload["date_verification"],
        payload["date_closed"],
    ]
    if any(a >= b for a, b in zip(ordered, ordered[1:])):
        raise HTTPException(status_code=422, detail="Datas fora de ordem cronológica")


def _parse_date(value: str):
    try:
        from datetime import date as _date

        return _date.fromisoformat(str(value))
    except ValueError:
        raise HTTPException(status_code=422, detail="Data inválida")


async def _get_edict_or_404(db: AsyncSession, edict_id: int):
    edict = await sb.get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


async def _set_phase_dates(db: AsyncSession, edict_id: int, payload: dict):
    for phase, key in PHASE_DATE_KEYS.items():
        value = payload[key]
        closed = value.date() if isinstance(value, datetime) else _parse_date(value)
        await db.execute(
            text(
                "update edict_phase set closed_date = :d where edict_id = :eid and phase = :p"
            ),
            {"d": closed, "eid": edict_id, "p": phase},
        )


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = "select id, title, year, semester, type, is_open, closed_date from edict where true"
    params: dict[str, Any] = {}
    if type is not None:
        query += " and type = :type"
        params["type"] = type
    if is_open is not None:
        query += " and is_open = :is_open"
        params["is_open"] = is_open
    query += " order by closed_date desc, id desc"
    rows = await db.execute(text(query), params)
    return [
        {
            "id": r.id,
            "title": r.title,
            "year": r.year,
            "semester": r.semester,
            "edict_type": r.type,
            "is_open": r.is_open,
            "closed_date": r.closed_date,
        }
        for r in rows
    ]


@router.post("/edicts")
async def create_edict(
    payload: InsertEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    _validate_dates(payload.model_dump())
    row = await db.execute(
        text(
            "insert into edict (title, description, candidate_forms, recommenders_forms, "
            "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
            "values (:title, :description, :candidate_forms, :recommenders_forms, :closed_date, "
            ":year, :semester, :type, 'inscricoes', :is_open, now(), now(), :user_id) returning id"
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
            "user_id": user["id"],
        },
    )
    edict_id = row.first().id
    for phase in PHASES:
        key = PHASE_DATE_KEYS[phase]
        value = getattr(payload, key)
        await db.execute(
            text(
                "insert into edict_phase (edict_id, closed_date, phase) values (:eid, :d, :p)"
            ),
            {"eid": edict_id, "d": value.date(), "p": phase},
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
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    phases = await db.execute(
        text(
            "select id, phase, closed_date from edict_phase where edict_id = :eid order by id"
        ),
        {"eid": edict_id},
    )
    slots = await db.execute(
        text(
            "select slots from user_edict_slots where user_id = :uid and edict_id = :eid"
        ),
        {"uid": user["id"], "eid": edict_id},
    )
    slots_row = slots.first()
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": str(edict["candidate_forms"] or ""),
        "recommender_form_id": str(edict["recommenders_forms"] or ""),
        "description": edict["description"] or "",
        "closed_date": edict["closed_date"],
        "created_at": edict["created_at"],
        "updated_at": edict["updated_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "phase": edict["phase"],
        "phases": [dict(r._mapping) for r in phases],
        "slots": str(slots_row[0]) if slots_row and slots_row[0] is not None else "0",
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    _validate_dates(payload.model_dump())
    try:
        year = int(payload.year)
        semester = int(payload.semester)
    except ValueError:
        raise HTTPException(status_code=422, detail="Ano/semestre inválidos")
    await db.execute(
        text(
            "update edict set title = :t, description = :d, year = :y, semester = :s, "
            "type = :ty, closed_date = :cd, updated_at = now() where id = :eid"
        ),
        {
            "t": payload.title,
            "d": payload.description,
            "y": year,
            "s": semester,
            "ty": payload.edict_type,
            "cd": payload.date_closed.date(),
            "eid": edict_id,
        },
    )
    await _set_phase_dates(db, edict_id, payload.model_dump())
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
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    closed = _parse_date(payload.closed_date)
    await db.execute(
        text("update edict set closed_date = :cd, updated_at = now() where id = :eid"),
        {"cd": closed, "eid": edict_id},
    )
    await db.execute(
        text(
            "update edict_phase set closed_date = :d where edict_id = :eid and phase = 'encerrado'"
        ),
        {"d": closed, "eid": edict_id},
    )
    await db.commit()
    return {"closed_date": closed}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    row = await db.execute(
        text("select id, phase from edict_phase where id = :pid and edict_id = :eid"),
        {"pid": payload.id, "eid": edict_id},
    )
    row = row.first()
    if not row:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    await db.execute(
        text("update edict set phase = :p, updated_at = now() where id = :eid"),
        {"p": row.phase, "eid": edict_id},
    )
    await db.commit()

    form_id = sb._to_int(edict.get("candidate_forms"))
    if form_id is not None:
        await forms_service.change_form_phase(
            fdb, form_id, PHASE_TO_FORMS.get(row.phase, "Completed")
        )
    return {"id": row.id, "label": row.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital já encerrado")
    await db.execute(
        text("update edict set is_open = false, updated_at = now() where id = :eid"),
        {"eid": edict_id},
    )
    await db.commit()
    return {"message": "Edital encerrado"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    await db.execute(text("delete from edict where id = :eid"), {"eid": edict_id})
    await db.commit()
    return {"message": "Edital removido"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user=Depends(get_current_user),
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
            raise HTTPException(status_code=422, detail="Quantidade inválida")
        if amount < 0:
            amount = 0
    existing = await db.execute(
        text(
            "select id from user_edict_slots where user_id = :uid and edict_id = :eid"
        ),
        {"uid": user["id"], "eid": edict_id},
    )
    if existing.first():
        await db.execute(
            text("update user_edict_slots set slots = :s where user_id = :uid and edict_id = :eid"),
            {"s": amount, "uid": user["id"], "eid": edict_id},
        )
    else:
        await db.execute(
            text(
                "insert into user_edict_slots (user_id, edict_id, slots) values (:uid, :eid, :s)"
            ),
            {"uid": user["id"], "eid": edict_id, "s": amount},
        )
    await db.commit()
    return {"amount": str(amount)}


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await _get_edict_or_404(db, edict_id)
    try:
        await sb.sync_submissions(db, fdb, edict)
    except Exception:
        logging.exception("falha ao sincronizar inscrições do edital %s", edict_id)
        await db.rollback()
    rows = await db.execute(
        text("select * from submission where edict_id = :eid order by id"),
        {"eid": edict_id},
    )
    submissions = []
    for row in rows:
        sub = dict(row._mapping)
        if stats is not None and sub["stats"] != stats:
            continue
        try:
            item = await sb.build_submission_view(db, fdb, edict, sub, user)
        except Exception:
            logging.exception("falha ao montar a inscrição %s", sub["id"])
            await db.rollback()
            item = sb.fallback_view(sub)
        if only_favorites and not item["is_favorite"]:
            continue
        submissions.append(item)
    return {"submissions": submissions}


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    payload: SectionsDocument | None = None,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    options = (payload or SectionsDocument()).model_dump()
    if mode == "pdf":
        job_id = reports.start_pdf_job(edict_id, options)
        return {"job_id": job_id, "status": "processing"}
    return await reports._interactors(edict_id)


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _get_edict_or_404(db, edict_id)
    job_id = reports.start_csv_job(edict_id)
    return {"job_id": job_id, "status": "processing"}


def _serve_job(job_id: str, media_type: str):
    import os

    path = reports.get_job_path(job_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    reports.pop_job(job_id)

    def cleanup():
        try:
            os.remove(path)
        except OSError:
            pass

    return FileResponse(path, media_type=media_type, background=BackgroundTask(cleanup))


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _serve_job(job_id, "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _serve_job(job_id, "text/csv")


# ---------------------------------------------------------------------------
# Mapeamentos de formulários (candidates / recommenders)
# ---------------------------------------------------------------------------


async def _validate_mapping_tree(fdb: AsyncSession, form_id: int, version: int, tree):
    sections = await forms_service.select_sections(fdb, form_id, version)
    valid = set()
    for section in sections:
        fields = await forms_service.select_fields(fdb, section["id"], version)
        for field in fields:
            valid.add((section["id"], field["id"]))

    def walk(node):
        if node is None:
            return
        if sb._is_leaf(node):
            if (node["section"], node["field"]) not in valid:
                raise HTTPException(
                    status_code=422, detail="Referência de seção/campo inválida"
                )
        elif isinstance(node, dict):
            for child in node.values():
                walk(child)

    walk(tree)


def _mapping_dict(row):
    return {
        "id": row["id"],
        "edict_id": row["edict_id"],
        "form_type": row["form_type"],
        "user_id": row["user_id"],
        "form_id": row["form_id"],
        "form_version": row["form_version"],
        "mapping": row["mapping"],
        "is_active": row["is_active"],
    }


async def _create_mapping(db, fdb, edict_id, form_type, version, tree, user):
    edict = await _get_edict_or_404(db, edict_id)
    form_key = "candidate_forms" if form_type == "candidate" else "recommenders_forms"
    form_id = sb._to_int(edict.get(form_key))
    if form_id is None:
        raise HTTPException(status_code=422, detail="Formulário não configurado")
    await _validate_mapping_tree(fdb, form_id, version, tree)
    existing = await sb.get_mapping(db, edict_id, form_type, version)
    if existing:
        raise HTTPException(status_code=409, detail="Mapeamento já existe")
    row = await db.execute(
        text(
            "insert into edict_form_mappings (edict_id, form_type, mapping, is_active, "
            "form_id, user_id, form_version) values (:eid, :ft, cast(:mapping as jsonb), "
            "true, :fid, :uid, :v) returning id, edict_id, form_type, mapping, is_active, "
            "form_id, user_id, form_version"
        ),
        {
            "eid": edict_id,
            "ft": form_type,
            "mapping": json.dumps(tree),
            "fid": str(form_id),
            "uid": user["id"],
            "v": version,
        },
    )
    await db.commit()
    return _mapping_dict(dict(row.first()._mapping))


async def _update_mapping(db, fdb, edict_id, form_type, version, mapping_id, tree):
    edict = await _get_edict_or_404(db, edict_id)
    form_key = "candidate_forms" if form_type == "candidate" else "recommenders_forms"
    form_id = sb._to_int(edict.get(form_key))
    if form_id is not None:
        await _validate_mapping_tree(fdb, form_id, version, tree)
    row = await db.execute(
        text(
            "select id from edict_form_mappings where id = :mid and edict_id = :eid "
            "and form_type = :ft and form_version = :v"
        ),
        {"mid": mapping_id, "eid": edict_id, "ft": form_type, "v": version},
    )
    if not row.first():
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    await db.execute(
        text(
            "update edict_form_mappings set mapping = cast(:mapping as jsonb) "
            "where id = :mid"
        ),
        {"mapping": json.dumps(tree), "mid": mapping_id},
    )
    await db.commit()
    return {"message": "Mapping updated successfully"}


async def _delete_mapping(db, edict_id, form_type, version, mapping_id):
    await _get_edict_or_404(db, edict_id)
    row = await db.execute(
        text(
            "select id from edict_form_mappings where id = :mid and edict_id = :eid "
            "and form_type = :ft and form_version = :v"
        ),
        {"mid": mapping_id, "eid": edict_id, "ft": form_type, "v": version},
    )
    if not row.first():
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    await db.execute(text("delete from edict_form_mappings where id = :mid"), {"mid": mapping_id})
    await db.commit()
    return {"message": "Mapping deleted successfully"}


async def _unmapped_versions(db, edict_id, form_type):
    await _get_edict_or_404(db, edict_id)
    rows = await db.execute(
        text(
            "select distinct s.candidate_form_version from submission s where s.edict_id = :eid "
            "and not exists (select 1 from edict_form_mappings m where m.edict_id = s.edict_id "
            "and m.form_type = :ft and m.form_version = s.candidate_form_version) "
            "order by s.candidate_form_version"
        ),
        {"eid": edict_id, "ft": form_type},
    )
    return [r[0] for r in rows]


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
async def create_candidate_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "candidate", version, tree, user)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
async def create_recommender_form_mapping(
    edict_id: int,
    version: int,
    tree: dict,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _create_mapping(db, fdb, edict_id, "recommender", version, tree, user)


@router.get("/edicts/{edict_id}/candidates/mappings")
async def get_candidate_mappings(
    edict_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await sb.get_mappings(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/mappings")
async def get_recommender_mappings(
    edict_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await sb.get_mappings(db, edict_id, "recommender")


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def update_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    tree: dict,
    user=Depends(require_admin),
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
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await _update_mapping(db, fdb, edict_id, "recommender", version, mapping_id, tree)


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
async def delete_candidate_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _delete_mapping(db, edict_id, "candidate", version, mapping_id)


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
async def delete_recommender_mapping(
    edict_id: int,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _delete_mapping(db, edict_id, "recommender", version, mapping_id)


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
async def get_candidates_unmapped_versions(
    edict_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _unmapped_versions(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
async def get_recommenders_unmapped_versions(
    edict_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _unmapped_versions(db, edict_id, "recommender")
