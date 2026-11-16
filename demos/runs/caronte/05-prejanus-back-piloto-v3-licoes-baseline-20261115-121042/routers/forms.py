from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, get_forms_db
from services import forms_service

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user: dict = Depends(get_current_user),
    fs=Depends(get_forms_db),
):
    del user
    return await forms_service.list_forms(fs, year, notice)


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user: dict = Depends(get_current_user),
    fs=Depends(get_forms_db),
):
    del user
    form = await forms_service.get_form(fs, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    sections = await forms_service.select_sections(fs, form_id, version)
    for section in sections:
        section["fields"] = await forms_service.select_fields(fs, section["id"], version)
    form["sections"] = sections
    return form


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user: dict = Depends(get_current_user),
    fs=Depends(get_forms_db),
):
    del user
    sections = await forms_service.select_sections(fs, form_id, version)
    return [section["id"] for section in sections]


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user: dict = Depends(get_current_user),
    fs=Depends(get_forms_db),
):
    del user
    return await forms_service.select_fields(fs, section_id, None)
