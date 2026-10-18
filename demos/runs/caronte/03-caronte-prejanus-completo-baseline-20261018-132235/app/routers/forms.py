"""Forms routes: list forms and inspect their structure and versions."""
from fastapi import APIRouter, Depends, HTTPException

from .. import formsdb
from ..db import get_db
from ..security import require_user

router = APIRouter(tags=["forms"])


@router.get("/forms")
def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(require_user),
):
    return formsdb.list_forms(year=year, notice=notice)


def _form_or_404(form_id: int) -> dict:
    form = formsdb.get_form(form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.get("/forms/{form_id}")
def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(require_user),
):
    form = _form_or_404(form_id)
    sections = formsdb.get_sections(form_id, version)
    return {
        "id": form.get("id"),
        "title": form.get("title") or form.get("name"),
        "description": form.get("description"),
        "tags": form.get("tags"),
        "phase": form.get("phase"),
        "sections": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "label": s.get("label") or s.get("name"),
                "position": s.get("position"),
                "version": s.get("version"),
                "fields": formsdb.get_fields(s.get("id")),
            }
            for s in sections
        ],
    }


@router.get("/forms/{form_id}/sections")
def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(require_user),
):
    _form_or_404(form_id)
    sections = formsdb.get_sections(form_id, version)
    return [s.get("id") for s in sections]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(require_user),
):
    _form_or_404(form_id)
    section = formsdb.get_section(section_id)
    if section is None or section.get("form_id") != form_id:
        raise HTTPException(status_code=404, detail="Section not found")
    return formsdb.get_fields(section_id)