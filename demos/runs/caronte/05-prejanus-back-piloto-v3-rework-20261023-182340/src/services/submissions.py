import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

BOOL_KEYS = {'disabilities', 'ethnicity_race', 'will_apply_scholarship'}
BIDDING_LABELS = ['decline', 'available', 'interested', 'agreed', 'interested_scholarship']
PHASE_TO_FORMS = {'inscricoes': 'Registration', 'homologacao': 'Approval',
                  'avaliacao': 'Completed', 'encerrado': 'Completed'}


def coerce(key: str, value):
    if value is None:
        return None
    if key in BOOL_KEYS:
        return str(value).strip().lower() in ('true', 'yes', 'sim', '1',
                                              'verdadeiro', 'verdadeira')
    try:
        parsed = json.loads(value)
        if isinstance(parsed, (bool, int, float)):
            return parsed
    except (ValueError, TypeError):
        pass
    return value


def extract_data(tree: dict, values: dict) -> dict:
    out = {}
    if not isinstance(tree, dict):
        return out
    for key, node in tree.items():
        if node is None:
            out[key] = None
        elif isinstance(node, dict):
            if isinstance(node.get('field'), int):
                out[key] = coerce(key, values.get(node['field']))
            else:
                out[key] = extract_data(node, values)
    return out


async def get_edict(psession: AsyncSession, edict_id: int) -> dict | None:
    row = (await psession.execute(
        text('SELECT * FROM edict WHERE id = :i'), {'i': edict_id})).mappings().first()
    return dict(row) if row else None


async def get_submission(psession: AsyncSession, submission_id: int) -> dict | None:
    row = (await psession.execute(
        text('SELECT * FROM submission WHERE id = :i'),
        {'i': submission_id})).mappings().first()
    return dict(row) if row else None


async def get_form_response(fsession: AsyncSession, response_id: int) -> dict | None:
    row = (await fsession.execute(
        text('SELECT * FROM form_response WHERE id = :i'),
        {'i': response_id})).mappings().first()
    return dict(row) if row else None


async def response_values(fsession: AsyncSession, response_id: int) -> dict:
    rows = (await fsession.execute(
        text('SELECT field_id, value FROM responses WHERE response_id = :r'),
        {'r': response_id})).all()
    return {r[0]: r[1] for r in rows}


async def get_mapping(psession: AsyncSession, edict_id: int, form_type: str,
                      version: int | None = None) -> dict | None:
    if version is not None:
        row = (await psession.execute(text(
            'SELECT * FROM edict_form_mappings WHERE edict_id = :e '
            'AND form_type = :t AND form_version = :v '
            'ORDER BY id DESC LIMIT 1'),
            {'e': edict_id, 't': form_type, 'v': version})).mappings().first()
        if row:
            return dict(row)
    row = (await psession.execute(text(
        'SELECT * FROM edict_form_mappings WHERE edict_id = :e '
        'AND form_type = :t ORDER BY form_version DESC, id DESC LIMIT 1'),
        {'e': edict_id, 't': form_type})).mappings().first()
    return dict(row) if row else None


async def base_data(psession: AsyncSession, fsession: AsyncSession,
                    edict: dict, sub: dict):
    resp = await get_form_response(fsession, sub['candidate_form_id'])
    if not resp:
        return None, {}, {}
    values = await response_values(fsession, resp['id'])
    mapping = await get_mapping(psession, edict['id'], 'candidate', resp['form_version'])
    data = extract_data(mapping['mapping'] if mapping else {}, values)
    return resp, values, data


