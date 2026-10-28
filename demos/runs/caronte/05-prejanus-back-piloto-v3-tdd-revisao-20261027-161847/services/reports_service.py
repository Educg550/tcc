import csv
import os
import uuid

from fpdf import FPDF
from sqlalchemy import text

from database import Session
from services import forms_service as forms
from services.submissions_service import get_edict

JOBS = {}  # job_id -> absolute path of the generated file


def _safe(value):
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


def new_job(extension):
    job_id = uuid.uuid4().hex
    path = os.path.join("/tmp", f"{job_id}.{extension}")
    JOBS[job_id] = path
    return job_id, path


def _interactors(edict_id):
    query = text(
        'select distinct u.id, u.name, u.email from "user" u where u.id in ('
        " select user_id from comment where submission_id in (select id from submission where edict_id = :e)"
        " union select user_id from favorites where submission_id in (select id from submission where edict_id = :e)"
        " union select user_id from labels where submission_id in (select id from submission where edict_id = :e)"
        " union select user_id from private_note where submission_id in (select id from submission where edict_id = :e)"
        ") order by u.id"
    )
    with Session() as s:
        rows = s.execute(query, {"e": edict_id}).mappings().all()
    return [dict(r) for r in rows]


def _edict_submissions(edict_id):
    with Session() as s:
        rows = s.execute(
            text("select * from submission where edict_id = :e order by id"),
            {"e": edict_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def _candidate_email(sub):
    resp = forms.get_response(sub["candidate_form_id"])
    return (resp or {}).get("email") or ""


def _statistics(edict):
    try:
        form_id = int(edict["candidate_forms"])
    except (TypeError, ValueError):
        return 0, 0
    with forms.FormsSession() as s:
        total = s.execute(
            text("select count(*) from form_response where form_id = :f"), {"f": form_id}
        ).scalar_one()
        finished = s.execute(
            text("select count(*) from form_response where form_id = :f and submitted_at is not null"),
            {"f": form_id},
        ).scalar_one()
    return finished, max(total - finished, 0)


def generate_pdf(job_id, path, edict_id, options):
    edict = get_edict(edict_id) or {}
    options = options or {}
    subs = _edict_submissions(edict_id)
    finished, in_progress = _statistics(edict)
    approved = [s for s in subs if s["stats"] == "approved"]
    pdf = FPDF()
    pdf.add_page()
    for image in ("assets/logo.png", "assets/usp.png"):
        if os.path.exists(image):
            pdf.image(image, w=30)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, text=f"Relatorio do Edital {edict.get('title', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, text=f"Ano: {edict.get('year', '')} - Semestre: {edict.get('semester', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    if options.get("general_statistics"):
        pdf.cell(0, 8, text=f"Candidaturas finalizadas: {finished}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, text=f"Candidaturas em preenchimento: {in_progress}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    if options.get("approved") or options.get("relation"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, text="Candidatos aprovados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for sub in approved:
            advisor = sub["advisor_id"] or ""
            pdf.cell(0, 7, text=f"Aprovado: inscricao {sub['id']} - Orientador: {advisor}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    if options.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, text="Orientadores", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        with Session() as s:
            advisors = s.execute(
                text(
                    'select distinct u.id, u.name, u.email from "user" u'
                    " where u.id in (select advisor_id from submission"
                    " where edict_id = :e and advisor_id is not null)"
                ),
                {"e": edict_id},
            ).mappings().all()
        for a in advisors:
            pdf.cell(0, 7, text=_safe(f"{a['name']} <{a['email'] or ''}>"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    if options.get("show_emails"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, text="Lista de e-mails", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for user in _interactors(edict_id):
            pdf.cell(0, 7, text=_safe(f"{user['name']} <{user['email'] or ''}>"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    if options.get("refused") or options.get("underreview"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, text="Situacoes", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for sub in subs:
            if (options.get("refused") and sub["stats"] == "refused") or (
                options.get("underreview") and sub["stats"] == "underreview"
            ):
                pdf.cell(0, 7, text=f"Inscricao {sub['id']}: {sub['stats']}", new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)
    JOBS[job_id] = path


def generate_csv(job_id, path, edict_id):
    edict = get_edict(edict_id) or {}
    with Session() as s:
        teachers = s.execute(
            text(
                'select distinct u.id, u.email from "user" u join labels l on l.user_id = u.id'
                " where l.context_type = 'bidding' and l.submission_id in"
                " (select id from submission where edict_id = :e) order by u.id"
            ),
            {"e": edict_id},
        ).mappings().all()
        slots = {
            r["user_id"]: r["slots"]
            for r in s.execute(
                text("select user_id, slots from user_edict_slots where edict_id = :e"),
                {"e": edict_id},
            ).mappings().all()
        }
        bids = s.execute(
            text(
                "select user_id, submission_id, label from labels"
                " where context_type = 'bidding' and submission_id in"
                " (select id from submission where edict_id = :e)"
            ),
            {"e": edict_id},
        ).mappings().all()
    subs = _edict_submissions(edict_id)
    emails = [t["email"] or "" for t in teachers]
    bid_map = {(b["user_id"], b["submission_id"]): b["label"] for b in bids}
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["#"] + emails)
        writer.writerow(["slots"] + [str(slots.get(t["id"]) or "") for t in teachers])
        for sub in subs:
            row = [_candidate_email(sub)]
            for t in teachers:
                row.append(bid_map.get((t["id"], sub["id"]), ""))
            writer.writerow(row)
    JOBS[job_id] = path


def read_and_remove(job_id):
    path = JOBS.get(job_id)
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        content = f.read()
    os.remove(path)
    return content
