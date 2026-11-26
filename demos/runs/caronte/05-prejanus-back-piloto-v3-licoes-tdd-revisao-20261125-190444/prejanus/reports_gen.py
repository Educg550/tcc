"""Geração de relatórios PDF e CSV em segundo plano."""

import csv
import os

from fpdf import FPDF
from sqlalchemy import select, text

from prejanus import forms_db, submissions_service
from prejanus.db import FormsSessionLocal, SessionLocal
from prejanus.models import Comment, Edict, Favorite, Label, PrivateNote, Submission, User, UserEdictSlots


def _pdf_path(job_id: str) -> str:
    return f"/tmp/prejanus_{job_id}.pdf"


def _csv_path(job_id: str) -> str:
    return f"/tmp/prejanus_{job_id}.csv"


class ReportPDF(FPDF):
    """multi_cell em bloco: volta à margem esquerda após cada célula."""

    def multi_cell(self, w, h=None, text="", **kwargs):
        left = self.l_margin
        try:
            return super().multi_cell(w, h, text, **kwargs)
        finally:
            self.set_x(left)


async def _interactors(db, edict_id: int):
    result = await db.execute(
        text(
            "select distinct u.id, u.name, u.email from \"user\" u"
            " where u.id in ("
            "  select c.user_id from comment c join submission s on s.id = c.submission_id where s.edict_id = :e"
            "  union select f.user_id from favorites f join submission s on s.id = f.submission_id where s.edict_id = :e"
            "  union select l.user_id from labels l join submission s on s.id = l.submission_id where s.edict_id = :e"
            "  union select p.user_id from private_note p join submission s on s.id = p.submission_id where s.edict_id = :e"
            ") order by u.id"
        ),
        {"e": edict_id},
    )
    return [dict(r) for r in result.mappings().all()]


async def generate_pdf(job_id: str, edict_id: int, options: dict) -> None:
    async with SessionLocal() as db, FormsSessionLocal() as fdb:
        edict = await db.get(Edict, edict_id)
        subs = (
            await db.execute(select(Submission).where(Submission.edict_id == edict_id))
        ).scalars().all()
        stats_counts = {}
        for sub in subs:
            stats_counts[sub.stats] = stats_counts.get(sub.stats, 0) + 1
        finalized = in_progress = 0
        try:
            cand_form = int(str(edict.candidate_forms))
            rows = await fdb.execute(
                text(
                    "select count(*) filter (where submitted_at is not null) as fin,"
                    " count(*) filter (where submitted_at is null) as prog"
                    " from form_response where form_id = :f"
                ),
                {"f": cand_form},
            )
            row = rows.mappings().first()
            finalized = row["fin"] or 0
            in_progress = row["prog"] or 0
        except (TypeError, ValueError):
            pass
        approved = []
        for sub in subs:
            if sub.stats == "approved":
                advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
                summary = await submissions_service.submission_summary(db, fdb, edict, sub, User(id=0, name="", email="", role=""))
                approved.append(
                    {
                        "name": summary.get("name") or "",
                        "email": summary.get("email") or "",
                        "advisor": advisor.name if advisor else "-",
                    }
                )
        interactors = await _interactors(db, edict_id)

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if os.path.exists("assets/logo.png"):
        pdf.image("assets/logo.png", x=10, y=8, w=33)
    if os.path.exists("assets/usp.png"):
        pdf.image("assets/usp.png", x=170, y=8, w=30)
    pdf.ln(30)
    pdf.set_font("helvetica", "B", 16)
    pdf.multi_cell(0, 10, f"Relatorio do edital: {edict.title}")
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 8, f"Ano: {edict.year} - Semestre: {edict.semester} - Tipo: {edict.type}")

    if options.get("general_statistics"):
        pdf.set_font("helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Estatisticas gerais")
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 6, f"Candidaturas finalizadas: {finalized}")
        pdf.multi_cell(0, 6, f"Candidaturas em preenchimento: {in_progress}")
        for stats, count in sorted(stats_counts.items()):
            pdf.multi_cell(0, 6, f"Situacao {stats}: {count}")

    if options.get("approved") or options.get("relation"):
        pdf.set_font("helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Candidatos aprovados")
        pdf.set_font("helvetica", "", 11)
        for item in approved:
            line = f"{item['name']}"
            if options.get("relation") or options.get("list_of_advisors"):
                line += f" - Orientador: {item['advisor']}"
            if options.get("show_emails"):
                line += f" - {item['email']}"
            pdf.multi_cell(0, 6, line)

    if options.get("refused"):
        pdf.set_font("helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Candidatos reprovados")
        pdf.set_font("helvetica", "", 11)
        for sub in subs:
            if sub.stats == "refused":
                pdf.multi_cell(0, 6, f"Inscricao {sub.id}")

    if options.get("underreview"):
        pdf.set_font("helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Candidatos em revisao")
        pdf.set_font("helvetica", "", 11)
        for sub in subs:
            if sub.stats == "underreview":
                pdf.multi_cell(0, 6, f"Inscricao {sub.id}")

    if options.get("list_of_advisors"):
        pdf.set_font("helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Orientadores")
        pdf.set_font("helvetica", "", 11)
        for item in approved:
            pdf.multi_cell(0, 6, item["advisor"])

    pdf.set_font("helvetica", "B", 13)
    pdf.multi_cell(0, 8, "Interatores")
    pdf.set_font("helvetica", "", 11)
    for user in interactors:
        line = f"{user['name']}"
        if options.get("show_emails"):
            line += f" - {user['email']}"
        pdf.multi_cell(0, 6, line)

    pdf.output(_pdf_path(job_id))


async def generate_csv(job_id: str, edict_id: int) -> None:
    async with SessionLocal() as db, FormsSessionLocal() as fdb:
        edict = await db.get(Edict, edict_id)
        subs = (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict_id).order_by(Submission.id)
            )
        ).scalars().all()
        bidding_rows = (
            await db.execute(
                text(
                    "select l.user_id, l.submission_id, l.label, u.email from labels l"
                    " join submission s on s.id = l.submission_id"
                    " join \"user\" u on u.id = l.user_id"
                    " where s.edict_id = :e and l.context_type = 'bidding'"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        slots_rows = (
            await db.execute(
                text(
                    "select u.email, sl.slots from user_edict_slots sl"
                    " join \"user\" u on u.id = sl.user_id where sl.edict_id = :e"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        candidate_emails = {}
        try:
            cand_form = int(str(edict.candidate_forms))
            for resp in await forms_db.get_submissions_raw(fdb, cand_form):
                candidate_emails[resp["id"]] = resp.get("email") or ""
        except (TypeError, ValueError):
            pass

    docentes = []
    seen = set()
    for row in bidding_rows:
        if row["label"] and row["email"] not in seen:
            seen.add(row["email"])
            docentes.append(row["email"])
    slots_by_email = {r["email"]: r["slots"] for r in slots_rows}
    bidding_by_sub: dict = {}
    for row in bidding_rows:
        bidding_by_sub.setdefault(row["submission_id"], {})[row["email"]] = row["label"]

    path = _csv_path(job_id)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["#"] + docentes)
        writer.writerow(["slots"] + [str(slots_by_email.get(d) or 0) for d in docentes])
        for sub in subs:
            email = candidate_emails.get(sub.candidate_form_id, "")
            row = [email]
            for docente in docentes:
                row.append(bidding_by_sub.get(sub.id, {}).get(docente, ""))
            writer.writerow(row)