async def sync_edict(psession: AsyncSession, fsession: AsyncSession, edict: dict) -> None:
    try:
        cand_form = int(edict['candidate_forms'])
    except (TypeError, ValueError):
        return
    responses = (await fsession.execute(text(
        'SELECT id, form_version FROM form_response '
        'WHERE form_id = :f AND submitted_at IS NOT NULL ORDER BY id'),
        {'f': cand_form})).mappings().all()
    subs = (await psession.execute(text(
        'SELECT id, candidate_form_id, recommenders_form_ids FROM submission '
        'WHERE edict_id = :e ORDER BY id'), {'e': edict['id']})).mappings().all()
    existing = {s['candidate_form_id'] for s in subs}
    rec_mapping = await get_mapping(psession, edict['id'], 'recommender')
    rec_version = rec_mapping['form_version'] if rec_mapping else 1
    created = False
    for r in responses:
        if r['id'] in existing:
            continue
        await psession.execute(text(
            "INSERT INTO submission (edict_id, candidate_form_id, stats, "
            "recommenders_form_ids, recommender_form_version, candidate_form_version, "
            "created_at, updated_at) VALUES (:e, :c, 'underreview', "
            "CAST('[]' AS json), :rv, :cv, now(), now())"),
            {'e': edict['id'], 'c': r['id'], 'rv': rec_version, 'cv': r['form_version']})
        created = True
    if created:
        await psession.commit()
        subs = (await psession.execute(text(
            'SELECT id, candidate_form_id, recommenders_form_ids FROM submission '
            'WHERE edict_id = :e ORDER BY id'), {'e': edict['id']})).mappings().all()

    try:
        rec_form = int(edict['recommenders_forms'])
    except (TypeError, ValueError):
        return
    recs = (await fsession.execute(text(
        'SELECT id, email, submitted_at, metadata FROM form_response '
        'WHERE form_id = :f ORDER BY id'), {'f': rec_form})).mappings().all()
    claimed = set()
    candidates = []
    for s in subs:
        resp = await get_form_response(fsession, s['candidate_form_id'])
        if not resp:
            continue
        values = await response_values(fsession, s['candidate_form_id'])
        mapping = await get_mapping(psession, edict['id'], 'candidate',
                                    resp['form_version'])
        data = extract_data(mapping['mapping'] if mapping else {}, values)
        claimed.update(s['recommenders_form_ids'] or [])
        candidates.append({
            'id': s['id'],
            'ids': list(s['recommenders_form_ids'] or []),
            'values': {v for v in values.values() if v},
            'email': data.get('email') or resp['email'],
            'name': data.get('name'),
            'token': str(resp['token']),
        })
    changed = False
    for r in recs:
        if r['id'] in claimed:
            continue
        r_values = {v for v in (await response_values(fsession, r['id'])).values() if v}
        if r['email']:
            r_values.add(r['email'])
        meta_values = ({str(v) for v in r['metadata'].values()}
                       if isinstance(r['metadata'], dict) else set())
        for c in candidates:
            if ((c['email'] and c['email'] in r_values)
                    or (c['name'] and c['name'] in r_values)
                    or (r['email'] and r['email'] in c['values'])
                    or (c['token'] in meta_values)):
                c['ids'].append(r['id'])
                await psession.execute(text(
                    'UPDATE submission SET recommenders_form_ids = CAST(:ids AS json), '
                    'updated_at = now() WHERE id = :i'),
                    {'ids': json.dumps(c['ids']), 'i': c['id']})
                claimed.add(r['id'])
                changed = True
                break
    if changed:
        await psession.commit()


async def accept_info(fsession: AsyncSession, sub: dict) -> dict:
    empty = {'sent': 'not_sent', 'accept': None, 'comments': None, 'submitted_at': None}
    if not sub['accept_form_id']:
        return empty
    r = await get_form_response(fsession, sub['accept_form_id'])
    if not r:
        return empty
    values = await response_values(fsession, r['id'])
    fields = (await fsession.execute(
        text('SELECT id, name FROM form_field WHERE form_id = :f'),
        {'f': r['form_id']})).all()
    by_name = {name: fid for fid, name in fields}
    return {
        'sent': 'replied' if r['submitted_at'] else 'sent',
        'accept': values.get(by_name['accept']) if 'accept' in by_name else None,
        'comments': values.get(by_name['comments']) if 'comments' in by_name else None,
        'submitted_at': r['submitted_at'].isoformat() if r['submitted_at'] else None,
    }


async def _user_labels(psession: AsyncSession, user_id: int, submission_id: int):
    rows = (await psession.execute(text(
        "SELECT id, label, color FROM labels WHERE user_id = :u "
        "AND submission_id = :s AND context_type = 'candidate' ORDER BY id"),
        {'u': user_id, 's': submission_id})).mappings().all()
    return [dict(r) for r in rows]


async def _bidding_users(psession: AsyncSession, edict: dict, sub: dict) -> dict:
    rows = (await psession.execute(text(
        "SELECT l.label, u.id, u.name, u.email, sl.slots FROM labels l "
        'JOIN "user" u ON u.id = l.user_id '
        'LEFT JOIN user_edict_slots sl ON sl.user_id = l.user_id AND sl.edict_id = :e '
        "WHERE l.submission_id = :s AND l.context_type = 'bidding' ORDER BY u.id"),
        {'e': edict['id'], 's': sub['id']})).mappings().all()
    data = {label: [] for label in BIDDING_LABELS}
    for r in rows:
        data.setdefault(r['label'], []).append({
            'id': r['id'], 'name': r['name'], 'email': r['email'],
            'slots': str(r['slots']) if r['slots'] is not None else None,
        })
    return data


