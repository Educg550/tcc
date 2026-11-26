from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from starlette.background import BackgroundTask

import forms_db
import reports
from auth import get_current_user, require_admin
from database import FormsSessionLocal, SessionLocal
from models import (
    Comment,
    Edict,
    EdictFormMapping,
    EdictPhase,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlot,
)
from submission_service import extract_summary, sync_edict_submissions

router = APIRouter(tags=["edicts"])

PHASES = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


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


def _check_dates(a, v, e, c):
    if not (a < v < e < c):
        raise HTTPException(status_code=422, detail="Datas fora de ordem cronológica")


async def _get_edict(db, edict_id: int) -> Edict:
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
):
    async with SessionLocal() as db:
        q = select(Edict).order_by(Edict.closed_date.desc())
        if type is not None:
            q = q.where(Edict.type == type)
        if is_open is not None:
            q = q.where(Edict.is_open == is_open)
        edicts = (await db.execute(q)).scalars().all()
        return [_edict_list_item(e) for e in edicts]


@router.post("/edicts")
async def create_edict(payload: InsertEdict, user: User = Depends(get_current_user)):
    require_admin(user)
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
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
            created_at=now,
            updated_at=now,
            user_id=user.id,
        )
        db.add(edict)
        await db.flush()
        phase_dates = {
            "inscricoes": payload.date_application.date(),
            "homologacao": payload.date_evaluation.date(),
            "avaliacao": payload.date_verification.date(),
            "encerrado": payload.date_closed.date(),
        }
        for phase in PHASES:
            db.add(
                EdictPhase(
                    edict_id=edict.id, phase=phase, closed_date=phase_dates[phase]
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
            "date_verification": payload.date_verification,
            "date_evaluation": payload.date_evaluation,
            "date_closed": payload.date_closed,
            "id": edict.id,
            "closed_date": payload.date_closed,
            "candidate_form_id": str(payload.candidate_forms),
            "recommender_form_id": str(payload.recommenders_forms),
            "accept_form_id": "",
        }


@router.get("/edicts/{edict_id}")
async def get_edict(edict_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        slot = (
            await db.execute(
                select(UserEdictSlot).where(
                    UserEdictSlot.user_id == user.id,
                    UserEdictSlot.edict_id == edict.id,
                )
            )
        ).scalar_one_or_none()
        return {
            "id": edict.id,
            "title": edict.title,
            "candidate_form_id": edict.candidate_forms or "",
            "recommender_form_id": edict.recommenders_forms or "",
            "accept_form_id": edict.accept_forms or "",
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
                {"id": p.id, "closed_date": p.closed_date, "phase": p.phase}
                for p in edict.phases
            ],
            "slots": str(slot.slots) if slot and slot.slots is not None else "0",
        }


@router.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int, payload: EditEdict, user: User = Depends(get_current_user)
):
    require_admin(user)
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        edict.title = payload.title
        edict.description = payload.description
        edict.year = int(payload.year)
        edict.semester = int(payload.semester)
        edict.type = payload.edict_type
        edict.closed_date = payload.date_closed.date()
        edict.updated_at = datetime.now(timezone.utc)
        phase_dates = {
            "inscricoes": payload.date_application.date(),
            "homologacao": payload.date_evaluation.date(),
            "avaliacao": payload.date_verification.date(),
            "encerrado": payload.date_closed.date(),
        }
        for p in edict.phases:
            p.closed_date = phase_dates.get(p.phase, p.closed_date)
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
    edict_id: int, payload: EditEdictDate, user: User = Depends(get_current_user)
):
    require_admin(user)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        edict.closed_date = payload.closed_date
        edict.updated_at = datetime.now(timezone.utc)
        for p in edict.phases:
            if p.phase == "encerrado":
                p.closed_date = payload.closed_date
        await db.commit()
        return {"closed_date": payload.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int, payload: AdvancePhase, user: User = Depends(get_current_user)
):
    require_admin(user)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        phase = (
            await db.execute(
                select(EdictPhase).where(
                    EdictPhase.id == payload.id, EdictPhase.edict_id == edict.id
                )
            )
        ).scalar_one_or_none()
        if phase is None:
            raise HTTPException(status_code=404, detail="Fase não encontrada")
        edict.phase = phase.phase
        edict.updated_at = datetime.now(timezone.utc)
        await db.commit()
    if edict.candidate_forms:
        async with FormsSessionLocal() as fdb:
            await forms_db.change_phase(
                fdb, int(edict.candidate_forms), FORMS_PHASE[phase.phase]
            )
    return {"id": phase.id, "label": phase.phase}


@router.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int, payload: CloseEdict, user: User = Depends(get_current_user)
):
    require_admin(user)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        if not edict.is_open:
            raise HTTPException(status_code=409, detail="Edital já encerrado")
        edict.is_open = False
        edict.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return {"message": "Edital encerrado"}


