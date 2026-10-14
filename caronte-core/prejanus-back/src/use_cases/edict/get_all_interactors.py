from src.infra.database.models.edict import Edict
from src.infra.database.models.submission import StatsEnum, Submission
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.favorites import Favorites
from src.infra.database.models.labels import Labels
from src.infra.database.models.private_note import PrivateNote
from sqlalchemy import select, text
from src.infra.database.models.user import User
from src.use_cases.dtos import UserDTO
from src.infra.database.models.comment import Comment
from src.use_cases.exceptions import InsufficientRole
from src.use_cases.submission.get_all_from_edict import query_get_all_submissions_from_edict
from src.utils import is_admin_role
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import matplotlib.dates as mdates

from src.utils.document_template import DocumentTemplate

async def get_users_interacted(edict_id: int, session: AsyncSession):
    sub_comments = (
        select(Comment.user_id)
        .join(Submission, Submission.id == Comment.submission_id)
        .where(Submission.edict_id == edict_id)
    )
    sub_favorites = (
        select(Favorites.user_id)
        .join(Submission, Submission.id == Favorites.submission_id)
        .where(Submission.edict_id == edict_id)
    )
    sub_labels = (
        select(Labels.user_id)
        .join(Submission, Submission.id == Labels.submission_id)
        .where(Submission.edict_id == edict_id)
    )
    sub_private_notes = (
        select(PrivateNote.user_id)
        .join(Submission, Submission.id == PrivateNote.submission_id)
        .where(Submission.edict_id == edict_id)
    )

    union_sub = sub_comments.union(sub_favorites, sub_labels, sub_private_notes).subquery()

    stmt_users = select(User).where(User.id.in_(select(union_sub.c.user_id)))
    result = await session.scalars(stmt_users)
    return result.all()

