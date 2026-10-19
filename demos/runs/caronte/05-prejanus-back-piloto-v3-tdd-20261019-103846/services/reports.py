import asyncio
import csv
import threading
import uuid
from datetime import date

from sqlalchemy import text

from database import FormsSession, PrejanusSession

JOBS: dict[str, str] = {}
_LOCK = threading.Lock()

UPLOADS_DIR = "/shared/uploads"
TMP_DIR = "/tmp"


def new_job_id():
    return uuid.uuid4().hex


def _register(job_id, path):
    with _LOCK:
        JOBS[job_id] = path


def get_job_path(job_id):
    with _LOCK:
        return JOBS.get(job_id)


def pop_job(job_id):
    with _LOCK:
        return JOBS.pop(job_id, None)


def _start(target):
    thread = threading.Thread(target=target, daemon=True)
    thread.start()


async def _interactors(edict_id):
    async with PrejanusSession() as db:
        rows = await db.execute(
            text(
                "select distinct u.id, u.name, u.email from \"user\" u where u.id in ("
                "select user_id from comment where submission_id in "
                "(select id from submission where edict_id = :eid) "
                "union select user_id from favorites where submission_id in "
                "(select id from submission where edict_id = :eid) "
                "union select user_id from labels where submission_id in "
                "(select id from submission where edict_id = :eid) "
                "union select user_id from private_note where submission_id in "
                "(select id from submission where edict_id = :eid)) order by u.id"
            ),
            {"eid": edict_id},
        )
        return [dict(r._mapping) for r in rows]


async def _edict_data(edict_id):
    async with PrejanusSession() as db:
        row = await db.execute(text("select * from edict where id = :eid"), {"eid": edict_id})
        edict = dict(row.first()._mapping)
        rows = await db.execute(
            text(
                "select s.id, s.stats, s.advisor_id, s.accept_form_id, s.candidate_form_id "
                "from submission s where s.edict_id = :eid"
            ),
            {"eid": edict_id},
        )
        submissions = [dict(r._mapping) for r in rows]
        rows = await db.execute(
            text(
                'select s.id, u.name as advisor_name, u.email as advisor_email from submission s '
                'left join "user" u on u.id = s.advisor_id where s.edict_id = :eid and s.stats = \'approved\''
            ),
            {"eid": edict_id},
        )
        approved = [dict(r._mapping) for r in rows]
        rows = await db.execute(
            text(
                "select l.user_id, u.email, u.name, s.slots from labels l "
                'join "user" u on u.id = l.user_id '
                "join submission sub on sub.id = l.submission_id and sub.edict_id = :eid "
                "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = :eid "
                "where l.context_type = 'bidding'"
            ),
            {"eid": edict_id},
        )
        biddings = [dict(r._mapping) for r in rows]
    async with FormsSession() as fdb:
        form_id = edict.get("candidate_forms")
        total = finished = 0
        if form_id:
            row = await fdb.execute(
                text(
                    "select count(*) as total, count(submitted_at) as finished "
                    "from form_response where form_id = :fid"
                ),
                {"fid": int(form_id)},
            )
            total, finished = row.first()
    return edict, submissions, approved, biddings, total, finished


def _pdf_body(job_id, edict_id, options):
    async def run():
        edict, submissions, approved, biddings, total, finished = await _edict_data(edict_id)
        interactors = await _interactors(edict_id)
        path = f"{TMP_DIR}/{job_id}.pdf"
        _build_pdf(path, edict, submissions, approved, biddings, total, finished,
                   interactors, options)
        _register(job_id, path)

    try:
        asyncio.run(run())
    except Exception:
        pass


