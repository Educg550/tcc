from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_current_user, get_forms_db
from services import forms_db

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    fdb: AsyncSession = Depends(get_forms_db),
    user=Depends(get_current_user),
):
    tag_filter = {}
    if year:
        tag_filter["Ano"] = year
    if notice:
        tag_filter["Edital"] = notice
    return await forms_db.list_forms(fdb, tag_filter or None)


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    fdb: AsyncSession = Depends(get_forms_db),
    user=Depends(get_current_user),
):
    form = await forms_db.get_form(fdb, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_db.get_sections(fdb, form_id, version)
    out_sections = []
    for section in sections:
        fields = await forms_db.get_fields(fdb, section["id"], version)
        out_sections.append({**section, "fields": fields})
    return {**form, "sections": out_sections}


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    fdb: AsyncSession = Depends(get_forms_db),
    user=Depends(get_current_user),
):
    form = await forms_db.get_form(fdb, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    return await forms_db.get_sections(fdb, form_id, version)


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    fdb: AsyncSession = Depends(get_forms_db),
    user=Depends(get_current_user),
):
    form = await forms_db.get_form(fdb, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    return await forms_db.get_fields(fdb, section_id)
