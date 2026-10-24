import smtplib
from email.message import EmailMessage

from src.config import get_settings

MONTHS_PT = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
             'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December']


def format_date_pt(d) -> str:
    return f'{d.day} de {MONTHS_PT[d.month - 1]} de {d.year}'


def format_date_en(d) -> str:
    return f'{MONTHS_EN[d.month - 1]} {d.day}, {d.year}'


def send(to: str, subject: str, body: str, cc: str | None = None,
         bcc: str | None = None) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg['From'] = settings.from_email
    msg['To'] = to
    if cc:
        msg['Cc'] = cc
    if bcc:
        msg['Bcc'] = bcc
    msg['Subject'] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