@router.delete("/edicts/{edict_id}/remove")
async def remove_edict(edict_id: int, user: User = Depends(get_current_user)):
    require_admin(user)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        await db.delete(edict)
        await db.commit()
    return {"message": "Edital removido"}


@router.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int, payload: SlotsSchema, user: User = Depends(get_current_user)
):
    amount = payload.amount.strip()
    if amount == "":
        value = 0
    else:
        try:
            value = int(amount)
        except ValueError:
            raise HTTPException(status_code=422, detail="Valor inválido")
        if value < 0:
            value = 0
    async with SessionLocal() as db:
        await _get_edict(db, edict_id)
        slot = (
            await db.execute(
                select(UserEdictSlot).where(
                    UserEdictSlot.user_id == user.id,
                    UserEdictSlot.edict_id == edict_id,
                )
            )
        ).scalar_one_or_none()
        if slot is None:
            db.add(
                UserEdictSlot(user_id=user.id, edict_id=edict_id, slots=value)
            )
        else:
            slot.slots = value
        await db.commit()
    return {"amount": str(value)}


# ---------- mapeamentos ----------

def _form_type(tipo: str) -> str:
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(status_code=404, detail="Tipo inválido")


def _mapping_dict(m: EdictFormMapping) -> dict:
    return {
        "id": m.id,
        "edict_id": m.edict_id,
        "form_type": m.form_type,
        "user_id": m.user_id,
        "form_id": m.form_id,
        "form_version": m.form_version,
        "mapping": m.mapping,
        "is_active": m.is_active,
        "created_at": m.created_at,
    }


def _leaves(tree):
    if isinstance(tree, dict):
        if set(tree.keys()) <= {"section", "field"} and tree:
            yield tree
            return
        for v in tree.values():
            yield from _leaves(v)


async def _validate_mapping(fdb, form_id: int, tree: dict) -> None:
    sections = set(await forms_db.get_form_sections_ids(fdb, form_id))
    fields = {f["id"]: f["section_id"] for f in await forms_db.get_form_fields(fdb, form_id)}
    for leaf in _leaves(tree):
        if leaf is None:
            continue
        sec, fld = leaf.get("section"), leaf.get("field")
        if sec not in sections or fld not in fields or fields[fld] != sec:
            raise HTTPException(status_code=422, detail="Referência de mapeamento inválida")


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    tree: dict,
    user: User = Depends(get_current_user),
):
    require_admin(user)
    form_type = _form_type(tipo)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        form_id = int(edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms)
        async with FormsSessionLocal() as fdb:
            await _validate_mapping(fdb, form_id, tree)
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
            raise HTTPException(status_code=409, detail="Mapeamento já existe")
        m = EdictFormMapping(
            edict_id=edict_id,
            form_type=form_type,
            mapping=tree,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            form_id=str(form_id),
            user_id=user.id,
            form_version=version,
        )
        db.add(m)
        try:
            await db.commit()
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Mapeamento já existe")
        await db.refresh(m)
        return _mapping_dict(m)


