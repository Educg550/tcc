from fastapi import APIRouter, Depends

import services.forms_db as forms_db
from auth import get_current_user

router = APIRouter(tags=["forms"])


@router.get("/forms")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user: dict = Depends(get_current_user),
):
    return await forms_db.list_forms(year, notice)


@router.get("/forms/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await forms_db.get_form_full(form_id, version)


@router.get("/forms/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await forms_db.get_sections(form_id, version)


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user: dict = Depends(get_current_user),
):
    return await forms_db.get_fields(section_id)
