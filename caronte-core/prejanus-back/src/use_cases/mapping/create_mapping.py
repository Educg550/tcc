from http import HTTPStatus
from src.use_cases.submission.exceptions import EdictNotFound
from src.use_cases.forms.exceptions import FormNotFound
from fastapi import (
    HTTPException,
)
from sqlalchemy import select, text
from src.infra.database.models.edict_form_mapping import EdictFormMapping
from src.infra.database.models.edict import Edict
from src.utils import is_admin_role
from src.utils.map_candidate import check_mapping


async def create_mapping(
    edict_id, mapping, form_type, version, auth_user, session, session_forms
):
    mapping = mapping.model_dump()
    edict = (
        await session.execute(select(Edict).where(Edict.id == edict_id))
    ).scalar_one_or_none()
    form_id = (
        edict.candidate_forms if form_type == "candidate" else edict.recommenders_forms
    )

    form = (
        await session_forms.execute(
            text("""
             SELECT id FROM form WHERE id = :form_id
             """),
            {"form_id": form_id},
        )
    ).scalar_one_or_none()

    if form is None:
        raise FormNotFound(form_id)

    if edict is None:
        raise EdictNotFound(edict_id)

    # Se não é administrador
    if not is_admin_role(auth_user.role):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
        )

    # Buscar fields de todas as sections da versão especificada
    fields_result = await session_forms.execute(
        text("""
            SELECT id, section_id FROM form_field 
            WHERE section_id IN (
                SELECT id FROM form_section 
                WHERE form_id = :form_id 
                  AND (version = :version OR (:version = 1 AND version IS NULL))
            )
        """),
        {"form_id": form_id, "version": version},
    )
    fields = fields_result.mappings().all()

    if not fields:
        fields_result = await session_forms.execute(
            text("""
                SELECT id, section_id FROM form_field 
                WHERE section_id IN (
                    SELECT id FROM form_section WHERE form_id = :form_id
                )
            """),
            {"form_id": form_id},
        )
        fields = fields_result.mappings().all()

    lookup = set()
    for field in fields:
        lookup.add(f'{field["section_id"]}:{field["id"]}')

    if not check_mapping(mapping, lookup):
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY)

    try:
        new_submission_view = EdictFormMapping(
            user_id=auth_user.id,
            edict_id=edict_id,
            form_id=form_id,
            form_type=form_type,
            mapping=mapping,
            is_active=True,
            form_version=version,
        )

        session.add(new_submission_view)
        await session.commit()
        await session.refresh(new_submission_view)
    except Exception as error:
        await session.rollback()

        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail=f"Database error: {str(error)}"
        )

    return {
        "id": new_submission_view.id,
        "edict_id": new_submission_view.edict_id,
        "form_type": new_submission_view.form_type,
        "user_id": new_submission_view.user_id,
        "version": new_submission_view.form_version,
        "mapping": (
            new_submission_view.mapping
            if isinstance(new_submission_view.mapping, dict)
            else dict(new_submission_view.mapping)
        ),
        "is_active": new_submission_view.is_active,
    }
