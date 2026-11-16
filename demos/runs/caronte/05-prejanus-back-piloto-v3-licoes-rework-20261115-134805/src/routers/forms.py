from fastapi import APIRouter, Depends
from sqlalchemy import text

from ..auth import current_user
from ..db import engine_forms
from ..services.forms_db import form_sections, section_fields

router = APIRouter(prefix='/forms', tags=['forms'])


def _section_dict(sec: dict) -> dict:
    return {'id': sec['id'], 'form_id': sec['form_id'],
            'title': (sec['title'] or {}).get('pt'),
            'description': (sec['description'] or {}).get('pt'),
            'position': sec['position'], 'is_active': sec['is_active'],
            'version': sec['version']}


def _field_dict(f: dict) -> dict:
    return {'id': f['id'], 'form_id': f['form_id'], 'section_id': f['section_id'],
            'label': (f['label'] or {}).get('pt'), 'name': f['name'],
            'description': (f['description'] or {}).get('pt'), 'type': f['type'],
            'placeholder': f['placeholder'], 'required': f['required'],
            'disabled': f['disabled'], 'position': f['position'],
            'is_active': f['is_active'], 'version': f['version']}


@router.get('')
def get_all_forms(year: str | None = None, notice: str | None = None,
                  user=Depends(current_user)):
    with engine_forms.connect() as conn:
        rows = [dict(r) for r in conn.execute(
            text('SELECT id, title, description, created_at, phase, tags, version '
                 'FROM form ORDER BY id')).mappings().all()]
    out = []
    for r in rows:
        tags = r['tags'] or {}
        if year and tags.get('Ano') != year:
            continue
        if notice and tags.get('Edital') != notice:
            continue
        out.append({'id': r['id'], 'title': (r['title'] or {}).get('pt'),
                    'description': (r['description'] or {}).get('pt'),
                    'created_at': r['created_at'], 'phase': r['phase'],
                    'tags': tags, 'version': r['version']})
    return out


@router.get('/{form_id}')
def get_form_full(form_id: int, version: int | None = None,
                  user=Depends(current_user)):
    with engine_forms.connect() as conn:
        sections = form_sections(conn, form_id, version)
        out = []
        for sec in sections:
            item = _section_dict(sec)
            item['fields'] = [_field_dict(f) for f in section_fields(conn, sec['id'])]
            out.append(item)
    return out


@router.get('/{form_id}/sections')
def get_form_sections(form_id: int, version: int | None = None,
                      user=Depends(current_user)):
    with engine_forms.connect() as conn:
        return [_section_dict(s) for s in form_sections(conn, form_id, version)]


@router.get('/{form_id}/sessions/{section_id}/fields')
def get_form_fields(form_id: int, section_id: int, user=Depends(current_user)):
    with engine_forms.connect() as conn:
        return [_field_dict(f) for f in section_fields(conn, section_id)]
