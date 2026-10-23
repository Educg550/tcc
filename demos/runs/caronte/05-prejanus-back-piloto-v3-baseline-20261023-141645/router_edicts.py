import json
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

import forms_service as forms
import reports
import submissions_service as service
from auth import current_user, require_admin
from db import PrejanusSession

router = APIRouter(tags=["edicts"])

PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
PHASE_ORDER = ["inscricoes", "homologacao", "avaliacao", "encerrado"]


class InsertEdict(BaseModel):
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


class EditEdict(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictDate(BaseModel):
    closed_date: date


class AdvancePhase(BaseModel):
    id: int


class CloseEdict(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


class Slots(BaseModel):
    amount: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


def _validate_dates(d1, d2, d3, d4):
    # phases in order: inscricoes < homologacao < avaliacao < encerrado
    if not (d1 < d2 < d3 < d4):
        raise HTTPException(422, "Dates must be in strict chronological order")


async def _get_edict_or_404(edict_id: int) -> dict:
    edict = await service.get_edict(edict_id)
    if not edict:
        raise HTTPException(404, "Edict not found")
    return edict


@router.get("/edicts")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(current_user),
):
    query = "select id, title, year, semester, type, is_open from edict"
    conditions, params = [], {}
    if type is not None:
        conditions.append("type = :t")
        params["t"] = type
    if is_open is not None:
        conditions.append("is_open = :o")
        params["o"] = is_open
    if conditions:
        query += " where " + " and ".join(conditions)
    query += " order by closed_date desc"
    async with PrejanusSession() as db:
        rows = (await db.execute(text(query), params)).mappings().all()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "year": r["year"],
            "semester": r["semester"],
            "edict_type": r["type"],
            "is_open": r["is_open"],
        }
        for r in rows
    ]


