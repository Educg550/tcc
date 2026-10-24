import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings


def send_email(subject: str, html: str, to: list[str], cc: list[str] | None = None,
               bcc: list[str] | None = None, inline_images: dict[str, str] | None = None):
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    recipients = [a for a in (to or []) if a]
    msg["To"] = ", ".join(recipients)
    if cc:
        cc = [a for a in cc if a]
        msg["Cc"] = ", ".join(cc)
        recipients += cc
    if bcc:
        recipients += [a for a in bcc if a]

    msg.attach(MIMEText(html, "html", "utf-8"))
    for cid, path in (inline_images or {}).items():
        try:
            with open(path, "rb") as f:
                img = MIMEImage(f.read())
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=path.split("/")[-1])
            msg.attach(img)
        except OSError:
            pass

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.FROM_EMAIL, recipients, msg.as_string())
