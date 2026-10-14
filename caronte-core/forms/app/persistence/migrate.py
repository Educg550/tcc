from .migrations.create_user_01 import run as create_user
from .migrations.create_form_02 import run as create_form
from .migrations.create_form_section_03 import run as create_form_section
from .migrations.create_form_field_04 import run as create_form_field
from .migrations.create_field_option_05 import run as create_field_option
from .migrations.create_form_shared_06 import run as create_form_shared
from .migrations.create_form_response_07 import run as create_form_response
from .migrations.create_responses_08 import run as create_responses
from .migrations.create_get_all_forms_09 import run as create_get_all_forms
from .migrations.create_get_all_submissions_10 import run as create_get_all_submissions
from .migrations.create_get_submissions_by_id_11 import run as create_get_submissions_by_id
from .migrations.create_form_collaborators_12 import run as create_form_collaborators
from .migrations.create_update_form_response_section_13 import run as create_update_form_response_section
from .migrations.create_change_form_phase_14 import run as create_change_form_phase
from .migrations.create_form_version_15 import run as create_form_version
from .migrations.create_form_section_version_16 import run as create_form_section_version

from app.logger import Logger

def migrate_runner(db):
    """
    Executar todas as migracoes necessarias:
    * Criar tabelas
    * Inserir valores iniciais
    * ...
    """

    try:
        create_user(db)
        create_form(db)
        create_form_section(db)
        create_form_field(db)
        create_field_option(db)
        create_form_shared(db)
        create_form_response(db)
        create_responses(db)
        create_get_all_forms(db)
        create_get_all_submissions(db)
        create_get_submissions_by_id(db)
        create_form_collaborators(db)
        create_update_form_response_section(db)
        create_change_form_phase(db)
        create_form_version(db)
        create_form_section_version(db)
    except Exception as exception:
        Logger.print.error(f"An error occurred while migrating to PostgreSQL server: {exception}")
    else:
        Logger.print.info("Migrated to PostgreSQL server.")
