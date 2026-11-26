import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from config import settings


def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    image_path: str | None = None,
) -> str:
    recipients = [to] if isinstance(to, str) else list(to)
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=settings.from_email.partition("@")[2] or "localhost")
    if cc:
        msg["Cc"] = ", ".join(cc)
        recipients.extend(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
        recipients.extend(bcc)
    msg.attach(MIMEText(html, "html", "utf-8"))
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<signature>")
            msg.attach(img)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.from_email, recipients, msg.as_string())
    return ", ".join(r for r in ([to] if isinstance(to, str) else to) if r)
