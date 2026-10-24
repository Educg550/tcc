import smtplib
from email.message import EmailMessage

from src.config import settings


def send_email(to: str, subject: str, body: str, cc: str | None = None, bcc: str | None = None) -> None:
    message = EmailMessage()
    message["From"] = settings.FROM_EMAIL
    message["To"] = to
    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc
    message["Subject"] = subject
    message.set_content(body, charset="utf-8", cte="quoted-printable")
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=30) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.send_message(message)
