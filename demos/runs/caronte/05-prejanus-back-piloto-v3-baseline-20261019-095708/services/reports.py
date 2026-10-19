import csv
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fpdf import FPDF
from sqlalchemy import select

from database import SessionLocal
from models import Comment, Edict, Favorite, Label, PrivateNote, Submission, User, UserEdictSlot

JOBS: dict[str, dict] = {}


def new_job(kind: str) -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"kind": kind, "ready": False, "path": None}
    return job_id


def _latin(text: Any) -> str:
    return str(text if text is not None else "").encode("latin-1", "replace").decode("latin-1")


async def get_interactors(edict_id: int) -> list[dict]:
    async with SessionLocal() as db:
        sub_ids = select(Submission.id).where(Submission.edict_id == edict_id)
        user_ids: set[int] = set()
        for stmt in (
            select(Comment.user_id).where(Comment.submission_id.in_(sub_ids)),
            select(Favorite.user_id).where(Favorite.submission_id.in_(sub_ids)),
            select(Label.user_id).where(Label.submission_id.in_(sub_ids)),
            select(PrivateNote.user_id).where(PrivateNote.submission_id.in_(sub_ids)),
        ):
            for row in (await db.execute(stmt)).fetchall():
                user_ids.add(row[0])
        users = []
        for uid in sorted(user_ids):
            user = await db.get(User, uid)
            if user:
                users.append({"id": user.id, "name": user.name, "email": user.email})
        return users


async def generate_pdf(job_id: str, edict_id: int, options: dict) -> None:
    async with SessionLocal() as db:
        edict = await db.get(Edict, edict_id)
        if edict is None:
            JOBS.pop(job_id, None)
            return
        subs = (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars().all()
        approved = [s for s in subs if s.stats == "approved"]
        refused = [s for s in subs if s.stats == "refused"]
        underreview = [s for s in subs if s.stats == "underreview"]
        advisors = []
        for sub in approved:
            if sub.advisor_id:
                advisor = await db.get(User, sub.advisor_id)
                if advisor:
                    advisors.append((sub, advisor))
        slots = (
            await db.execute(select(UserEdictSlot, User).join(User, User.id == UserEdictSlot.user_id).where(UserEdictSlot.edict_id == edict_id))
        ).all()
        interactors = await get_interactors(edict_id)

    import services.forms_service as forms_service

    finalized = 0
    in_progress = 0
    try:
        responses = await forms_service.get_form_responses(int(edict.candidate_forms))
        finalized = sum(1 for r in responses if r["submitted_at"] is not None)
        in_progress = sum(1 for r in responses if r["submitted_at"] is None)
    except (TypeError, ValueError):
        pass

    pdf = FPDF()
    pdf.add_page()
    for image in ("assets/usp.png", "assets/logo.png"):
        if os.path.exists(image):
            try:
                pdf.image(image, w=40)
                pdf.ln(5)
            except Exception:
                pass
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _latin(f"Relatorio do Edital {edict.title}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, _latin(f"Ano: {edict.year}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        8,
        _latin(f"Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    if options.get("general_statistics"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _latin("Estatisticas gerais"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 6, _latin(f"Candidaturas finalizadas: {finalized}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _latin(f"Candidaturas em preenchimento: {in_progress}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _latin(f"Aprovadas: {len(approved)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _latin(f"Recusadas: {len(refused)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, _latin(f"Em analise: {len(underreview)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    if options.get("relation") or options.get("approved"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _latin("Relacao de aprovados e orientadores"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for sub, advisor in advisors:
            pdf.cell(0, 6, _latin(f"Inscricao #{sub.id} - Orientador: {advisor.name}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    if options.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _latin("Lista de orientadores"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for _sub, advisor in advisors:
            pdf.cell(0, 6, _latin(advisor.name), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    if options.get("show_emails"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _latin("Lista de e-mails"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for user in interactors:
            pdf.cell(0, 6, _latin(f"{user['name']} <{user['email']}>"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    path = os.path.join("/tmp", f"report_{job_id}.pdf")
    pdf.output(path)
    JOBS[job_id] = {"kind": "pdf", "ready": True, "path": path}


async def generate_csv(job_id: str, edict_id: int) -> None:
    async with SessionLocal() as db:
        edict = await db.get(Edict, edict_id)
        if edict is None:
            JOBS.pop(job_id, None)
            return
        subs = (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars().all()
        bidding_rows = (
            await db.execute(
                select(Label).where(
                    Label.submission_id.in_([s.id for s in subs]),
                    Label.context_type == "bidding",
                )
            )
        ).scalars().all()
        slots_rows = (
            await db.execute(
                select(UserEdictSlot, User)
                .join(User, User.id == UserEdictSlot.user_id)
                .where(UserEdictSlot.edict_id == edict_id)
            )
        ).all()

    teachers = []
    slots_by_user = {}
    for slot, user in slots_rows:
        teachers.append(user)
        slots_by_user[user.id] = slot.slots
    for label in bidding_rows:
        if label.user_id not in slots_by_user:
            user = None
            async with SessionLocal() as db2:
                user = await db2.get(User, label.user_id)
            if user:
                teachers.append(user)
                slots_by_user[user.id] = None

    # keep only teachers with bidding manifestations
    bidding_users = {l.user_id for l in bidding_rows}
    teachers = [t for t in teachers if t.id in bidding_users]
    seen = set()
    unique_teachers = []
    for t in teachers:
        if t.id not in seen:
            seen.add(t.id)
            unique_teachers.append(t)
    teachers = unique_teachers

    bidding_by_sub: dict[int, dict[int, str]] = {}
    for label in bidding_rows:
        bidding_by_sub.setdefault(label.submission_id, {})[label.user_id] = label.label

    import services.forms_service as forms_service
    import services.submissions_service as submissions_service

    candidate_emails = {}
    for sub in subs:
        resp = await forms_service.get_response(sub.candidate_form_id)
        candidate_emails[sub.id] = (resp or {}).get("email") or ""

    path = os.path.join("/tmp", f"pairing_{job_id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#"] + [t.email for t in teachers])
        writer.writerow(["slots"] + [str(slots_by_user.get(t.id) or 0) for t in teachers])
        for sub in subs:
            row = [candidate_emails.get(sub.id, "")]
            for t in teachers:
                row.append(bidding_by_sub.get(sub.id, {}).get(t.id, ""))
            writer.writerow(row)

    JOBS[job_id] = {"kind": "csv", "ready": True, "path": path}
