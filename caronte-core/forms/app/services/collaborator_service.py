from app.extension import get_locale
from app.repositories.form_repository import get_form_dict_raw
from flask_babel import gettext

from app.common.Result import Result
from app.entities.User import UserType
from app.repositories.collaborator_service import add_collaborator, get_collaborator
from app.services.user_service import get_user_by_email


def can_access_form(
        db,
        user: UserType, 
        form_id: int, 
        action='view'
    ):
    if user.get("role") == 'administrator':
        return Result(True)
    
    form = get_form_dict_raw(db, form_id, get_locale())
    if form is None:
        return Result(False)

    if form.get("created_by") == user.get("id"):
        return Result(True)
    
    collaborator = get_collaborator(db, form_id, user.get("id"))
    if not collaborator:
        return Result(False)
    
    if action == 'view':
        return Result(True)
    elif action == 'edit' and collaborator.get("can_edit"):
        return Result(True)
    
    return Result(False)

def invite_collaborator_form(db, form_id, inviter, invitee_email, can_edit=False):
    invitee = get_user_by_email(db, invitee_email)
    if not invitee.succeeded:
        return Result(message=gettext("Usuário não existe"))

    if not can_access_form(db, inviter, form_id, action='edit').succeeded:
        return Result(message=gettext("Sem permissão para convidar"))

    add_collaborator(db, form_id, invitee.data.get("id"), can_edit, inviter.get("id"))
    #send_email_invite(invitee_email, form_id)

    return Result(True)