from fastapi import APIRouter, Depends, HTTPException

from prejanus import formsdb
from prejanus.auth import get_current_user
from prejanus.models import User

router = APIRouter(tags=["forms"])


@router.get("/forms")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user: User = Depends(get_current_user),
):
    forms = await formsdb.list_forms()
    if year is not None and year != "":
        forms = [f for f in forms if (f["tags"] or {}).get("Ano") == year]
    if notice is not None and notice != "":
        forms = [f for f in forms if (f["tags"] or {}).get("Edital") == notice]
    return forms


@router.get("/forms/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user: User = Depends(get_current_user),
):
    form = await formsdb.get_form(form_id)
    if not form:
        raise HTTPException(404, "form not found")
    sections = await formsdb.get_sections(form_id, version)
    out_sections = []
    for section in sections:
        if version is not None:
            fields = await formsdb.get_fields_for_version(section["id"], version)
        else:
            fields = await formsdb.get_fields(section["id"])
        entry = dict(section)
        entry["fields"] = fields
        out_sections.append(entry)
    return {
        "id": form["id"],
        "title": formsdb._label(form["title"]),
        "description": formsdb._label(form["description"]),
        "created_at": form["created_at"],
        "phase": form["phase"],
        "tags": form["tags"] or {},
        "version": form["version"],
        "sections": out_sections,
    }


@router.get("/forms/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user: User = Depends(get_current_user),
):
    return await formsdb.get_sections(form_id, version)


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user: User = Depends(get_current_user),
):
    return await formsdb.get_fields(section_id)
