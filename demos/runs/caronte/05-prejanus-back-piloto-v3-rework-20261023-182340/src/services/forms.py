from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def localize(value):
    if isinstance(value, dict):
        return value.get('pt') or next((v for v in value.values() if v), None)
    return value


def _row(r) -> dict:
    return dict(r)


async def form_exists(fsession: AsyncSession, form_id: int) -> bool:
    row = (await fsession.execute(
        text('SELECT id FROM form WHERE id = :f'), {'f': form_id})).first()
    return row is not None


async def get_form_version(fsession: AsyncSession, form_id: int) -> int:
    row = (await fsession.execute(
        text('SELECT version FROM form WHERE id = :f'), {'f': form_id})).first()
    return row[0] if row else 1


async def list_forms(fsession: AsyncSession, year: str | None = None,
                     notice: str | None = None) -> list[dict]:
    rows = (await fsession.execute(text(
        'SELECT id, title, description, created_at, created_by, tags, phase, version '
        'FROM form WHERE (:y IS NULL OR tags->>\'Ano\' = :y) '
        'AND (:n IS NULL OR tags->>\'Edital\' = :n) ORDER BY id'),
        {'y': year, 'n': notice})).mappings().all()
    out = []
    for r in rows:
        d = _row(r)
        d['title'] = localize(d['title'])
        d['description'] = localize(d['description'])
        out.append(d)
    return out


async def get_sections(fsession: AsyncSession, form_id: int,
                       version: int | None = None) -> list[dict]:
    if version is None:
        rows = (await fsession.execute(text(
            'SELECT * FROM form_section WHERE form_id = :f AND is_active '
            'ORDER BY position, id'), {'f': form_id})).mappings().all()
    else:
        rows = (await fsession.execute(text(
            'SELECT * FROM form_section WHERE form_id = :f AND version = :v '
            'ORDER BY position, id'), {'f': form_id, 'v': version})).mappings().all()
        if not rows:
            rows = (await fsession.execute(text(
                'SELECT * FROM form_section WHERE form_id = :f '
                'ORDER BY position, id'), {'f': form_id})).mappings().all()
    out = []
    for r in rows:
        d = _row(r)
        d['title'] = localize(d['title'])
        d['description'] = localize(d['description'])
        out.append(d)
    return out


async def get_fields(fsession: AsyncSession, section_id: int) -> list[dict]:
    rows = (await fsession.execute(text(
        'SELECT * FROM form_field WHERE section_id = :s ORDER BY position, id'),
        {'s': section_id})).mappings().all()
    return [_row(r) for r in rows]


async def validate_mapping(fsession: AsyncSession, form_id: int, version: int,
                           tree: dict) -> None:
    sections = {r['id'] for r in (await fsession.execute(
        text('SELECT id FROM form_section WHERE form_id = :f'),
        {'f': form_id})).mappings().all()}
    version_sections = {r['id'] for r in (await fsession.execute(
        text('SELECT id FROM form_section WHERE form_id = :f AND version = :v'),
        {'f': form_id, 'v': version})).mappings().all()}
    fields = {r['id']: r['section_id'] for r in (await fsession.execute(
        text('SELECT id, section_id FROM form_field WHERE form_id = :f'),
        {'f': form_id})).mappings().all()}

    def check(node):
        if not isinstance(node, dict):
            raise HTTPException(status_code=422, detail='Invalid mapping structure')
        for value in node.values():
            if value is None:
                continue
            if not isinstance(value, dict):
                raise HTTPException(status_code=422, detail='Invalid mapping structure')
            if set(value) == {'section', 'field'}:
                field_id = value['field']
                if (field_id not in fields
                        or fields[field_id] != value['section']
                        or value['section'] not in sections):
                    raise HTTPException(status_code=422, detail='Invalid field reference')
                if version_sections and value['section'] not in version_sections:
                    raise HTTPException(
                        status_code=422,
                        detail='Field is not available in this form version')
            else:
                check(value)

    check(tree)
