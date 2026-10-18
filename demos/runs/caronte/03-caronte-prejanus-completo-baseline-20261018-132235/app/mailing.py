"""Outgoing e-mail delivery through the local SMTP server of the pilot."""
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib

from .config import settings


def send_email(
    to: list[str],
    subject: str,
    html: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    images: dict[str, bytes] | None = None,
) -> None:
    """Send an HTML message. Raises on delivery failure."""
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg.attach(MIMEText(html, "html", "utf-8"))
    for cid, data in (images or {}).items():
        image = MIMEImage(data)
        image.add_header("Content-ID", f"<{cid}>")
        msg.attach(image)

    recipients = list(to) + list(cc or []) + list(bcc or [])
    server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
    try:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg, from_addr=settings.FROM_EMAIL, to_addrs=recipients)
    finally:
        server.quit()