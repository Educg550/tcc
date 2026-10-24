import csv
import os

from fpdf import FPDF
from sqlalchemy import text

from database import FormsSession, PrejanusSession
from services import forms_service
from services.common import parse_form_ids
from services.submission_data import build_bidding_users

INTERACTORS_SQL = text(
    'select distinct u.id, u.name, u.email, u.nusp, u.role from "user" u where u.id in ('
    "select c.user_id from comment c join submission s on s.id = c.submission_id where s.edict_id = :e"
    " union select f.user_id from favorites f join submission s on s.id = f.submission_id where s.edict_id = :e"
    " union select l.user_id from labels l join submission s on s.id = l.submission_id where s.edict_id = :e"
    " union select p.user_id from private_note p join submission s on s.id = p.submission_id where s.edict_id = :e"
    ") order by u.id"
)


def get_interactors(ps, edict_id):
    return ps.execute(INTERACTORS_SQL, {"e": edict_id}).mappings().all()


INTERACTOR_OF_SQL = text(
    "select exists ("
    "select 1 from comment c join submission s on s.id = c.submission_id where s.edict_id = :e and c.user_id = :u"
    " union select 1 from favorites f join submission s on s.id = f.submission_id where s.edict_id = :e and f.user_id = :u"
    " union select 1 from labels l join submission s on s.id = l.submission_id where s.edict_id = :e and l.user_id = :u"
    " union select 1 from private_note p join submission s on s.id = p.submission_id where s.edict_id = :e and p.user_id = :u"
    ")"
)


def user_is_interactor(ps, edict_id, user_id):
    return bool(ps.execute(INTERACTOR_OF_SQL, {"e": edict_id, "u": user_id}).scalar())


def _safe(value):
    """Fontes core do fpdf2 exigem latin-1."""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _submission_stats(ps, fs, edict):
    finished = 0
    in_progress = 0
    with FormsSession() as fs:
        for form_id in parse_form_ids(edict["candidate_forms"]):
            finished += fs.execute(
                text("select count(*) from form_response where form_id=:f and submitted_at is not null"),
                {"f": form_id},
            ).scalar()
            in_progress += fs.execute(
                text("select count(*) from form_response where form_id=:f and submitted_at is null"),
                {"f": form_id},
            ).scalar()
    return finished, in_progress


def _write_minimal_pdf(path, text):
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size " + str(len(objects) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n" + str(xref_pos).encode() + b"\n%%EOF"
    )
    with open(path, "wb") as f:
        f.write(out)


def generate_pdf_report(path, edict_id, options):
    try:
        _generate_pdf(path, edict_id, options)
    except Exception:
        title = ""
        try:
            with PrejanusSession() as ps:
                row = ps.execute(text("select title from edict where id=:i"), {"i": edict_id}).first()
                if row:
                    title = row[0]
        except Exception:
            title = ""
        _write_minimal_pdf(path, f"Relatorio do Edital: {title}")


def _generate_pdf(path, edict_id, options):
    with PrejanusSession() as ps, FormsSession() as fs:
        edict = ps.execute(text("select * from edict where id=:i"), {"i": edict_id}).mappings().first()
        if edict is None:
            _write_minimal_pdf(path, "Edital inexistente")
            return
        try:
            subs = ps.execute(
                text(
                    'select s.*, u.name as advisor_name from submission s left join "user" u on u.id = s.advisor_id '
                    "where s.edict_id=:e order by s.id"
                ),
                {"e": edict_id},
            ).mappings().all()
        except Exception:
            subs = []
        try:
            finished, in_progress = _submission_stats(ps, fs, edict)
        except Exception:
            finished = in_progress = 0
        try:
            interactors = get_interactors(ps, edict_id)
        except Exception:
            interactors = []

    pdf = FPDF()
    pdf.add_page()
    for image in ("assets/logo.png", "assets/usp.png"):
        if os.path.exists(image):
            try:
                pdf.image(image, w=30)
            except Exception:
                pass
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _safe(f"Relatorio do Edital: {edict['title']}"))
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, _safe(f"Ano: {edict['year']}   Semestre: {edict['semester']}   Tipo: {edict['type']}"))
    pdf.multi_cell(0, 8, _safe(f"Fase atual: {edict['phase']}   Aberto: {'sim' if edict['is_open'] else 'nao'}"))

    if options.get("general_statistics"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Estatisticas gerais")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 8, f"Candidaturas finalizadas: {finished}")
        pdf.multi_cell(0, 8, f"Candidaturas em preenchimento: {in_progress}")
        pdf.multi_cell(0, 8, f"Total de inscricoes registradas: {len(subs)}")

    sections = [
        ("approved", "approved", "Candidatos aprovados"),
        ("refused", "refused", "Candidatos reprovados"),
        ("underreview", "underreview", "Candidatos em revisao"),
    ]
    for option, stats_value, title in sections:
        if options.get(option):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, title)
            pdf.set_font("Helvetica", size=12)
            for sub in subs:
                if sub["stats"] == stats_value:
                    advisor = sub["advisor_name"] or "-"
                    pdf.multi_cell(0, 8, _safe(f"Inscricao {sub['id']} - orientador: {advisor}"))

    if options.get("relation") or options.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, "Relacao de aprovados e orientadores")
        pdf.set_font("Helvetica", size=12)
        for sub in subs:
            if sub["stats"] == "approved":
                pdf.multi_cell(0, 8, _safe(f"Inscricao {sub['id']} - orientador: {sub['advisor_name'] or '-'}"))

    if options.get("show_emails"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, "E-mails dos participantes")
        pdf.set_font("Helvetica", size=12)
        for user in interactors:
            pdf.multi_cell(0, 8, _safe(f"{user['name']} <{user['email']}>"))

    pdf.output(path)


def generate_csv_report(path, edict_id):
    with PrejanusSession() as ps, FormsSession() as fs:
        edict = ps.execute(text("select * from edict where id=:i"), {"i": edict_id}).mappings().first()
        if edict is None:
            return
        subs = ps.execute(
            text("select * from submission where edict_id=:e order by id"), {"e": edict_id}
        ).mappings().all()
        teachers = {}
        for sub in subs:
            for bidder in build_bidding_users(ps, sub, edict):
                teachers[bidder["id"]] = bidder
        teacher_ids = sorted(teachers)
        slots_by_teacher = {}
        for tid in teacher_ids:
            slots = ps.execute(
                text("select slots from user_edict_slots where user_id=:u and edict_id=:e"),
                {"u": tid, "e": edict_id},
            ).scalar()
            slots_by_teacher[tid] = str(slots) if slots is not None else "0"
        bidding_by_sub = {}
        for sub in subs:
            rows = ps.execute(
                text("select user_id, label from labels where submission_id=:s and context_type='bidding'"),
                {"s": sub["id"]},
            ).all()
            bidding_by_sub[sub["id"]] = {r[0]: r[1] for r in rows}

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#"] + [teachers[tid]["email"] for tid in teacher_ids])
            writer.writerow(["slots"] + [slots_by_teacher[tid] for tid in teacher_ids])
            for sub in subs:
                emails = fs.execute(
                    text("select email from form_response where id=:i"), {"i": sub["candidate_form_id"]}
                ).scalars().all()
                candidate_email = emails[0] if emails else f"submission-{sub['id']}"
                writer.writerow(
                    [candidate_email] + [bidding_by_sub[sub["id"]].get(tid, "") for tid in teacher_ids]
                )
