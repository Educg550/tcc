import smtplib
from email.message import EmailMessage

from babel.dates import format_date

from ..config import settings


def _send(to: list[str], subject: str, body: str, cc: list[str] | None = None,
          bcc: list[str] | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def send_correction(edict_title: str, candidate_name: str, candidate_email: str,
                    text: str, link: str, requester_email: str | None) -> None:
    body = (
        f"Prezado(a) {candidate_name},\n\n"
        f"Sua inscrição no edital \"{edict_title}\" precisa de correção:\n\n"
        f"{text}\n\n"
        f"Para editar suas respostas, acesse o formulário pelo link abaixo:\n"
        f"{link}\n\n"
        "Atenciosamente,\n"
        "Comissão de Pós-Graduação"
    )
    _send([candidate_email], f"Correção de inscrição - {edict_title}", body,
          bcc=[requester_email] if requester_email else None)


def send_accept(edict_title: str, candidate_name: str, candidate_email: str,
                link: str, deadline, advisor_email: str | None) -> None:
    pt = format_date(deadline, format="long", locale="pt_BR")
    en = format_date(deadline, format="long", locale="en_US")
    body = (
        f"Prezado(a) {candidate_name},\n\n"
        f"Parabéns! Sua inscrição no edital \"{edict_title}\" foi aprovada.\n\n"
        f"Para confirmar a aceitação da vaga, preencha o formulário de aceite "
        f"até {pt} / until {en}:\n\n"
        f"{link}\n\n"
        "Atenciosamente,\n"
        "Comissão de Pós-Graduação"
    )
    _send([candidate_email], f"Formulário de aceite - {edict_title}", body,
          cc=[advisor_email] if advisor_email else None)


def send_letter(edict_title: str, candidate_name: str, candidate_email: str) -> None:
    body = (
        f"Prezado(a) {candidate_name},\n\n"
        f"Confirmamos a aprovação de sua inscrição no edital \"{edict_title}\". "
        "A carta de aprovação segue anexa a esta mensagem.\n\n"
        "Atenciosamente,\n"
        "Comissão de Pós-Graduação"
    )
    _send([candidate_email], f"Carta de aprovação - {edict_title}", body)
