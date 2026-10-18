"""Background report jobs: interactors PDF and pairing biddings CSV."""
import csv
import threading
import uuid
from pathlib import Path

from fpdf import FPDF
from sqlalchemy import select

from .config import settings
from .db import SessionLocal
from .models import (
    Bidding,
    Comment,
    Edict,
    Favorite,
    Label,
    PrivateNote,
    Slot,
    Submission,
    SubmissionAdvisor,
    User,
)

JOBS: dict[str, dict] = {}


def new_job(kind: str) -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"kind": kind, "path": None}
    return job_id


def _finish(job_id: str, path: str) -> None:
    JOBS[job_id]["path"] = path


def _interactors(db, edict_id: int) -> list[User]:
    """Users that interacted with the edict by comment, favorite, label or note."""
    user_ids: set[int] = set()
    for model in (Comment, Favorite, Label, PrivateNote):
        rows = db.execute(
            select(model.user_id)
            .join(Submission, model.submission_id == Submission.id)
            .where(Submission.edict_id == edict_id)
        ).scalars().all()
        user_ids.update(rows)
    if not user_ids:
        return []
    return db.query(User).filter(User.id.in_(user_ids)).order_by(User.id).all()


def _generate_pdf(job_id: str, edict_id: int, options: dict) -> None:
    db = SessionLocal()
    try:
        edict = db.get(Edict, edict_id)
        submissions = (
            db.query(Submission).filter(Submission.edict_id == edict_id).all()
        )
        approved = [s for s in submissions if s.stats == "approved"]
        refused = [s for s in submissions if s.stats == "refused"]
        underreview = [s for s in submissions if s.stats == "underreview"]
        waitlist = [s for s in submissions if s.stats == "waitlist"]
        interactors = _interactors(db, edict_id)

        advisors: dict[int, str] = {}
        for sub in approved:
            adv = (
                db.query(User)
                .join(SubmissionAdvisor, SubmissionAdvisor.user_id == User.id)
                .filter(SubmissionAdvisor.submission_id == sub.id)
                .first()
            )
            advisors[sub.id] = adv.name if adv else ""

        pdf = FPDF()
        pdf.add_page()
        for img in ("assets/logo.png", "assets/usp.png"):
            if Path(img).exists():
                pdf.image(img, w=40)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Relatorio do Edital {edict.title if edict else ''}", ln=1)
        pdf.set_font("Helvetica", size=12)
        if edict:
            pdf.cell(0, 10, f"Ano: {edict.year}", ln=1)

        if options.get("general_statistics"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Estatisticas gerais", ln=1)
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 8, f"Candidaturas finalizadas: {len(submissions)}", ln=1)
            pdf.cell(0, 8, "Candidaturas em preenchimento: 0", ln=1)

        if options.get("approved"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Aprovados", ln=1)
            pdf.set_font("Helvetica", size=12)
            for sub in approved:
                line = f"{sub.name} <{sub.email}>"
                if options.get("list_of_advisors"):
                    line += f" - Orientador: {advisors.get(sub.id, '')}"
                pdf.cell(0, 8, line, ln=1)

        if options.get("refused"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Reprovados", ln=1)
            pdf.set_font("Helvetica", size=12)
            for sub in refused:
                pdf.cell(0, 8, f"{sub.name} <{sub.email}>", ln=1)

        if options.get("underreview"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Em revisao", ln=1)
            pdf.set_font("Helvetica", size=12)
            for sub in underreview + waitlist:
                pdf.cell(0, 8, f"{sub.name} <{sub.email}>", ln=1)

        if options.get("relation"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Relacao de aprovados e orientadores", ln=1)
            pdf.set_font("Helvetica", size=12)
            for sub in approved:
                pdf.cell(0, 8, f"{sub.name} - {advisors.get(sub.id, '')}", ln=1)

        if options.get("show_emails"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Lista de e-mails", ln=1)
            pdf.set_font("Helvetica", size=12)
            for user in interactors:
                pdf.cell(0, 8, f"{user.name} <{user.email}>", ln=1)

        path = str(Path(settings.TMP_DIR) / f"{job_id}.pdf")
        pdf.output(path)
        _finish(job_id, path)
    finally:
        db.close()


def _generate_csv(job_id: str, edict_id: int) -> None:
    db = SessionLocal()
    try:
        submissions = (
            db.query(Submission)
            .filter(Submission.edict_id == edict_id)
            .order_by(Submission.id)
            .all()
        )
        biddings = (
            db.query(Bidding)
            .join(Submission, Bidding.submission_id == Submission.id)
            .filter(Submission.edict_id == edict_id)
            .all()
        )
        teachers = sorted({b.user_id for b in biddings})
        users = (
            {u.id: u for u in db.query(User).filter(User.id.in_(teachers))}
            if teachers
            else {}
        )
        slots = {
            s.user_id: s.amount
            for s in db.query(Slot).filter(Slot.edict_id == edict_id)
        }
        by_user: dict[int, dict[int, str]] = {}
        for b in biddings:
            by_user.setdefault(b.user_id, {})[b.submission_id] = b.bidding

        path = Path(settings.TMP_DIR) / f"{job_id}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["#"] + [users[t].email or "" for t in teachers])
            writer.writerow(["slots"] + [slots.get(t, "0") for t in teachers])
            for sub in submissions:
                writer.writerow(
                    [sub.email]
                    + [by_user.get(t, {}).get(sub.id, "") for t in teachers]
                )
        _finish(job_id, str(path))
    finally:
        db.close()


def start_pdf_job(edict_id: int, options: dict) -> str:
    job_id = new_job("pdf")
    threading.Thread(
        target=_generate_pdf, args=(job_id, edict_id, options), daemon=True
    ).start()
    return job_id


def start_csv_job(edict_id: int) -> str:
    job_id = new_job("csv")
    threading.Thread(
        target=_generate_csv, args=(job_id, edict_id), daemon=True
    ).start()
    return job_id