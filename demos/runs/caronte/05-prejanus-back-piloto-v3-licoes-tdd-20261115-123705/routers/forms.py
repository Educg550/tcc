from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_db as forms_db
from auth import get_current_user
from db import get_forms_db

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    return await forms_db.list_forms(db, year=year, notice=notice)


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    form = await forms_db.get_form(db, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_db.get_sections(db, form_id, version)
    out_sections = []
    for section in sections:
        fields = await forms_db.get_fields(db, form_id, section["id"])
        out_sections.append(
            {
                **forms_db.section_dict(section),
                "fields": fields,
            }
        )
    return {**form, "sections": out_sections}


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    form = await forms_db.get_form(db, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_db.get_sections(db, form_id, version)
    return [forms_db.section_dict(s) for s in sections]


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_forms_db),
):
    fields = await forms_db.get_fields(db, form_id, section_id)
    if not fields:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    return fields
