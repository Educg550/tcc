from babel.dates import format_date
from datetime import datetime
import json
import uuid
from fastapi import BackgroundTasks
from fastapi_mail import MessageSchema
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update

from src.infra.database.models.submission import StatsEnum, Submission
from src.infra.mail import SendEmailResponse, footer, get_mail_builder
from src.settings import get_settings
from src.use_cases.submission.exceptions import AcceptFormsAlreadyCreated, AcceptFormsNotFound, AllowedOnlyForApprovedCandidates
from src.use_cases.submission.get_by_id import get_submissions_forms_by_id
from src.use_cases.submission.exceptions import SubmissionNotFound

class SendAcceptFormsByIdResponse(SendEmailResponse):
    pass

settings = get_settings()

def template_email(candidate_name, url, expiration_at):
    pt_message = f"""
<p>Prezado(a) {candidate_name},</p><br/>

<p>Temos o prazer de informar que sua inscrição no Programa de Mestrado em Ciência da Computação do IME-USP foi <b>aceita</b>. Parabéns!</p>

<p>Confira o/a orientador/a designado/a e a previsão do seu semestre de entrada, indicados pela Comissão de Seleção em <a href="https://www.ime.usp.br/pos-computacao/processo-seletivo">https://www.ime.usp.br/pos-computacao/processo-seletivo</a>.</p>

<p>Para darmos continuidade ao seu processo de ingresso, você deve manifestar ou recusar seu interesse pela vaga, respondendo até {format_date(expiration_at, format='long', locale='pt_BR')} o formulário disponível no seguinte endereço:</p>

<p>
    <a href="{url}">Formulário de aceite</a> (Envio Único)
</p>

<p>A falta de manifestação favorável ao aceite da vaga dentro do prazo será considerada uma desistência com a consequente liberação da vaga.</p>

<p>Caso tenha desistido de sua candidatura, pedimos a gentileza de preencher o formulário com a opção de recusa.</p>

{footer()}
"""
    en_message = f"""
<p>---</p>

<p>Dear {candidate_name},</p><br/>

<p>We are pleased to inform you that your application to the Master’s in Computer Science at IME-USP has been accepted. Congratulations! You can check your assigned advisor and entrance semester at <a href="https://www.ime.usp.br/pos-computacao/processo-seletivo">https://www.ime.usp.br/pos-computacao/processo-seletivo</a>.</p>

<p>Please manifest your intention to accept our offer by filling out the form in the link below until {format_date(expiration_at, format='long', locale='en_US')}:<p/>

<p>
    <a href="{url}">Form</a> (Single submission)
</p>

<p>The lack of response within the due date will be taken as unwillingness to accept our offer.</p>

<p>We kindly ask you to respond to the above form, even in case you do not wish to accept our offer.</p>

<br/><p>Greetings,</p>

<p>Selection Committee - Coordinating Committee</p>
<p>Master’s in Computer Science Program</p>
<p>Institute of Mathematics, Statistics and Computer Science</p>
<p>University of Sao Paulo</p>
"""
    return f"""
    {pt_message}

    {en_message}
"""

async def create_partial_response(accept_form_id, candidate_email, expiration_at, session_forms):
    accept_token = {
        "form_id": accept_form_id,
        "unique_answers": True,
        "expiration_at": expiration_at,
        "is_public": False,
        "token": str(uuid.uuid4()),
        "created_at": datetime.today()
    }

    shared = (await session_forms.execute(
        text("""
            insert into form_shared(form_id, unique_answers, expiration_at, is_public, token, created_at)
                values(cast(:form_id as int), cast(:unique_answers as boolean), cast(:expiration_at as timestamp), cast(:is_public as boolean), cast(:token as uuid), cast(:created_at as timestamp))
            returning id;
        """),
        accept_token
    )).fetchone()

    response_token = str(uuid.uuid4())
    form_response = {
        "form_id": accept_form_id,
        "email": candidate_email,
        "shared_id": shared[0],
        "token": response_token,
        "metadata": json.dumps({ })
    }

    response = (await session_forms.execute(
        text("""
            insert into form_response(form_id, email, shared_id, token, metadata) 
                values(cast(:form_id as int), cast(:email as text), cast(:shared_id as int), cast(:token as uuid), cast(:metadata as jsonb)) returning id;   
        """), 
        form_response
    )).fetchone()

    await session_forms.commit()

    return response_token, response

async def send_accept_forms_by_id(
        submission_id: int, 
        session: AsyncSession,
        session_forms: AsyncSession,
        background_tasks: BackgroundTasks
        ) -> SendAcceptFormsByIdResponse:

    stmt = (
        select(Submission)
        .options(
            joinedload(Submission.edict),
            joinedload(Submission.advisor)
        )
        .where(Submission.id == submission_id)
    )
    result = await session.execute(stmt)
    submission: Submission = result.unique().scalar_one_or_none()

    if submission is None:
        raise SubmissionNotFound(submission_id)
    if submission.edict.accept_forms is None:
        raise AcceptFormsNotFound()
    if submission.accept_form_id is not None:
        raise AcceptFormsAlreadyCreated()
    if submission.stats.lower() != StatsEnum.APPROVED.value:
        raise AllowedOnlyForApprovedCandidates()

    
    accept_form_id = int(submission.edict.accept_forms)
    expiration_at = submission.edict.closed_date

    candidates_forms_submissions = await get_submissions_forms_by_id(submission.candidate_form_id, session_forms)
    
    candidate_email = candidates_forms_submissions["email"]
    dict_responses = {k: v for d in candidates_forms_submissions['responses'] for k, v in d.items()}
    
    response_token, response = await create_partial_response(accept_form_id, candidate_email, expiration_at, session_forms)

    stmt = (
        update(Submission)
        .where(Submission.id == submission_id)
        .values(accept_form_id=response[0])
    )
    await session.execute(stmt)
    await session.commit()

    fm = get_mail_builder()

    url = f'{settings.BASE_URL}/form/{str(response_token)}'    
    email_body = template_email(dict_responses.get("fullname")["value"], url, expiration_at)

    #TODO: adicionar outros e-mails em cc e bcc
    message = MessageSchema(
        subject="PPGCC IME-USP: Manifestação de aceite de vaga no programa de Mestrado 2026",
        recipients=[candidate_email],
        body=email_body,
        cc=[submission.advisor.email],
        bcc=[],
        subtype="html",
    )
    background_tasks.add_task(fm.send_message, message)

    return SendAcceptFormsByIdResponse(
        message="Emails sent successfully.",
        email_sent=candidate_email
    )
