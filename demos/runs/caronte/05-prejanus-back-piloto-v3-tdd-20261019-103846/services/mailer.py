import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings


def _connect():
    server = smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30)
    try:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        return server
    except Exception:
        server.quit()
        raise


def send_email(to, subject, html, cc=None, bcc=None, image_path=None):
    """Envia um e-mail HTML. `to` pode ser string ou lista."""
    recipients = [to] if isinstance(to, str) else list(to)
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = ", ".join(recipients)
    if cc:
        cc_list = [cc] if isinstance(cc, str) else list(cc)
        msg["Cc"] = ", ".join(cc_list)
        recipients.extend(cc_list)
    if bcc:
        bcc_list = [bcc] if isinstance(bcc, str) else list(bcc)
        recipients.extend(bcc_list)

    msg.attach(MIMEText(html, "html", "utf-8"))
    if image_path:
        try:
            with open(image_path, "rb") as fh:
                img = MIMEImage(fh.read())
            img.add_header("Content-ID", "<signature>")
            msg.attach(img)
        except OSError:
            pass

    with _connect() as server:
        server.sendmail(settings.from_email, recipients, msg.as_string())
    return recipients[0]
