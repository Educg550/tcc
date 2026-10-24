"""Relatórios: lista de interatores, PDF e CSV de interesses, com jobs em /tmp."""
import csv
import os
import threading
import uuid

from fpdf import FPDF
from sqlalchemy import text

from ..db import SessionForms, SessionLocal
from .forms_integration import get_response
from .submissions import build_submission_item, get_edict

JOBS: dict = {}


def start_job(kind: str, task, *args) -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"kind": kind, "ready": False, "path": f"/tmp/{job_id}.{kind}"}
    threading.Thread(target=_run, args=(job_id, task, args), daemon=True).start()
    return job_id


def _run(job_id, task, args):
    try:
        task(job_id, *args)
        JOBS[job_id]["ready"] = True
    except Exception:
        JOBS.pop(job_id, None)


def pop_ready(job_id: str, kind: str):
    job = JOBS.get(job_id)
    if (
        not job
        or job["kind"] != kind
        or not job["ready"]
        or not os.path.exists(job["path"])
    ):
        return None
    JOBS.pop(job_id, None)
    return job["path"]


def interactors_list(db, edict_id) -> list[dict]:
    rows = db.execute(
        text('SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
             "SELECT user_id FROM comment WHERE submission_id IN "
             "(SELECT id FROM submission WHERE edict_id = :e) "
             "UNION SELECT user_id FROM favorites WHERE submission_id IN "
             "(SELECT id FROM submission WHERE edict_id = :e) "
             "UNION SELECT user_id FROM labels WHERE submission_id IN "
             "(SELECT id FROM submission WHERE edict_id = :e) "
             "UNION SELECT user_id FROM private_note WHERE submission_id IN "
             "(SELECT id FROM submission WHERE edict_id = :e)) "
             "ORDER BY u.id"),
        {"e": edict_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def _latin(value: str) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _pdf_lines(edict, items, options, finalized, in_progress):
    lines = [(edict["title"], True)]

    def section(title, values):
        lines.append((title, True))
        for value in values or ["(sem registros)"]:
            lines.append((value, False))

    if options.get("relation"):
        section(
            "Relação de candidatos",
            [
                it["name"] + (
                    f" ({it['email']})"
                    if options.get("show_emails") and it["email"] else ""
                )
                for it in items
            ],
        )
    if options.get("approved"):
        section("Candidatos aprovados", [it["name"] for it in items if it["stats"] == "approved"])
    if options.get("refused"):
        section("Candidatos recusados", [it["name"] for it in items if it["stats"] == "refused"])
    if options.get("underreview"):
        section("Candidatos em análise", [it["name"] for it in items if it["stats"] == "underreview"])
    if options.get("list_of_advisors"):
        names = sorted({it["advisor"]["name"] for it in items if it["advisor"]})
        section("Lista de orientadores", names)
    if options.get("general_statistics"):
        section(
            "Estatísticas Gerais",
            [
                f"{finalized} submissões finalizadas",
                f"{in_progress} submissões em andamento",
            ],
        )
    section("Observações Finais", ["Relatório gerado pelo sistema de pós-graduação."])
    return lines


def _fpdf_render(path, lines) -> None:
    pdf = FPDF()
    pdf.add_page()
    for text, is_header in lines:
        pdf.set_font("Helvetica", "B" if is_header else "", 16 if is_header else 11)
        pdf.multi_cell(0, 8 if is_header else 6, _latin(text))
    pdf.output(path)


def _fallback_pdf(path, lines) -> None:
    def esc(value):
        return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    parts = ["BT"]
    y = 800
    for text, _ in lines:
        parts.append(f"/F1 11 Tf 40 {y} Td ({esc(_latin(text))}) Tj")
        y -= 16
    parts.append("ET")
    stream = "\n".join(parts).encode("cp1252", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    body = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = "".join(f"{o:010d} 00000 n \n" for o in offsets)
    body += (
        f"xref\n0 6\n0000000000 65535 f \n{xref}trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{len(body)}\n%%EOF\n"
    ).encode()
    with open(path, "wb") as fh:
        fh.write(body)


def start_pdf(edict_id: int, options: dict) -> str:
    job_id = str(uuid.uuid4())
    path = f"/tmp/{job_id}.pdf"
    generate_pdf(path, edict_id, options)
    JOBS[job_id] = {"kind": "pdf", "ready": True, "path": path}
    return job_id


def generate_pdf(path: str, edict_id: int, options: dict) -> None:
    with SessionLocal() as db, SessionForms() as fdb:
        edict = get_edict(db, edict_id)
        subs = db.execute(
            text("SELECT * FROM submission WHERE edict_id = :e ORDER BY id"),
            {"e": edict_id},
        ).mappings().all()
        items = [build_submission_item(db, fdb, s, edict, None) for s in subs]
        cand_form = int(edict["candidate_forms"])
        finalized = fdb.execute(
            text("SELECT count(*) FROM form_response "
                 "WHERE form_id = :f AND submitted_at IS NOT NULL"),
            {"f": cand_form},
        ).scalar()
        in_progress = fdb.execute(
            text("SELECT count(*) FROM form_response "
                 "WHERE form_id = :f AND submitted_at IS NULL"),
            {"f": cand_form},
        ).scalar()
        lines = _pdf_lines(edict, items, options, finalized, in_progress)
    try:
        _fpdf_render(path, lines)
    except Exception:
        _fallback_pdf(path, lines)


def generate_csv(job_id: str, edict_id: int) -> None:
    path = JOBS[job_id]["path"]
    with SessionLocal() as db, SessionForms() as fdb:
        edict = get_edict(db, edict_id)
        subs = db.execute(
            text("SELECT * FROM submission WHERE edict_id = :e ORDER BY id"),
            {"e": edict_id},
        ).mappings().all()
        teacher_ids = [
            r[0] for r in db.execute(
                text("SELECT user_id FROM user_edict_slots WHERE edict_id = :e "
                     "UNION SELECT l.user_id FROM labels l "
                     "JOIN submission s ON s.id = l.submission_id "
                     "WHERE s.edict_id = :e AND l.context_type = 'bidding'"),
                {"e": edict_id},
            )
        ]
        teachers = []
        for tid in sorted(set(teacher_ids)):
            user = db.execute(
                text('SELECT id, name, email FROM "user" WHERE id = :i'), {"i": tid}
            ).mappings().first()
            if user:
                teachers.append(dict(user))
        teachers.sort(key=lambda t: t["email"] or "")
        slots = {
            r["user_id"]: r["slots"] for r in db.execute(
                text("SELECT user_id, slots FROM user_edict_slots WHERE edict_id = :e"),
                {"e": edict_id},
            ).mappings().all()
        }
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["#"] + [t["email"] for t in teachers])
            writer.writerow(
                ["slots"] + [str(slots.get(t["id"]) or "") for t in teachers]
            )
            for sub in subs:
                resp = get_response(fdb, sub["candidate_form_id"])
                email = resp["email"] if resp else ""
                row = [email]
                for teacher in teachers:
                    label = db.execute(
                        text("SELECT label FROM labels WHERE submission_id = :s "
                             "AND user_id = :u AND context_type = 'bidding'"),
                        {"s": sub["id"], "u": teacher["id"]},
                    ).scalar()
                    row.append(label or "")
                writer.writerow(row)
