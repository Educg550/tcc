import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from starlette.background import BackgroundTask

import forms_service as forms
import reports
import submissions_service as service
from config import settings
from db import FormsSession, PrejanusSession
from mapping_utils import validate_tree
from schemas import (AdvancePhaseEdictSchema, CloseEdictSchema, EditEdictDateSchema,
                     EditEdictSchema, InsertEdictSchema, SectionsDocument, SlotsSchema)
from security import get_current_user, require_admin

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASES = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


def _check_chronology(date_application, date_evaluation, date_verification, date_closed):
    if not (date_application < date_evaluation < date_verification < date_closed):
        raise HTTPException(status_code=422, detail="Dates must be in strict chronological order")


async def _get_edict_or_404(psession, edict_id):
    edict = await service.get_edict(psession, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


async def _set_phase_dates(psession, edict_id, date_application, date_evaluation,
                           date_verification, date_closed):
    for phase, date in (("inscricoes", date_application), ("homologacao", date_evaluation),
                        ("avaliacao", date_verification), ("encerrado", date_closed)):
        await psession.execute(text(
            "update edict_phase set closed_date = :d where edict_id = :e and phase = :p"),
            {"d": date.date(), "e": edict_id, "p": phase})


@router.get("")
async def get_all_edicts(type: str | None = None, is_open: bool | None = None,
                         user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        q = "select * from edict where 1=1"
        params = {}
        if type is not None:
            q += " and type = :t"
            params["t"] = type
        if is_open is not None:
            q += " and is_open = :o"
            params["o"] = is_open
        q += " order by closed_date desc"
        rows = (await s.execute(text(q), params)).mappings().all()
    return [{"id": r["id"], "title": r["title"], "year": r["year"], "semester": r["semester"],
             "edict_type": r["type"], "is_open": r["is_open"]} for r in rows]


@router.get("/{edict_id}")
async def get_edict(edict_id: int, user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        edict = await _get_edict_or_404(s, edict_id)
        phases = (await s.execute(text(
            "select id, closed_date, phase from edict_phase where edict_id = :e order by id"),
            {"e": edict_id})).mappings().all()
        slots = (await s.execute(text(
            "select slots from user_edict_slots where edict_id = :e and user_id = :u"),
            {"e": edict_id, "u": user["id"]})).scalar()
    return {
        "id": edict["id"], "title": edict["title"],
        "candidate_form_id": str(edict["candidate_forms"]),
        "recommender_form_id": str(edict["recommenders_forms"]),
        "description": edict["description"] or "",
        "closed_date": edict["closed_date"], "created_at": edict["created_at"],
        "year": edict["year"], "semester": edict["semester"], "type": edict["type"],
        "is_open": edict["is_open"], "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": [{"id": p["id"], "closed_date": p["closed_date"], "phase": p["phase"]} for p in phases],
        "slots": str(slots) if slots is not None else "0",
    }


@router.post("")
async def create_edict(body: InsertEdictSchema, user=Depends(require_admin)):
    _check_chronology(body.date_application, body.date_evaluation,
                      body.date_verification, body.date_closed)
    async with PrejanusSession() as s:
        edict_id = (await s.execute(text(
            "insert into edict (title, description, candidate_forms, recommenders_forms, closed_date, "
            "year, semester, type, phase, is_open, created_at, updated_at, user_id) "
            "values (:t, :d, :cf, :rf, :cd, :y, :sem, :ty, 'inscricoes', :o, now(), now(), :u) returning id"),
            {"t": body.title, "d": body.description, "cf": str(body.candidate_forms),
             "rf": str(body.recommenders_forms), "cd": body.date_closed.date(), "y": body.year,
             "sem": body.semester, "ty": body.edict_type, "o": body.is_open, "u": user["id"]})).scalar()
        for phase, date in (("inscricoes", body.date_application), ("homologacao", body.date_evaluation),
                            ("avaliacao", body.date_verification), ("encerrado", body.date_closed)):
            await s.execute(text(
                "insert into edict_phase (edict_id, closed_date, phase) values (:e, :d, :p)"),
                {"e": edict_id, "d": date.date(), "p": phase})
        await s.commit()
    return {
        "title": body.title, "description": body.description, "year": body.year,
        "semester": body.semester, "edict_type": body.edict_type, "is_open": body.is_open,
        "candidate_forms": body.candidate_forms, "recommenders_forms": body.recommenders_forms,
        "date_application": body.date_application, "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation, "date_closed": body.date_closed,
        "id": edict_id, "closed_date": body.date_closed,
    }


@router.post("/{edict_id}/edit")
async def edit_edict(edict_id: int, body: EditEdictSchema, user=Depends(require_admin)):
    _check_chronology(body.date_application, body.date_evaluation,
                      body.date_verification, body.date_closed)
    try:
        year = int(body.year)
        semester = int(body.semester)
    except ValueError:
        raise HTTPException(status_code=422, detail="year and semester must be integers")
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        await s.execute(text(
            "update edict set title = :t, description = :d, year = :y, semester = :sem, type = :ty, "
            "closed_date = :cd, updated_at = now() where id = :i"),
            {"t": body.title, "d": body.description, "y": year, "sem": semester,
             "ty": body.edict_type, "cd": body.date_closed.date(), "i": edict_id})
        await _set_phase_dates(s, edict_id, body.date_application, body.date_evaluation,
                               body.date_verification, body.date_closed)
        await s.commit()
    return {
        "title": body.title, "description": body.description, "year": body.year,
        "semester": body.semester, "edict_type": body.edict_type,
        "date_application": body.date_application, "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation, "date_closed": body.date_closed,
    }


@router.post("/{edict_id}/edit-date")
async def edit_edict_date(edict_id: int, body: EditEdictDateSchema, user=Depends(require_admin)):
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        await s.execute(text("update edict set closed_date = :d, updated_at = now() where id = :i"),
                        {"d": body.closed_date, "i": edict_id})
        await s.execute(text(
            "update edict_phase set closed_date = :d where edict_id = :e and phase = 'encerrado'"),
            {"d": body.closed_date, "e": edict_id})
        await s.commit()
    return {"closed_date": body.closed_date}


@router.post("/{edict_id}/advance-phase")
async def advance_phase(edict_id: int, body: AdvancePhaseEdictSchema, user=Depends(require_admin)):
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        phase = (await s.execute(text(
            "select * from edict_phase where id = :i and edict_id = :e"),
            {"i": body.id, "e": edict_id})).mappings().first()
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        await s.execute(text("update edict set phase = :p, updated_at = now() where id = :i"),
                        {"p": phase["phase"], "i": edict_id})
        await s.commit()
    async with PrejanusSession() as s:
        edict = await _get_edict_or_404(s, edict_id)
    await forms.change_form_phase(int(edict["candidate_forms"]), PHASE_TO_FORMS[phase["phase"]])
    return {"id": body.id, "label": phase["phase"]}


@router.patch("/{edict_id}/close")
async def close_edict(edict_id: int, body: CloseEdictSchema, user=Depends(require_admin)):
    async with PrejanusSession() as s:
        edict = await _get_edict_or_404(s, edict_id)
        if not edict["is_open"]:
            raise HTTPException(status_code=409, detail="Edict already closed")
        await s.execute(text("update edict set is_open = false, updated_at = now() where id = :i"),
                        {"i": edict_id})
        await s.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/{edict_id}/remove")
async def remove_edict(edict_id: int, user=Depends(require_admin)):
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        await s.execute(text("delete from edict where id = :i"), {"i": edict_id})
        await s.commit()
    return {"message": "Edict deleted successfully"}


@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(edict_id: int, stats: str | None = None,
                                         only_favorites: bool = False,
                                         user=Depends(get_current_user)):
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            edict = await _get_edict_or_404(ps, edict_id)
            responses, subs = await service.sync_submissions(ps, fs, edict)
            await service.associate_recommendations(ps, fs, edict, responses, subs)
            items = []
            for sub in subs.values():
                if stats is not None and sub["stats"] != stats:
                    continue
                if only_favorites and not await service.is_favorite(ps, sub, user["id"]):
                    continue
                items.append(await service.build_submission_item(ps, fs, edict, sub, user["id"]))
    return {"submissions": items}


@router.post("/{edict_id}/slots")
async def set_user_slots(edict_id: int, body: SlotsSchema, user=Depends(get_current_user)):
    amount = (body.amount or "").strip()
    if amount == "":
        amount = "0"
    try:
        value = int(amount)
    except ValueError:
        raise HTTPException(status_code=422, detail="amount must be an integer")
    if value < 0:
        value = 0
        amount = "0"
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        existing = (await s.execute(text(
            "select id from user_edict_slots where user_id = :u and edict_id = :e"),
            {"u": user["id"], "e": edict_id})).scalar()
        if existing:
            await s.execute(text("update user_edict_slots set slots = :v where id = :i"),
                            {"v": value, "i": existing})
        else:
            await s.execute(text(
                "insert into user_edict_slots (user_id, edict_id, slots) values (:u, :e, :v)"),
                {"u": user["id"], "e": edict_id, "v": value})
        await s.commit()
    return {"amount": amount}


def _form_type(tipo: str):
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(status_code=404, detail="Unknown mapping type")


def _mapping_dict(row):
    return {"id": row["id"], "edict_id": row["edict_id"], "form_type": row["form_type"],
            "user_id": row["user_id"], "form_id": row["form_id"], "form_version": row["form_version"],
            "mapping": row["mapping"], "is_active": row["is_active"]}


async def _valid_pairs(fsession, form_id, version):
    sections = await forms.get_sections(form_id, version)
    sec_ids = {s["id"] for s in sections}
    fields = await forms.get_form_fields(form_id, version)
    return {(f["section_id"], f["id"]) for f in fields if f["section_id"] in sec_ids}


@router.post("/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(edict_id: int, tipo: str, version: int, payload: dict,
                         user=Depends(require_admin)):
    form_type = _form_type(tipo)
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            edict = await _get_edict_or_404(ps, edict_id)
            form_id = int(edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"])
            if not validate_tree(payload, await _valid_pairs(fs, form_id, version)):
                raise HTTPException(status_code=422, detail="Invalid section/field reference")
            existing = (await ps.execute(text(
                "select id from edict_form_mappings where edict_id = :e and form_type = :t "
                "and form_version = :v"),
                {"e": edict_id, "t": form_type, "v": version})).scalar()
            if existing:
                raise HTTPException(status_code=409, detail="Mapping already exists for this version")
            mapping_id = (await ps.execute(text(
                "insert into edict_form_mappings (edict_id, form_type, mapping, is_active, "
                "form_id, user_id, form_version) values (:e, :t, :m, true, :f, :u, :v) returning id"),
                {"e": edict_id, "t": form_type, "m": json.dumps(payload), "f": str(form_id),
                 "u": user["id"], "v": version})).scalar()
            await ps.commit()
            row = (await ps.execute(text(
                "select * from edict_form_mappings where id = :i"), {"i": mapping_id})).mappings().first()
    return _mapping_dict(row)


@router.get("/{edict_id}/{tipo}/mappings")
async def get_mappings(edict_id: int, tipo: str, user=Depends(get_current_user)):
    form_type = _form_type(tipo)
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        rows = (await s.execute(text(
            "select * from edict_form_mappings where edict_id = :e and form_type = :t order by id"),
            {"e": edict_id, "t": form_type})).mappings().all()
    return [_mapping_dict(r) for r in rows]


async def _find_mapping(psession, edict_id, form_type, version, mapping_id):
    row = (await psession.execute(text(
        "select * from edict_form_mappings where id = :i and edict_id = :e and form_type = :t "
        "and form_version = :v"),
        {"i": mapping_id, "e": edict_id, "t": form_type, "v": version})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return row


@router.put("/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(edict_id: int, tipo: str, version: int, mapping_id: int, payload: dict,
                         user=Depends(require_admin)):
    form_type = _form_type(tipo)
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            edict = await _get_edict_or_404(ps, edict_id)
            await _find_mapping(ps, edict_id, form_type, version, mapping_id)
            form_id = int(edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"])
            if not validate_tree(payload, await _valid_pairs(fs, form_id, version)):
                raise HTTPException(status_code=422, detail="Invalid section/field reference")
            await ps.execute(text(
                "update edict_form_mappings set mapping = :m where id = :i"),
                {"m": json.dumps(payload), "i": mapping_id})
            await ps.commit()
            row = (await ps.execute(text(
                "select * from edict_form_mappings where id = :i"), {"i": mapping_id})).mappings().first()
    return _mapping_dict(row)


@router.delete("/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(edict_id: int, tipo: str, version: int, mapping_id: int,
                         user=Depends(require_admin)):
    form_type = _form_type(tipo)
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        await _find_mapping(s, edict_id, form_type, version, mapping_id)
        await s.execute(text("delete from edict_form_mappings where id = :i"), {"i": mapping_id})
        await s.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/{edict_id}/{tipo}/forms/versions/unmapped")
async def get_unmapped_versions(edict_id: int, tipo: str, user=Depends(get_current_user)):
    form_type = _form_type(tipo)
    column = "candidate_form_version" if form_type == "candidate" else "recommender_form_version"
    async with PrejanusSession() as s:
        await _get_edict_or_404(s, edict_id)
        versions = (await s.execute(text(
            f"select distinct {column} from submission where edict_id = :e"), {"e": edict_id})).scalars().all()
        mapped = (await s.execute(text(
            "select form_version from edict_form_mappings where edict_id = :e and form_type = :t"),
            {"e": edict_id, "t": form_type})).scalars().all()
    return sorted(set(versions) - set(mapped))


@router.post("/{edict_id}/interactors_list")
async def interactors_list(edict_id: int, mode: str = "plain_text",
                           body: SectionsDocument | None = None,
                           user=Depends(require_admin)):
    options = body or SectionsDocument()
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            edict = await _get_edict_or_404(ps, edict_id)
            rows = (await ps.execute(text(
                "select distinct u.id, u.name, u.email from \"user\" u where u.id in ("
                "  select user_id from comment where submission_id in "
                "    (select id from submission where edict_id = :e)"
                "  union select user_id from favorites where submission_id in "
                "    (select id from submission where edict_id = :e)"
                "  union select user_id from labels where submission_id in "
                "    (select id from submission where edict_id = :e)"
                "  union select user_id from private_note where submission_id in "
                "    (select id from submission where edict_id = :e)"
                ") order by u.id"),
                {"e": edict_id})).mappings().all()
            if mode != "pdf":
                return [dict(r) for r in rows]
            subs = (await ps.execute(text(
                "select * from submission where edict_id = :e"), {"e": edict_id})).mappings().all()
            finalized = len(subs)
            in_progress = await forms.count_in_progress(int(edict["candidate_forms"]))
            approved_list = []
            advisors = []
            emails = []
            for sub in subs:
                if sub["stats"] == "approved":
                    payload = await service.candidate_payload(ps, fs, edict, dict(sub))
                    adv = await service.advisor_info(ps, dict(sub))
                    approved_list.append({"name": payload["name"], "email": payload["email"],
                                          "advisor": adv["name"] if adv else ""})
                    if adv and adv["id"] not in [a["id"] for a in advisors]:
                        advisors.append(adv)
                    if payload["email"]:
                        emails.append(payload["email"])
            data = {
                "general_statistics": options.general_statistics,
                "relation": options.relation, "approved": options.approved,
                "list_of_advisors": options.list_of_advisors,
                "show_emails": options.show_emails,
                "stats": {"finalized": finalized, "in_progress": in_progress},
                "approved_list": approved_list, "advisors": advisors, "emails": emails,
            }
    job_id = reports.start_pdf(edict, data)
    return {"job_id": job_id, "status": "processing"}


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(edict_id: int, user=Depends(require_admin)):
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            edict = await _get_edict_or_404(ps, edict_id)
            subs = (await ps.execute(text(
                "select * from submission where edict_id = :e order by id"), {"e": edict_id})).mappings().all()
            teachers = (await ps.execute(text(
                "select distinct u.id, u.email, s.slots from \"user\" u "
                "join labels l on l.user_id = u.id and l.context_type = 'bidding' "
                "left join user_edict_slots s on s.user_id = u.id and s.edict_id = :e "
                "order by u.id"), {"e": edict_id})).mappings().all()
            rows = [["#"] + [t["email"] for t in teachers]]
            rows.append(["slots"] + [str(t["slots"]) if t["slots"] is not None else "" for t in teachers])
            for sub in subs:
                payload = await service.candidate_payload(ps, fs, edict, dict(sub))
                interests = (await ps.execute(text(
                    "select user_id, label from labels where submission_id = :i and context_type = 'bidding'"),
                    {"i": sub["id"]})).all()
                by_user = {uid: label for uid, label in interests}
                rows.append([payload["email"]] + [by_user.get(t["id"], "") for t in teachers])
    job_id = reports.start_csv(rows)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, kind: str, media_type: str):
    job = reports.get_job(job_id)
    if not job or job["type"] != kind:
        raise HTTPException(status_code=404, detail="Report not found")
    path = job["path"]
    try:
        with open(path, "rb"):
            pass
    except OSError:
        raise HTTPException(status_code=404, detail="Report not ready")
    reports.pop_job(job_id)
    return FileResponse(path, media_type=media_type,
                        headers={"Content-Disposition": "inline"},
                        background=BackgroundTask(_cleanup, path))


def _cleanup(path: str):
    try:
        import os
        os.unlink(path)
    except OSError:
        pass


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _download(job_id, "pdf", "application/pdf")


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _download(job_id, "csv", "text/csv")
