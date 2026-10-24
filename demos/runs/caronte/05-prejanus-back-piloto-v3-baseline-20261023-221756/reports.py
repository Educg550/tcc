import csv
import threading
import uuid
from pathlib import Path

from fpdf import FPDF

JOBS = {}  # job_id -> {"path": str, "type": "pdf"|"csv"}
LOCK = threading.Lock()


def new_job(kind: str) -> str:
    job_id = str(uuid.uuid4())
    with LOCK:
        JOBS[job_id] = {"path": f"/tmp/{job_id}.{'pdf' if kind == 'pdf' else 'csv'}", "type": kind}
    return job_id


def get_job(job_id: str):
    return JOBS.get(job_id)


def pop_job(job_id: str):
    with LOCK:
        return JOBS.pop(job_id, None)


def _run(target, *args):
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()


def _pdf_header(pdf: FPDF, title: str):
    pdf.add_page()
    for img in ("assets/logo.png", "assets/usp.png"):
        if Path(img).exists():
            pdf.image(img, w=30)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(2)


def generate_pdf(job_id: str, edict, data: dict):
    path = JOBS[job_id]["path"]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    _pdf_header(pdf, f"{edict['title']} - Edital {edict['year']}")

    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 6, f"Ano: {edict['year']}  Semestre: {edict['semester']}  Tipo: {edict['type']}")
    pdf.ln(3)

    if data.get("general_statistics"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Estatisticas gerais", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Candidaturas finalizadas: {data['stats']['finalized']}", ln=True)
        pdf.cell(0, 6, f"Candidaturas em preenchimento: {data['stats']['in_progress']}", ln=True)
        pdf.ln(3)

    if data.get("relation") or data.get("approved"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Relacao de aprovados e orientadores", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for item in data["approved_list"]:
            pdf.cell(0, 6, f"{item['name']} ({item['email']}) - Orientador: {item['advisor']}", ln=True)
        pdf.ln(3)

    if data.get("list_of_advisors"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Orientadores", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for adv in data["advisors"]:
            pdf.cell(0, 6, f"{adv['name']} ({adv['email']})", ln=True)
        pdf.ln(3)

    if data.get("show_emails"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Listas de e-mails", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for email in data["emails"]:
            pdf.cell(0, 6, email, ln=True)
        pdf.ln(3)

    pdf.output(path)


def generate_csv(job_id: str, rows: list[list[str]]):
    path = JOBS[job_id]["path"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def start_pdf(edict, data):
    job_id = new_job("pdf")
    _run(generate_pdf, job_id, edict, data)
    return job_id


def start_csv(rows):
    job_id = new_job("csv")
    _run(generate_csv, job_id, rows)
    return job_id