def _build_pdf(path, edict, submissions, approved, biddings, total, finished,
               interactors, options):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.image("assets/logo.png", w=30)
        pdf.image("assets/usp.png", w=30, x=160)
    except Exception:
        pass
    pdf.set_font("Helvetica", "B", 16)
    pdf.ln(20)
    pdf.cell(0, 10, f"Relatorio do Edital {edict['title']}", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Ano: {edict['year']} - Semestre: {edict['semester']}", ln=True)
    pdf.ln(5)

    if options.get("general_statistics"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Estatisticas gerais", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Candidaturas finalizadas: {finished}", ln=True)
        pdf.cell(0, 6, f"Candidaturas em preenchimento: {total - finished}", ln=True)
        pdf.ln(3)

    if options.get("approved"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Candidatos aprovados", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for item in approved:
            pdf.cell(0, 6, f"Inscricao {item['id']} - Orientador: {item['advisor_name']}", ln=True)
        pdf.ln(3)

    if options.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Orientadores", ln=True)
        pdf.set_font("Helvetica", "", 11)
        seen = set()
        for item in approved:
            if item["advisor_id"] and item["advisor_id"] not in seen:
                seen.add(item["advisor_id"])
                pdf.cell(0, 6, f"{item['advisor_name']} <{item['advisor_email']}>", ln=True)
        pdf.ln(3)

    if options.get("relation"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Relacao de aprovados e orientadores", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for item in approved:
            pdf.cell(0, 6, f"Inscricao {item['id']}: {item['advisor_name']}", ln=True)
        pdf.ln(3)

    for status, title in (("refused", "Recusados"), ("underreview", "Em revisao")):
        if options.get(status):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, title, ln=True)
            pdf.set_font("Helvetica", "", 11)
            for sub in submissions:
                if sub["stats"] == status:
                    pdf.cell(0, 6, f"Inscricao {sub['id']}", ln=True)
            pdf.ln(3)

    if options.get("show_emails"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "E-mails dos participantes", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for user in interactors:
            pdf.cell(0, 6, f"{user['name']} <{user['email']}>", ln=True)

    pdf.output(path)


def start_pdf_job(edict_id, options):
    job_id = new_job_id()
    _start(lambda: _pdf_body(job_id, edict_id, options))
    return job_id


def _csv_body(job_id, edict_id):
    async def run():
        edict, submissions, approved, biddings, total, finished = await _edict_data(edict_id)
        async with PrejanusSession() as db:
            rows = await db.execute(
                text(
                    "select id, candidate_form_id from submission "
                    "where edict_id = :eid order by id"
                ),
                {"eid": edict_id},
            )
            local_subs = [dict(r._mapping) for r in rows]
            rows = await db.execute(
                text(
                    "select distinct l.user_id, u.email, s.slots from labels l "
                    'join "user" u on u.id = l.user_id '
                    "join submission sub on sub.id = l.submission_id and sub.edict_id = :eid "
                    "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = :eid "
                    "where l.context_type = 'bidding' order by l.user_id"
                ),
                {"eid": edict_id},
            )
            teachers = [dict(r._mapping) for r in rows]
            rows = await db.execute(
                text(
                    "select l.submission_id, l.user_id, l.label from labels l "
                    "join submission sub on sub.id = l.submission_id and sub.edict_id = :eid "
                    "where l.context_type = 'bidding'"
                ),
                {"eid": edict_id},
            )
            interests = [dict(r._mapping) for r in rows]

        emails = {}
        if local_subs:
            async with FormsSession() as fdb:
                rows = await fdb.execute(
                    text("select id, email from form_response where id = any(:ids)"),
                    {"ids": [s["candidate_form_id"] for s in local_subs]},
                )
                emails = {r.id: r.email for r in rows}
        candidates = [
            {"id": s["id"], "email": emails.get(s["candidate_form_id"])}
            for s in local_subs
        ]

        path = f"{TMP_DIR}/{job_id}.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["#"] + [t["email"] for t in teachers])
            writer.writerow(
                ["slots"] + [str(t["slots"]) if t["slots"] is not None else "" for t in teachers]
            )
            interest_map = {(i["submission_id"], i["user_id"]): i["label"] for i in interests}
            for candidate in candidates:
                row = [candidate["email"]]
                for teacher in teachers:
                    row.append(
                        interest_map.get((candidate["id"], teacher["user_id"]), "")
                    )
                writer.writerow(row)
        _register(job_id, path)

    try:
        asyncio.run(run())
    except Exception:
        pass


def start_csv_job(edict_id):
    job_id = new_job_id()
    _start(lambda: _csv_body(job_id, edict_id))
    return job_id
