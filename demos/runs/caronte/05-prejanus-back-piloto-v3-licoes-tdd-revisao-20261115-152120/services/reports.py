import os


def _latin(text) -> str:
    return str(text if text is not None else "").encode("latin-1", "replace").decode(
        "latin-1"
    )


def render_pdf(path: str, document: dict) -> None:
    from fpdf import FPDF

    options = document.get("options") or {}
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    def image(name):
        p = os.path.join("assets", name)
        if os.path.isfile(p):
            try:
                pdf.image(p, w=40)
            except Exception:
                pass

    def heading(text):
        pdf.set_font("helvetica", "B", 14)
        pdf.multi_cell(0, 8, _latin(text))
        pdf.ln(2)

    def line(text):
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 6, _latin(text))

    pdf.add_page()
    image("logo.png")
    pdf.ln(4)
    heading(f"Relatório do Edital — {document['title']}")
    line(f"Ano: {document['year']}")
    line(f"Semestre: {document['semester']}")
    line(f"Tipo: {document['edict_type']}")
    pdf.ln(4)

    if options.get("general_statistics"):
        heading("Estatísticas gerais")
        stats = document["statistics"]
        line(f"Candidaturas finalizadas: {stats['finished']}")
        line(f"Candidaturas em preenchimento: {stats['in_progress']}")
        for status, count in stats["by_status"].items():
            line(f"{status}: {count}")
        pdf.ln(4)

    if options.get("list_of_advisors"):
        heading("Orientadores")
        for adv in document["advisors"]:
            line(f"{adv['name']} ({adv['email']}) — vagas: {adv['slots']}")
        pdf.ln(4)

    if options.get("relation"):
        heading("Relação de aprovados e orientadores")
        for item in document["approved"]:
            advisor = item.get("advisor")
            advisor_name = advisor.get("name") if isinstance(advisor, dict) else None
            line(f"{item['name']} — orientador: {advisor_name or '—'}")
        pdf.ln(4)

    for status, title in (
        ("approved", "Aprovados"),
        ("refused", "Reprovados"),
        ("underreview", "Em análise"),
    ):
        if options.get(status):
            heading(title)
            for item in document["by_status"].get(status, []):
                line(item["name"])
            pdf.ln(4)

    if options.get("show_emails"):
        heading("E-mails")
        for email in document["emails"]:
            line(email)
        pdf.ln(4)

    image("usp.png")
    pdf.output(path)


def render_csv(path: str, rows: list[list[str]]) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
