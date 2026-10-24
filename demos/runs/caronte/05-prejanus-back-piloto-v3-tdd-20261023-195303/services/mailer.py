import base64
import os
import smtplib
from email.message import EmailMessage

from config import settings


def _signature_data_uri():
    path = os.path.join("data", "signature.png")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{encoded}"


def send_email(to, subject, html, cc=None, bcc=None):
    msg = EmailMessage()
    msg["From"] = settings.from_email
    msg["Subject"] = subject
    recipients = [to] if isinstance(to, str) else list(to)
    msg["To"] = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc if isinstance(cc, list) else [cc])
    if bcc:
        msg["Bcc"] = ", ".join(bcc if isinstance(bcc, list) else [bcc])
    msg.set_content("Sua cliente de e-mail não suporta HTML.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return ", ".join(recipients)


def resubmission_email(candidate_name, text, link):
    return f"""
    <html><body>
    <p>Prezado(a) {candidate_name},</p>
    <p>Sua candidatura foi devolvida para correção durante a homologação.</p>
    <p>Motivo: {text}</p>
    <p>Para corrigir e reenviar sua candidatura, acesse o link abaixo:</p>
    <p><a href="{link}">{link}</a></p>
    </body></html>
    """


def accept_form_email(candidate_name, deadline, link):
    return f"""
    <html><body>
    <p>Prezado(a) {candidate_name},</p>
    <p>Dear {candidate_name},</p>
    <p>Sua candidatura foi aprovada. Preencha o formulário de aceite até {deadline}.</p>
    <p>Your application has been approved. Please fill the acceptance form by {deadline}.</p>
    <p><a href="{link}">{link}</a></p>
    </body></html>
    """


def acceptance_letter_html(candidate_name, advisor_name, semester, year):
    signature = _signature_data_uri()
    sig_html = f'<p><img src="{signature}" alt="Assinatura" height="80"></p>' if signature else ""
    return f"""
    <html><body>
    <h2>Carta de Aceite</h2>
    <p>Prezado(a) {candidate_name},</p>
    <p>É com satisfação que comunicamos a aprovação de sua candidatura ao programa de
    pós-graduação, sob orientação do(a) professor(a) {advisor_name}, com ingresso no
    {semester} de {year}.</p>
    {sig_html}
    </body></html>
    """
