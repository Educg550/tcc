"""Envio de e-mail pelo SMTP do ensaio."""
import smtplib
from email.message import EmailMessage

from config import settings

MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_EN = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"]


def date_pt(d) -> str:
    return f"{d.day} de {MESES_PT[d.month - 1]} de {d.year}"


def date_en(d) -> str:
    return f"{MESES_EN[d.month - 1]} {d.day}, {d.year}"


def send_email(to: str, subject: str, body: str, cc: str | None = None,
               bcc: str | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = settings.from_email
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def send_correction_email(name: str, to: str, token: str, text: str) -> None:
    body = (
        f"Olá, {name}.\n\n"
        "Sua inscrição precisa de correção. Motivo informado pela comissão:\n\n"
        f"{text}\n\n"
        "Acesse o formulário para revisar e reenviar sua inscrição:\n"
        f"{settings.base_url}/form/{token}\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação."
    )
    send_email(to, "Solicitação de correção de inscrição", body, bcc=settings.from_email)


def send_accept_email(name: str, to: str, token: str, deadline, cc: str | None = None) -> None:
    pt = date_pt(deadline)
    en = date_en(deadline)
    body = (
        f"Olá, {name}.\n\n"
        "Parabéns! Sua inscrição foi aprovada no programa de pós-graduação. "
        f"Por favor, preencha o formulário de aceite até {pt}:\n\n"
        f"{settings.base_url}/form/{token}\n\n"
        f"Hello, {name}.\n\n"
        "Congratulations! Your application has been approved. "
        f"Please fill the acceptance form until {en}:\n\n"
        f"{settings.base_url}/form/{token}\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação."
    )
    send_email(to, "Formulário de aceite - Programa de Pós-Graduação", body, cc=cc)


def send_letter_email(name: str, to: str) -> None:
    body = (
        f"Olá, {name}.\n\n"
        "Sua inscrição foi aprovada e a carta de aprovação foi emitida. "
        "Bem-vindo(a) ao programa de pós-graduação.\n\n"
        "Atenciosamente,\nComissão de Pós-Graduação."
    )
    send_email(to, "Carta de aprovação - Programa de Pós-Graduação", body)
