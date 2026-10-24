import asyncio
import csv
import io
import uuid

from fastapi import HTTPException, Response
from sqlalchemy import text

from src.services.submissions_service import submission_context

jobs: dict[str, dict] = {}
_tasks: set = set()


def start_job(kind: str, builder, *args) -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"kind": kind, "data": None}
    task = asyncio.create_task(_run(job_id, builder, args))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return job_id


async def _run(job_id: str, builder, args) -> None:
    try:
        data = await asyncio.to_thread(builder, *args)
    except Exception:
        import traceback

        data = raw_pdf(["REPORT BUILD ERROR", traceback.format_exc()])
    if job_id in jobs:
        jobs[job_id]["data"] = data


def download(job_id: str, media_type: str, extension: str) -> Response:
    job = jobs.get(job_id)
    if job is None or job.get("data") is None:
        raise HTTPException(status_code=404, detail="Report not found")
    data = jobs.pop(job_id)["data"]
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{job_id}{extension}"'},
    )


def _latin(value: str) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _pdf_escape(value: str) -> str:
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def raw_pdf(lines: list) -> bytes:
    stream = "BT /F1 12 Tf 72 720 Td\n"
    for line in lines:
        stream += f"({_pdf_escape(_latin(line))}) Tj 0 -14 Td\n"
    stream += "ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    body = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref = "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    trailer = (
        f"xref\n0 6\n0000000000 65535 f \n{xref}trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{len(body)}\n%%EOF\n"
    )
    return body + trailer.encode("latin-1")


def build_pdf(data: dict) -> bytes:
    lines = [data["title"], ""]
    for header, section_lines in data["sections"]:
        lines.append(header)
        lines.extend(section_lines)
        lines.append("")
    return raw_pdf(lines)


def build_csv(data: dict) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["#"] + data["columns"])
    for key, values in data["rows"]:
        writer.writerow([key] + [values.get(column, "") for column in data["columns"]])
    return buffer.getvalue().encode("utf-8")


async def get_interactors(db, edict_id: int) -> list[dict]:
    result = await db.execute(
        text(
            'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
            "SELECT c.user_id FROM comment c JOIN submission s ON s.id = c.submission_id "
            "WHERE s.edict_id = :e "
            "UNION SELECT f.user_id FROM favorites f JOIN submission s ON s.id = f.submission_id "
            "WHERE s.edict_id = :e "
            "UNION SELECT l.user_id FROM labels l JOIN submission s ON s.id = l.submission_id "
            "WHERE s.edict_id = :e "
            "UNION SELECT p.user_id FROM private_note p JOIN submission s ON s.id = p.submission_id "
            "WHERE s.edict_id = :e) ORDER BY u.id"
        ),
        {"e": edict_id},
    )
    return [dict(r._mapping) for r in result]


async def _edict_candidates(db, fdb, edict: dict) -> list[dict]:
    result = await db.execute(
        text("SELECT * FROM submission WHERE edict_id = :e ORDER BY id"), {"e": edict["id"]}
    )
    candidates = []
    for sub in [dict(r._mapping) for r in result]:
        data, response, _ = await submission_context(db, fdb, edict, sub)
        candidates.append(
            {
                "name": data.get("name") or "",
                "email": data.get("email") or (response["email"] if response else ""),
                "stats": sub["stats"],
            }
        )
    return candidates


async def collect_pdf_data(db, fdb, edict: dict, options: dict) -> dict:
    form_id = int(edict["candidate_forms"])
    finalized = (
        await fdb.execute(
            text(
                "SELECT count(*) FROM form_response "
                "WHERE form_id = :f AND submitted_at IS NOT NULL"
            ),
            {"f": form_id},
        )
    ).scalar()
    draft = (
        await fdb.execute(
            text(
                "SELECT count(*) FROM form_response "
                "WHERE form_id = :f AND submitted_at IS NULL"
            ),
            {"f": form_id},
        )
    ).scalar()
    candidates = await _edict_candidates(db, fdb, edict)
    sections = []
    if options.get("relation"):
        sections.append(
            (
                "Relação de candidatos",
                [
                    c["name"] + (f" - {c['email']}" if options.get("show_emails") else "")
                    for c in candidates
                ],
            )
        )
    for stats, header in (
        ("approved", "Candidatos aprovados"),
        ("refused", "Candidatos recusados"),
        ("underreview", "Candidatos em análise"),
    ):
        if options.get(stats):
            sections.append((header, [c["name"] for c in candidates if c["stats"] == stats]))
    if options.get("general_statistics"):
        sections.append(
            (
                "Estatísticas Gerais",
                [
                    f"{finalized} submissões finalizadas",
                    f"{draft} submissões em preenchimento",
                ],
            )
        )
    if options.get("list_of_advisors"):
        result = await db.execute(
            text(
                'SELECT u.name, u.email, s.slots FROM "user" u '
                "JOIN user_edict_slots s ON s.user_id = u.id WHERE s.edict_id = :e"
            ),
            {"e": edict["id"]},
        )
        sections.append(
            ("Anexo - Orientadores", [f"{r[0]}: {r[2]}" for r in result])
        )
    sections.append(("Observações Finais", [f"Total de candidatos: {len(candidates)}"]))
    return {"title": f"Relatório do edital {edict['title']}", "sections": sections}


async def collect_csv_data(db, fdb, edict: dict) -> dict:
    edict_id = edict["id"]
    result = await db.execute(
        text(
            'SELECT u.id, u.email, s.slots FROM "user" u '
            "JOIN user_edict_slots s ON s.user_id = u.id WHERE s.edict_id = :e"
        ),
        {"e": edict_id},
    )
    advisors = {r[0]: {"email": r[1], "slots": r[2]} for r in result}
    result = await db.execute(
        text(
            'SELECT DISTINCT u.id, u.email FROM "user" u '
            "JOIN labels l ON l.user_id = u.id "
            "JOIN submission sub ON sub.id = l.submission_id "
            "WHERE sub.edict_id = :e AND l.context_type = 'bidding'"
        ),
        {"e": edict_id},
    )
    for uid, email in result:
        if uid not in advisors:
            advisors[uid] = {"email": email, "slots": None}
    columns = sorted(a["email"] for a in advisors.values())
    rows = [
        (
            "slots",
            {a["email"]: str(a["slots"]) if a["slots"] is not None else "" for a in advisors.values()},
        )
    ]
    result = await db.execute(
        text("SELECT id FROM submission WHERE edict_id = :e ORDER BY id"), {"e": edict_id}
    )
    submission_ids = [r[0] for r in result]
    candidates = await _edict_candidates(db, fdb, edict)
    for sid, candidate in zip(submission_ids, candidates):
        result = await db.execute(
            text(
                "SELECT l.label, u.email FROM labels l "
                'JOIN "user" u ON u.id = l.user_id '
                "WHERE l.submission_id = :s AND l.context_type = 'bidding'"
            ),
            {"s": sid},
        )
        rows.append((candidate["email"], {email: label for label, email in result}))
    return {"columns": columns, "rows": rows}
