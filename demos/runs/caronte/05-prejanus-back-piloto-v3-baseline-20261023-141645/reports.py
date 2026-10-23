import csv
import uuid
from datetime import date
from pathlib import Path

from fpdf import FPDF
from sqlalchemy import text

from db import PrejanusSession

JOBS: dict[str, dict] = {}
TMP = Path("/tmp")


def new_job(kind: str) -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"kind": kind, "path": None}
    return job_id


async def _interactors(edict_id: int) -> list[dict]:
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select distinct u.id, u.name, u.email from \"user\" u "
                    "join submission s on true where s.edict_id = :e and ("
                    "u.id in (select user_id from comment c join submission s2 on c.submission_id = s2.id where s2.edict_id = :e) or "
                    "u.id in (select user_id from favorites f join submission s2 on f.submission_id = s2.id where s2.edict_id = :e) or "
                    "u.id in (select user_id from labels l join submission s2 on l.submission_id = s2.id where s2.edict_id = :e) or "
                    "u.id in (select user_id from private_note p join submission s2 on p.submission_id = s2.id where s2.edict_id = :e))"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


async def _report_data(edict_id: int) -> dict:
    async with PrejanusSession() as db:
        edict = (
            await db.execute(text("select * from edict where id = :i"), {"i": edict_id})
        ).mappings().first()
        submissions = (
            await db.execute(
                text(
                    "select s.*, u.name as advisor_name, u.email as advisor_email "
                    "from submission s left join \"user\" u on s.advisor_id = u.id "
                    "where s.edict_id = :e order by s.id"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        biddings = (
            await db.execute(
                text(
                    "select l.submission_id, l.user_id, l.label, u.name, u.email from labels l "
                    "join \"user\" u on l.user_id = u.id "
                    "where l.context_type = 'bidding' and l.submission_id in "
                    "(select id from submission where edict_id = :e)"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        slots = (
            await db.execute(
                text(
                    "select u.email, u.name, sl.slots from user_edict_slots sl "
                    "join \"user\" u on sl.user_id = u.id where sl.edict_id = :e"
                ),
                {"e": edict_id},
            )
        ).mappings().all()
    return {
        "edict": dict(edict) if edict else {},
        "submissions": [dict(r) for r in submissions],
        "biddings": [dict(r) for r in biddings],
        "slots": [dict(r) for r in slots],
    }


async def generate_pdf(job_id: str, edict_id: int, options: dict) -> None:
    data = await _report_data(edict_id)
    edict = data["edict"]
    path = TMP / f"report_{job_id}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    for img in ("assets/logo.png", "assets/usp.png"):
        if Path(img).exists():
            pdf.image(img, w=30)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, f"Relatorio do Edital - {edict.get('title', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Ano: {edict.get('year', '')} - Semestre: {edict.get('semester', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    subs = data["submissions"]
    if options.get("general_statistics"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "Estatisticas gerais", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total de candidaturas: {len(subs)}", new_x="LMARGIN", new_y="NEXT")
        for stat in ("approved", "refused", "underreview", "waitlist"):
            n = sum(1 for s in subs if s["stats"] == stat)
            pdf.cell(0, 6, f"{stat}: {n}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if options.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "Orientadores", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in subs:
            if s["advisor_name"]:
                pdf.cell(0, 6, f"{s['advisor_name']} <{s['advisor_email'] or ''}>", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if options.get("relation") or options.get("approved"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "Aprovados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in subs:
            if s["stats"] == "approved":
                line = f"Candidatura #{s['id']}"
                if s["advisor_name"]:
                    line += f" - Orientador: {s['advisor_name']}"
                pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if options.get("refused"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "Reprovados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in subs:
            if s["stats"] == "refused":
                pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if options.get("underreview"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "Em revisao", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in subs:
            if s["stats"] == "underreview":
                pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if options.get("show_emails"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "E-mails", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in subs:
            if s["advisor_email"]:
                pdf.cell(0, 6, s["advisor_email"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    pdf.output(str(path))
    JOBS[job_id]["path"] = str(path)


async def generate_csv(job_id: str, edict_id: int) -> None:
    data = await _report_data(edict_id)
    teachers = []
    seen = set()
    for b in data["biddings"]:
        if b["user_id"] not in seen:
            seen.add(b["user_id"])
            teachers.append({"user_id": b["user_id"], "email": b["email"]})
    slots_map = {s["email"]: s["slots"] for s in data["slots"]}
    path = TMP / f"biddings_{job_id}.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["#"] + [t["email"] for t in teachers])
        writer.writerow(["slots"] + [str(slots_map.get(t["email"], "") or "") for t in teachers])
        import forms_service as forms

        for s in data["submissions"]:
            resp = await forms.get_response_row(s["candidate_form_id"])
            row = [resp["email"] if resp else s["candidate_form_id"]]
            for t in teachers:
                bid = next(
                    (b["label"] for b in data["biddings"] if b["submission_id"] == s["id"] and b["user_id"] == t["user_id"]),
                    "",
                )
                row.append(bid)
            writer.writerow(row)
    JOBS[job_id]["path"] = str(path)