@router.get("/edicts/{edict_id}")
async def get_edict(edict_id: int, user=Depends(current_user)):
    edict = await _get_edict_or_404(edict_id)
    async with PrejanusSession() as db:
        phases = (
            await db.execute(
                text(
                    "select id, closed_date, phase from edict_phase "
                    "where edict_id = :e order by id"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        slot = (
            await db.execute(
                text(
                    "select slots from user_edict_slots where user_id = :u and edict_id = :e"
                ),
                {"u": user["id"], "e": edict_id},
            )
        ).first()
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": edict["candidate_forms"] or "",
        "recommender_form_id": edict["recommenders_forms"] or "",
        "description": edict["description"] or "",
        "closed_date": edict["closed_date"],
        "created_at": edict["created_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": [dict(p) for p in phases],
        "slots": str(slot.slots) if slot and slot.slots is not None else "0",
    }


@router.post("/edicts")
async def create_edict(body: InsertEdict, user=Depends(current_user)):
    require_admin(user)
    _validate_dates(body.date_application, body.date_evaluation, body.date_verification, body.date_closed)
    async with PrejanusSession() as db:
        result = await db.execute(
            text(
                "insert into edict (title, description, candidate_forms, recommenders_forms, "
                "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
                "values (:t, :d, :cf, :rf, :cd, :y, :s, :ty, 'inscricoes', :o, now(), now(), :u) "
                "returning id"
            ),
            {
                "t": body.title,
                "d": body.description,
                "cf": str(body.candidate_forms),
                "rf": str(body.recommenders_forms),
                "cd": body.date_closed.date(),
                "y": body.year,
                "s": body.semester,
                "ty": body.edict_type,
                "o": body.is_open,
                "u": user["id"],
            },
        )
        edict_id = result.scalar()
        for phase, dt in zip(
            PHASE_ORDER,
            [body.date_application, body.date_evaluation, body.date_verification, body.date_closed],
        ):
            await db.execute(
                text(
                    "insert into edict_phase (edict_id, closed_date, phase) values (:e, :d, :p)"
                ),
                {"e": edict_id, "d": dt.date(), "p": phase},
            )
        await db.commit()
    return {
        "id": edict_id,
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
        "closed_date": body.date_closed,
    }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(edict_id: int, body: EditEdict, user=Depends(current_user)):
    require_admin(user)
    await _get_edict_or_404(edict_id)
    _validate_dates(body.date_application, body.date_evaluation, body.date_verification, body.date_closed)
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "update edict set title = :t, description = :d, year = :y, semester = :s, "
                "type = :ty, closed_date = :cd, updated_at = now() where id = :i"
            ),
            {
                "t": body.title,
                "d": body.description,
                "y": int(body.year),
                "s": int(body.semester),
                "ty": body.edict_type,
                "cd": body.date_closed.date(),
                "i": edict_id,
            },
        )
        for phase, dt in zip(
            PHASE_ORDER,
            [body.date_application, body.date_evaluation, body.date_verification, body.date_closed],
        ):
            await db.execute(
                text(
                    "update edict_phase set closed_date = :d "
                    "where edict_id = :e and phase = :p"
                ),
                {"d": dt.date(), "e": edict_id, "p": phase},
            )
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
async def edit_edict_date(edict_id: int, body: EditEdictDate, user=Depends(current_user)):
    require_admin(user)
    await _get_edict_or_404(edict_id)
    async with PrejanusSession() as db:
        await db.execute(
            text("update edict set closed_date = :d, updated_at = now() where id = :i"),
            {"d": body.closed_date, "i": edict_id},
        )
        await db.execute(
            text(
                "update edict_phase set closed_date = :d "
                "where edict_id = :e and phase = 'encerrado'"
            ),
            {"d": body.closed_date, "e": edict_id},
        )
        await db.commit()
    return {"closed_date": body.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_phase(edict_id: int, body: AdvancePhase, user=Depends(current_user)):
    require_admin(user)
    edict = await _get_edict_or_404(edict_id)
    async with PrejanusSession() as db:
        phase_row = (
            await db.execute(
                text(
                    "select id, phase from edict_phase where id = :i and edict_id = :e"
                ),
                {"i": body.id, "e": edict_id},
            )
        ).first()
    if not phase_row:
        raise HTTPException(404, "Phase not found")
    async with PrejanusSession() as db:
        await db.execute(
            text("update edict set phase = :p, updated_at = now() where id = :i"),
            {"p": phase_row.phase, "i": edict_id},
        )
        await db.commit()
    if edict["candidate_forms"]:
        forms_phase = PHASE_TO_FORMS.get(phase_row.phase)
        if forms_phase:
            await forms.change_form_phase(int(edict["candidate_forms"]), forms_phase)
    return {"id": phase_row.id, "label": phase_row.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(edict_id: int, body: CloseEdict, user=Depends(current_user)):
    require_admin(user)
    edict = await _get_edict_or_404(edict_id)
    if not edict["is_open"]:
        raise HTTPException(409, "Edict already closed")
    async with PrejanusSession() as db:
        await db.execute(
            text("update edict set is_open = false, updated_at = now() where id = :i"),
            {"i": edict_id},
        )
        await db.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(edict_id: int, user=Depends(current_user)):
    require_admin(user)
    await _get_edict_or_404(edict_id)
    async with PrejanusSession() as db:
        await db.execute(text("delete from edict where id = :i"), {"i": edict_id})
        await db.commit()
    return {"message": "Edict deleted successfully"}


# --- mappings ---

def _form_type(tipo: str) -> str:
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(404, "Unknown mapping type")


def _collect_leaves(tree, out):
    if isinstance(tree, dict):
        if set(tree.keys()) == {"section", "field"}:
            out.append(tree)
        else:
            for v in tree.values():
                _collect_leaves(v, out)


async def _validate_mapping_tree(edict: dict, form_type: str, version: int, tree: dict):
    raw = edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"]
    if not raw:
        raise HTTPException(422, "Edict has no form configured for this type")
    form_id = int(raw)
    fields = await forms.get_form_fields(form_id, version)
    if not fields:
        fields = await forms.get_form_fields(form_id)
    valid = {(f["section_id"], f["id"]) for f in fields}
    leaves: list[dict] = []
    _collect_leaves(tree, leaves)
    for leaf in leaves:
        if (leaf["section"], leaf["field"]) not in valid:
            raise HTTPException(422, "Invalid section/field reference in mapping")


def _mapping_response(row: dict) -> dict:
    mapping = row["mapping"]
    if isinstance(mapping, str):
        mapping = json.loads(mapping)
    return {
        "id": row["id"],
        "edict_id": row["edict_id"],
        "form_type": row["form_type"],
        "user_id": row["user_id"],
        "form_id": row["form_id"],
        "form_version": row["form_version"],
        "mapping": mapping,
        "is_active": row["is_active"],
    }


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int, tipo: str, version: int, tree: dict, user=Depends(current_user)
):
    require_admin(user)
    edict = await _get_edict_or_404(edict_id)
    form_type = _form_type(tipo)
    await _validate_mapping_tree(edict, form_type, version, tree)
    raw = edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"]
    async with PrejanusSession() as db:
        existing = (
            await db.execute(
                text(
                    "select id from edict_form_mappings where edict_id = :e "
                    "and form_type = :t and form_version = :v"
                ),
                {"e": edict_id, "t": form_type, "v": version},
            )
        ).first()
        if existing:
            raise HTTPException(409, "Mapping already exists for this version")
        row = (
            await db.execute(
                text(
                    "insert into edict_form_mappings "
                    "(edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
                    "values (:e, :t, cast(:m as jsonb), true, :f, :u, :v) returning *"
                ),
                {
                    "e": edict_id,
                    "t": form_type,
                    "m": json.dumps(tree),
                    "f": str(raw) if raw else "",
                    "u": user["id"],
                    "v": version,
                },
            )
        ).mappings().first()
        await db.commit()
    return _mapping_response(dict(row))


@router.get("/edicts/{edict_id}/{tipo}/mappings")
async def list_mappings(edict_id: int, tipo: str, user=Depends(current_user)):
    await _get_edict_or_404(edict_id)
    form_type = _form_type(tipo)
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select * from edict_form_mappings where edict_id = :e "
                    "and form_type = :t order by id"
                ),
                {"e": edict_id, "t": form_type},
            )
        ).mappings().all()
    return [_mapping_response(dict(r)) for r in rows]


