from sqlalchemy import text


def response_values(fconn, response_id: int) -> dict:
    rows = fconn.execute(
        text('SELECT field_id, value FROM responses WHERE response_id = :r'),
        {'r': response_id})
    return {row[0]: row[1] for row in rows}


def get_response(fconn, response_id: int) -> dict | None:
    row = fconn.execute(
        text('SELECT id, form_id, shared_id, email, token, current_section, '
             'submitted_at, form_version FROM form_response WHERE id = :r'),
        {'r': response_id}).mappings().first()
    return dict(row) if row else None


def form_sections(fconn, form_id: int, version: int | None = None) -> list[dict]:
    if version is not None:
        rows = fconn.execute(
            text('SELECT * FROM form_section WHERE form_id = :f AND version = :v '
                 'ORDER BY position, id'),
            {'f': form_id, 'v': version}).mappings().all()
        if rows:
            return [dict(r) for r in rows]
        rows = fconn.execute(
            text('SELECT * FROM form_section WHERE form_id = :f ORDER BY position, id'),
            {'f': form_id}).mappings().all()
        return [dict(r) for r in rows]
    rows = fconn.execute(
        text('SELECT * FROM form_section WHERE form_id = :f AND is_active '
             'ORDER BY position, id'),
        {'f': form_id}).mappings().all()
    return [dict(r) for r in rows]


def section_fields(fconn, section_id: int) -> list[dict]:
    rows = fconn.execute(
        text('SELECT * FROM form_field WHERE section_id = :s ORDER BY position, id'),
        {'s': section_id}).mappings().all()
    return [dict(r) for r in rows]


def mapping_targets(fconn, form_id: int, version: int) -> tuple[set, set]:
    """Conjuntos de ids de seção e pares (campo, seção) válidos para a versão."""
    rows = fconn.execute(
        text('SELECT id FROM form_section WHERE form_id = :f AND version = :v'),
        {'f': form_id, 'v': version}).scalars().all()
    if not rows:
        rows = fconn.execute(
            text('SELECT id FROM form_section WHERE form_id = :f'),
            {'f': form_id}).scalars().all()
    sections = set(rows)
    fields = set()
    if sections:
        rows = fconn.execute(
            text('SELECT id, section_id FROM form_field WHERE section_id = ANY(:s)'),
            {'s': list(sections)}).all()
        fields = {(r[0], r[1]) for r in rows}
    return sections, fields
