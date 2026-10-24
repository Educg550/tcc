from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from src.auth import get_current_user
from src.db import get_forms_db
from src.services.forms_service import fields_of_section, sections_of

router = APIRouter(prefix="/forms", tags=["forms"])


def _localized(value):
    if isinstance(value, dict):
        return value.get("pt") or ""
    return value


@router.get("")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    query = (
        "SELECT id, title, description, created_at, phase::text AS phase, "
        "created_by, tags, metadata, version FROM form WHERE 1=1"
    )
    params = {}
    if year is not None:
        query += " AND tags ->> 'Ano' = :year"
        params["year"] = year
    if notice is not None:
        query += " AND tags ->> 'Edital' = :notice"
        params["notice"] = notice
    query += " ORDER BY id"
    result = await fdb.execute(text(query), params)
    forms = []
    for row in result:
        form = dict(row._mapping)
        form["title"] = _localized(form["title"])
        form["description"] = _localized(form["description"])
        forms.append(form)
    return forms


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    result = await fdb.execute(text("SELECT id FROM form WHERE id = :i"), {"i": form_id})
    if not result.first():
        raise HTTPException(status_code=404, detail="Form not found")
    sections = await sections_of(fdb, form_id, version)
    for section in sections:
        section["fields"] = await fields_of_section(fdb, section["id"])
    return sections


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    return await sections_of(fdb, form_id, version)


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
    fdb=Depends(get_forms_db),
):
    return await fields_of_section(fdb, section_id)
