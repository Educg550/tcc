from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_user
from src.db import get_forms_session
from src.services import forms as forms_svc

router = APIRouter(prefix='/forms', tags=['forms'])


async def _sections_with_fields(fsession: AsyncSession, form_id: int,
                                version: int | None) -> list[dict]:
    sections = await forms_svc.get_sections(fsession, form_id, version)
    out = []
    for sec in sections:
        fields = await forms_svc.get_fields(fsession, sec['id'])
        out.append({**sec, 'fields': fields})
    return out


@router.get('')
async def get_all(year: str | None = None, notice: str | None = None,
                  user: dict = Depends(get_current_user),
                  fsession: AsyncSession = Depends(get_forms_session)):
    return await forms_svc.list_forms(fsession, year, notice)


@router.get('/{form_id}')
async def get_form_full(form_id: int, version: int | None = None,
                        user: dict = Depends(get_current_user),
                        fsession: AsyncSession = Depends(get_forms_session)):
    if not await forms_svc.form_exists(fsession, form_id):
        raise HTTPException(status_code=404, detail='Form not found')
    return await _sections_with_fields(fsession, form_id, version)


@router.get('/{form_id}/sections')
async def get_form_sections(form_id: int, version: int | None = None,
                            user: dict = Depends(get_current_user),
                            fsession: AsyncSession = Depends(get_forms_session)):
    if not await forms_svc.form_exists(fsession, form_id):
        raise HTTPException(status_code=404, detail='Form not found')
    return await _sections_with_fields(fsession, form_id, version)


@router.get('/{form_id}/sessions/{section_id}/fields')
async def get_form_fields(form_id: int, section_id: int,
                          user: dict = Depends(get_current_user),
                          fsession: AsyncSession = Depends(get_forms_session)):
    return await forms_svc.get_fields(fsession, section_id)
