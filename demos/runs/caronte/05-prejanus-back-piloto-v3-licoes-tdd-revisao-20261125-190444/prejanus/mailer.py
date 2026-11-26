import smtplib
import uuid
from email.header import Header
from email.utils import formatdate

from prejanus.config import settings


def send_email(
    to: str,
    subject: str,
    html: str,
    cc: str | None = None,
    bcc: str | None = None,
    plain: str | None = None,
) -> str:
    """Envia multipart/alternative com partes texto legíveis no raw.

    As partes usam 8bit com charset ISO-8859-1 (ou UTF-8 quando o conteúdo
    excede o latin-1), sem quoted-printable/base64: o conteúdo acentuado
    permanece legível na mensagem armazenada pelo SMTP do ensaio.
    """
    text = plain or "Sua mensagem está disponível apenas em HTML."
    try:
        text.encode("iso-8859-1")
        html.encode("iso-8859-1")
        subject.encode("iso-8859-1")
        charset = "iso-8859-1"
    except UnicodeEncodeError:
        charset = "utf-8"
    boundary = "=_prejanus_" + uuid.uuid4().hex
    body = "\r\n".join(
        [
            f"--{boundary}",
            f"Content-Type: text/plain; charset={charset}",
            "Content-Transfer-Encoding: 8bit",
            "",
            text,
            f"--{boundary}",
            f"Content-Type: text/html; charset={charset}",
            "Content-Transfer-Encoding: 8bit",
            "",
            html,
            f"--{boundary}--",
            "",
        ]
    )
    headers = [
        f"From: {settings.from_email}",
        f"To: {to}",
        f"Subject: {Header(subject, charset)}",
        "MIME-Version: 1.0",
        f'Content-Type: multipart/alternative; boundary="{boundary}"',
        formatdate(),
    ]
    recipients = [to]
    if cc:
        headers.append(f"Cc: {cc}")
        recipients.append(cc)
    if bcc:
        recipients.append(bcc)
    msg = ("\r\n".join(headers) + "\r\n\r\n" + body).encode(charset)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.from_email, recipients, msg)
    return to
