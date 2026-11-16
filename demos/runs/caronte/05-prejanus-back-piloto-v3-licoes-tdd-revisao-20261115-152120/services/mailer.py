import smtplib
from email.message import EmailMessage

from config import settings


def _connect():
    server = smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=60)
    if settings.smtp_use_tls:
        server.starttls()
    if settings.smtp_user and settings.smtp_password:
        server.login(settings.smtp_user, settings.smtp_password)
    return server


def send_email(
    to: list[str],
    subject: str,
    html: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.from_email
    msg["To"] = ", ".join(a for a in to if a)
    if cc:
        msg["Cc"] = ", ".join(a for a in cc if a)
    if bcc:
        msg["Bcc"] = ", ".join(a for a in bcc if a)
    msg.set_content("Sua aplicação de e-mail não suporta HTML.")
    msg.add_alternative(html, subtype="html")
    if attachments:
        for filename, content, content_id in attachments:
            msg.get_payload()[1].add_related(
                content, maintype="image", subtype="png", cid=content_id,
                filename=filename,
            )
    with _connect() as server:
        server.send_message(msg)


def send_resubmission(to: str, bcc: str, text: str, link: str) -> None:
    html = f"""
    <html><body>
    <p>Prezado(a) candidato(a),</p>
    <p>Sua candidatura precisa de correção. Motivo informado pela comissão:</p>
    <p><strong>{text}</strong></p>
    <p>Para corrigir e reenviar sua candidatura, acesse o link abaixo:</p>
    <p><a href="{link}">{link}</a></p>
    </body></html>
    """
    send_email(
        to=[to],
        subject="Correção de candidatura — Programa de Pós-Graduação",
        html=html,
        bcc=[bcc],
    )


def send_accept_form(to: str, cc: list[str], name: str, deadline, link: str) -> None:
    html = f"""
    <html><body>
    <p>Prezado(a) {name},</p>
    <p>Parabéns! Sua candidatura foi aprovada. Você deve preencher o formulário
    de aceite até <strong>{deadline}</strong>.</p>
    <p><a href="{link}">{link}</a></p>
    <hr/>
    <p>Dear {name},</p>
    <p>Congratulations! Your application has been approved. Please fill the
    acceptance form until <strong>{deadline}</strong>.</p>
    <p><a href="{link}">{link}</a></p>
    </body></html>
    """
    send_email(
        to=[to],
        subject="Formulário de aceite / Acceptance form",
        html=html,
        cc=cc,
    )


def send_accept_letter(
    to: str, cc: list[str], name: str, advisor: str, semester: str, year,
    signature: bytes | None,
) -> None:
    sig = ""
    attachments = None
    if signature:
        attachments = [("signature.png", signature, "<signature>")]
        sig = '<p><img src="cid:signature" alt="Assinatura"/></p>'
    html = f"""
    <html><body>
    <h2>Carta de Aceite / Acceptance Letter</h2>
    <p>Prezado(a) <strong>{name}</strong>,</p>
    <p>Informamos que sua candidatura foi <strong>APROVADA</strong> no processo
    seletivo do programa de pós-graduação.</p>
    <ul>
      <li>Candidato(a): {name}</li>
      <li>Orientador(a): {advisor}</li>
      <li>Semestre de ingresso: {semester}</li>
      <li>Ano de ingresso: {year}</li>
    </ul>
    {sig}
    </body></html>
    """
    send_email(
        to=[to],
        subject="Carta de Aceite / Acceptance Letter",
        html=html,
        cc=cc,
        attachments=attachments,
    )
