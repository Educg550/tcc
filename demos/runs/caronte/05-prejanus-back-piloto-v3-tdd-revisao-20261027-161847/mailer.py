import os
import smtplib
from email.message import EmailMessage

from config import settings


def _set_html(msg, html):
    if html.isascii():
        msg.set_content(html, subtype="html")
        return
    try:
        msg.set_content(html, subtype="html", cte="8bit")
    except (ValueError, TypeError):
        msg.set_content(html, subtype="html", cte="quoted-printable")


def send_email(to, subject, html, cc=None, bcc=None, images=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    _set_html(msg, html)
    for cid, path in (images or {}).items():
        if os.path.exists(path):
            with open(path, "rb") as f:
                msg.add_related(f.read(), maintype="image", subtype="png", cid=cid)
    recipients = [to] + list(cc or []) + list(bcc or [])
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.from_email, recipients, msg.as_bytes())
