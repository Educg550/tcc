from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from ..auth import current_user, require_admin
from ..db import fetch, fetch_one, forms_engine, prejanus_engine, run
from ..schemas import (AdvancePhaseEdictSchema, CloseEdictSchema, EditEdictDateSchema,
                       EditEdictSchema, InsertEdictSchema, SectionsDocument, SlotsSchema)
from ..services import forms_service, reports, submissions_service

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASE_DATES = {
    "inscricoes": "date_application",
    "avaliacao": "date_verification",
    "homologacao": "date_evaluation",
    "encerrado": "date_closed",
}
FORMS_PHASE = {"inscricoes": "Registration", "homologacao": "Approval"}
KINDS = {"candidates": "candidate", "recommenders": "recommender"}


async def _get_edict(edict_id: int) -> dict:
    edict = await submissions_service.get_edict(edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


def _validate_dates(dates: dict) -> None:
    ordem = [dates[k] for k in ("date_application", "date_verification", "date_evaluation", "date_closed")]
    if any(a >= b for a, b in zip(ordem, ordem[1:])):
        raise HTTPException(status_code=400, detail="Datas do edital fora de ordem cronológica")


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _serve_job(job_id)


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _serve_job(job_id)


def _serve_job(job_id: str) -> FileResponse:
    entry = reports.pop_job(job_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    path, media_type = entry
    if not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return FileResponse(path, media_type=media_type, filename=Path(path).name,
                        content_disposition_type="inline")


@router.get("")
async def get_all_edicts(type: str | None = None, is_open: bool | None = None,
                         user: dict = Depends(current_user)):
    sql = "SELECT id, title, year, semester, type AS edict_type, is_open FROM edict WHERE 1=1"
    params: dict = {}
    if type is not None:
        sql += " AND type=:type"
        params["type"] = type
    if is_open is not None:
        sql += " AND is_open=:is_open"
        params["is_open"] = is_open
    sql += " ORDER BY closed_date DESC, id DESC"
    return await fetch(prejanus_engine, sql, params)


@router.post("")
async def create_edict(body: InsertEdictSchema, user: dict = Depends(current_user)):
    require_admin(user)
    _validate_dates(body.model_dump())
    rows = await run(
        prejanus_engine,
        "INSERT INTO edict (title, description, year, semester, type, phase, is_open, "
        "candidate_forms, recommenders_forms, user_id, closed_date, created_at, updated_at) "
        "VALUES (:title, :description, :year, :semester, :type, 'inscricoes', :is_open, "
        ":candidate_forms, :recommenders_forms, :user_id, :closed_date, now(), now()) RETURNING id",
        {"title": body.title, "description": body.description, "year": body.year,
         "semester": body.semester, "type": body.edict_type, "is_open": body.is_open,
         "candidate_forms": body.candidate_forms, "recommenders_forms": body.recommenders_forms,
         "user_id": user["id"], "closed_date": body.date_closed.date()},
    )
    edict_id = rows[0]["id"]
    for phase, attr in PHASE_DATES.items():
        await run(
            prejanus_engine,
            "INSERT INTO edict_phase (edict_id, closed_date, phase) VALUES (:e, :d, :p)",
            {"e": edict_id, "d": getattr(body, attr).date(), "p": phase},
        )
    return {
        "id": edict_id, "title": body.title, "description": body.description,
        "year": body.year, "semester": body.semester, "edict_type": body.edict_type,
        "is_open": body.is_open, "candidate_forms": int(body.candidate_forms),
        "recommenders_forms": int(body.recommenders_forms),
        "date_application": body.date_application, "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation, "date_closed": body.date_closed,
        "closed_date": body.date_closed,
    }


@router.get("/{edict_id}")
async def get_edict_by_id(edict_id: int, user: dict = Depends(current_user)):
    edict = await _get_edict(edict_id)
    phases = await fetch(
        prejanus_engine,
        "SELECT id, closed_date, phase FROM edict_phase WHERE edict_id=:e ORDER BY id",
        {"e": edict_id},
    )
    slot = await fetch_one(
        prejanus_engine,
        "SELECT slots FROM user_edict_slots WHERE user_id=:u AND edict_id=:e",
        {"u": user["id"], "e": edict_id},
    )
    return {
        "id": edict["id"], "title": edict["title"],
        "candidate_form_id": edict["candidate_forms"],
        "recommender_form_id": edict["recommenders_forms"],
        "description": edict["description"], "closed_date": edict["closed_date"],
        "created_at": edict["created_at"], "year": edict["year"], "semester": edict["semester"],
        "type": edict["type"], "is_open": edict["is_open"], "updated_at": edict["updated_at"],
        "phase": edict["phase"], "phases": phases,
        "slots": str(slot["slots"]) if slot and slot["slots"] is not None else "0",
    }


@router.post("/{edict_id}/edit")
async def edit_edict(edict_id: int, body: EditEdictSchema, user: dict = Depends(current_user)):
    require_admin(user)
    await _get_edict(edict_id)
    _validate_dates(body.model_dump())
    await run(
        prejanus_engine,
        "UPDATE edict SET title=:t, description=:d, year=:y, semester=:s, type=:ty, "
        "closed_date=:c, updated_at=now() WHERE id=:i",
        {"t": body.title, "d": body.description, "y": int(body.year), "s": int(body.semester),
         "ty": body.edict_type, "c": body.date_closed.date(), "i": edict_id},
    )
    for phase, attr in PHASE_DATES.items():
        await run(
            prejanus_engine,
            "UPDATE edict_phase SET closed_date=:d WHERE edict_id=:e AND phase=:p",
            {"d": getattr(body, attr).date(), "e": edict_id, "p": phase},
        )
    return body.model_dump()


@router.post("/{edict_id}/edit-date")
async def edit_edict_date(edict_id: int, body: EditEdictDateSchema, user: dict = Depends(current_user)):
    require_admin(user)
    await _get_edict(edict_id)
    await run(
        prejanus_engine,
        "UPDATE edict SET closed_date=:c, updated_at=now() WHERE id=:i",
        {"c": body.closed_date, "i": edict_id},
    )
    await run(
        prejanus_engine,
        "UPDATE edict_phase SET closed_date=:c WHERE edict_id=:e AND phase='encerrado'",
        {"c": body.closed_date, "e": edict_id},
    )
    return {"closed_date": body.closed_date.isoformat()}


@router.post("/{edict_id}/advance-phase")
async def advance_edict(edict_id: int, body: AdvancePhaseEdictSchema, user: dict = Depends(current_user)):
    require_admin(user)
    edict = await _get_edict(edict_id)
    phase = await fetch_one(
        prejanus_engine,
        "SELECT id, phase, closed_date FROM edict_phase WHERE id=:i AND edict_id=:e",
        {"i": body.id, "e": edict_id},
    )
    if phase is None:
        raise HTTPException(status_code=404, detail="Fase não encontrada")
    await run(
        prejanus_engine,
        "UPDATE edict SET phase=:p, updated_at=now() WHERE id=:i",
        {"p": phase["phase"], "i": edict_id},
    )
    await forms_service.set_form_phase(
        int(edict["candidate_forms"]), FORMS_PHASE.get(phase["phase"], "Completed")
    )
    return {"id": phase["id"], "label": phase["phase"]}


@router.patch("/{edict_id}/close")
async def close_edict(edict_id: int, body: CloseEdictSchema, user: dict = Depends(current_user)):
    require_admin(user)
    edict = await _get_edict(edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital já está fechado")
    await run(
        prejanus_engine,
        "UPDATE edict SET is_open=false, updated_at=now() WHERE id=:i", {"i": edict_id}
    )
    return {"message": "Edital fechado"}


@router.delete("/{edict_id}/remove")
async def remove_edict(edict_id: int, user: dict = Depends(current_user)):
    require_admin(user)
    await _get_edict(edict_id)
    await run(prejanus_engine, "DELETE FROM edict WHERE id=:i", {"i": edict_id})
    return {"message": "Edital removido"}


@router.post("/{edict_id}/slots")
async def set_user_slots(edict_id: int, body: SlotsSchema, user: dict = Depends(current_user)):
    await _get_edict(edict_id)
    try:
        amount = int(body.amount)
    except (TypeError, ValueError):
        amount = 0
    if amount < 0:
        amount = 0
    await run(
        prejanus_engine,
        "INSERT INTO user_edict_slots (user_id, edict_id, slots) VALUES (:u, :e, :s) "
        "ON CONFLICT (user_id, edict_id) DO UPDATE SET slots=:s",
        {"u": user["id"], "e": edict_id, "s": amount},
    )
    return {"amount": str(amount)}


@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(edict_id: int, stats: str | None = None,
                                         only_favorites: bool = False,
                                         user: dict = Depends(current_user)):
    edict = await _get_edict(edict_id)
    await submissions_service.ensure_submissions(edict)
    await submissions_service.associate_recommenders(edict)
    subs = await fetch(
        prejanus_engine, "SELECT * FROM submission WHERE edict_id=:e ORDER BY id", {"e": edict_id}
    )
    if stats is not None:
        subs = [s for s in subs if s["stats"] == stats]
    if only_favorites:
        favs = {
            r["submission_id"]
            for r in await fetch(
                prejanus_engine,
                "SELECT submission_id FROM favorites WHERE user_id=:u",
                {"u": user["id"]},
            )
        }
        subs = [s for s in subs if s["id"] in favs]
    return {"submissions": [await submissions_service.build_payload(s, user) for s in subs]}


@router.post("/{edict_id}/interactors_list")
async def interactors_list(edict_id: int, mode: str = "plain_text",
                           payload: SectionsDocument | None = None,
                           user: dict = Depends(current_user)):
    require_admin(user)
    edict = await _get_edict(edict_id)
    options = payload or SectionsDocument()
    inter = await reports.interactors(edict_id)
    if mode != "pdf":
        return inter
    await submissions_service.ensure_submissions(edict)
    job_id = await reports.build_pdf_report(edict, options, inter)
    return {"status": "processing", "job_id": job_id}


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(edict_id: int, user: dict = Depends(current_user)):
    require_admin(user)
    edict = await _get_edict(edict_id)
    await submissions_service.ensure_submissions(edict)
    job_id = await reports.build_pairing_csv(edict)
    return {"status": "processing", "job_id": job_id}


async def _mapping_form_id(edict: dict, form_type: str) -> int:
    coluna = "candidate_forms" if form_type == "candidate" else "recommenders_forms"
    return int(edict[coluna])


async def _validate_mapping(form_id: int, version: int, tree: dict) -> None:
    fields = await fetch(
        forms_engine,
        "SELECT id, section_id FROM form_field WHERE form_id=:f AND version=:v",
        {"f": form_id, "v": version},
    )
    if not fields:
        fields = await fetch(
            forms_engine, "SELECT id, section_id FROM form_field WHERE form_id=:f", {"f": form_id}
        )
    validos = {(f["section_id"], f["id"]) for f in fields}

    def check(node):
        if not isinstance(node, dict):
            return
        for value in node.values():
            if value is None:
                continue
            if isinstance(value, dict):
                if isinstance(value.get("field"), int) and isinstance(value.get("section"), int):
                    if (value["section"], value["field"]) not in validos:
                        raise HTTPException(status_code=422, detail="Referência inválida no mapeamento")
                else:
                    check(value)

    check(tree)


@router.post("/{edict_id}/{kind}/mappings/versions/{version}/")
async def create_mapping(edict_id: int, kind: str, version: int, payload: dict,
                         user: dict = Depends(current_user)):
    require_admin(user)
    form_type = KINDS.get(kind)
    if form_type is None:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento desconhecido")
    edict = await _get_edict(edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    await _validate_mapping(form_id, version, payload)
    import json as _json
    rows = await run(
        prejanus_engine,
        "INSERT INTO edict_form_mappings (edict_id, form_type, mapping, is_active, created_at, "
        "form_id, user_id, form_version) VALUES (:e, :t, CAST(:m AS jsonb), true, now(), :f, :u, :v) "
        "RETURNING id, created_at",
        {"e": edict_id, "t": form_type, "m": _json.dumps(payload), "f": str(form_id),
         "u": user["id"], "v": version},
    )
    return {
        "id": rows[0]["id"], "edict_id": edict_id, "form_type": form_type,
        "user_id": user["id"], "is_active": True, "mapping": payload,
        "version": version, "form_id": str(form_id), "created_at": rows[0]["created_at"],
    }


@router.get("/{edict_id}/{kind}/mappings")
async def get_mappings(edict_id: int, kind: str, user: dict = Depends(current_user)):
    form_type = KINDS.get(kind)
    if form_type is None:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento desconhecido")
    await _get_edict(edict_id)
    return await fetch(
        prejanus_engine,
        "SELECT id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, "
        "form_version AS version, form_version FROM edict_form_mappings "
        "WHERE edict_id=:e AND form_type=:t ORDER BY id",
        {"e": edict_id, "t": form_type},
    )


@router.put("/{edict_id}/{kind}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(edict_id: int, kind: str, version: int, mapping_id: int, payload: dict,
                         user: dict = Depends(current_user)):
    require_admin(user)
    form_type = KINDS.get(kind)
    if form_type is None:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento desconhecido")
    await _get_edict(edict_id)
    existing = await fetch_one(
        prejanus_engine,
        "SELECT id FROM edict_form_mappings WHERE id=:i AND edict_id=:e "
        "AND form_type=:t AND form_version=:v",
        {"i": mapping_id, "e": edict_id, "t": form_type, "v": version},
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    edict = await _get_edict(edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    await _validate_mapping(form_id, version, payload)
    import json as _json
    await run(
        prejanus_engine,
        "UPDATE edict_form_mappings SET mapping=CAST(:m AS jsonb) WHERE id=:i AND edict_id=:e "
        "AND form_type=:t AND form_version=:v",
        {"m": _json.dumps(payload), "i": mapping_id, "e": edict_id, "t": form_type, "v": version},
    )
    return {"id": mapping_id, "mapping": payload}


@router.delete("/{edict_id}/{kind}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(edict_id: int, kind: str, version: int, mapping_id: int,
                         user: dict = Depends(current_user)):
    require_admin(user)
    form_type = KINDS.get(kind)
    if form_type is None:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento desconhecido")
    rows = await run(
        prejanus_engine,
        "DELETE FROM edict_form_mappings WHERE id=:i AND edict_id=:e AND form_type=:t "
        "AND form_version=:v RETURNING id",
        {"i": mapping_id, "e": edict_id, "t": form_type, "v": version},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
    return {"message": "Mapping deleted successfully"}


@router.get("/{edict_id}/{kind}/forms/versions/unmapped")
async def get_unmapped_versions(edict_id: int, kind: str, user: dict = Depends(current_user)):
    form_type = KINDS.get(kind)
    if form_type is None:
        raise HTTPException(status_code=404, detail="Tipo de mapeamento desconhecido")
    edict = await _get_edict(edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    versions = set(await forms_service.form_versions(form_id))
    mapped = {
        r["form_version"]
        for r in await fetch(
            prejanus_engine,
            "SELECT DISTINCT form_version FROM edict_form_mappings WHERE edict_id=:e AND form_type=:t",
            {"e": edict_id, "t": form_type},
        )
    }
    return sorted(versions - mapped)
