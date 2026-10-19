"""Consultas de formulários no banco do Forms."""
from fastapi import APIRouter, Depends, HTTPException

from db import get_forms_db
import forms_db

router = APIRouter()


def _match_tag(tags, key, value):
    for t in tags if isinstance(tags, list) else []:
        s = str(t)
        if s.lower().startswith(str(key).lower() + ":") and s.partition(":")[2].strip() == str(value):
            return True
        if s.lower() == str(value).lower():
            return True
    return False


@router.get("/forms")
def list_forms(year: str | None = None, notice: str | None = None, fs=Depends(get_forms_db)):
    forms = forms_db.list_forms(fs)
    if year is not None:
        forms = [f for f in forms if _match_tag(f["tags"], "Ano", year) or str(year) in str(f["tags"])]
    if notice is not None:
        forms = [f for f in forms if _match_tag(f["tags"], "Edital", notice) or str(notice) in str(f["tags"])]
    return forms


@router.get("/forms/{form_id}")
def get_form(form_id: str, version: str | None = None, fs=Depends(get_forms_db)):
    form = forms_db.get_form(fs, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    sections = forms_db.select_sections(fs, form_id, version)
    form["sections"] = [
        {**s, "fields": forms_db.section_fields(fs, s["id"])}
        for s in sections
    ]
    return form


@router.get("/forms/{form_id}/sections")
def get_sections(form_id: str, version: str | None = None, fs=Depends(get_forms_db)):
    sections = forms_db.select_sections(fs, form_id, version)
    return [s["id"] for s in sections]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_section_fields(form_id: str, section_id: str, fs=Depends(get_forms_db)):
    return forms_db.section_fields(fs, section_id)
