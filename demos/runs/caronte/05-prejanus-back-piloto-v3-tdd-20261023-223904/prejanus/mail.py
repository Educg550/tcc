import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from prejanus.config import settings


def _html_part(html: str) -> MIMEText:
    try:
        return MIMEText(html, "html", "us-ascii")
    except UnicodeEncodeError:
        return MIMEText(html, "html", "utf-8")


def send_email(to: list[str], subject: str, html: str,
               cc: list[str] | None = None, bcc: list[str] | None = None,
               image_path: str | None = None) -> str:
    tos = [a for a in to if a]
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = ", ".join(tos)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    alt = MIMEMultipart("alternative")
    alt.attach(_html_part(html))
    msg.attach(alt)
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
        img.add_header("Content-ID", "<signature>")
        msg.attach(img)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return tos[0] if tos else ""
