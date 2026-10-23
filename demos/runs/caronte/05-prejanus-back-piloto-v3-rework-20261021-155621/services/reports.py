"""Relatórios (PDF/CSV) e registro de jobs de download."""
import csv
import uuid
from pathlib import Path

from fpdf import FPDF
from sqlalchemy import text

from database import FormsSessionLocal, SessionLocal
from services import forms_service, submissions as subs_service

JOBS: dict[str, str] = {}


def create_job(kind: str) -> tuple[str, str]:
    job_id = str(uuid.uuid4())
    path = f"/tmp/{job_id}.{kind}"
    JOBS[job_id] = path
    return job_id, path


async def get_interactors(db, edict_id: int) -> list[dict]:
    ids: set[int] = set()
    for table in ("comment", "favorites", "labels", "private_note"):
        rows = (
            await db.execute(
                text(
                    f"SELECT DISTINCT t.user_id FROM {table} t "
                    "JOIN submission s ON s.id = t.submission_id WHERE s.edict_id = :e"
                ),
                {"e": edict_id},
            )
        ).all()
        ids.update(r[0] for r in rows)
    if not ids:
        return []
    id_list = ",".join(str(int(i)) for i in ids)
    rows = (
        await db.execute(
            text(f'SELECT id, name, email FROM "user" WHERE id IN ({id_list}) ORDER BY id')
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def _build_pdf(path: str, title: str, sections: list[tuple[str, list[str]]]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title)
    for heading, lines in sections:
        if heading:
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, heading)
        pdf.set_font("Helvetica", "", 11)
        for line in lines:
            pdf.multi_cell(0, 7, line)
    pdf.output(path)


async def generate_pdf_report(edict_id: int, options, path: str) -> None:
    async with SessionLocal() as db, FormsSessionLocal() as fdb:
        edict = (
            await db.execute(text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id})
        ).mappings().first()
        edict = dict(edict)
        synced = await subs_service.sync_edict_submissions(db, fdb, edict)
        items = [await subs_service.build_listing_item(db, fdb, edict, e, None) for e in synced]
        interactors = await get_interactors(db, edict_id)
        cand_form = subs_service.to_int(edict.get("candidate_forms"))
        finalized = await forms_service.count_responses(fdb, cand_form, True) if cand_form else 0
        drafts = await forms_service.count_responses(fdb, cand_form, False) if cand_form else 0

    show_emails = bool(options.show_emails)

    def label(item):
        if show_emails and item.get("email"):
            return f"{item['name']} ({item['email']})"
        return item["name"] or ""

    sections: list[tuple[str, list[str]]] = []
    if options.general_statistics:
        sections.append(
            (
                "Estatísticas Gerais",
                [f"{finalized} submissões finalizadas", f"{drafts} submissões em preenchimento"],
            )
        )
    if options.relation:
        sections.append(("Relação de candidatos", [label(i) for i in items]))
    if options.approved:
        sections.append(("Aprovados", [label(i) for i in items if i["stats"] == "approved"]))
    if options.refused:
        sections.append(("Recusados", [label(i) for i in items if i["stats"] == "refused"]))
    if options.underreview:
        sections.append(("Em análise", [label(i) for i in items if i["stats"] == "underreview"]))
    inter_lines = [
        f"{u['name']} ({u['email']})" if show_emails and u.get("email") else u["name"]
        for u in interactors
    ]
    sections.append(("Quem interagiu com o edital", inter_lines))
    if options.list_of_advisors:
        advisors = sorted({i["advisor"]["name"] for i in items if i.get("advisor")})
        sections.append(("Anexo", ["Orientadores: " + ", ".join(advisors) if advisors else "Nenhum orientador definido."]))
    sections.append(("Observações Finais", ["Relatório gerado automaticamente pelo sistema."]))
    _build_pdf(path, f"Edital {edict['id']} - {edict['title']}", sections)


async def generate_pairing_csv(edict_id: int, path: str) -> None:
    async with SessionLocal() as db, FormsSessionLocal() as fdb:
        edict = (
            await db.execute(text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id})
        ).mappings().first()
        edict = dict(edict)
        synced = await subs_service.sync_edict_submissions(db, fdb, edict)
        items = [await subs_service.build_listing_item(db, fdb, edict, e, None) for e in synced]
        advisors = (
            await db.execute(
                text(
                    "SELECT u.email, sl.slots FROM user_edict_slots sl "
                    'JOIN "user" u ON u.id = sl.user_id WHERE sl.edict_id = :e ORDER BY u.email'
                ),
                {"e": edict_id},
            )
        ).mappings().all()
        sub_ids = [e["submission"]["id"] for e in synced]
        bidding = []
        if sub_ids:
            id_list = ",".join(str(int(i)) for i in sub_ids)
            bidding = (
                await db.execute(
                    text(
                        "SELECT l.submission_id, u.email, l.label FROM labels l "
                        f'JOIN "user" u ON u.id = l.user_id WHERE l.context_type = \'bidding\' '
                        f"AND l.submission_id IN ({id_list})"
                    )
                )
            ).mappings().all()

    header = [a["email"] for a in advisors]
    rows = [("slots", {a["email"]: str(a["slots"]) for a in advisors})]
    for item in items:
        values = {b["email"]: b["label"] for b in bidding if b["submission_id"] == item["id"]}
        rows.append((item["email"] or "", values))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#"] + header)
        for key, values in rows:
            writer.writerow([key] + [values.get(h, "") for h in header])
