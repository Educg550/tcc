from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from auth import get_current_user
from database import FormsSession
from services import forms_service

router = APIRouter(tags=["forms"])


@router.get("/forms")
def get_all_forms(year: str | None = None, notice: str | None = None, user=Depends(get_current_user)):
    query = "select * from form"
    conditions = []
    params = {}
    if year:
        conditions.append("tags->>'Ano' = :year")
        params["year"] = year
    if notice:
        conditions.append("tags->>'Edital' = :notice")
        params["notice"] = notice
    if conditions:
        query += " where " + " and ".join(conditions)
    query += " order by id"
    with FormsSession() as fs:
        rows = fs.execute(text(query), params).mappings().all()
        return [forms_service.form_dict(r) for r in rows]


@router.get("/forms/{form_id}")
def get_form_full(form_id: int, version: int | None = None, user=Depends(get_current_user)):
    with FormsSession() as fs:
        form = forms_service.get_form(fs, form_id)
        if form is None:
            raise HTTPException(status_code=404, detail="Formulário não encontrado")
        result = forms_service.form_dict(form)
        sections = []
        for section in forms_service.get_sections(fs, form_id, version):
            entry = forms_service.section_dict(section)
            entry["fields"] = [forms_service.field_dict(f) for f in forms_service.get_fields(fs, section["id"])]
            sections.append(entry)
        result["sections"] = sections
        return result


@router.get("/forms/{form_id}/sections")
def get_form_sections(form_id: int, version: int | None = None, user=Depends(get_current_user)):
    with FormsSession() as fs:
        if forms_service.get_form(fs, form_id) is None:
            raise HTTPException(status_code=404, detail="Formulário não encontrado")
        return [forms_service.section_dict(s) for s in forms_service.get_sections(fs, form_id, version)]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_form_fields(form_id: int, section_id: int, user=Depends(get_current_user)):
    with FormsSession() as fs:
        section = fs.execute(
            text("select * from form_section where id=:i and form_id=:f"), {"i": section_id, "f": form_id}
        ).mappings().first()
        if section is None:
            raise HTTPException(status_code=404, detail="Seção não encontrada")
        return [forms_service.field_dict(f) for f in forms_service.get_fields(fs, section_id)]
