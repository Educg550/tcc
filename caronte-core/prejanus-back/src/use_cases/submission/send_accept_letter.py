from datetime import datetime
from fastapi import BackgroundTasks
from fastapi_mail import MessageSchema
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infra.database.models.submission import StatsEnum, Submission
from src.infra.mail import SendEmailResponse, get_mail_builder
from src.settings import get_settings
from src.use_cases.submission.change_semester import process_semester
from src.use_cases.submission.exceptions import AllowedOnlyForApprovedCandidates, EmailAlreadySent
from src.use_cases.submission.get_by_id import get_submissions_forms_by_id
from src.use_cases.submission.exceptions import SubmissionNotFound


class SendAcceptFormsByIdResponse(SendEmailResponse):
    pass

settings = get_settings()

def template_email(candidate_email, advisor_email, candidate_name, advisor_name, semester, year):
    datetime.now()

    return f"""
<p>Prezado/a <b>{candidate_name}</b>,</p><br/>

<p>Em nome da Comissão Coordenadora do Programa de Pós-graduação em Ciência da Computação do IME-USP, tenho a satisfação de formalizar que sua inscrição no programa de mestrado com <b>início no {semester} semestre de {year}</b> foi aceita. Estamos contentes com sua presença em nosso programa!</p>

<p>Aqui vão algumas informações importantes. Por favor, leia com atenção as informações a seguir e as normas regulamentares do programa. Para informações gerais sobre o programa e o instituto, acesse https://www.ime.usp.br/pos-computacao.</p>

<h3 style="color: #073763">Orientação acadêmica</h3>

<p>Considerando os interesses manifestos em sua candidatura e as vagas de orientador(a) do programa, designamos como seu/sua orientador(a) acadêmico/a o/a Prof(a). <b>{advisor_name}</b>, que está em cópia. Vocês <b>devem</b> discutir diretamente um plano de disciplinas a serem cursadas e o tema de pesquisa.</p>

Caso haja necessidade de alterar o semestre de entrada, basta combinar com seu(sua) orientador(a) e solicitar a mudança antes do período de matrícula do primeiro semestre.

<h3 style="color: #073763">Manifestação de interesse</h3>

<p>Você está recebendo esta carta, pois manifestou o aceite conforme as notificações enviadas anteriormente via o nosso sistema de seleção. De toda forma, caso você não tenha mais interesse na vaga, pedimos a gentileza de informar sua mudança de decisão para o e-mail poscomp@ime.usp.br.</p>


<h3 style="color: #073763">Bolsas institucionais</h3>

<p>O programa possui um número reduzido de bolsas institucionais de estudo disponíveis. Se você manifestou interesse em concorrer a uma dessas bolsas na sua inscrição, <b>a notificação da decisão será feita por e-mail até o dia 22/12/2025</b>.</p>

<p>Os contemplados com bolsas institucionais receberão, posteriormente, por e-mail, as instruções para implementação da bolsa. Para os que não forem contemplados neste momento, informações sobre outras possibilidades de financiamento serão fornecidas no evento de boas-vindas (ver abaixo).</p>

<h3 style="color: #073763">Matrícula</h3>

<p><b><u>Ingressantes no primeiro semestre</u>:</b> a matrícula deve ser efetuada no período de <b>26/1/2026 a 8/2/2026</b>.</p>

<p><b><u>Ingressantes no segundo semestre</u>:</b> a matrícula deve ser efetuada no período de <b>13/07/2026 a 26/07/2026</b>.</p>

<p>Conforme sinalizado no começo da mensagem, você foi aceito para ingresso no {semester} semestre, e deve realizar a matrícula na janela apropriada acima.</p>

<p>A matrícula é realizada por meio do preenchimento do formulário "ALUNOS INGRESSANTES - PRIMEIRA MATRÍCULA", disponível no período de matrícula em https://www.ime.usp.br/pos-computacao/formularios-alunos/.</p>

<p>As disciplinas a serem cursadas no semestre de ingresso no curso devem ser comunicadas no formulário de matrícula, no período indicado acima. Você deve discutir com seu(sua) orientador(a) as disciplinas a serem cursadas, considerando as normas regulamentares do programa.</p>

<p><b>Dúvidas sobre o processo de matrícula devem ser encaminhadas à secretaria do programa por meio do endereço eletrônico poscomp@ime.usp.br, a partir de 6/1/2026. 
Recomendamos que seu/sua orientador(a) seja copiado em qualquer comunicação com o programa.</b></p>

<h3 style="color: #073763">Disciplinas</h3>

<p>As aulas no IME, no primeiro semestre, iniciam-se em <b>23/2/2026</b>; já no segundo semestre, o início será em <b>03/08/2026</b>.</p>

<p><b>As disciplinas de pós-graduação no IME são presenciais e é importante comparecer desde a primeira aula, na qual informações importantes sobre a forma de avaliação e o conteúdo programático são fornecidas.</b> O calendário acadêmico de 2026 pode ser consultado em https://www.ime.usp.br/pos-computacao/calendarios/.</p>

<h3 style="color: #073763">Boas-vindas</h3>

<p>Para os ingressantes no <b>primeiro semestre</b>, no dia 20/2/2026, das 14:00 às 17:00, haverá um <b>evento de recepção dos ingressantes de pós-graduação</b> no Auditório Imre Simon, no CCSL do IME-USP (anexo ao Bloco C), ver como chegar em https://ccsl.ime.usp.br/pt-br/localizacao.</p> 

<p>O evento objetiva transmitir informações essenciais sobre o programa de pós e a vida acadêmica e promover um primeiro contato com o ambiente do IME, com alunos veteranos do programa e com os orientadores. <b>A presença é obrigatória</b>.</p>

<p>Para os ingressantes no <b>segundo semestre</b>, o mesmo evento está previsto para o dia 31/7/2026 (enviaremos um lembrete em uma data mais próxima).</p> 

<p>Por favor, organize-se para estar presente na data, conforme o seu semestre de entrada, e inicie, juntos conosco, sua trajetória em nosso programa.</p>

<p>Nosso evento de boas-vindas é distinto das atividades de recepção aos(às) alunos(as) ingressantes previstas no calendário acadêmico. A recepção institucional é destinada a todos os novos discentes dos programas de pós-graduação do IME, enquanto a nossa programação é específica do Programa de Pós-Graduação em Ciência da Computação, organizada pela comissão coordenadora e pelos orientadores do programa.</p>

<h3 style="color: #073763">Vistos para estrangeiros</h3>

<p>Estrangeiros não residentes no Brasil devem solicitar ao consulado brasileiro no seu país de residência o <b>Visto Temporário de Estudos (VITEM IV)</b> para entrada no país. De acordo com as leis vigentes no Brasil, ao chegar ao país, o estrangeiro detentor de um visto temporário tem um prazo de 30 dias (quando a autorização de residência for publicada no Diário Oficial da União) ou 90 dias (quando o ingresso no país ocorrer por meio de vistos consulares) para solicitar a autorização de permanência temporária. Esse procedimento é realizado por meio da obtenção do Registro Nacional Migratório (RNM). A obtenção do RNM, que deve ser apresentado à secretaria de pós-graduação obrigatoriamente antes do início das aulas, é necessária para realizar a matrícula na USP.</p>

<p>Caso o RNM não seja obtido a tempo, o estudante poderá apresentar à secretaria o protocolo de solicitação. Os documentos a serem apresentados para solicitar seu RNM dependem do seu país de origem. Mais informações sobre vistos e RNM estão disponíveis em: https://internationaloffice.usp.br/new/intercambio/documentos-para-migracao/.</p>

<p>Dúvidas sobre o processo de migração podem ser encaminhadas para a Comissão de Relações Internacionais do IME-USP no e-mail crint@ime.usp.br. <b>Recomendamos que seu/sua orientador(a) seja copiado em qualquer comunicação com o programa.</b></p>
<p>Por favor, note que a capacidade da comissão de auxiliar com trâmites consulares e migratórios é limitada.</p>

<br/><p>Saudações acadêmicas,</p>

<img width="200px" src="cid:signature">

<p style="color: #073763"><b>Denis Deratani Mauá</b></p>
<p style="color: #073763">Coordenador do Programa de Pós-Graduação em Ciência da Computação</p>
<p style="color: #073763">Instituto de Matemática, Estatística e Ciência da Computação</p>
<p style="color: #073763">Universidade de São Paulo</p>
"""

