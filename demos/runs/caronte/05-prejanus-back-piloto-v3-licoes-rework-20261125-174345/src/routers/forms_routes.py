from fastapi import APIRouter, Depends, HTTPException

from ..auth import current_user
from ..services import forms_service

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(year: str | None = None, notice: str | None = None,
                        user: dict = Depends(current_user)):
    return await forms_service.list_forms(year, notice)


async def _sections(form_id: int, version: int | None) -> list[dict]:
    form = await forms_service.get_form(form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_service.form_sections(form_id, version)
    for section in sections:
        section["fields"] = await forms_service.section_fields(section["id"])
    return sections


@router.get("/{form_id}")
async def get_form_full(form_id: int, version: int | None = None,
                        user: dict = Depends(current_user)):
    return await _sections(form_id, version)


@router.get("/{form_id}/sections")
async def get_form_sections(form_id: int, version: int | None = None,
                            user: dict = Depends(current_user)):
    return await _sections(form_id, version)


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(form_id: int, section_id: int, user: dict = Depends(current_user)):
    return await forms_service.section_fields(section_id)
