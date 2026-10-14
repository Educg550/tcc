from fastapi import BackgroundTasks
from fastapi_mail import MessageSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, text
from src.infra.database.models.edict import Edict
from src.infra.mail import SendEmailResponse, footer, get_mail_builder
from src.settings import get_settings
from src.infra.database.models.submission import Submission
from pydantic import BaseModel
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.use_cases.submission.exceptions import SubmissionNotFound
from src.utils import is_admin_role
from src.utils.get_edict_phase import check_edict_phase_by_submission

class RequestReesendSchema(BaseModel):
    text: str

class RequestReesendResponse(SendEmailResponse):
    pass


async def request_reesend(
    submission_id: int, 
    session: AsyncSession, 
    session_forms: AsyncSession,
    data: RequestReesendSchema, 
    user: UserDTO,
    background_tasks: BackgroundTasks
):
    if not is_admin_role(user.role):
        raise InsufficientRole()

    stmt = (
        select(Submission)
        .options(
            joinedload(Submission.edict)
            .joinedload(Edict.edict_phases)
        )
        .where(Submission.id == submission_id)
    )
    result = await session.execute(stmt)
    existing: Submission = result.unique().scalar_one_or_none()

    if existing is None:
        raise SubmissionNotFound(submission_id)

    await check_edict_phase_by_submission(submission_id, ["homologacao"], "reesend", session)
    
    query = text("""
        select * from get_submissions_by_id(
            cast(:p_response_id as int),
            cast(:p_lang as text)
        )
    """)
    params = {
        "p_response_id": int(existing.candidate_form_id),
        "p_lang": "pt" 
    }
    result = await session_forms.execute(
        query,
        params
    )

    candidates_forms_submissions = dict(result.fetchone()._mapping)
    email_sent = candidates_forms_submissions["email"]

    query = text('''
        select * from update_form_response_section(
            cast(:p_id as int),
            cast(:p_current_section as int)
        );
    ''')
    params = {
        "p_current_section": 0,
        "p_id": int(existing.candidate_form_id)
    }
    await session_forms.execute(
        query,
        params
    )
    await session_forms.commit()

    fm = get_mail_builder()
    
    settings = get_settings()
    email_body = f"""
        <p>Prezado(a) Candidato(a), {email_sent},</p><br/>

        <p>Notamos que seu formulário de inscrição precisa de alguns ajustes antes de podermos avaliá-lo.</p>

        <p>Motivo da solicitação:</p>
        <p>{data.text}</p>

        <p>Para revisar e enviar novamente seu formulário, acesse o link abaixo:</p>
        <p>
            <a href="{settings.BASE_URL}/form/{candidates_forms_submissions["token"]}">Revisar formulário</a>
        </p><br/>

        <p>Por favor, verifique se todos os campos obrigatórios foram preenchidos antes de reenviar.</p><br/>

        {footer()}
    """

    message = MessageSchema(
        subject="Solicitação para completar ou corrigir seu formulário de inscrição",
        recipients=[email_sent],
        body=email_body,
        bcc=[user.email],
        subtype="html",
    )
    background_tasks.add_task(fm.send_message, message)

    return RequestReesendResponse(
        message="Emails sent successfully.",
        email_sent=email_sent
    )
