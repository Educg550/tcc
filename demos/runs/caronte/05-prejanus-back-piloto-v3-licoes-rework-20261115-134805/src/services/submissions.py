import json

from sqlalchemy import text

from .forms_db import form_sections, get_response, response_values, section_fields
from .mapping import walk_tree


def to_bool(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('', 'false', 'no', 'não', 'nao', '0'):
        return False
    return True


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_edict(conn, edict_id: int) -> dict:
    from fastapi import HTTPException
    row = conn.execute(text('SELECT * FROM edict WHERE id = :i'),
                       {'i': edict_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail='Edital não encontrado')
    return dict(row)


def get_submission(conn, submission_id: int) -> dict:
    from fastapi import HTTPException
    row = conn.execute(text('SELECT * FROM submission WHERE id = :i'),
                       {'i': submission_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail='Inscrição não encontrada')
    return dict(row)


def user_by_id(conn, user_id) -> dict | None:
    if not user_id:
        return None
    row = conn.execute(text('SELECT id, name, email FROM "user" WHERE id = :i'),
                       {'i': user_id}).mappings().first()
    return dict(row) if row else None


def _mappings(conn, edict_id: int, form_type: str) -> dict:
    rows = conn.execute(
        text('SELECT form_version, mapping FROM edict_form_mappings '
             'WHERE edict_id = :e AND form_type = :t'),
        {'e': edict_id, 't': form_type}).mappings().all()
    return {r['form_version']: r['mapping'] for r in rows}


def _mapping_for(mappings: dict, version) -> dict | None:
    if not mappings:
        return None
    if version in mappings:
        return mappings[version]
    return mappings[max(mappings)]


def sync_submissions(conn, fconn, edict: dict) -> None:
    """Cria inscrições para respostas finalizadas e associa recomendações."""
    form_id = int(edict['candidate_forms'])
    mappings = _mappings(conn, edict['id'], 'candidate')
    responses = [dict(r) for r in fconn.execute(
        text('SELECT id, form_version FROM form_response '
             'WHERE form_id = :f AND submitted_at IS NOT NULL'),
        {'f': form_id}).mappings().all()]
    existing = {r[0] for r in conn.execute(
        text('SELECT candidate_form_id FROM submission WHERE edict_id = :e'),
        {'e': edict['id']}).all()}
    for r in responses:
        if r['id'] in existing:
            continue
        conn.execute(
            text("INSERT INTO submission (edict_id, candidate_form_id, stats, "
                 "recommenders_form_ids, candidate_form_version, recommender_form_version) "
                 "VALUES (:e, :c, 'underreview', '[]'::json, :cv, 1)"),
            {'e': edict['id'], 'c': r['id'], 'cv': r['form_version']})

    rec_form = int(edict['recommenders_forms'])
    recs = [dict(r) for r in fconn.execute(
        text('SELECT id FROM form_response WHERE form_id = :f AND submitted_at IS NOT NULL'),
        {'f': rec_form}).mappings().all()]
    rec_sets = {}
    for r in recs:
        vals = response_values(fconn, r['id'])
        rec_sets[r['id']] = {str(v).strip().lower() for v in vals.values() if v}

    resp_versions = {r['id']: r['form_version'] for r in responses}
    subs = [dict(s) for s in conn.execute(
        text('SELECT id, candidate_form_id, recommenders_form_ids FROM submission '
             'WHERE edict_id = :e'),
        {'e': edict['id']}).mappings().all()]
    for s in subs:
        rid = s['candidate_form_id']
        mapping = _mapping_for(mappings, resp_versions.get(rid))
        if not mapping:
            continue
        data = walk_tree(mapping, response_values(fconn, rid))
        keys = {str(v).strip().lower() for v in (data.get('name'), data.get('email')) if v}
        if not keys:
            continue
        matched = sorted(rid2 for rid2, vals in rec_sets.items() if keys & vals)
        if matched != (s['recommenders_form_ids'] or []):
            conn.execute(
                text('UPDATE submission SET recommenders_form_ids = CAST(:r AS json) '
                     'WHERE id = :i'),
                {'r': json.dumps(matched), 'i': s['id']})


def user_labels(conn, user_id: int, submission_id: int) -> list[dict]:
    rows = conn.execute(
        text("SELECT id, label, color FROM labels WHERE user_id = :u "
             "AND submission_id = :s AND context_type = 'candidate' ORDER BY id"),
        {'u': user_id, 's': submission_id}).mappings().all()
    return [dict(r) for r in rows]


def bidding_users(conn, edict_id: int, submission_id: int) -> dict:
    rows = conn.execute(
        text("SELECT l.label, u.id, u.name, u.email, sl.slots FROM labels l "
             'JOIN "user" u ON u.id = l.user_id '
             'LEFT JOIN user_edict_slots sl ON sl.user_id = u.id AND sl.edict_id = :e '
             "WHERE l.submission_id = :s AND l.context_type = 'bidding' ORDER BY u.id"),
        {'e': edict_id, 's': submission_id}).mappings().all()
    data = {}
    for r in rows:
        data.setdefault(r['label'], []).append(
            {'id': r['id'], 'name': r['name'], 'email': r['email'],
             'slots': str(r['slots'] or 0)})
    return {'data': data}


def accept_info(conn, fconn, submission: dict) -> dict:
    empty = {'sent': 'not_sent', 'accept': None, 'comments': None, 'submitted_at': None}
    if not submission['accept_form_id']:
        return empty
    fr = get_response(fconn, submission['accept_form_id'])
    if not fr:
        return empty
    rows = fconn.execute(
        text('SELECT f.name, r.value FROM responses r JOIN form_field f ON f.id = r.field_id '
             'WHERE r.response_id = :rid'),
        {'rid': submission['accept_form_id']}).all()
    vals = {r[0]: r[1] for r in rows}
    return {'sent': 'replied' if fr['submitted_at'] else 'sent',
            'accept': vals.get('accept'), 'comments': vals.get('comments'),
            'submitted_at': fr['submitted_at']}


def _mapped_data(fconn, mappings: dict, response_id: int, form_version) -> dict:
    mapping = _mapping_for(mappings, form_version) or {}
    return walk_tree(mapping, response_values(fconn, response_id))


def build_item(conn, fconn, edict: dict, submission: dict, mappings: dict, user_id: int) -> dict:
    fr = get_response(fconn, submission['candidate_form_id']) or {}
    data = _mapped_data(fconn, mappings, submission['candidate_form_id'], fr.get('form_version'))
    grad = data.get('graduation') or {}
    research = data.get('research') or {}
    field = research.get('field') or {}
    poscomp = data.get('poscomp')
    favorite = conn.execute(
        text('SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s'),
        {'u': user_id, 's': submission['id']}).first() is not None
    return {
        'id': submission['id'],
        'token': str(fr.get('token')) if fr.get('token') else None,
        'name': data.get('name'),
        'email': data.get('email') or fr.get('email'),
        'phone_number': data.get('phone_number'),
        'nationality': data.get('nationality'),
        'personal_website': data.get('personal_website'),
        'gender': data.get('gender'),
        'advisor': user_by_id(conn, submission['advisor_id']),
        'birth_date': data.get('birth_date'),
        'graduation': {'country': grad.get('country'), 'course': grad.get('course'),
                       'institution': grad.get('institution'), 'year': to_int(grad.get('year'))},
        'poscomp': ({'year': to_int(poscomp.get('year')), 'score': str(poscomp.get('score'))}
                    if poscomp else None),
        'current_occupation': data.get('current_occupation'),
        'research': {'program': research.get('program'), 'semester': research.get('semester'),
                     'field': {'primary': field.get('primary'), 'secondary': field.get('secondary')},
                     'will_apply_scholarship': to_bool(research.get('will_apply_scholarship')),
                     'dedication_level': research.get('dedication_level')},
        'lattes_curriculum': data.get('lattes_curriculum'),
        'stats': submission['stats'],
        'is_favorite': favorite,
        'bidding_users': bidding_users(conn, edict['id'], submission['id']),
        'labels': user_labels(conn, user_id, submission['id']),
        'disabilities': to_bool(data.get('disabilities')),
        'ethnicity_race': to_bool(data.get('ethnicity_race')),
        'accept': accept_info(conn, fconn, submission),
    }


def list_submissions(conn, fconn, edict: dict, user_id: int,
                     stats: str | None = None, only_favorites: bool = False) -> list[dict]:
    sync_submissions(conn, fconn, edict)
    mappings = _mappings(conn, edict['id'], 'candidate')
    rows = [dict(r) for r in conn.execute(
        text('SELECT * FROM submission WHERE edict_id = :e ORDER BY id'),
        {'e': edict['id']}).mappings().all()]
    if stats:
        rows = [s for s in rows if s['stats'] == stats]
    if only_favorites:
        favs = {r[0] for r in conn.execute(
            text('SELECT submission_id FROM favorites WHERE user_id = :u'),
            {'u': user_id}).all()}
        rows = [s for s in rows if s['id'] in favs]
    return [build_item(conn, fconn, edict, s, mappings, user_id) for s in rows]


def submission_summary(conn, fconn, submission: dict, user_id: int) -> dict:
    edict = get_edict(conn, submission['edict_id'])
    mappings = _mappings(conn, submission['edict_id'], 'candidate')
    fr = get_response(fconn, submission['candidate_form_id']) or {}
    data = _mapped_data(fconn, mappings, submission['candidate_form_id'], fr.get('form_version'))
    grad = data.get('graduation') or {}
    research = data.get('research') or {}
    field = research.get('field') or {}
    poscomp = data.get('poscomp')
    rec_mappings = _mappings(conn, submission['edict_id'], 'recommender')
    recommenders = []
    for rid in (submission['recommenders_form_ids'] or []):
        rr = get_response(fconn, rid)
        if not rr:
            continue
        d = _mapped_data(fconn, rec_mappings, rid, rr.get('form_version'))
        recommenders.append({
            'fullname': d.get('fullname'), 'email': d.get('email'),
            'affiliation': d.get('affiliation'), 'rating': d.get('rating'),
            'sent': to_bool(d.get('sent')) if d.get('sent') is not None else True,
        })
    note = conn.execute(
        text('SELECT note FROM private_note WHERE user_id = :u AND submission_id = :s'),
        {'u': user_id, 's': submission['id']}).scalar()
    return {
        'id': submission['id'],
        'name': data.get('name'),
        'email': data.get('email') or fr.get('email'),
        'phone_number': data.get('phone_number'),
        'nationality': data.get('nationality'),
        'personal_website': data.get('personal_website'),
        'gender': data.get('gender'),
        'advisor': user_by_id(conn, submission['advisor_id']),
        'birth_date': data.get('birth_date'),
        'graduation': {'country': grad.get('country'), 'course': grad.get('course'),
                       'institution': grad.get('institution'), 'year': to_int(grad.get('year'))},
        'poscomp': ({'year': to_int(poscomp.get('year')), 'score': str(poscomp.get('score'))}
                    if poscomp else None),
        'current_occupation': data.get('current_occupation'),
        'research': {'program': research.get('program'), 'semester': research.get('semester'),
                     'field': {'primary': field.get('primary'), 'secondary': field.get('secondary')},
                     'will_apply_scholarship': to_bool(research.get('will_apply_scholarship')),
                     'dedication_level': research.get('dedication_level')},
        'lattes_curriculum': data.get('lattes_curriculum'),
        'stats': submission['stats'],
        'letter_sent': submission['letter_sent'],
        'private_note': note or '',
        'entry_semester': submission['entry_semester'] or '',
        'recommenders': recommenders,
        'labels': user_labels(conn, user_id, submission['id']),
        'disabilities': to_bool(data.get('disabilities')),
        'ethnicity_race': to_bool(data.get('ethnicity_race')),
        'accept': accept_info(conn, fconn, submission),
    }


def submission_form(fconn, response: dict) -> list[dict]:
    sections = form_sections(fconn, response['form_id'], response.get('form_version'))
    values = response_values(fconn, response['id'])
    out = []
    for sec in sections:
        fields = []
        for f in section_fields(fconn, sec['id']):
            fields.append({'id': f['id'], 'section_id': f['section_id'], 'name': f['name'],
                           'label': (f['label'] or {}).get('pt'), 'type': f['type'],
                           'position': f['position'], 'value': values.get(f['id'])})
        out.append({'id': sec['id'], 'form_id': sec['form_id'],
                    'title': (sec['title'] or {}).get('pt'),
                    'description': (sec['description'] or {}).get('pt'),
                    'position': sec['position'], 'is_active': sec['is_active'],
                    'version': sec['version'], 'fields': fields})
    return out
