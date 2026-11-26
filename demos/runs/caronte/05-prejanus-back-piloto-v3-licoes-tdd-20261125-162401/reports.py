from __future__ import annotations

import csv
import os
import threading
import uuid

from fpdf import FPDF

jobs: dict[str, dict] = {}


def new_job(kind: str) -> str:
    job_id = uuid.uuid4().hex
    ext = "pdf" if kind == "pdf" else "csv"
    jobs[job_id] = {"kind": kind, "path": f"/tmp/{job_id}.{ext}"}
    return job_id


def _run(fn, *args):
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()


def generate_pdf_job(data: dict, options: dict) -> str:
    job_id = new_job("pdf")
    _run(_write_pdf, jobs[job_id]["path"], data, options)
    return job_id


def generate_csv_job(rows: list[list[str]]) -> str:
    job_id = new_job("csv")
    _run(_write_csv, jobs[job_id]["path"], rows)
    return job_id


def _write_pdf(path: str, data: dict, options: dict) -> None:
    try:
        pdf = FPDF()
        pdf.add_page()
        x = 10
        for asset in ("assets/logo.png", "assets/usp.png"):
            if os.path.exists(asset):
                try:
                    pdf.image(asset, x=x, w=22)
                    x += 26
                except Exception:
                    pass
        pdf.set_font("helvetica", "B", 16)
        pdf.ln(20)
        pdf.cell(0, 10, text=f"Relatorio do Edital: {data['title']}")
        pdf.ln(8)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, text=f"Ano: {data['year']}  Semestre: {data['semester']}")
        pdf.ln(8)

        if options.get("general_statistics"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Estatisticas gerais")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 7, text=f"Candidaturas finalizadas: {data['finalized']}")
            pdf.ln(7)
            pdf.cell(0, 7, text=f"Candidaturas em preenchimento: {data['in_progress']}")
            pdf.ln(7)
            pdf.cell(0, 7, text=f"Total de inscricoes: {data['total']}")
            pdf.ln(8)

        if options.get("approved"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Candidatos aprovados")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for name, advisor in data["approved"]:
                pdf.cell(0, 7, text=f"- {name} (orientador: {advisor})")
                pdf.ln(7)
            pdf.ln(4)

        if options.get("relation"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Relacao de aprovados e orientadores")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for name, advisor in data["approved"]:
                pdf.cell(0, 7, text=f"{name} -> {advisor}")
                pdf.ln(7)
            pdf.ln(4)

        if options.get("list_of_advisors"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Orientadores")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for advisor in data["advisors"]:
                pdf.cell(0, 7, text=f"- {advisor}")
                pdf.ln(7)
            pdf.ln(4)

        if options.get("refused"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Candidatos reprovados")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for name in data["refused"]:
                pdf.cell(0, 7, text=f"- {name}")
                pdf.ln(7)
            pdf.ln(4)

        if options.get("underreview"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="Candidatos em analise")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for name in data["underreview"]:
                pdf.cell(0, 7, text=f"- {name}")
                pdf.ln(7)
            pdf.ln(4)

        if options.get("show_emails"):
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, text="E-mails dos candidatos")
            pdf.ln(8)
            pdf.set_font("helvetica", size=12)
            for email in data["emails"]:
                pdf.cell(0, 7, text=f"- {email}")
                pdf.ln(7)

        pdf.output(path)
    except Exception:
        if os.path.exists(path):
            os.remove(path)


def _write_csv(path: str, rows: list[list[str]]) -> None:
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
    except Exception:
        if os.path.exists(path):
            os.remove(path)
