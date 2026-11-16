import csv
import io
import os
import threading
import uuid

from fastapi import HTTPException, Response
from fpdf import FPDF
from sqlalchemy import text

from ..db import engine, engine_forms
from . import submissions as subsvc

JOBS: dict[str, str] = {}


def start_job(content: bytes, ext: str) -> str:
    job_id = uuid.uuid4().hex
    path = f'/tmp/{job_id}.{ext}'

    def run():
        with open(path, 'wb') as f:
            f.write(content)

    threading.Thread(target=run, daemon=True).start()
    JOBS[job_id] = path
    return job_id


def download(job_id: str, media_type: str, ext: str) -> Response:
    path = JOBS.get(job_id)
    if path is None or not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Relatório não encontrado')
    del JOBS[job_id]
    with open(path, 'rb') as f:
        data = f.read()
    os.remove(path)
    return Response(data, media_type=media_type,
                    headers={'content-disposition': f'inline; filename="relatorio.{ext}"'})


def interactors(conn, edict_id: int) -> list[dict]:
    q = text('''
        SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN (
          SELECT c.user_id FROM comment c JOIN submission s ON s.id = c.submission_id
            WHERE s.edict_id = :e
          UNION SELECT f.user_id FROM favorites f JOIN submission s ON s.id = f.submission_id
            WHERE s.edict_id = :e
          UNION SELECT l.user_id FROM labels l JOIN submission s ON s.id = l.submission_id
            WHERE s.edict_id = :e
          UNION SELECT p.user_id FROM private_note p JOIN submission s ON s.id = p.submission_id
            WHERE s.edict_id = :e
        ) ORDER BY u.id''')
    return [dict(r) for r in conn.execute(q, {'e': edict_id}).mappings().all()]


def _pdf_bytes(conn, fconn, edict: dict, opts) -> bytes:
    items = subsvc.list_submissions(conn, fconn, edict, 0)
    form_id = int(edict['candidate_forms'])
    finalized = fconn.execute(
        text('SELECT count(*) FROM form_response WHERE form_id = :f AND submitted_at IS NOT NULL'),
        {'f': form_id}).scalar()
    drafts = fconn.execute(
        text('SELECT count(*) FROM form_response WHERE form_id = :f AND submitted_at IS NULL'),
        {'f': form_id}).scalar()

    def name_of(item):
        label = item['name'] or item['email'] or str(item['id'])
        if opts.show_emails and item['email']:
            label = f"{label} ({item['email']})"
        return label

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.multi_cell(0, 10, f'Relatório do Edital: {edict["title"]}')
    pdf.set_font('Helvetica', '', 12)
    if opts.general_statistics:
        pdf.multi_cell(0, 8, 'Estatísticas Gerais')
        pdf.multi_cell(0, 8, f'{finalized} submissões finalizadas')
        pdf.multi_cell(0, 8, f'{drafts} submissões em preenchimento')
    if opts.relation:
        pdf.multi_cell(0, 8, 'Relação de candidatos')
        for item in items:
            pdf.multi_cell(0, 8, name_of(item))
    if opts.list_of_advisors:
        pdf.multi_cell(0, 8, 'Anexo - Lista de Orientadores')
        seen = set()
        for item in items:
            adv = item['advisor']
            if adv and adv['id'] not in seen:
                seen.add(adv['id'])
                label = adv['name']
                if opts.show_emails and adv.get('email'):
                    label = f"{label} ({adv['email']})"
                pdf.multi_cell(0, 8, label)
    for flag, title, stat in ((opts.approved, 'Candidatos Aprovados', 'approved'),
                              (opts.refused, 'Candidatos Recusados', 'refused'),
                              (opts.underreview, 'Candidatos Em Análise', 'underreview')):
        if flag:
            pdf.multi_cell(0, 8, title)
            for item in items:
                if item['stats'] == stat:
                    pdf.multi_cell(0, 8, name_of(item))
    pdf.multi_cell(0, 8, 'Observações Finais')
    pdf.multi_cell(0, 8, 'Relatório gerado automaticamente pelo sistema.')
    return bytes(pdf.output())


def start_pdf_job(edict_id: int, opts) -> str:
    with engine.begin() as conn, engine_forms.connect() as fconn:
        edict = subsvc.get_edict(conn, edict_id)
        content = _pdf_bytes(conn, fconn, edict, opts)
    return start_job(content, 'pdf')


def _csv_bytes(conn, fconn, edict: dict) -> bytes:
    items = subsvc.list_submissions(conn, fconn, edict, 0)
    teachers: dict[int, dict] = {}
    for r in conn.execute(
            text('SELECT u.id, u.email, s.slots FROM "user" u '
                 'JOIN user_edict_slots s ON s.user_id = u.id WHERE s.edict_id = :e'),
            {'e': edict['id']}).mappings().all():
        teachers[r['id']] = {'email': r['email'], 'slots': r['slots'] or 0}
    for r in conn.execute(
            text("SELECT DISTINCT l.user_id FROM labels l JOIN \"user\" u ON u.id = l.user_id "
                 "WHERE l.context_type = 'bidding' AND l.submission_id IN "
                 '(SELECT id FROM submission WHERE edict_id = :e)'),
            {'e': edict['id']}).mappings().all():
        if r['user_id'] not in teachers:
            row = conn.execute(text('SELECT id, email FROM "user" WHERE id = :i'),
                               {'i': r['user_id']}).mappings().first()
            if row:
                teachers[row['id']] = {'email': row['email'], 'slots': 0}
    order = sorted(teachers.items(), key=lambda kv: kv[1]['email'])
    bidding = {}
    for r in conn.execute(
            text("SELECT user_id, submission_id, label FROM labels WHERE context_type = 'bidding' "
                 'AND submission_id IN (SELECT id FROM submission WHERE edict_id = :e)'),
            {'e': edict['id']}).mappings().all():
        bidding[(r['submission_id'], r['user_id'])] = r['label']

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['#'] + [t['email'] for _, t in order])
    writer.writerow(['slots'] + [str(t['slots']) for _, t in order])
    for item in items:
        writer.writerow([item['email']] + [
            bidding.get((item['id'], uid), '') for uid, _ in order])
    return buf.getvalue().encode()


def start_csv_job(edict_id: int) -> str:
    with engine.begin() as conn, engine_forms.connect() as fconn:
        edict = subsvc.get_edict(conn, edict_id)
        content = _csv_bytes(conn, fconn, edict)
    return start_job(content, 'csv')
