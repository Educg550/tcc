import csv
import io
import uuid
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import Response
from fpdf import FPDF

JOBS: dict[str, dict] = {}


def store(content: bytes, ext: str, media_type: str) -> str:
    job_id = uuid.uuid4().hex
    path = Path('/tmp') / f'{job_id}.{ext}'
    path.write_bytes(content)
    JOBS[job_id] = {'path': str(path), 'media_type': media_type,
                    'filename': f'report.{ext}'}
    return job_id


def download(job_id: str) -> Response:
    job = JOBS.pop(job_id, None)
    if job is None:
        raise HTTPException(status_code=404, detail='Report not found')
    path = Path(job['path'])
    if not path.is_file():
        raise HTTPException(status_code=404, detail='Report not found')
    content = path.read_bytes()
    path.unlink(missing_ok=True)
    return Response(content, media_type=job['media_type'],
                    headers={'Content-Disposition':
                             f'inline; filename="{job["filename"]}"'})


def _labeled(items: list[dict], options: dict) -> list[str]:
    lines = []
    for it in items:
        line = it.get('name') or it.get('email') or str(it.get('id'))
        if options.get('show_emails') and it.get('email'):
            line += f" ({it['email']})"
        lines.append(line)
    return lines or ['Nenhum registro.']


def build_interactors_pdf(title: str, options: dict, statistics: dict,
                          candidates: list[dict], advisors: list[dict],
                          status_lists: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    logo = Path('assets/logo.png')
    if logo.is_file():
        try:
            pdf.image(str(logo), 10, 8, 30)
        except Exception:
            pass
    pdf.set_font('Helvetica', 'B', 16)
    pdf.multi_cell(0, 10, title)
    pdf.ln(2)

    sections = []
    if options.get('general_statistics'):
        sections.append(('Estatísticas Gerais', [
            f"{statistics['finalized']} submissões finalizadas",
            f"{statistics['drafts']} submissões em preenchimento"]))
    if options.get('relation'):
        sections.append(('Relação de candidatos', _labeled(candidates, options)))
    if options.get('list_of_advisors'):
        sections.append(('Relação de orientadores', _labeled(advisors, options)))
    anexo = []
    for flag, label in (('approved', 'Aprovados'), ('refused', 'Recusados'),
                        ('underreview', 'Em análise')):
        if options.get(flag):
            names = status_lists.get(flag) or []
            anexo.append(f"{label}: " + (', '.join(names) if names else 'nenhum'))
    if anexo:
        sections.append(('Anexo', anexo))
    sections.append(('Observações Finais',
                     ['Relatório gerado automaticamente pelo sistema.']))

    for header, lines in sections:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.multi_cell(0, 8, header)
        pdf.set_font('Helvetica', '', 11)
        for line in lines:
            pdf.multi_cell(0, 7, line)
        pdf.ln(2)
    return bytes(pdf.output())


def build_biddings_csv(advisor_emails: list[str], slots_map: dict,
                       rows: list[tuple]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['#'] + advisor_emails)
    writer.writerow(['slots'] + [slots_map.get(e, '0') for e in advisor_emails])
    for email, values in rows:
        writer.writerow([email] + [values.get(e, '') for e in advisor_emails])
    return buf.getvalue().encode('utf-8')