async def build_submission(psession: AsyncSession, fsession: AsyncSession,
                           edict: dict, sub: dict, user_id: int) -> dict:
    resp, values, data = await base_data(psession, fsession, edict, sub)
    email = data.get('email') or (resp['email'] if resp else None)
    advisor = None
    if sub['advisor_id']:
        arow = (await psession.execute(
            text('SELECT id, name, email FROM "user" WHERE id = :i'),
            {'i': sub['advisor_id']})).first()
        if arow:
            advisor = {'id': arow[0], 'name': arow[1], 'email': arow[2]}
    fav = (await psession.execute(
        text('SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s'),
        {'u': user_id, 's': sub['id']})).first()
    return {
        'id': sub['id'],
        'token': str(resp['token']) if resp else None,
        'name': data.get('name'),
        'email': email,
        'phone_number': data.get('phone_number'),
        'nationality': data.get('nationality'),
        'personal_website': data.get('personal_website'),
        'gender': data.get('gender'),
        'advisor': advisor,
        'birth_date': data.get('birth_date'),
        'graduation': data.get('graduation') or {},
        'poscomp': data.get('poscomp'),
        'current_occupation': data.get('current_occupation'),
        'research': data.get('research') or {},
        'lattes_curriculum': data.get('lattes_curriculum'),
        'stats': sub['stats'],
        'is_favorite': fav is not None,
        'bidding_users': {'data': await _bidding_users(psession, edict, sub)},
        'labels': await _user_labels(psession, user_id, sub['id']),
        'disabilities': data.get('disabilities'),
        'ethnicity_race': data.get('ethnicity_race'),
        'accept': await accept_info(fsession, sub),
    }


async def build_summary(psession: AsyncSession, fsession: AsyncSession,
                        edict: dict, sub: dict, user_id: int) -> dict:
    resp, values, data = await base_data(psession, fsession, edict, sub)
    email = data.get('email') or (resp['email'] if resp else None)
    recommenders = []
    for rid in (sub['recommenders_form_ids'] or []):
        r = await get_form_response(fsession, rid)
        if not r:
            continue
        rvals = await response_values(fsession, rid)
        mapping = await get_mapping(psession, edict['id'], 'recommender',
                                    r['form_version'])
        rd = extract_data(mapping['mapping'] if mapping else {}, rvals)
        recommenders.append({
            'fullname': rd.get('fullname'),
            'rating': rd.get('rating'),
            'affiliation': rd.get('affiliation'),
            'email': r['email'],
            'sent': r['submitted_at'].isoformat() if r['submitted_at'] else None,
        })
    note = (await psession.execute(
        text('SELECT note FROM private_note WHERE user_id = :u AND submission_id = :s'),
        {'u': user_id, 's': sub['id']})).first()
    return {
        'id': sub['id'],
        'token': str(resp['token']) if resp else None,
        'name': data.get('name'),
        'email': email,
        'phone_number': data.get('phone_number'),
        'birth_date': data.get('birth_date'),
        'nationality': data.get('nationality'),
        'gender': data.get('gender'),
        'personal_website': data.get('personal_website'),
        'current_occupation': data.get('current_occupation'),
        'lattes_curriculum': data.get('lattes_curriculum'),
        'graduation': data.get('graduation') or {},
        'research': data.get('research') or {},
        'poscomp': data.get('poscomp'),
        'stats': sub['stats'],
        'letter_sent': sub['letter_sent'],
        'private_note': note[0] if note else '',
        'entry_semester': sub['entry_semester'],
        'recommenders': recommenders,
        'labels': await _user_labels(psession, user_id, sub['id']),
        'accept': await accept_info(fsession, sub),
    }


async def build_submission_form(fsession: AsyncSession, resp: dict) -> list[dict]:
    from src.services import forms as forms_svc
    sections = await forms_svc.get_sections(fsession, resp['form_id'],
                                            version=resp['form_version'])
    values = await response_values(fsession, resp['id'])
    out = []
    for sec in sections:
        fields = await forms_svc.get_fields(fsession, sec['id'])
        out.append({**sec, 'fields': [{**f, 'value': values.get(f['id'])}
                                      for f in fields]})
    return out