class SendAcceptLettersByIdResponse(SendEmailResponse):
    pass

async def send_accept_letter_by_id(
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
    if submission.stats.lower() != StatsEnum.APPROVED.value:
        raise AllowedOnlyForApprovedCandidates()
    if submission.letter_sent:
        raise EmailAlreadySent()

    candidates_forms_submissions = await get_submissions_forms_by_id(submission.candidate_form_id, session_forms)
    #check if accept
    #candidates_accept_info_forms_submissions = await get_accept_info(submission, session_forms)
    candidate_email = candidates_forms_submissions["email"]
    dict_responses = {k: v for d in candidates_forms_submissions['responses'] for k, v in d.items()}
    entry_semester = submission.entry_semester if submission.entry_semester is not None else process_semester(dict_responses.get("semester")["value"])
    
    fm = get_mail_builder()

    email_body = template_email(
        candidate_email, 
        submission.advisor.email,
        dict_responses.get("fullname")["value"], 
        submission.advisor.name,
        "primeiro" if "Primeiro" in entry_semester else "segundo", 
        submission.edict.year)

    message = MessageSchema(
        subject="PPGCC IME-USP: Carta de aceite no programa de Mestrado em Ciência da Computação 2026",
        recipients=[candidate_email],
        body=email_body,
        cc=[submission.advisor.email],
        bcc=[],
        subtype="html",
        attachments=[
            {
                "file": "data/signature.png",
                "headers": {"Content-ID": "<signature>"},
            }
        ],
    )
    background_tasks.add_task(fm.send_message, message)

    submission.letter_sent = True
    await session.commit()

    return SendAcceptFormsByIdResponse(
        message="Emails sent successfully.",
        email_sent=candidate_email
    )
