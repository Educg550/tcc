import asyncio
import csv
import datetime
import logging
import os
import uuid

from fastapi import BackgroundTasks

from prejanus import formsdb, subservice
from prejanus.db import SessionLocal
from prejanus.models import (
    Comment,
    Edict,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlots,
)
from prejanus.schemas import SectionsDocument
from sqlalchemy import select

logger = logging.getLogger("prejanus.reports")

JOBS: dict = {}


def new_job(kind: str) -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"kind": kind, "path": None}
    return job_id


async def _interactors(db, edict_id: int) -> list[dict]:
    sub_ids = [
        s.id
        for s in (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars()
    ]
    if not sub_ids:
        return []
    user_ids: set[int] = set()
    for model in (Comment, Favorite, Label, PrivateNote):
        rows = await db.execute(
            select(model.user_id).where(model.submission_id.in_(sub_ids))
        )
        user_ids.update(r[0] for r in rows)
    out = []
    for uid in sorted(user_ids):
        user = await db.get(User, uid)
        if user:
            out.append({"id": user.id, "name": user.name, "email": user.email})
    return out


async def _collect_pdf_data(db, edict: Edict, options: SectionsDocument) -> dict:
    subs = list(
        (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
            )
        ).scalars()
    )
    finalized = in_progress = 0
    try:
        form_id = int(edict.candidate_forms)
        rows = await formsdb.fetch_all(
            "select count(*) filter (where submitted_at is not null) as fin, "
            "count(*) filter (where submitted_at is null) as prog "
            "from form_response where form_id = :f",
            {"f": form_id},
        )
        if rows:
            finalized = rows[0]["fin"] or 0
            in_progress = rows[0]["prog"] or 0
    except (TypeError, ValueError):
        pass
    candidates = []
    for sub in subs:
        name, email, _resp, _mapped, _values = await subservice.candidate_identity(db, edict, sub)
        advisor = None
        if sub.advisor_id:
            advisor_user = await db.get(User, sub.advisor_id)
            if advisor_user:
                advisor = advisor_user.name
        candidates.append(
            {"name": name, "email": email, "stats": sub.stats, "advisor": advisor}
        )
    return {
        "title": edict.title,
        "year": edict.year,
        "finalized": finalized,
        "in_progress": in_progress,
        "candidates": candidates,
        "interactors": await _interactors(db, edict.id),
        "options": options.model_dump(),
    }


def _safe(text) -> str:
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _write_pdf(path: str, data: dict) -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    for image in ("assets/usp.png", "assets/logo.png"):
        if os.path.exists(image):
            try:
                pdf.image(image, w=40)
            except Exception:
                pass
    pdf.set_font("helvetica", "B", 16)
    pdf.multi_cell(0, 10, _safe(f"Relatorio do Edital - {data['title']} ({data['year']})"))
    pdf.set_font("helvetica", size=11)
    options = data["options"]
    if options.get("general_statistics"):
        pdf.multi_cell(
            0,
            8,
            _safe(
                f"Estatisticas gerais: candidaturas finalizadas: {data['finalized']}; "
                f"em preenchimento: {data['in_progress']}"
            ),
        )
    else:
        pdf.multi_cell(0, 8, _safe(f"Candidaturas finalizadas: {data['finalized']}"))
    if options.get("approved"):
        pdf.multi_cell(0, 8, "Candidatos aprovados:")
        for c in data["candidates"]:
            if c["stats"] == "approved":
                line = f"  {c['name']}"
                if c["advisor"]:
                    line += f" - orientador: {c['advisor']}"
                if options.get("show_emails") and c["email"]:
                    line += f" - {c['email']}"
                pdf.multi_cell(0, 7, _safe(line))
    if options.get("refused"):
        pdf.multi_cell(0, 8, "Candidatos reprovados:")
        for c in data["candidates"]:
            if c["stats"] == "refused":
                pdf.multi_cell(0, 7, _safe(f"  {c['name']}"))
    if options.get("underreview"):
        pdf.multi_cell(0, 8, "Candidatos em revisao:")
        for c in data["candidates"]:
            if c["stats"] == "underreview":
                pdf.multi_cell(0, 7, _safe(f"  {c['name']}"))
    if options.get("list_of_advisors") or options.get("relation"):
        pdf.multi_cell(0, 8, "Orientadores:")
        for c in data["candidates"]:
            if c["stats"] == "approved" and c["advisor"]:
                pdf.multi_cell(0, 7, _safe(f"  {c['advisor']} - {c['name']}"))
    if options.get("show_emails"):
        pdf.multi_cell(0, 8, "E-mails dos participantes:")
        for c in data["candidates"]:
            if c["email"]:
                pdf.multi_cell(0, 7, _safe(f"  {c['name']}: {c['email']}"))
    pdf.multi_cell(0, 8, _safe(f"Interatores do edital: {len(data['interactors'])}"))
    for user in data["interactors"]:
        pdf.multi_cell(0, 7, _safe(f"  {user['name']}"))
    pdf.output(path)


