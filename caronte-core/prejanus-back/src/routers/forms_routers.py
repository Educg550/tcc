from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.infra.database.session import get_session_forms
from src.auth.senhaunica_auth import get_user
from src.use_cases.auth.get_or_register_user import UserDTO
from src.use_cases.forms.get_forms_by_tag import get_forms_by_tag

router = APIRouter(prefix='/forms', tags=['forms'])

@router.get("")
async def get_all(
        auth_user: UserDTO = Depends(get_user), # force auth route
        session: AsyncSession = Depends(get_session_forms),
        year: str | None = Query(None, description="Year."),
        notice: str | None = Query(None, description="Edict Type.")
        ):
    tags = { }
    if year is not None:
        tags["Ano"] = year
    if notice is not None:
        tags["Edital"] = notice
    forms = await get_forms_by_tag(session, tags)
    return forms

@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = Query(None, description="Form version."),
    auth_user: UserDTO = Depends(get_user),
    session_forms: AsyncSession = Depends(get_session_forms),
):
    if version is not None:
        sections_result = await session_forms.execute(
            text("""
                SELECT * FROM form_section 
                WHERE form_id = :form_id 
                  AND (version = :version OR (:version = 1 AND version IS NULL))
                ORDER BY position
            """),
            {"form_id": form_id, "version": version},
        )
        sections = sections_result.mappings().all()

        fields_result = await session_forms.execute(
            text("""
                SELECT id, name, label, type, validation, section_id, position FROM form_field 
                WHERE section_id IN (
                    SELECT id FROM form_section 
                    WHERE form_id = :form_id 
                      AND (version = :version OR (:version = 1 AND version IS NULL))
                )
                ORDER BY position
            """),
            {"form_id": form_id, "version": version},
        )
        fields = fields_result.mappings().all()
    else:
        sections_result = await session_forms.execute(
            text("""
                SELECT * FROM form_section 
                WHERE form_id = :form_id AND is_active = true 
                ORDER BY position
            """),
            {"form_id": form_id},
        )
        sections = sections_result.mappings().all()

        fields_result = await session_forms.execute(
            text("""
                SELECT id, name, label, type, validation, section_id, position FROM form_field 
                WHERE section_id IN (
                    SELECT id FROM form_section 
                    WHERE form_id = :form_id AND is_active = true
                )
                ORDER BY position
            """),
            {"form_id": form_id},
        )
        fields = fields_result.mappings().all()

    if not sections:
        sections_result = await session_forms.execute(
            text("SELECT * FROM form_section WHERE form_id = :form_id ORDER BY position"),
            {"form_id": form_id},
        )
        sections = sections_result.mappings().all()

        fields_result = await session_forms.execute(
            text("""
                SELECT id, name, label, type, validation, section_id, position FROM form_field 
                WHERE section_id IN (
                    SELECT id FROM form_section WHERE form_id = :form_id
                )
                ORDER BY position
            """),
            {"form_id": form_id},
        )
        fields = fields_result.mappings().all()

    fields_by_section = {}
    for field in fields:
        fields_by_section.setdefault(field["section_id"], []).append(field)

    result = []
    for section in sections:
        section_id = section["id"]
        result.append({
            **section,
            "fields": fields_by_section.get(section_id, []),
        })

    return result


# Essa rota será necessária para quando for criar o mapeamento
@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = Query(None, description="Form version."),
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session_forms: AsyncSession = Depends(get_session_forms),
):
    if version is not None:
        query = text("""
            SELECT id FROM form_section 
            WHERE form_id = :form_id 
              AND (version = :version OR (:version = 1 AND version IS NULL))
            ORDER BY position
        """)
        params = {"form_id": int(form_id), "version": version}
    else:
        query = text("SELECT id FROM form_section WHERE form_id = :form_id AND is_active = true ORDER BY position")
        params = {"form_id": int(form_id)}

    response_record = (await session_forms.execute(query, params)).mappings().all()
    if not response_record:
        response_record = (await session_forms.execute(
            text("SELECT id FROM form_section WHERE form_id = :form_id ORDER BY position"),
            {"form_id": int(form_id)},
        )).mappings().all()

    return response_record


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    auth_user: UserDTO = Depends(get_user),  # force auth route
    session_forms: AsyncSession = Depends(get_session_forms),
):
    response_record = (await session_forms.execute(
        text("SELECT * FROM form_field WHERE section_id = :section_id ORDER BY position"),
        {
            "section_id": int(section_id),
        },
    )).mappings().all()

    return response_record


