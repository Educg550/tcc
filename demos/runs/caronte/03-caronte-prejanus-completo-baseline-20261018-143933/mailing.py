"""Envio de e-mails pelo SMTP local do ensaio."""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from config import settings


def send_mail(subject, recipients, html, cc=None, bcc=None):
    """Entrega a mensagem ao SMTP local. Retorna True quando aceita."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.attach(MIMEText(html, "html", "utf-8"))
    all_recipients = list(recipients) + list(cc or []) + list(bcc or [])
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.EMAIL_FROM, all_recipients, msg.as_string())
        return True
    except Exception:
        return False
