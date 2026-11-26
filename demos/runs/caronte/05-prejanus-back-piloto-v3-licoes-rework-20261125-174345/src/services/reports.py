import csv
import uuid
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from ..db import fetch, fetch_one, forms_engine, prejanus_engine
from . import forms_service, submissions_service

JOBS: dict[str, tuple[str, str]] = {}
TMP = Path("/tmp")


def register_job(path: Path, media_type: str) -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = (str(path), media_type)
    return job_id


def pop_job(job_id: str) -> tuple[str, str] | None:
    return JOBS.pop(job_id, None)


def _t(s) -> str:
    return str(s or "").encode("latin-1", "replace").decode("latin-1")


async def interactors(edict_id: int) -> list[dict]:
    sql = (
        'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
        "SELECT user_id FROM comment WHERE submission_id IN (SELECT id FROM submission WHERE edict_id=:e)"
        "UNION SELECT user_id FROM favorites WHERE submission_id IN (SELECT id FROM submission WHERE edict_id=:e)"
        "UNION SELECT user_id FROM labels WHERE submission_id IN (SELECT id FROM submission WHERE edict_id=:e)"
        "UNION SELECT user_id FROM private_note WHERE submission_id IN (SELECT id FROM submission WHERE edict_id=:e)"
        ") ORDER BY u.id"
    )
    return await fetch(prejanus_engine, sql, {"e": edict_id})


async def _edict_submissions(edict_id: int) -> list[dict]:
    return await fetch(
        prejanus_engine, "SELECT * FROM submission WHERE edict_id=:e ORDER BY id", {"e": edict_id}
    )


async def build_pdf_report(edict: dict, options, inter: list[dict]) -> str:
    form_id = int(edict["candidate_forms"])
    counts = await fetch_one(
        forms_engine,
        "SELECT count(*) FILTER (WHERE submitted_at IS NOT NULL) AS finais, "
        "count(*) FILTER (WHERE submitted_at IS NULL) AS rascunhos "
        "FROM form_response WHERE form_id=:f",
        {"f": form_id},
    )
    subs = await _edict_submissions(edict["id"])
    candidatos = []
    for sub in subs:
        mapped = await submissions_service.candidate_mapped(sub)
        candidatos.append({
            "name": submissions_service._s(mapped.get("name")),
            "email": submissions_service._s(mapped.get("email")),
            "stats": sub["stats"],
            "advisor": await submissions_service._advisor(sub),
        })

    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _t(f"Relatório do Edital: {edict['title']}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    NX, NY = XPos.LMARGIN, YPos.NEXT
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _t("Usuários que interagiram"), new_x=NX, new_y=NY)
    pdf.set_font("Helvetica", "", 11)
    for u in inter:
        linha = u["name"] + (f" ({u['email']})" if options.show_emails and u["email"] else "")
        pdf.cell(0, 6, _t(linha), new_x=NX, new_y=NY)

    if options.general_statistics:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _t("Estatísticas Gerais"), new_x=NX, new_y=NY)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, _t(f"{counts['finais']} submissões finalizadas"), new_x=NX, new_y=NY)
        pdf.cell(0, 6, _t(f"{counts['rascunhos']} submissões em preenchimento"), new_x=NX, new_y=NY)

    if options.relation:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _t("Relação de candidatos"), new_x=NX, new_y=NY)
        pdf.set_font("Helvetica", "", 11)
        for c in candidatos:
            linha = c["name"] + (f" ({c['email']})" if options.show_emails else "")
            pdf.cell(0, 6, _t(linha), new_x=NX, new_y=NY)
        for rotulo, chave in (("Aprovados", "approved"), ("Recusados", "refused"), ("Em análise", "underreview")):
            if getattr(options, chave):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, _t(rotulo), new_x=NX, new_y=NY)
                pdf.set_font("Helvetica", "", 11)
                for c in candidatos:
                    if c["stats"] == chave:
                        pdf.cell(0, 6, _t(c["name"]), new_x=NX, new_y=NY)

    if options.list_of_advisors:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _t("Anexo - Lista de Orientadores"), new_x=NX, new_y=NY)
        pdf.set_font("Helvetica", "", 11)
        for c in candidatos:
            if c["advisor"]:
                pdf.cell(0, 6, _t(c["advisor"]["name"]), new_x=NX, new_y=NY)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _t("Observações Finais"), new_x=NX, new_y=NY)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, _t(
        "Este relatório foi gerado automaticamente pelo sistema de pós-graduação. "
        "Os dados refletem o estado atual do edital no momento da emissão."
    ))

    path = TMP / f"{uuid.uuid4().hex}.pdf"
    pdf.output(str(path))
    return register_job(path, "application/pdf")


async def build_pairing_csv(edict: dict) -> str:
    edict_id = edict["id"]
    teachers = await fetch(
        prejanus_engine,
        'SELECT DISTINCT u.id, u.email FROM "user" u WHERE u.id IN ('
        "SELECT user_id FROM user_edict_slots WHERE edict_id=:e"
        "UNION SELECT l.user_id FROM labels l WHERE l.context_type='bidding' "
        "AND l.submission_id IN (SELECT id FROM submission WHERE edict_id=:e))",
        {"e": edict_id},
    )
    slots = {
        r["user_id"]: r["slots"]
        for r in await fetch(
            prejanus_engine, "SELECT user_id, slots FROM user_edict_slots WHERE edict_id=:e", {"e": edict_id}
        )
    }
    email_by_id = {t["id"]: t["email"] for t in teachers}
    id_by_email = {t["email"]: t["id"] for t in teachers}
    cols = sorted(email_by_id.values())
    bids = await fetch(
        prejanus_engine,
        "SELECT l.user_id, l.submission_id, l.label FROM labels l WHERE l.context_type='bidding' "
        "AND l.submission_id IN (SELECT id FROM submission WHERE edict_id=:e) ORDER BY l.id",
        {"e": edict_id},
    )
    by_sub: dict[int, dict[int, str]] = {}
    for b in bids:
        by_sub.setdefault(b["submission_id"], {})[b["user_id"]] = b["label"]

    linhas = [["#"] + cols]
    linhas.append(["slots"] + [str(slots.get(id_by_email[email]) or 0) for email in cols])
    for sid in sorted(by_sub):
        sub = await submissions_service.get_submission(sid)
        if sub is None:
            continue
        resp = await forms_service.get_response(sub["candidate_form_id"])
        email = resp["email"] if resp else ""
        linhas.append([email] + [by_sub[sid].get(id_by_email[c], "") for c in cols])

    path = TMP / f"{uuid.uuid4().hex}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(linhas)
    return register_job(path, "text/csv")
