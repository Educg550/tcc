import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from config import settings


def _smtp() -> smtplib.SMTP:
    server = smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30)
    if settings.smtp_use_tls:
        server.starttls()
    if settings.smtp_user:
        server.login(settings.smtp_user, settings.smtp_password)
    return server


def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    attachments: list[tuple[str, bytes]] | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("PreJanus", settings.from_email))
    if isinstance(to, str):
        to = [to]
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join([cc] if isinstance(cc, str) else cc)
    if bcc:
        msg["Bcc"] = ", ".join([bcc] if isinstance(bcc, str) else bcc)
    msg.set_content("Sua cliente de e-mail não suporta mensagens HTML.")
    msg.add_alternative(html, subtype="html")
    if attachments:
        for filename, content in attachments:
            maintype, _, subtype = filename.rpartition(".")
            msg.get_payload()[1].add_attachment(
                content,
                maintype="image",
                subtype=subtype or "png",
                filename=filename,
                cid=filename,
            )
    with _smtp() as server:
        server.send_message(msg)
