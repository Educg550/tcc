"""Rotas de leitura do Forms."""
from fastapi import APIRouter, Depends, HTTPException

from auth.session import get_current_user
from database import get_forms_db
from services import forms_service

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    forms = await forms_service.list_forms(fdb)
    if year is not None:
        forms = [f for f in forms if (f["tags"] or {}).get("Ano") == year]
    if notice is not None:
        forms = [f for f in forms if (f["tags"] or {}).get("Edital") == notice]
    return forms


async def _sections_with_fields(fdb, form_id: int, version: int | None, with_fields: bool):
    sections = await forms_service.get_sections(fdb, form_id, version)
    if not with_fields:
        return sections
    for section in sections:
        section["fields"] = await forms_service.get_fields_for_section(fdb, section["id"])
    return sections


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    form = await forms_service.list_forms(fdb)
    if not any(f["id"] == form_id for f in form):
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    return await _sections_with_fields(fdb, form_id, version, with_fields=True)


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    return await _sections_with_fields(fdb, form_id, version, with_fields=False)


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    return await forms_service.get_fields_for_section(fdb, section_id)
