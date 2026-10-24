import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_user, require_admin
from src.db import get_forms_session, get_session
from src.schemas import (AdvancePhaseEdictSchema, CloseEdictSchema,
                         EditEdictDateSchema, EditEdictSchema, InsertEdictSchema,
                         SectionsDocument, SlotsSchema)
from src.services import forms as forms_svc
from src.services import reports
from src.services import submissions as subs

router = APIRouter(prefix='/edicts', tags=['edicts'])

# label da fase -> campo de data do corpo do edital
PHASE_OF_DATE = [('inscricoes', 'date_application'),
                 ('homologacao', 'date_evaluation'),
                 ('avaliacao', 'date_verification'),
                 ('encerrado', 'date_closed')]


async def _get_edict(psession: AsyncSession, edict_id: int) -> dict:
    edict = await subs.get_edict(psession, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail='Edict not found')
    return edict


def _validate_dates(body) -> None:
    if not (body.date_application <= body.date_verification
            <= body.date_evaluation <= body.date_closed):
        raise HTTPException(status_code=400, detail='Dates are out of order')


@router.get('')
async def get_all(type: str | None = None, is_open: bool | None = None,
                  user: dict = Depends(get_current_user),
                  session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(text(
        'SELECT id, title, year, semester, type, is_open FROM edict '
        'WHERE (:t IS NULL OR type = :t) AND (:o IS NULL OR is_open = :o) '
        'ORDER BY closed_date DESC NULLS LAST, id DESC'),
        {'t': type, 'o': is_open})).mappings().all()
    return [{'id': r['id'], 'title': r['title'], 'year': r['year'],
             'semester': r['semester'], 'edict_type': r['type'],
             'is_open': r['is_open']} for r in rows]


@router.post('')
async def create_edict(body: InsertEdictSchema,
                       user: dict = Depends(require_admin),
                       session: AsyncSession = Depends(get_session)):
    _validate_dates(body)
    row = (await session.execute(text(
        'INSERT INTO edict (title, description, candidate_forms, recommenders_forms, '
        'closed_date, year, semester, type, phase, is_open, created_at, updated_at, '
        "user_id) VALUES (:t, :d, :cf, :rf, :cd, :y, :s, :ty, 'inscricoes', :o, "
        'now(), now(), :u) RETURNING id'),
        {'t': body.title, 'd': body.description,
         'cf': str(body.candidate_forms), 'rf': str(body.recommenders_forms),
         'cd': body.date_closed.date(), 'y': body.year, 's': body.semester,
         'ty': body.edict_type, 'o': body.is_open, 'u': user['id']})).first()
    edict_id = row[0]
    for phase, attr in PHASE_OF_DATE:
        await session.execute(text(
            'INSERT INTO edict_phase (edict_id, closed_date, phase) '
            'VALUES (:e, :d, :p)'),
            {'e': edict_id, 'd': getattr(body, attr).date(), 'p': phase})
    await session.commit()
    return {'id': edict_id, 'title': body.title, 'description': body.description,
            'year': body.year, 'semester': body.semester,
            'edict_type': body.edict_type, 'is_open': body.is_open,
            'candidate_forms': body.candidate_forms,
            'recommenders_forms': body.recommenders_forms,
            'date_application': body.date_application.isoformat(),
            'date_verification': body.date_verification.isoformat(),
            'date_evaluation': body.date_evaluation.isoformat(),
            'date_closed': body.date_closed.isoformat(),
            'closed_date': body.date_closed.date().isoformat()}


@router.get('/download_pdf/{job_id}')
async def download_pdf(job_id: str):
    return reports.download(job_id)


@router.get('/download_csv/{job_id}')
async def download_csv(job_id: str):
    return reports.download(job_id)


