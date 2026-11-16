import smtplib
from email.message import EmailMessage

from config import settings


def send_email(
    subject: str,
    html: str,
    to: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[tuple[str, bytes]] | None = None,
) -> str:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.from_email
    message["To"] = to
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    message.set_content(html, subtype="html")
    for filename, content in attachments or []:
        message.add_attachment(content, maintype="image", subtype="png", filename=filename)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
    return to
