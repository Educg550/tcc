from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel

class SendEmailResponse(BaseModel):
    message: str
    email_list: list[str]
    confirmation_deadline: str


async def send_emails_to_approved_submissions(
    session: AsyncSession, 
    edict_id: int,
    confirmation_deadline: date,
    background_tasks: BackgroundTasks
):
    pass
#     edict_name_query = select(Edict.title).where(Edict.id == edict_id)
#     edict_result = await session.execute(edict_name_query)
#     edict_name = edict_result.scalar_one_or_none()

#     if not edict_name:
#         raise HTTPException(status_code=404, detail="Edict not found.")

#     query = (
#         select(Submission)
#         .options(joinedload(Submission.applicant))
#         .where(Submission.edict_id == edict_id, Submission.approved.is_(True))
#     )
#     result = await session.execute(query)
#     submissions = result.scalars().all()

#     if not submissions:
#         raise HTTPException(status_code=404, detail="No approved submissions found for this edict.")

#     fm = _get_mail_builder()
#     emails_sent = []

#     for submission in submissions:
#         if not submission.advisor or not submission.advisor_email:
#             continue

#         applicant = submission.applicant
#         if not applicant or not applicant.email:
#             continue

#         email_body = f"""
#             <p>Prezado/a <strong>{applicant.name}</strong>,</p>

#             <p>Em nome da Comissão Coordenadora do Programa de Pós-graduação em Ciência 
#             da Computação do IME-USP, tenho a satisfação de lhe informar que <strong>sua inscrição 
#             no programa de {edict_name} foi aceita.</strong><br>Parabéns!</p>

#             <p>Aqui vão algumas informações importantes. Por favor, leia com atenção.</p>

#             <h4>Orientação acadêmica</h4>
#             <p>Considerando os interesses manifestos em sua candidatura e as vagas dos 
#             orientadores do programa, <strong>designamos como seu/sua orientador(a) acadêmico/a 
#             o/a Prof(a). {submission.advisor}</strong>, que está em cópia. Vocês <strong>devem</strong> discutir diretamente 
#             um plano de disciplinas a serem cursadas e o tema de pesquisa.</p>

#             <h4>Manifestação de interesse</h4>
#             <p><strong>Por favor manifeste seu interesse em preencher a vaga respondendo este 
#             email para <a href="mailto:poscomp@ime.usp.br">poscomp@ime.usp.br</a> até {confirmation_deadline.strftime('%d/%m/%Y')}, com cópia para o/a 
#             orientador(a) designado/a.</strong> Caso você não tenha interesse em aceitar a vaga, 
#             pedimos a gentileza de responder a mensagem com a negativa.</p>

#             <p>Atenciosamente,<br>
#             <strong>Comissão Coordenadora</strong><br>
#             Programa de Pós-graduação em Ciência da Computação do IME-USP</p>
#         """


#         message = MessageSchema(
#             subject="Aceitação no Programa de Pós-Graduação IME-USP",
#             recipients=[applicant.email],
#             cc=[submission.advisor_email],
#             body=email_body,
#             subtype="html",
#         )
#         background_tasks.add_task(fm.send_message, message)
#         emails_sent.append(applicant.email)

#     return SendEmailResponse(
#         message= "Emails sent successfully.",
#         email_list= emails_sent,
#         confirmation_deadline= confirmation_deadline.strftime("%Y-%m-%d"),
#     )
