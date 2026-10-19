from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_forms_db
from services import forms_service

router = APIRouter(tags=["forms"])


@router.get("/forms")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    return await forms_service.list_forms(db, year, notice)


@router.get("/forms/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    form = await forms_service.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_service.select_sections(db, form_id, version)
    for section in sections:
        title = section.get("title") or {}
        section["title"] = title.get("pt") or title.get("en") or ""
        section["fields"] = await forms_service.select_fields(db, section["id"], version)
    form["sections"] = sections
    return form


@router.get("/forms/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    sections = await forms_service.select_sections(db, form_id, version)
    for section in sections:
        title = section.get("title") or {}
        section["title"] = title.get("pt") or title.get("en") or ""
    return sections


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    return await forms_service.select_fields(db, section_id)
