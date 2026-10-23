import asyncio
import csv
import os
from pathlib import Path

from fastapi import HTTPException, Response
from sqlalchemy import text

from config import settings
from database import SessionLocal

MEDIA = {"pdf": "application/pdf", "csv": "text/csv"}


def _tmp_path(job_id: str, ext: str) -> Path:
    return Path(settings.tmp_dir) / f"prejanus_{job_id}.{ext}"


def serve_report(job_id: str, ext: str) -> Response:
    path = _tmp_path(job_id, ext)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    content = path.read_bytes()
    path.unlink()
    return Response(
        content=content,
        media_type=MEDIA[ext],
        headers={"Content-Disposition": f'inline; filename="report.{ext}"'},
    )


def schedule_pdf(job_id: str, edict_id: int, options: dict) -> None:
    asyncio.get_running_loop().create_task(_generate_pdf(job_id, edict_id, options))


def schedule_csv(job_id: str, edict_id: int) -> None:
    asyncio.get_running_loop().create_task(_generate_csv(job_id, edict_id))


async def _report_data(edict_id: int) -> dict:
    async with SessionLocal() as s:
        edict = (
            await s.execute(text("select * from edict where id = :id"), {"id": edict_id})
        ).fetchone()
        submissions = (
            await s.execute(
                text("select * from submission where edict_id = :e order by id"),
                {"e": edict_id},
            )
        ).fetchall()
        biddings = (
            await s.execute(
                text(
                    'select l.user_id, u.name, u.email, l.label, l.submission_id'
                    ' from labels l join "user" u on u.id = l.user_id'
                    " where l.context_type = 'bidding' and l.submission_id in"
                    " (select id from submission where edict_id = :e)"
                ),
                {"e": edict_id},
            )
        ).fetchall()
        slots = (
            await s.execute(
                text(
                    'select u.id, u.name, u.email, coalesce(sl.slots, 0) as slots'
                    ' from "user" u left join user_edict_slots sl'
                    " on sl.user_id = u.id and sl.edict_id = :e"
                    " where u.id in (select user_id from user_edict_slots where edict_id = :e)",
                ),
                {"e": edict_id},
            )
        ).fetchall()
        advisors = (
            await s.execute(
                text(
                    'select distinct u.id, u.name, u.email from "user" u'
                    " where u.id in (select advisor_id from submission"
                    " where edict_id = :e and advisor_id is not null)"
                ),
                {"e": edict_id},
            )
        ).fetchall()
        return {
            "edict": dict(edict._mapping) if edict else {},
            "submissions": [dict(r._mapping) for r in submissions],
            "biddings": [dict(r._mapping) for r in biddings],
            "slots": [dict(r._mapping) for r in slots],
            "advisors": [dict(r._mapping) for r in advisors],
        }


async def _generate_pdf(job_id: str, edict_id: int, options: dict) -> None:
    from fpdf import FPDF

    data = await _report_data(edict_id)
    edict = data["edict"]
    subs = data["submissions"]
    approved = [s for s in subs if s["stats"] == "approved"]
    refused = [s for s in subs if s["stats"] == "refused"]
    underreview = [s for s in subs if s["stats"] == "underreview"]

    pdf = FPDF()
    pdf.add_page()
    for asset in ("logo.png", "usp.png"):
        path = Path(settings.assets_dir) / asset
        if path.exists():
            pdf.image(str(path), w=30)
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 16)
    title = f"Relatório do Edital {edict.get('title', '')} ({edict.get('year', '')})"
    pdf.multi_cell(0, 8, title)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"Ano: {edict.get('year', '')} - Semestre: {edict.get('semester', '')}")

    if options.get("general_statistics"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Estatísticas gerais", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total de candidaturas: {len(subs)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Aprovadas: {len(approved)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Recusadas: {len(refused)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Em análise: {len(underreview)}", new_x="LMARGIN", new_y="NEXT")

    if options.get("list_of_advisors"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Orientadores", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for a in data["advisors"]:
            line = a["name"]
            if options.get("show_emails"):
                line += f" <{a['email']}>"
            pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    if options.get("relation"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Relação de aprovados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in approved:
            pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")

    if options.get("approved"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Aprovados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in approved:
            pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")

    if options.get("refused"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Recusados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in refused:
            pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")

    if options.get("underreview"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Em análise", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in underreview:
            pdf.cell(0, 6, f"Candidatura #{s['id']}", new_x="LMARGIN", new_y="NEXT")

    if options.get("show_emails"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "E-mails dos orientadores", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for a in data["advisors"]:
            pdf.cell(0, 6, a["email"] or "", new_x="LMARGIN", new_y="NEXT")

    path = _tmp_path(job_id, "pdf")
    pdf.output(str(path))


async def _generate_csv(job_id: str, edict_id: int) -> None:
    data = await _report_data(edict_id)
    teachers = sorted({b["user_id"] for b in data["biddings"]})
    user_by_id = {s["id"]: s for s in data["slots"]}
    emails = []
    for uid in teachers:
        u = user_by_id.get(uid)
        emails.append(u["email"] if u else str(uid))

    bidding_by_sub: dict = {}
    for b in data["biddings"]:
        bidding_by_sub.setdefault(b["submission_id"], {})[b["user_id"]] = b["label"]

    slot_by_user = {s["id"]: str(s["slots"]) for s in data["slots"]}

    import services.forms_db as forms_db

    sub_emails = {}
    for s in data["submissions"]:
        fr = await forms_db.get_response(s["candidate_form_id"])
        sub_emails[s["id"]] = fr.email if fr else ""

    path = _tmp_path(job_id, "csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["#"] + emails)
        writer.writerow(["slots"] + [slot_by_user.get(uid, "0") for uid in teachers])
        for s in data["submissions"]:
            row = [sub_emails.get(s["id"], "")]
            bids = bidding_by_sub.get(s["id"], {})
            row += [bids.get(uid, "") for uid in teachers]
            writer.writerow(row)
