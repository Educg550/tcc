import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from config import settings


def send_email(to: str, subject: str, html: str, cc=None, bcc=None) -> list[str]:
    recipients = [to] + list(cc or []) + list(bcc or [])
    recipients = [r for r in recipients if r]
    if not recipients:
        return []
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to or recipients[0]
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Date"] = formatdate()
    msg["Message-ID"] = make_msgid()
    msg.set_content("Esta mensagem requer um cliente de e-mail com suporte a HTML.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg, from_addr=settings.from_email, to_addrs=recipients)
    return recipients
