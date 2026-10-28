from fastapi import APIRouter, Depends, HTTPException

from auth import current_user
from services import forms_service as forms

router = APIRouter(tags=["forms"])


@router.get("/forms")
def get_all_forms(year: str | None = None, notice: str | None = None, user=Depends(current_user)):
    return forms.list_forms(year=year, notice=notice)


@router.get("/forms/{form_id}")
def get_form_full(form_id: int, version: int | None = None, user=Depends(current_user)):
    form = forms.get_form(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    sections = []
    for sec in forms.select_sections(form_id, version):
        sj = forms.section_json(sec)
        sj["fields"] = [forms.field_json(f) for f in forms.get_fields(sec["id"])]
        sections.append(sj)
    form["sections"] = sections
    return form


@router.get("/forms/{form_id}/sections")
def get_form_sections(form_id: int, version: int | None = None, user=Depends(current_user)):
    return [forms.section_json(s) for s in forms.select_sections(form_id, version)]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_form_fields(form_id: int, section_id: int, user=Depends(current_user)):
    return [forms.field_json(f) for f in forms.get_fields(section_id)]