async def _get_mapping_or_404(edict_id: int, form_type: str, version: int, mapping_id: int) -> dict:
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text(
                    "select * from edict_form_mappings where id = :i and edict_id = :e "
                    "and form_type = :t and form_version = :v"
                ),
                {"i": mapping_id, "e": edict_id, "t": form_type, "v": version},
            )
        ).mappings().first()
    if not row:
        raise HTTPException(404, "Mapping not found")
    return dict(row)


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int, tipo: str, version: int, mapping_id: int, tree: dict, user=Depends(current_user)
):
    require_admin(user)
    edict = await _get_edict_or_404(edict_id)
    form_type = _form_type(tipo)
    await _get_mapping_or_404(edict_id, form_type, version, mapping_id)
    await _validate_mapping_tree(edict, form_type, version, tree)
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "update edict_form_mappings set mapping = cast(:m as jsonb) where id = :i"
            ),
            {"m": json.dumps(tree), "i": mapping_id},
        )
        await db.commit()
    row = await _get_mapping_or_404(edict_id, form_type, version, mapping_id)
    return _mapping_response(row)


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int, tipo: str, version: int, mapping_id: int, user=Depends(current_user)
):
    require_admin(user)
    form_type = _form_type(tipo)
    await _get_mapping_or_404(edict_id, form_type, version, mapping_id)
    async with PrejanusSession() as db:
        await db.execute(
            text("delete from edict_form_mappings where id = :i"), {"i": mapping_id}
        )
        await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def unmapped_versions(edict_id: int, tipo: str, user=Depends(current_user)):
    await _get_edict_or_404(edict_id)
    form_type = _form_type(tipo)
    column = "candidate_form_version" if form_type == "candidate" else "recommender_form_version"
    async with PrejanusSession() as db:
        versions = {
            r[0]
            for r in await db.execute(
                text(
                    f"select distinct {column} from submission where edict_id = :e"
                ),
                {"e": edict_id},
            )
        }
        mapped = {
            r[0]
            for r in await db.execute(
                text(
                    "select distinct form_version from edict_form_mappings "
                    "where edict_id = :e and form_type = :t"
                ),
                {"e": edict_id, "t": form_type},
            )
        }
    return sorted(versions - mapped)