@router.get('/{edict_id}')
async def get_edict_by_id(edict_id: int,
                          user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    edict = await _get_edict(session, edict_id)
    phases = (await session.execute(text(
        'SELECT id, phase, closed_date FROM edict_phase WHERE edict_id = :e '
        'ORDER BY id'), {'e': edict_id})).mappings().all()
    slots = (await session.execute(text(
        'SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e'),
        {'u': user['id'], 'e': edict_id})).first()
    return {'id': edict['id'], 'title': edict['title'],
            'candidate_form_id': edict['candidate_forms'],
            'recommender_form_id': edict['recommenders_forms'],
            'description': edict['description'],
            'closed_date': str(edict['closed_date']) if edict['closed_date'] else None,
            'created_at': edict['created_at'].isoformat() if edict['created_at'] else None,
            'year': edict['year'], 'semester': edict['semester'],
            'type': edict['type'], 'is_open': edict['is_open'],
            'updated_at': edict['updated_at'].isoformat() if edict['updated_at'] else None,
            'phase': edict['phase'],
            'phases': [{'id': p['id'],
                        'closed_date': str(p['closed_date']) if p['closed_date'] else None,
                        'phase': p['phase']} for p in phases],
            'slots': str(slots[0]) if slots and slots[0] is not None else '0'}


@router.post('/{edict_id}/edit')
async def edit_edict(edict_id: int, body: EditEdictSchema,
                     user: dict = Depends(require_admin),
                     session: AsyncSession = Depends(get_session)):
    await _get_edict(session, edict_id)
    _validate_dates(body)
    await session.execute(text(
        'UPDATE edict SET title = :t, description = :d, year = :y, semester = :s, '
        'type = :ty, closed_date = :cd, updated_at = now() WHERE id = :i'),
        {'t': body.title, 'd': body.description, 'y': body.year,
         's': body.semester, 'ty': body.edict_type,
         'cd': body.date_closed.date(), 'i': edict_id})
    for phase, attr in PHASE_OF_DATE:
        await session.execute(text(
            'UPDATE edict_phase SET closed_date = :d '
            'WHERE edict_id = :e AND phase = :p'),
            {'d': getattr(body, attr).date(), 'e': edict_id, 'p': phase})
    await session.commit()
    return {'title': body.title, 'description': body.description,
            'year': body.year, 'semester': body.semester,
            'edict_type': body.edict_type,
            'date_application': body.date_application.isoformat(),
            'date_verification': body.date_verification.isoformat(),
            'date_evaluation': body.date_evaluation.isoformat(),
            'date_closed': body.date_closed.isoformat()}


@router.post('/{edict_id}/edit-date')
async def edit_edict_date_only(edict_id: int, body: EditEdictDateSchema,
                               user: dict = Depends(require_admin),
                               session: AsyncSession = Depends(get_session)):
    await _get_edict(session, edict_id)
    await session.execute(text(
        'UPDATE edict SET closed_date = :d, updated_at = now() WHERE id = :i'),
        {'d': body.closed_date, 'i': edict_id})
    await session.execute(text(
        "UPDATE edict_phase SET closed_date = :d "
        "WHERE edict_id = :e AND phase = 'encerrado'"),
        {'d': body.closed_date, 'e': edict_id})
    await session.commit()
    return {'closed_date': str(body.closed_date)}


@router.post('/{edict_id}/advance-phase')
async def advance_edict(edict_id: int, body: AdvancePhaseEdictSchema,
                        user: dict = Depends(require_admin),
                        session: AsyncSession = Depends(get_session),
                        fsession: AsyncSession = Depends(get_forms_session)):
    edict = await _get_edict(session, edict_id)
    phase_row = (await session.execute(text(
        'SELECT id, phase FROM edict_phase WHERE id = :i AND edict_id = :e'),
        {'i': body.id, 'e': edict_id})).mappings().first()
    if not phase_row:
        raise HTTPException(status_code=404, detail='Phase not found')
    await session.execute(text(
        'UPDATE edict SET phase = :p, updated_at = now() WHERE id = :i'),
        {'p': phase_row['phase'], 'i': edict_id})
    await session.commit()
    try:
        form_id = int(edict['candidate_forms'])
    except (TypeError, ValueError):
        form_id = None
    if form_id:
        forms_phase = subs.PHASE_TO_FORMS.get(phase_row['phase'])
        if forms_phase:
            await fsession.execute(text(
                'SELECT * FROM change_form_phase(:f, CAST(:p AS form_phase))'),
                {'f': form_id, 'p': forms_phase})
            await fsession.commit()
    return {'id': phase_row['id'], 'label': phase_row['phase']}


@router.delete('/{edict_id}/remove')
async def remove_edict(edict_id: int,
                       user: dict = Depends(require_admin),
                       session: AsyncSession = Depends(get_session)):
    await _get_edict(session, edict_id)
    await session.execute(text('DELETE FROM edict WHERE id = :i'), {'i': edict_id})
    await session.commit()
    return {'message': 'Edict removed successfully'}


@router.patch('/{edict_id}/close')
async def close_edict(edict_id: int, body: CloseEdictSchema,
                      user: dict = Depends(require_admin),
                      session: AsyncSession = Depends(get_session)):
    edict = await _get_edict(session, edict_id)
    if not edict['is_open']:
        raise HTTPException(status_code=409, detail='Edict is already closed')
    await session.execute(text(
        'UPDATE edict SET is_open = false, updated_at = now() WHERE id = :i'),
        {'i': edict_id})
    await session.execute(text(
        "UPDATE edict_phase SET closed_date = :d "
        "WHERE edict_id = :e AND phase = 'encerrado'"),
        {'d': body.confirmation_deadline, 'e': edict_id})
    await session.commit()
    return {'message': 'Edict closed'}


@router.post('/{edict_id}/slots')
async def set_user_slots(edict_id: int, body: SlotsSchema,
                         user: dict = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)):
    await _get_edict(session, edict_id)
    try:
        amount = int(body.amount)
    except (TypeError, ValueError):
        amount = 0
    amount = max(amount, 0)
    await session.execute(text(
        'INSERT INTO user_edict_slots (user_id, edict_id, slots) '
        'VALUES (:u, :e, :s) ON CONFLICT (user_id, edict_id) DO UPDATE SET slots = :s'),
        {'u': user['id'], 'e': edict_id, 's': amount})
    await session.commit()
    return {'amount': str(amount)}


