import csv
import io
import uuid
from datetime import datetime, timezone

from fpdf import FPDF
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import LOGO_PATH, TMP_DIR, USP_LOGO_PATH
from services import forms_service, submission_service

JOBS: dict[str, str] = {}


def new_job(extension: str) -> tuple[str, str]:
    job_id = str(uuid.uuid4())
    path = f"{TMP_DIR}/{job_id}.{extension}"
    JOBS[job_id] = path
    return job_id, path


async def _edict_data(db: AsyncSession, fs: AsyncSession, edict: dict) -> dict:
    submissions = []
    result = await db.execute(
        text("select * from submission where edict_id = :eid order by id"),
        {"eid": edict["id"]},
    )
    rows = [dict(r) for r in result.mappings()]
    for row in rows:
        response = await forms_service.get_response(fs, row["candidate_form_id"])
        values = await forms_service.get_response_values(fs, row["candidate_form_id"])
        mapping_row = await submission_service.get_mapping(
            db, edict["id"], "candidate", row["candidate_form_version"]
        )
        tree = mapping_row["mapping"] if mapping_row else None
        name = None
        email = None
        if tree:
            name = submission_service.resolve_value(tree, ("personal", "name"), values)
            email = submission_service.resolve_value(tree, ("personal", "email"), values)
        advisor = await submission_service.get_advisor(db, row.get("advisor_id"))
        submissions.append(
            {
                "id": row["id"],
                "name": name,
                "email": email or (response.get("email") if response else None),
                "stats": row["stats"],
                "advisor": advisor,
                "submitted": response.get("submitted_at") is not None if response else False,
            }
        )
    return {"submissions": submissions}


async def generate_pdf(db: AsyncSession, fs: AsyncSession, edict: dict, options) -> str:
    data = await _edict_data(db, fs, edict)
    submissions = data["submissions"]
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.image(LOGO_PATH, w=30)
    except (RuntimeError, FileNotFoundError):
        pass
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Relatorio do Edital {edict['id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"{edict['title']} - Ano {edict['year']}", new_x="LMARGIN", new_y="NEXT")

    if options.general_statistics:
        finished = sum(1 for s in submissions if s["submitted"])
        in_progress = sum(1 for s in submissions if not s["submitted"])
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Estatisticas", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Candidaturas finalizadas: {finished}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Candidaturas em preenchimento: {in_progress}", new_x="LMARGIN", new_y="NEXT")

    for section, key in (
        ("Aprovados", "approved"),
        ("Reprovados", "refused"),
        ("Em revisao", "underreview"),
    ):
        if getattr(options, key):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, section, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 12)
            for s in submissions:
                if s["stats"] == key:
                    line = s["name"] or f"Submission {s['id']}"
                    if options.show_emails and s["email"]:
                        line += f" ({s['email']})"
                    pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")

    if options.relation or options.list_of_advisors:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Relacao de aprovados e orientadores", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        for s in submissions:
            if s["stats"] == "approved":
                advisor = s["advisor"]["name"] if s["advisor"] else "Sem orientador"
                line = f"{s['name'] or s['id']} - {advisor}"
                if options.show_emails and s["email"]:
                    line += f" ({s['email']})"
                pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")

    if options.show_emails:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Lista de e-mails", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        for s in submissions:
            if s["email"]:
                pdf.cell(0, 8, s["email"], new_x="LMARGIN", new_y="NEXT")

    try:
        pdf.image(USP_LOGO_PATH, w=30)
    except (RuntimeError, FileNotFoundError):
        pass
    job_id, path = new_job("pdf")
    pdf.output(path)
    return job_id


async def generate_csv(db: AsyncSession, fs: AsyncSession, edict: dict) -> str:
    result = await db.execute(
        text(
            "select distinct l.user_id, u.name, u.email, s.slots from labels l "
            'join "user" u on u.id = l.user_id '
            "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = :eid "
            "where l.context_type = 'bidding' and l.submission_id in "
            "(select id from submission where edict_id = :eid) order by l.user_id"
        ),
        {"eid": edict["id"]},
    )
    teachers = [dict(r) for r in result.mappings()]

    subs = await db.execute(
        text("select * from submission where edict_id = :eid order by id"), {"eid": edict["id"]}
    )
    submissions = [dict(r) for r in subs.mappings()]

    biddings: dict[int, dict[int, str]] = {}
    for sub in submissions:
        row = await db.execute(
            text(
                "select user_id, label from labels where submission_id = :sid "
                "and context_type = 'bidding'"
            ),
            {"sid": sub["id"]},
        )
        biddings[sub["id"]] = {r.user_id: r.label or "" for r in row.mappings()}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["#"] + [t["email"] or t["name"] for t in teachers])
    writer.writerow(["slots"] + [str(t["slots"] or 0) for t in teachers])
    for sub in submissions:
        response = await forms_service.get_response(fs, sub["candidate_form_id"])
        email = response.get("email") if response else None
        if not email:
            values = await forms_service.get_response_values(fs, sub["candidate_form_id"])
            mapping_row = await submission_service.get_mapping(
                db, edict["id"], "candidate", sub["candidate_form_version"]
            )
            if mapping_row:
                email = submission_service.resolve_value(
                    mapping_row["mapping"], ("personal", "email"), values
                )
        row = [email or ""]
        for teacher in teachers:
            row.append(biddings.get(sub["id"], {}).get(teacher["user_id"], ""))
        writer.writerow(row)

    job_id, path = new_job("csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(buffer.getvalue())
    return job_id


def now_utc():
    return datetime.now(timezone.utc)
