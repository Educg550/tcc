from fastapi import APIRouter, Depends

import forms_service as forms
from security import get_current_user

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(year: str | None = None, notice: str | None = None,
                        user=Depends(get_current_user)):
    return await forms.list_forms(year, notice)


@router.get("/{form_id}")
async def get_form_full(form_id: int, version: int | None = None,
                        user=Depends(get_current_user)):
    return await forms.get_form_full(form_id, version)


@router.get("/{form_id}/sections")
async def get_form_sections(form_id: int, version: int | None = None,
                            user=Depends(get_current_user)):
    sections = await forms.get_sections(form_id, version)
    return [s["id"] for s in sections]


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(form_id: int, section_id: int,
                          user=Depends(get_current_user)):
    return await forms.get_section_fields(form_id, section_id)