# --- slots, interactors, reports ---

@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(edict_id: int, body: Slots, user=Depends(current_user)):
    await _get_edict_or_404(edict_id)
    raw = (body.amount or "").strip()
    if raw == "":
        amount = 0
    else:
        try:
            amount = int(raw)
        except ValueError:
            raise HTTPException(422, "Amount must be an integer")
        if amount < 0:
            amount = 0
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "insert into user_edict_slots (user_id, edict_id, slots) values (:u, :e, :s) "
                "on conflict (user_id, edict_id) do update set slots = excluded.slots"
            ),
            {"u": user["id"], "e": edict_id, "s": amount},
        )
        await db.commit()
    return {"amount": str(amount)}


@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    background: BackgroundTasks,
    mode: str = "plain_text",
    options: SectionsDocument | None = None,
    user=Depends(current_user),
):
    require_admin(user)
    await _get_edict_or_404(edict_id)
    options = options or SectionsDocument()
    if mode == "pdf":
        job_id = reports.new_job("pdf")
        background.add_task(_run_pdf, job_id, edict_id, options.model_dump())
        return {"job_id": job_id, "status": "processing"}
    return await reports._interactors(edict_id)


async def _run_pdf(job_id, edict_id, options):
    await reports.generate_pdf(job_id, edict_id, options)


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int, background: BackgroundTasks, user=Depends(current_user)
):
    require_admin(user)
    await _get_edict_or_404(edict_id)
    job_id = reports.new_job("csv")
    background.add_task(_run_csv, job_id, edict_id)
    return {"job_id": job_id, "status": "processing"}


async def _run_csv(job_id, edict_id):
    await reports.generate_csv(job_id, edict_id)


def _download(job_id: str, kind: str, media_type: str):
    job = reports.JOBS.get(job_id)
    if not job or job["kind"] != kind or not job["path"]:
        raise HTTPException(404, "Report not found")
    path = job["path"]
    try:
        with open(path, "rb") as fh:
            content = fh.read()
    except FileNotFoundError:
        raise HTTPException(404, "Report not found")
    reports.JOBS.pop(job_id, None)
    try:
        import os

        os.remove(path)
    except OSError:
        pass
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={os.path.basename(path)}"},
    )


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str, user=Depends(current_user)):
    return _download(job_id, "pdf", "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str, user=Depends(current_user)):
    return _download(job_id, "csv", "text/csv")


# --- submissions listing ---

@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(current_user),
):
    edict = await _get_edict_or_404(edict_id)
    await service.sync_submissions(edict)
    async with PrejanusSession() as db:
        query = "select * from submission where edict_id = :e"
        params: dict = {"e": edict_id}
        if stats:
            query += " and stats = :s"
            params["s"] = stats
        if only_favorites:
            query += " and id in (select submission_id from favorites where user_id = :u)"
            params["u"] = user["id"]
        rows = (await db.execute(text(query + " order by id"), params)).mappings().all()
    items = []
    for row in rows:
        items.append(await service.build_submission_item(dict(row), user["id"]))
    return {"submissions": items}