@router.get('/{edict_id}/submissions')
async def get_all_submissions_from_edict(edict_id: int,
                                         stats: str | None = None,
                                         only_favorites: bool = False,
                                         user: dict = Depends(get_current_user),
                                         session: AsyncSession = Depends(get_session),
                                         fsession: AsyncSession = Depends(get_forms_session)):
    edict = await _get_edict(session, edict_id)
    await subs.sync_edict(session, fsession, edict)
    query = 'SELECT * FROM submission WHERE edict_id = :e'
    params: dict = {'e': edict_id}
    if stats:
        query += ' AND stats = :st'
        params['st'] = stats
    if only_favorites:
        query += ' AND id IN (SELECT submission_id FROM favorites WHERE user_id = :u)'
        params['u'] = user['id']
    query += ' ORDER BY id'
    rows = (await session.execute(text(query), params)).mappings().all()
    submissions = [await subs.build_submission(session, fsession, edict, dict(r),
                                               user['id']) for r in rows]
    return {'submissions': submissions}


async def _interactors(session: AsyncSession, edict_id: int) -> list[dict]:
    rows = (await session.execute(text(
        'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
        'SELECT c.user_id FROM comment c JOIN submission s ON s.id = c.submission_id '
        'WHERE s.edict_id = :e '
        'UNION SELECT f.user_id FROM favorites f JOIN submission s '
        'ON s.id = f.submission_id WHERE s.edict_id = :e '
        'UNION SELECT l.user_id FROM labels l JOIN submission s '
        'ON s.id = l.submission_id WHERE s.edict_id = :e '
        'UNION SELECT p.user_id FROM private_note p JOIN submission s '
        'ON s.id = p.submission_id WHERE s.edict_id = :e '
        ') ORDER BY u.id'), {'e': edict_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post('/{edict_id}/interactors_list')
async def interactors_list(edict_id: int, mode: str = 'plain_text',
                           options: SectionsDocument | None = None,
                           user: dict = Depends(require_admin),
                           session: AsyncSession = Depends(get_session),
                           fsession: AsyncSession = Depends(get_forms_session)):
    edict = await _get_edict(session, edict_id)
    options = options or SectionsDocument()
    await subs.sync_edict(session, fsession, edict)
    users = await _interactors(session, edict_id)
    if mode != 'pdf':
        return users
    subs_rows = (await session.execute(text(
        'SELECT * FROM submission WHERE edict_id = :e ORDER BY id'),
        {'e': edict_id})).mappings().all()
    candidates = []
    status_lists: dict[str, list] = {}
    for r in subs_rows:
        sub = dict(r)
        _, _, data = await subs.base_data(session, fsession, edict, sub)
        candidates.append({'name': data.get('name'), 'email': data.get('email')})
        status_lists.setdefault(sub['stats'], []).append(data.get('name') or '')
    try:
        cand_form = int(edict['candidate_forms'])
    except (TypeError, ValueError):
        cand_form = None
    finalized = drafts = 0
    if cand_form:
        counts = (await fsession.execute(text(
            "SELECT count(*) FILTER (WHERE submitted_at IS NOT NULL) AS finalized, "
            "count(*) FILTER (WHERE submitted_at IS NULL) AS drafts "
            'FROM form_response WHERE form_id = :f'), {'f': cand_form})).first()
        finalized, drafts = counts[0], counts[1]
    advisors = (await session.execute(text(
        'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
        'SELECT user_id FROM user_edict_slots WHERE edict_id = :e '
        "UNION SELECT l.user_id FROM labels l JOIN submission s "
        "ON s.id = l.submission_id WHERE s.edict_id = :e "
        "AND l.context_type = 'bidding') ORDER BY u.email"),
        {'e': edict_id})).mappings().all()
    content = reports.build_interactors_pdf(
        edict['title'], options.model_dump(),
        {'finalized': finalized, 'drafts': drafts},
        candidates, [dict(a) for a in advisors], status_lists)
    job_id = reports.store(content, 'pdf', 'application/pdf')
    return {'status': 'processing', 'job_id': job_id}


@router.post('/{edict_id}/pairing-biddings')
async def pairing_biddings(edict_id: int,
                           user: dict = Depends(require_admin),
                           session: AsyncSession = Depends(get_session),
                           fsession: AsyncSession = Depends(get_forms_session)):
    edict = await _get_edict(session, edict_id)
    await subs.sync_edict(session, fsession, edict)
    advisors = (await session.execute(text(
        'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
        'SELECT user_id FROM user_edict_slots WHERE edict_id = :e '
        "UNION SELECT l.user_id FROM labels l JOIN submission s "
        "ON s.id = l.submission_id WHERE s.edict_id = :e "
        "AND l.context_type = 'bidding') ORDER BY u.email"),
        {'e': edict_id})).mappings().all()
    advisor_emails = [a['email'] for a in advisors]
    email_by_id = {a['id']: a['email'] for a in advisors}
    slots_rows = (await session.execute(text(
        'SELECT u.email, s.slots FROM user_edict_slots s '
        'JOIN "user" u ON u.id = s.user_id WHERE s.edict_id = :e'),
        {'e': edict_id})).all()
    slots_map = {r[0]: str(r[1]) for r in slots_rows if r[1] is not None}
    subs_rows = (await session.execute(text(
        'SELECT * FROM submission WHERE edict_id = :e ORDER BY id'),
        {'e': edict_id})).mappings().all()
    rows = []
    for r in subs_rows:
        sub = dict(r)
        resp, _, data = await subs.base_data(session, fsession, edict, sub)
        email = data.get('email') or (resp['email'] if resp else None)
        if not email:
            continue
        bids = (await session.execute(text(
            "SELECT user_id, label FROM labels WHERE submission_id = :s "
            "AND context_type = 'bidding'"), {'s': sub['id']})).all()
        values = {email_by_id[uid]: label for uid, label in bids if uid in email_by_id}
        rows.append((email, values))
    content = reports.build_biddings_csv(advisor_emails, slots_map, rows)
    job_id = reports.store(content, 'csv', 'text/csv; charset=utf-8')
    return {'status': 'processing', 'job_id': job_id}


def _mapping_out(row: dict) -> dict:
    d = dict(row)
    if d.get('created_at'):
        d['created_at'] = d['created_at'].isoformat()
    return d


async def _mapping_form_id(edict: dict, form_type: str) -> int:
    key = 'candidate_forms' if form_type == 'candidate' else 'recommenders_forms'
    try:
        return int(edict[key])
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail='Form not configured for edict')


async def _create_mapping(edict_id: int, version: int, form_type: str, payload: dict,
                          user: dict, session: AsyncSession,
                          fsession: AsyncSession) -> dict:
    edict = await _get_edict(session, edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    await forms_svc.validate_mapping(fsession, form_id, version, payload)
    row = (await session.execute(text(
        'INSERT INTO edict_form_mappings (edict_id, form_type, mapping, is_active, '
        'created_at, form_id, user_id, form_version) VALUES (:e, CAST(:t AS '
        'form_type_enum), CAST(:m AS jsonb), true, now(), :f, :u, :v) RETURNING *'),
        {'e': edict_id, 't': form_type, 'm': json.dumps(payload),
         'f': str(form_id), 'u': user['id'], 'v': version})).mappings().first()
    await session.commit()
    out = _mapping_out(row)
    out['version'] = out['form_version']
    return out


@router.post('/{edict_id}/candidates/mappings/versions/{version}/')
async def create_candidate_form_mapping(edict_id: int, version: int,
                                        payload: dict,
                                        user: dict = Depends(require_admin),
                                        session: AsyncSession = Depends(get_session),
                                        fsession: AsyncSession = Depends(get_forms_session)):
    return await _create_mapping(edict_id, version, 'candidate', payload, user,
                                 session, fsession)


@router.post('/{edict_id}/recommenders/mappings/versions/{version}/')
async def create_recommender_form_mapping(edict_id: int, version: int,
                                          payload: dict,
                                          user: dict = Depends(require_admin),
                                          session: AsyncSession = Depends(get_session),
                                          fsession: AsyncSession = Depends(get_forms_session)):
    return await _create_mapping(edict_id, version, 'recommender', payload, user,
                                 session, fsession)


async def _list_mappings(session: AsyncSession, edict_id: int, form_type: str):
    await _get_edict(session, edict_id)
    rows = (await session.execute(text(
        'SELECT * FROM edict_form_mappings WHERE edict_id = :e '
        'AND form_type = :t ORDER BY id'),
        {'e': edict_id, 't': form_type})).mappings().all()
    return [_mapping_out(r) for r in rows]


@router.get('/{edict_id}/candidates/mappings')
async def get_submission_form_mapping(edict_id: int,
                                      user: dict = Depends(get_current_user),
                                      session: AsyncSession = Depends(get_session)):
    return await _list_mappings(session, edict_id, 'candidate')


@router.get('/{edict_id}/recommenders/mappings')
async def get_recommender_form_mapping(edict_id: int,
                                       user: dict = Depends(get_current_user),
                                       session: AsyncSession = Depends(get_session)):
    return await _list_mappings(session, edict_id, 'recommender')


async def _update_mapping(edict_id: int, version: int, mapping_id: int,
                          form_type: str, payload: dict, user: dict,
                          session: AsyncSession, fsession: AsyncSession) -> dict:
    edict = await _get_edict(session, edict_id)
    row = (await session.execute(text(
        'SELECT * FROM edict_form_mappings WHERE id = :i AND edict_id = :e '
        'AND form_type = :t AND form_version = :v'),
        {'i': mapping_id, 'e': edict_id, 't': form_type, 'v': version})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail='Mapping not found')
    form_id = await _mapping_form_id(edict, form_type)
    await forms_svc.validate_mapping(fsession, form_id, version, payload)
    updated = (await session.execute(text(
        'UPDATE edict_form_mappings SET mapping = CAST(:m AS jsonb) '
        'WHERE id = :i RETURNING *'),
        {'m': json.dumps(payload), 'i': mapping_id})).mappings().first()
    await session.commit()
    return _mapping_out(updated)


@router.put('/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}')
async def update_candidate_mapping(edict_id: int, version: int, mapping_id: int,
                                   payload: dict,
                                   user: dict = Depends(require_admin),
                                   session: AsyncSession = Depends(get_session),
                                   fsession: AsyncSession = Depends(get_forms_session)):
    return await _update_mapping(edict_id, version, mapping_id, 'candidate',
                                 payload, user, session, fsession)


@router.put('/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}')
async def update_recommender_mapping(edict_id: int, version: int, mapping_id: int,
                                     payload: dict,
                                     user: dict = Depends(require_admin),
                                     session: AsyncSession = Depends(get_session),
                                     fsession: AsyncSession = Depends(get_forms_session)):
    return await _update_mapping(edict_id, version, mapping_id, 'recommender',
                                 payload, user, session, fsession)


async def _delete_mapping(edict_id: int, version: int, mapping_id: int,
                          form_type: str, session: AsyncSession) -> dict:
    await _get_edict(session, edict_id)
    result = await session.execute(text(
        'DELETE FROM edict_form_mappings WHERE id = :i AND edict_id = :e '
        'AND form_type = :t AND form_version = :v'),
        {'i': mapping_id, 'e': edict_id, 't': form_type, 'v': version})
    if not result.rowcount:
        raise HTTPException(status_code=404, detail='Mapping not found')
    await session.commit()
    return {'message': 'Mapping deleted successfully'}


@router.delete('/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}')
async def delete_candidate_mapping(edict_id: int, version: int, mapping_id: int,
                                   user: dict = Depends(require_admin),
                                   session: AsyncSession = Depends(get_session)):
    return await _delete_mapping(edict_id, version, mapping_id, 'candidate', session)


@router.delete('/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}')
async def delete_recommender_mapping(edict_id: int, version: int, mapping_id: int,
                                     user: dict = Depends(require_admin),
                                     session: AsyncSession = Depends(get_session)):
    return await _delete_mapping(edict_id, version, mapping_id, 'recommender', session)


async def _unmapped_versions(session: AsyncSession, fsession: AsyncSession,
                             edict_id: int, form_type: str) -> list[int]:
    edict = await _get_edict(session, edict_id)
    form_id = await _mapping_form_id(edict, form_type)
    versions = {r[0] for r in (await fsession.execute(text(
        'SELECT DISTINCT version FROM form_section WHERE form_id = :f'),
        {'f': form_id})).all()}
    mapped = {r[0] for r in (await session.execute(text(
        'SELECT DISTINCT form_version FROM edict_form_mappings '
        'WHERE edict_id = :e AND form_type = :t'),
        {'e': edict_id, 't': form_type})).all()}
    return sorted(versions - mapped)


@router.get('/{edict_id}/candidates/forms/versions/unmapped')
async def get_candidates_unmapped_versions(edict_id: int,
                                           user: dict = Depends(get_current_user),
                                           session: AsyncSession = Depends(get_session),
                                           fsession: AsyncSession = Depends(get_forms_session)):
    return await _unmapped_versions(session, fsession, edict_id, 'candidate')


@router.get('/{edict_id}/recommenders/forms/versions/unmapped')
async def get_recommenders_unmapped_versions(edict_id: int,
                                             user: dict = Depends(get_current_user),
                                             session: AsyncSession = Depends(get_session),
                                             fsession: AsyncSession = Depends(get_forms_session)):
    return await _unmapped_versions(session, fsession, edict_id, 'recommender')
