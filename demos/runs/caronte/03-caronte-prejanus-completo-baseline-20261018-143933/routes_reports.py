"""Relatórios: lista de participantes, PDF e CSV."""
import csv
import os

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from fpdf import FPDF

from auth import current_user
from config import settings
from db import PrejanusSession, get_db, get_forms_db
from models import (Bidding, Comment, Edict, Favorite, Job, Label, PrivateNote,
                    Slot, Submission, User)
import forms_db

router = APIRouter()


def _get_edict(db, edict_id):
    edict = db.get(Edict, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def _interactors(db, edict_id):
    """Usuários que interagiram no edital por comentários, favoritos, etiquetas ou notas."""
    subs = [s.id for s in db.query(Submission).filter(Submission.edict_id == edict_id).all()]
    if not subs:
        return []
    ids = set()
    for model, col in ((Comment, Comment.user_id), (Favorite, Favorite.user_id),
                       (Label, Label.user_id), (PrivateNote, PrivateNote.user_id)):
        for row in db.query(col).filter(
                model.submission_id.in_(subs)).distinct().all():
            ids.add(row[0])
    users = []
    for uid in ids:
        u = db.get(User, uid)
        if u:
            users.append(u)
    return users


@router.post("/edicts/{edict_id}/interactors_list")
def interactors_list(edict_id: str, background: BackgroundTasks,
                     body: dict = Body(default=None),
                     user=Depends(current_user), db=Depends(get_db)):
    body = body or {}
    mode = body.get("mode", "plain_text")
    edict = _get_edict(db, edict_id)
    if mode != "pdf":
        users = _interactors(db, edict_id)
        show_emails = bool(body.get("show_emails", False))
        return [
            {"id": u.id, "name": u.name,
             **({"email": u.email} if show_emails else {})}
            for u in users
        ]
    job = Job(edict_id=edict_id, kind="pdf", status="processing")
    db.add(job)
    db.commit()
    background.add_task(_generate_pdf, job.id, edict_id, dict(body))
    return {"job_id": job.id, "status": "processing"}


def _generate_pdf(job_id, edict_id, options):
    db = PrejanusSession()
    try:
        edict = db.get(Edict, edict_id)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "b", 16)
        pdf.cell(0, 10, f"Relatorio - Edital {edict.title} ({edict.year})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        subs = db.query(Submission).filter(Submission.edict_id == edict_id).all()
        finalized = [s for s in subs if s.stats != "underreview"]
        pdf.cell(0, 8, f"Candidaturas finalizadas: {len(finalized)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Candidaturas em preenchimento: {len(subs) - len(finalized)}", new_x="LMARGIN", new_y="NEXT")
        if options.get("approved"):
            pdf.set_font("helvetica", "b", 12)
            pdf.cell(0, 8, "Aprovados", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            for s in subs:
                if s.stats == "approved":
                    advisors = ", ".join(
                        (db.get(User, uid).name if db.get(User, uid) else "")
                        for uid in (s.advisors or []))
                    pdf.cell(0, 8, f"{s.id} - orientador: {advisors}", new_x="LMARGIN", new_y="NEXT")
        if options.get("list_of_advisors"):
            pdf.set_font("helvetica", "b", 12)
            pdf.cell(0, 8, "Orientadores", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            for s in subs:
                for uid in s.advisors or []:
                    u = db.get(User, uid)
                    if u:
                        pdf.cell(0, 8, u.name + (f" ({u.email})" if options.get("show_emails") else ""), new_x="LMARGIN", new_y="NEXT")
        if options.get("relation"):
            pdf.set_font("helvetica", "b", 12)
            pdf.cell(0, 8, "Relacao de candidaturas", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            for s in subs:
                pdf.cell(0, 8, f"{s.id}: {s.stats}", new_x="LMARGIN", new_y="NEXT")
        if options.get("show_emails"):
            pdf.set_font("helvetica", "b", 12)
            pdf.cell(0, 8, "E-mails", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            for u in _interactors(db, edict_id):
                pdf.cell(0, 8, u.email, new_x="LMARGIN", new_y="NEXT")
        path = os.path.join(settings.TMP_DIR, f"report_{job_id}.pdf")
        pdf.output(path)
        job = db.get(Job, job_id)
        job.filename = path
        job.status = "ready"
        db.commit()
    finally:
        db.close()


@router.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(edict_id: str, background: BackgroundTasks,
                     user=Depends(current_user), db=Depends(get_db)):
    _get_edict(db, edict_id)
    job = Job(edict_id=edict_id, kind="csv", status="processing")
    db.add(job)
    db.commit()
    background.add_task(_generate_csv, job.id, edict_id)
    return {"job_id": job.id, "status": "processing"}


def _generate_csv(job_id, edict_id):
    db = PrejanusSession()
    try:
        subs = db.query(Submission).filter(Submission.edict_id == edict_id).all()
        teacher_ids = sorted({b.user_id for b in db.query(Bidding).all()})
        teachers = [db.get(User, tid) for tid in teacher_ids]
        header = ["#"] + [t.email if t else str(tid) for t, tid in zip(teachers, teacher_ids)]
        rows = [header]
        slot_row = ["slots"]
        for tid in teacher_ids:
            slot = db.query(Slot).filter(Slot.edict_id == edict_id, Slot.user_id == tid).first()
            slot_row.append(slot.amount if slot else "")
        rows.append(slot_row)
        for s in subs:
            row = [s.id]
            for tid in teacher_ids:
                b = db.get(Bidding, (s.id, tid))
                row.append(b.bidding if b else "")
            rows.append(row)
        path = os.path.join(settings.TMP_DIR, f"report_{job_id}.csv")
        with open(path, "w", newline="") as f:
            csv.writer(f).writerows(rows)
        job = db.get(Job, job_id)
        job.filename = path
        job.status = "ready"
        db.commit()
    finally:
        db.close()


@router.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    return _download(job_id, "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    return _download(job_id, "text/csv")


def _download(job_id, media_type):
    db = PrejanusSession()
    try:
        job = db.get(Job, job_id)
        if not job or job.status != "ready" or not job.filename or not os.path.exists(job.filename):
            raise HTTPException(status_code=404, detail="Report not ready")
        path = job.filename
        job.status = "consumed"
        job.filename = ""
        db.commit()
    finally:
        db.close()
    return FileResponse(path, media_type=media_type, headers={"Content-Disposition": "inline"})
