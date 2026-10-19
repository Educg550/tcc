from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
import services.forms_service as forms_service

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def get_all_forms(
    year: str | None = None,
    notice: str | None = None,
    user=Depends(get_current_user),
):
    return await forms_service.list_forms(year, notice)


@router.get("/{form_id}")
async def get_form_full(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
):
    form = await forms_service.get_form_full(form_id, version)
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.get("/{form_id}/sections")
async def get_form_sections(
    form_id: int,
    version: int | None = None,
    user=Depends(get_current_user),
):
    if await forms_service.get_form(form_id) is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return await forms_service.get_section_ids(form_id, version)


@router.get("/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user=Depends(get_current_user),
):
    fields = await forms_service.get_fields(section_id)
    out = []
    for field in fields:
        label = field["label"] if isinstance(field["label"], dict) else {}
        out.append(
            {
                "id": field["id"],
                "name": field["name"],
                "label": label.get("pt") or label.get("en") or "",
                "description": field["description"] if not isinstance(field["description"], dict) else (field["description"].get("pt") or ""),
                "type": field["type"],
                "prefix": field["prefix"],
                "placeholder": field["placeholder"],
                "required": field["required"],
                "position": field["position"],
                "version": field["version"],
            }
        )
    return out
