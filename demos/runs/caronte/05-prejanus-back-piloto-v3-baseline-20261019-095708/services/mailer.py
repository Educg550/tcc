import smtplib
from email.message import EmailMessage
from email.utils import formatdate

from config import settings


def _send(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


def send_email(
    subject: str,
    body: str,
    to: str | list[str],
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    html: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> str:
    message = EmailMessage()
    message["From"] = settings.from_email
    recipients = [to] if isinstance(to, str) else list(to)
    message["To"] = ", ".join(recipients)
    if cc:
        message["Cc"] = ", ".join([cc] if isinstance(cc, str) else cc)
    if bcc:
        message["Bcc"] = ", ".join([bcc] if isinstance(bcc, str) else bcc)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")
    if attachments:
        for filename, content, maintype in attachments:
            message.add_attachment(content, maintype=maintype, subtype="octet-stream", filename=filename)
    _send(message)
    return ", ".join(recipients)
