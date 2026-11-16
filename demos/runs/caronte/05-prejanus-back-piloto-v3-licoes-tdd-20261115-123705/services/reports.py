"""Geração de relatórios PDF e CSV em segundo plano, em /tmp."""

import csv
import os
import uuid

from fpdf import FPDF

JOBS_DIR = "/tmp"


def new_job_id() -> str:
    return str(uuid.uuid4())


def _latin(text) -> str:
    return str(text or "").encode("latin-1", "replace").decode("latin-1")


def _pdf_text(pdf: FPDF, text, size=11, bold=False, height=6):
    pdf.set_font("helvetica", "B" if bold else "", size)
    pdf.cell(0, height, _latin(text), new_x="LMARGIN", new_y="NEXT")


def _pdf_logo(pdf: FPDF, path):
    if os.path.exists(path):
        try:
            pdf.image(path, w=40)
            pdf.ln(4)
        except Exception:
            pass


def generate_pdf(job_id: str, edict, data: dict):
    pdf = FPDF()
    pdf.add_page()
    _pdf_logo(pdf, os.path.join("assets", "logo.png"))
    _pdf_text(pdf, f"Relatorio do Edital {edict.title}", 16, bold=True)
    _pdf_text(pdf, f"Ano: {edict.year} - Semestre: {edict.semester}", 11)
    _pdf_logo(pdf, os.path.join("assets", "usp.png"))
    pdf.ln(4)

    if data.get("general_statistics"):
        _pdf_text(pdf, "Estatisticas gerais", 13, bold=True)
        for line in data["statistics_lines"]:
            _pdf_text(pdf, line)
        pdf.ln(4)

    if data.get("relation") or data.get("approved"):
        _pdf_text(pdf, "Candidatos aprovados", 13, bold=True)
        for line in data["approved_lines"]:
            _pdf_text(pdf, line)
        pdf.ln(4)

    if data.get("refused"):
        _pdf_text(pdf, "Candidatos reprovados", 13, bold=True)
        for line in data["refused_lines"]:
            _pdf_text(pdf, line)
        pdf.ln(4)

    if data.get("underreview"):
        _pdf_text(pdf, "Candidatos em analise", 13, bold=True)
        for line in data["underreview_lines"]:
            _pdf_text(pdf, line)
        pdf.ln(4)

    if data.get("list_of_advisors"):
        _pdf_text(pdf, "Orientadores", 13, bold=True)
        for line in data["advisor_lines"]:
            _pdf_text(pdf, line)
        pdf.ln(4)

    if data.get("show_emails"):
        _pdf_text(pdf, "E-mails", 13, bold=True)
        for line in data["email_lines"]:
            _pdf_text(pdf, line)

    path = os.path.join(JOBS_DIR, f"{job_id}.pdf")
    pdf.output(path)


def generate_csv(job_id: str, rows: list[list]):
    path = os.path.join(JOBS_DIR, f"{job_id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
