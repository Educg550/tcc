"""Envio de e-mails pelo SMTP configurado."""
import smtplib
from datetime import date
from email.message import EmailMessage

from babel.dates import format_date

from ..config import settings


def send_email(to: str, subject: str, body: str, cc=None, bcc=None) -> None:
    message = EmailMessage()
    message["From"] = settings.from_email
    message["To"] = to
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    message["Subject"] = subject
    message.set_content(body)
    recipients = [to] + list(cc or []) + list(bcc or [])
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message, to_addrs=recipients)


def send_resend_email(to: str, name: str, text: str, token: str, bcc) -> None:
    body = (
        f"Prezado(a) {name},\n\n"
        "Sua inscrição requer correção. Observações da comissão:\n\n"
        f"{text}\n\n"
        "Acesse o link abaixo para revisar e reenviar sua inscrição:\n"
        f"{settings.base_url}/form/{token}\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação\n"
    )
    send_email(to, "Solicitação de correção de inscrição", body, bcc=bcc)


def send_accept_email(to: str, name: str, token: str, expiration: date, cc) -> None:
    pt = format_date(expiration, format="long", locale="pt_BR") if expiration else ""
    en = format_date(expiration, format="long", locale="en_US") if expiration else ""
    body = (
        f"Prezado(a) {name},\n\n"
        "Parabéns! Sua inscrição foi aprovada no processo seletivo. "
        "Para confirmar a vaga, preencha o formulário de aceite:\n"
        f"{settings.base_url}/form/{token}\n\n"
        f"O prazo para resposta é {pt} ({en}).\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação\n"
    )
    send_email(to, "Formulário de aceite", body, cc=cc)


def send_letter_email(to: str, name: str) -> None:
    body = (
        f"Prezado(a) {name},\n\n"
        "Temos o prazer de informar que sua inscrição foi aprovada no processo "
        "seletivo do programa de pós-graduação. Esta mensagem confirma a "
        "concessão da vaga.\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação\n"
    )
    send_email(to, "Carta de aceite", body)
