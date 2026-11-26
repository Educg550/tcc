from fastapi import APIRouter, Depends

import forms_db
from auth import get_current_user
from database import FormsSessionLocal
from models import User

router = APIRouter(tags=["forms"])


@router.get("/forms")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user: User = Depends(get_current_user),
):
    async with FormsSessionLocal() as fdb:
        return await forms_db.list_forms(fdb, year, notice)


@router.get("/forms/{form_id}")
async def get_form_full(
    form_id: int, version: int | None = None, user: User = Depends(get_current_user)
):
    async with FormsSessionLocal() as fdb:
        form = await forms_db.get_form(fdb, form_id)
        if form is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Formulário não encontrado")
        sections = await forms_db.select_sections(fdb, form_id, version)
        out_sections = []
        for sec in sections:
            fields = await forms_db.get_fields(fdb, sec["id"], version=version)
            out_sections.append(
                {
                    "id": sec["id"],
                    "title": forms_db._pick(sec["title"]),
                    "description": forms_db._pick(sec["description"]),
                    "position": sec["position"],
                    "is_active": sec["is_active"],
                    "version": sec["version"],
                    "fields": [
                        {
                            "id": f["id"],
                            "name": f["name"],
                            "label": forms_db._pick(f["label"]),
                            "type": f["type"],
                            "prefix": f["prefix"],
                            "position": f["position"],
                            "required": f["required"],
                        }
                        for f in fields
                    ],
                }
            )
        return {**form, "sections": out_sections}


@router.get("/forms/{form_id}/sections")
async def get_form_sections(
    form_id: int, version: int | None = None, user: User = Depends(get_current_user)
):
    async with FormsSessionLocal() as fdb:
        sections = await forms_db.select_sections(fdb, form_id, version)
        return [s["id"] for s in sections]


@router.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int, section_id: int, user: User = Depends(get_current_user)
):
    async with FormsSessionLocal() as fdb:
        fields = await forms_db.get_fields(fdb, section_id, active_only=True)
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "label": forms_db._pick(f["label"]),
                "description": forms_db._pick(f["description"]),
                "type": f["type"],
                "placeholder": f["placeholder"],
                "prefix": f["prefix"],
                "position": f["position"],
                "required": f["required"],
                "disabled": f["disabled"],
                "is_active": f["is_active"],
                "version": f["version"],
            }
            for f in fields
        ]