@router.get("/edicts/{edict_id}/{tipo}/mappings")
async def get_mappings(edict_id: int, tipo: str, user: User = Depends(get_current_user)):
    form_type = _form_type(tipo)
    async with SessionLocal() as db:
        await _get_edict(db, edict_id)
        rows = (
            await db.execute(
                select(EdictFormMapping)
                .where(
                    EdictFormMapping.edict_id == edict_id,
                    EdictFormMapping.form_type == form_type,
                )
                .order_by(EdictFormMapping.id)
            )
        ).scalars().all()
        return [_mapping_dict(m) for m in rows]


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    tree: dict,
    user: User = Depends(get_current_user),
):
    require_admin(user)
    form_type = _form_type(tipo)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
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
        form_id = int(edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms)
        async with FormsSessionLocal() as fdb:
            await _validate_mapping(fdb, form_id, tree)
        m.mapping = tree
        await db.commit()
        await db.refresh(m)
        return _mapping_dict(m)


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    user: User = Depends(get_current_user),
):
    require_admin(user)
    form_type = _form_type(tipo)
    async with SessionLocal() as db:
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


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def get_unmapped_versions(edict_id: int, tipo: str, user: User = Depends(get_current_user)):
    form_type = _form_type(tipo)
    column = (
        Submission.candidate_form_version
        if form_type == "candidate"
        else Submission.recommender_form_version
    )
    async with SessionLocal() as db:
        await _get_edict(db, edict_id)
        versions = (
            await db.execute(
                select(column)
                .where(Submission.edict_id == edict_id)
                .distinct()
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
        return sorted(v for v in versions if v not in mapped)


# ---------- relatórios ----------

@router.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    options: SectionsDocument | None = None,
    user: User = Depends(get_current_user),
):
    require_admin(user)
    opts = (options or SectionsDocument()).model_dump()
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        subs = (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars().all()
        sub_ids = [s.id for s in subs]
        user_ids: set[int] = set()
        if sub_ids:
            for model, col in (
                (Comment, Comment.user_id),
                (Favorite, Favorite.user_id),
                (Label, Label.user_id),
                (PrivateNote, PrivateNote.user_id),
            ):
                rows = (
                    await db.execute(
                        select(col).where(model.submission_id.in_(sub_ids))
                    )
                ).scalars().all()
                user_ids.update(rows)
        interactors = []
        for uid in sorted(user_ids):
            u = await db.get(User, uid)
            if u:
                interactors.append({"id": u.id, "name": u.name, "email": u.email})

        if mode != "pdf":
            return interactors

        async with FormsSessionLocal() as fdb:
            finalized = in_progress = 0
            names = {"approved": [], "refused": [], "underreview": []}
            advisors: list[str] = []
            emails: list[str] = []
            try:
                form_id = int(edict.candidate_forms)
            except (TypeError, ValueError):
                form_id = None
            if form_id is not None:
                responses = await forms_db.get_responses(fdb, form_id)
                finalized = len(responses)
                all_responses = (
                    await fdb.execute(
                        text("SELECT count(*) FROM form_response WHERE form_id = :f"),
                        {"f": form_id},
                    )
                ).scalar()
                in_progress = max((all_responses or 0) - finalized, 0)
            for s in subs:
                resp = await forms_db.get_response(fdb, s.candidate_form_id)
                details = await forms_db.get_response_details(fdb, s.candidate_form_id)
                summ = extract_summary(details, (resp or {}).get("email") or "")
                if s.stats in names:
                    advisor = await db.get(User, s.advisor_id) if s.advisor_id else None
                    names[s.stats].append((summ["name"], advisor.name if advisor else "-"))
                    if advisor and advisor.name not in advisors:
                        advisors.append(advisor.name)
                if summ["email"]:
                    emails.append(summ["email"])

        data = {
            "title": edict.title,
            "year": edict.year,
            "semester": edict.semester,
            "finalized": finalized,
            "in_progress": in_progress,
            "total": finalized + in_progress,
            "approved": names["approved"],
            "refused": [n for n, _ in names["refused"]],
            "underreview": [n for n, _ in names["underreview"]],
            "advisors": advisors,
            "emails": emails,
        }
        job_id = reports.generate_pdf_job(data, opts)
        return {"job_id": job_id, "status": "processing"}


@router.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(edict_id: int, user: User = Depends(get_current_user)):
    require_admin(user)
    async with SessionLocal() as db:
        edict = await _get_edict(db, edict_id)
        subs = (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars().all()
        # docentes com manifestações de interesse
        rows = (
            await db.execute(
                select(Label).where(
                    Label.submission_id.in_([s.id for s in subs]) if subs else Label.id < 0,
                    Label.context_type == "bidding",
                )
            )
        ).scalars().all()
        teacher_ids = sorted({l.user_id for l in rows})
        teachers = []
        for tid in teacher_ids:
            u = await db.get(User, tid)
            if u:
                slot = (
                    await db.execute(
                        select(UserEdictSlot).where(
                            UserEdictSlot.user_id == tid,
                            UserEdictSlot.edict_id == edict_id,
                        )
                    )
                ).scalar_one_or_none()
                teachers.append(
                    {
                        "id": tid,
                        "email": u.email,
                        "slots": str(slot.slots) if slot and slot.slots is not None else "0",
                    }
                )
        bids: dict[tuple[int, int], str] = {(l.user_id, l.submission_id): l.label for l in rows}

        csv_rows = [["#"] + [t["email"] for t in teachers]]
        slots_row = ["slots"] + [t["slots"] for t in teachers]
        csv_rows.append(slots_row)
        async with FormsSessionLocal() as fdb:
            for s in subs:
                resp = await forms_db.get_response(fdb, s.candidate_form_id)
                email = (resp or {}).get("email") or ""
                row = [email] + [
                    bids.get((t["id"], s.id), "") for t in teachers
                ]
                csv_rows.append(row)
    job_id = reports.generate_csv_job(csv_rows)
    return {"job_id": job_id, "status": "processing"}


def _serve_job(job_id: str, media_type: str, filename: str):
    job = reports.jobs.get(job_id)
    if not job or not os.path.exists(job["path"]):
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    def cleanup():
        j = reports.jobs.pop(job_id, None)
        if j and os.path.exists(j["path"]):
            try:
                os.remove(j["path"])
            except OSError:
                pass

    return FileResponse(
        job["path"],
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
        background=BackgroundTask(cleanup),
    )


@router.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _serve_job(job_id, "application/pdf", "relatorio.pdf")


@router.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _serve_job(job_id, "text/csv", "interesses.csv")
