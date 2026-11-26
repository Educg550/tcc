from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import forms_db
from prejanus.db import get_forms_db
from prejanus.deps import get_current_user

router = APIRouter(tags=["forms"])


@router.get("/forms")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
    fdb: AsyncSession = Depends(get_forms_db),
):
    return await forms_db.list_forms(fdb, year, notice)


@router.get("/forms/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb: AsyncSession = Depends(get_forms_db),
):
    form = await forms_db.get_form(fdb, form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    sections = await forms_db.get_sections(fdb, form_id, version)
    out = []
    for section in sections:
        sec = forms_db.section_dict(section)
        fields = await forms_db.get_fields(fdb, form_id, [section["id"]], version)
        sec["fields"] = [forms_db.field_dict(f) for f in fields]
        out.append(sec)
    return out


@router.get("/forms/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sections = await forms_db.get_sections(fdb, form_id, version)
    return [{"id": s["id"], "title": forms_db.section_dict(s)["title"]} for s in sections]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
    fdb: AsyncSession = Depends(get_forms_db),
):
    fields = await forms_db.get_fields_of_section(fdb, section_id)
    return [forms_db.field_dict(f) for f in fields]
