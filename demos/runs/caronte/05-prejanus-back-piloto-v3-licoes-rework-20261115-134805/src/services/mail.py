import smtplib
from email.message import EmailMessage

from ..config import settings


def send_email(to: str, subject: str, body: str, cc: list | None = None,
               bcc: list | None = None) -> None:
    msg = EmailMessage()
    msg['From'] = settings.from_email
    msg['To'] = to
    if cc:
        msg['Cc'] = ', '.join(cc)
    if bcc:
        msg['Bcc'] = ', '.join(bcc)
    msg['Subject'] = subject
    msg.set_content(body)
    recipients = [to] + list(cc or []) + list(bcc or [])
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.from_email, recipients, msg.as_string())