async def get_all_interactors(edict_id: int, user: UserDTO, session: AsyncSession, session_forms: AsyncSession, section_document, mode="plain_text"):
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    users_interacted: list[User] = await get_users_interacted(edict_id, session)

    submissions: list[Submission] = await query_get_all_submissions_from_edict(
        session=session, 
        session_forms=session_forms, 
        edict_id=edict_id, 
        auth_user_id=user.id, 
        user_id=None,
        stats=None
    )

    smtpt_edict = select(Edict).where(Edict.id == edict_id)
    query_result = await session.scalars(smtpt_edict)
    edict: Edict = query_result.one_or_none()

    result = await session_forms.execute(
        text("""
            select 
                count(*),
                current_section 
            from form_response 
            where form_id = cast(:p_form_id as int) and submitted_at is null
                group by current_section
                order by current_section;
        """),
        { "p_form_id": int(edict.candidate_forms) }
    )
    histogram_current_section = [dict(row._mapping) for row in result.fetchall()]

    result = await session_forms.execute(
        text("""
            select 
                extract(epoch from submitted_at) as unix_submitted_at
            from form_response 
            where form_id = cast(:p_form_id as int) and submitted_at is not null;
        """),
        { "p_form_id": int(edict.candidate_forms) }
    )
    histogram_submitted_at = [dict(row._mapping) for row in result.fetchall()]

    await session.close()
    await session_forms.close()


    if mode == "pdf":
        document = DocumentTemplate(year=edict.year)
        document.add_page()
        document.add_title("Sistema Caronte Prejanus - Relatório de Submissões")

        document.add_content(f'''\
Este relatório apresenta o panorama das submissões referentes ao edital de ingresso {edict.year} do Sistema Caronte - módulo Prejanus. O objetivo é fornecer uma visão geral das interações entre candidatos e orientadores, bem como informações sobre o status das submissões.                 
''')
        if section_document.general_statistics:
            document.add_subtitle("Estatísticas Gerais")
            document.add_content("Esta seção apresenta uma visão resumida dos dados coletados, permitindo identificar rapidamente o volume de submissões e a participação dos orientadores.")

            document.add_content(f"O edital conta com {len(submissions)} submissões finalizadas e {len(users_interacted)} orientadores envolvidos.")

            fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
            ax.bar(
                [value["current_section"] for value in histogram_current_section],
                [value["count"] for value in histogram_current_section],
                color = "#073763"
            )
            plt.title('Distribuição dos Usuários Não Submetidos por Seção')
            plt.ylabel('Número de candidatos Não Submetidos')
            plt.xlabel('Seções do Edital')
            plt.tight_layout()
            document.add_plot(fig)

            fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
            ax.hist(
                [datetime.fromtimestamp(int(value["unix_submitted_at"]), tz=timezone.utc) for value in histogram_submitted_at],
                color = "#073763",
                edgecolor = "black"
            )
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator())
            plt.title('Distribuição de Submissões por Dia')
            plt.ylabel('Número de Submissões')
            plt.xlabel('Horário da Submissão (dia)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            document.add_plot(fig)

        if section_document.list_of_advisors:
            document.add_subtitle("Lista de orientadores que interagiram no edital")
            
            document.add_content("Relação de orientadores que interagiram no edital:")
            
            for index, user in enumerate(users_interacted, start=1):
                document.add_content(f"{index}. {user.name} { f'({user.email})' if section_document.show_emails else ''}")
        
        if section_document.relation:
            document.add_subtitle("Relação de candidatos e orientadores")

            header = ["Candidato", "Orientador"]
            data = [ 
                [ 
                    f"{submission.name} { f'({submission.email})' if section_document.show_emails else ''}", f"{submission.advisor.name} { f'({submission.advisor.email})' if section_document.show_emails else ''}" 
                ] for submission in submissions if submission.advisor is not None and submission.advisor.name != "" and submission.stats == StatsEnum.APPROVED.value
            ]
            col_widths = [80, 80]
            document.add_table(header, data, col_widths)

        document.add_subtitle("Observações Finais")
        document.add_content(f'''\
Todas as informações contidas neste relatório foram geradas automaticamente pelo Sistema Caronte - módulo Prejanus, refletindo o status atualizado das submissões do processo de ingresso {edict.year}.<br/>

É importante considerar que:<br/>

<ul style="line-height:2.0;">
    <li>As listas de e-mails e relações apresentadas correspondem ao momento da geração do relatório e podem sofrer alterações futuras;</li>
    <li>Caso o relatório tenha sido gerado sem inclusão de e-mails, apenas as informações essenciais sobre candidatos e orientadores estão disponíveis;</li>
    <li>O relatório tem caráter informativo e visa auxiliar na organização e acompanhamento das submissões, garantindo transparência e fácil acesso aos dados.</li>
</ul>
''')

        anexo_number = 1

        if section_document.list_of_advisors and section_document.show_emails:
            document.add_page()
            document.add_subtitle(f"Anexo {anexo_number}. E-mails orientadores")
            anexo_number+=1
            content = ""
            for index, user in enumerate(users_interacted, start=1):
                content += f"{user.email},"
            document.add_content(content)

        if section_document.approved and section_document.show_emails:
            document.add_page()
            document.add_subtitle(f"Anexo {anexo_number}. E-mails candidatos aprovados")
            anexo_number+=1
            content = ""
            for index, submission in enumerate(submissions, start=1):
                if submission.stats.lower() == StatsEnum.APPROVED.value:
                    content += f"{submission.email},"
            document.add_content(content)

        if section_document.refused and section_document.show_emails:
            document.add_page()
            document.add_subtitle(f"Anexo {anexo_number}. E-mails candidatos reprovados e/ou em lista de espera")
            anexo_number+=1
            content = ""
            for index, submission in enumerate(submissions, start=1):
                if submission.stats.lower() == StatsEnum.REFUSED.value or submission.stats.lower() == StatsEnum.WAITLIST.value:
                    content += f"{submission.email},"
            document.add_content(content)

        if section_document.underreview and section_document.show_emails:
            document.add_page()
            document.add_subtitle(f"Anexo {anexo_number}. E-mails candidatos em análise")
            anexo_number+=1
            content = ""
            for index, submission in enumerate(submissions, start=1):
                if submission.stats.lower() == StatsEnum.UNDERREVIEW.value:
                    content += f"{submission.email},"
            document.add_content(content)

        return bytes(document.output())

    return users_interacted