async def _pdf_job(job_id: str, edict_id: int, options: dict) -> None:
    try:
        options_model = SectionsDocument(**options)
        async with SessionLocal() as db:
            edict = await db.get(Edict, edict_id)
            if edict is None:
                return
            data = await _collect_pdf_data(db, edict, options_model)
        path = f"/tmp/{job_id}.pdf"
        await asyncio.to_thread(_write_pdf, path, data)
        JOBS[job_id]["path"] = path
    except Exception:
        logger.exception("pdf job %s failed", job_id)


async def _collect_csv_data(db, edict: Edict) -> dict:
    subs = list(
        (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
            )
        ).scalars()
    )
    teacher_ids: list[int] = []
    bidding_by_sub: dict[int, dict[int, str]] = {s.id: {} for s in subs}
    for sub in subs:
        rows = await db.execute(
            select(Label).where(
                Label.submission_id == sub.id, Label.context_type == "bidding"
            ).order_by(Label.id)
        )
        for label in rows.scalars():
            if label.user_id not in teacher_ids:
                teacher_ids.append(label.user_id)
            bidding_by_sub[sub.id][label.user_id] = label.label
    emails: list[str] = []
    slots: list[str] = []
    for uid in teacher_ids:
        user = await db.get(User, uid)
        emails.append(user.email if user else "")
        slot_row = (
            await db.execute(
                select(UserEdictSlots).where(
                    UserEdictSlots.user_id == uid,
                    UserEdictSlots.edict_id == edict.id,
                )
            )
        ).scalar_one_or_none()
        slots.append(str(slot_row.slots) if slot_row and slot_row.slots is not None else "")
    rows = []
    for sub in subs:
        _name, email, _resp, _mapped, _values = await subservice.candidate_identity(db, edict, sub)
        rows.append([email] + [bidding_by_sub[sub.id].get(uid, "") for uid in teacher_ids])
    return {"emails": emails, "slots": slots, "rows": rows}


def _write_csv(path: str, data: dict) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#"] + data["emails"])
        writer.writerow(["slots"] + data["slots"])
        for row in data["rows"]:
            writer.writerow(row)


async def _csv_job(job_id: str, edict_id: int) -> None:
    try:
        async with SessionLocal() as db:
            edict = await db.get(Edict, edict_id)
            if edict is None:
                return
            data = await _collect_csv_data(db, edict)
        path = f"/tmp/{job_id}.csv"
        await asyncio.to_thread(_write_csv, path, data)
        JOBS[job_id]["path"] = path
    except Exception:
        logger.exception("csv job %s failed", job_id)


def start_pdf_job(background_tasks: BackgroundTasks, edict: Edict, options: SectionsDocument) -> str:
    job_id = new_job("pdf")
    background_tasks.add_task(_pdf_job, job_id, edict.id, options.model_dump())
    return job_id


def start_csv_job(background_tasks: BackgroundTasks, edict: Edict) -> str:
    job_id = new_job("csv")
    background_tasks.add_task(_csv_job, job_id, edict.id)
    return job_id
