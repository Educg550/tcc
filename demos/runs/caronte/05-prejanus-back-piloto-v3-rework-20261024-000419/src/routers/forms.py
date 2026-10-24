"""Rotas de leitura dos formulários do Forms."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from ..auth import require_user
from ..db import get_forms_db
from ..services.forms_integration import (
    form_sections,
    get_form,
    section_fields,
)

router = APIRouter(tags=["forms"])


def _form_dict(row):
    return {
        "id": row["id"],
        "title": (row["title"] or {}).get("pt"),
        "description": (row["description"] or {}).get("pt"),
        "created_at": row["created_at"],
        "phase": str(row["phase"]),
        "tags": row["tags"],
        "version": row["version"],
    }


def _field_dict(field):
    return {
        "id": field["id"],
        "form_id": field["form_id"],
        "section_id": field["section_id"],
        "label": (field["label"] or {}).get("pt"),
        "name": field["name"],
        "description": (field["description"] or {}).get("pt"),
        "type": str(field["type"]),
        "placeholder": field["placeholder"],
        "required": field["required"],
        "disabled": field["disabled"],
        "validation": field["validation"],
        "error_message": (field["error_message"] or {}).get("pt"),
        "prefix": field["prefix"],
        "position": field["position"],
        "is_active": field["is_active"],
        "version": field["version"],
    }


def _section_dict(section):
    return {
        "id": section["id"],
        "form_id": section["form_id"],
        "title": (section["title"] or {}).get("pt"),
        "description": (section["description"] or {}).get("pt"),
        "position": section["position"],
        "is_active": section["is_active"],
        "version": section["version"],
    }


@router.get("/forms")
def get_all_forms(year: str | None = Query(default=None),
                 notice: str | None = Query(default=None),
                 user=Depends(require_user), fdb=Depends(get_forms_db)):
    query = "SELECT * FROM form WHERE true"
    params: dict = {}
    if year is not None:
        query += " AND tags->>'Ano' = :year"
        params["year"] = year
    if notice is not None:
        query += " AND tags->>'Edital' = :notice"
        params["notice"] = notice
    query += " ORDER BY id"
    rows = fdb.execute(text(query), params).mappings().all()
    return [_form_dict(r) for r in rows]


@router.get("/forms/{form_id}")
def get_form_full(form_id: int, version: int | None = Query(default=None),
                  user=Depends(require_user), fdb=Depends(get_forms_db)):
    if get_form(fdb, form_id) is None:
        raise HTTPException(status_code=404, detail="Form not found")
    sections = form_sections(fdb, form_id, version)
    out = []
    for section in sections:
        item = _section_dict(section)
        item["fields"] = [
            _field_dict(f) for f in
            section_fields(fdb, section["id"], version=version,
                           only_active=(version is None))
        ]
        out.append(item)
    return out


@router.get("/forms/{form_id}/sections")
def get_form_sections(form_id: int, version: int | None = Query(default=None),
                      user=Depends(require_user), fdb=Depends(get_forms_db)):
    if get_form(fdb, form_id) is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return [_section_dict(s) for s in form_sections(fdb, form_id, version)]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_form_fields(form_id: int, section_id: int,
                    user=Depends(require_user), fdb=Depends(get_forms_db)):
    if get_form(fdb, form_id) is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return [_field_dict(f) for f in section_fields(fdb, section_id)]
