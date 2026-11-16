import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

from ..auth import current_user, require_staff
from ..db import engine, engine_forms
from ..schemas import (AdvancePhaseEdictSchema, CloseEdictSchema, EditEdictDateSchema,
                       EditEdictSchema, InsertEdictSchema, SectionsDocument, SlotsSchema)
from ..services import reports
from ..services import submissions as subsvc
from ..services.forms_db import mapping_targets
from ..services.mapping import CANDIDATE_SPEC, RECOMMENDER_SPEC, validate_tree

router = APIRouter(prefix='/edicts', tags=['edicts'])

PHASE_DATES = (('inscricoes', 'date_application'), ('avaliacao', 'date_verification'),
               ('homologacao', 'date_evaluation'), ('encerrado', 'date_closed'))
FORMS_PHASE = {'inscricoes': 'Registration', 'homologacao': 'Approval'}


def get_edict(conn, edict_id: int) -> dict:
    row = conn.execute(text('SELECT * FROM edict WHERE id = :i'),
                       {'i': edict_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail='Edital não encontrado')
    return dict(row)


def _validate_dates(dates: tuple) -> None:
    if not (dates[0] < dates[1] < dates[2] < dates[3]):
        raise HTTPException(status_code=400, detail='Datas fora de ordem')


@router.get('')
def list_edicts(type: str | None = None, is_open: bool | None = None,
                user=Depends(current_user)):
    q = 'SELECT id, title, year, semester, type AS edict_type, is_open FROM edict WHERE 1=1'
    params = {}
    if type is not None:
        q += ' AND type = :type'
        params['type'] = type
    if is_open is not None:
        q += ' AND is_open = :is_open'
        params['is_open'] = is_open
    q += ' ORDER BY closed_date DESC, id DESC'
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text(q), params).mappings().all()]


@router.post('')
def create_edict(payload: InsertEdictSchema, user=Depends(current_user)):
    require_staff(user)
    dates = (payload.date_application.date(), payload.date_verification.date(),
             payload.date_evaluation.date(), payload.date_closed.date())
    _validate_dates(dates)
    with engine.begin() as conn:
        eid = conn.execute(
            text('INSERT INTO edict (title, description, candidate_forms, recommenders_forms, '
                 'closed_date, year, semester, type, phase, is_open, created_at, updated_at, '
                 "user_id) VALUES (:t, :d, :cf, :rf, :cd, :y, :s, :ty, 'inscricoes', :io, "
                 'now(), now(), :u) RETURNING id'),
            {'t': payload.title, 'd': payload.description, 'cf': payload.candidate_forms,
             'rf': payload.recommenders_forms, 'cd': dates[3], 'y': payload.year,
             's': payload.semester, 'ty': payload.edict_type, 'io': payload.is_open,
             'u': user['id']}).scalar()
        for (phase, attr), value in zip(PHASE_DATES, dates):
            conn.execute(text('INSERT INTO edict_phase (edict_id, phase, closed_date) '
                              'VALUES (:e, :p, :d)'),
                         {'e': eid, 'p': phase, 'd': value})
    return {'id': eid, 'title': payload.title, 'description': payload.description,
            'year': payload.year, 'semester': payload.semester,
            'edict_type': payload.edict_type, 'is_open': payload.is_open,
            'candidate_forms': int(payload.candidate_forms),
            'recommenders_forms': int(payload.recommenders_forms),
            'date_application': payload.date_application,
            'date_verification': payload.date_verification,
            'date_evaluation': payload.date_evaluation,
            'date_closed': payload.date_closed,
            'closed_date': payload.date_closed}


@router.get('/{edict_id}')
def get_edict_by_id(edict_id: int, user=Depends(current_user)):
    with engine.connect() as conn:
        e = get_edict(conn, edict_id)
        phases = [dict(r) for r in conn.execute(
            text('SELECT id, phase, closed_date FROM edict_phase WHERE edict_id = :e '
                 'ORDER BY id'), {'e': edict_id}).mappings().all()]
        slots = conn.execute(
            text('SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e'),
            {'u': user['id'], 'e': edict_id}).scalar()
    return {'id': e['id'], 'title': e['title'],
            'candidate_form_id': e['candidate_forms'],
            'recommender_form_id': e['recommenders_forms'],
            'description': e['description'],
            'closed_date': str(e['closed_date']) if e['closed_date'] else None,
            'created_at': e['created_at'], 'year': e['year'], 'semester': e['semester'],
            'type': e['type'], 'is_open': e['is_open'], 'updated_at': e['updated_at'],
            'phase': e['phase'],
            'phases': [{'id': p['id'], 'phase': p['phase'],
                        'closed_date': str(p['closed_date']) if p['closed_date'] else None}
                       for p in phases],
            'slots': str(slots or 0)}


@router.post('/{edict_id}/edit')
def edit_edict(edict_id: int, payload: EditEdictSchema, user=Depends(current_user)):
    require_staff(user)
    dates = (payload.date_application.date(), payload.date_verification.date(),
             payload.date_evaluation.date(), payload.date_closed.date())
    _validate_dates(dates)
    with engine.begin() as conn:
        get_edict(conn, edict_id)
        conn.execute(
            text('UPDATE edict SET title = :t, description = :d, year = :y, semester = :s, '
                 'type = :ty, closed_date = :cd, updated_at = now() WHERE id = :i'),
            {'t': payload.title, 'd': payload.description, 'y': int(payload.year),
             's': int(payload.semester), 'ty': payload.edict_type, 'cd': dates[3],
             'i': edict_id})
        for (phase, _), value in zip(PHASE_DATES, dates):
            conn.execute(text('UPDATE edict_phase SET closed_date = :d '
                              'WHERE edict_id = :e AND phase = :p'),
                         {'d': value, 'e': edict_id, 'p': phase})
    return {'title': payload.title, 'description': payload.description,
            'year': payload.year, 'semester': payload.semester,
            'edict_type': payload.edict_type,
            'date_application': payload.date_application,
            'date_verification': payload.date_verification,
            'date_evaluation': payload.date_evaluation,
            'date_closed': payload.date_closed}


@router.post('/{edict_id}/edit-date')
def edit_date_edict(edict_id: int, payload: EditEdictDateSchema,
                    user=Depends(current_user)):
    require_staff(user)
    with engine.begin() as conn:
        get_edict(conn, edict_id)
        conn.execute(text('UPDATE edict SET closed_date = :d, updated_at = now() '
                          'WHERE id = :i'), {'d': payload.closed_date, 'i': edict_id})
        conn.execute(text("UPDATE edict_phase SET closed_date = :d "
                          "WHERE edict_id = :e AND phase = 'encerrado'"),
                     {'d': payload.closed_date, 'e': edict_id})
    return {'closed_date': str(payload.closed_date)}


@router.post('/{edict_id}/advance-phase')
def advance_edict(edict_id: int, payload: AdvancePhaseEdictSchema,
                  user=Depends(current_user)):
    require_staff(user)
    with engine.begin() as conn:
        e = get_edict(conn, edict_id)
        ph = conn.execute(text('SELECT id, phase FROM edict_phase '
                               'WHERE id = :id AND edict_id = :e'),
                          {'id': payload.id, 'e': edict_id}).mappings().first()
        if not ph:
            raise HTTPException(status_code=404, detail='Fase não encontrada')
        conn.execute(text('UPDATE edict SET phase = :p, updated_at = now() WHERE id = :i'),
                     {'p': ph['phase'], 'i': edict_id})
    with engine_forms.begin() as fconn:
        form_phase = FORMS_PHASE.get(ph['phase'], 'Completed')
        fconn.execute(text('SELECT * FROM change_form_phase(:f, CAST(:p AS form_phase))'),
                      {'f': int(e['candidate_forms']), 'p': form_phase})
    return {'id': ph['id'], 'label': ph['phase']}


@router.delete('/{edict_id}/remove')
def remove_edict(edict_id: int, user=Depends(current_user)):
    require_staff(user)
    with engine.begin() as conn:
        get_edict(conn, edict_id)
        conn.execute(text('DELETE FROM edict WHERE id = :i'), {'i': edict_id})
    return {'message': 'Edital removido com sucesso'}


@router.post('/{edict_id}/slots')
def set_user_slots(edict_id: int, payload: SlotsSchema, user=Depends(current_user)):
    try:
        amount = int(payload.amount)
    except (TypeError, ValueError):
        amount = 0
    if amount < 0:
        amount = 0
    with engine.begin() as conn:
        get_edict(conn, edict_id)
        existing = conn.execute(
            text('SELECT id FROM user_edict_slots WHERE user_id = :u AND edict_id = :e'),
            {'u': user['id'], 'e': edict_id}).scalar()
        if existing:
            conn.execute(text('UPDATE user_edict_slots SET slots = :s WHERE id = :i'),
                         {'s': amount, 'i': existing})
        else:
            conn.execute(text('INSERT INTO user_edict_slots (user_id, edict_id, slots) '
                              'VALUES (:u, :e, :s)'),
                         {'u': user['id'], 'e': edict_id, 's': amount})
    return {'amount': str(amount)}


@router.patch('/{edict_id}/close')
def close_edict(edict_id: int, payload: CloseEdictSchema, user=Depends(current_user)):
    require_staff(user)
    with engine.begin() as conn:
        e = get_edict(conn, edict_id)
        if not e['is_open']:
            raise HTTPException(status_code=409, detail='Edital já encerrado')
        conn.execute(text('UPDATE edict SET is_open = false, updated_at = now() '
                          'WHERE id = :i'), {'i': edict_id})
    return {'message': 'Edital encerrado'}


@router.get('/{edict_id}/submissions')
def get_all_submissions_from_edict(edict_id: int, stats: str | None = None,
                                   only_favorites: bool = False,
                                   user=Depends(current_user)):
    with engine.begin() as conn, engine_forms.connect() as fconn:
        e = get_edict(conn, edict_id)
        items = subsvc.list_submissions(conn, fconn, e, user['id'],
                                        stats=stats, only_favorites=only_favorites)
    return {'submissions': items}


@router.post('/{edict_id}/interactors_list')
def interactors_list(edict_id: int, mode: str = 'plain_text',
                     payload: SectionsDocument | None = None,
                     user=Depends(current_user)):
    require_staff(user)
    opts = payload or SectionsDocument()
    if mode == 'pdf':
        job_id = reports.start_pdf_job(edict_id, opts)
        return {'status': 'processing', 'job_id': job_id}
    with engine.connect() as conn:
        get_edict(conn, edict_id)
        return reports.interactors(conn, edict_id)


@router.post('/{edict_id}/pairing-biddings')
def pairing_biddings(edict_id: int, user=Depends(current_user)):
    require_staff(user)
    job_id = reports.start_csv_job(edict_id)
    return {'status': 'processing', 'job_id': job_id}


@router.get('/download_pdf/{job_id}')
def download_pdf(job_id: str):
    return reports.download(job_id, 'application/pdf', 'pdf')


@router.get('/download_csv/{job_id}')
def download_csv(job_id: str):
    return reports.download(job_id, 'text/csv', 'csv')


def _kind(rota: str) -> str:
    if rota == 'candidates':
        return 'candidate'
    if rota == 'recommenders':
        return 'recommender'
    raise HTTPException(status_code=404, detail='Rota não encontrada')


def _form_id_of(e: dict, kind: str) -> int:
    return int(e['candidate_forms'] if kind == 'candidate' else e['recommenders_forms'])


def _mapping_row(r: dict) -> dict:
    return {'id': r['id'], 'edict_id': r['edict_id'], 'form_type': r['form_type'],
            'mapping': r['mapping'], 'is_active': r['is_active'],
            'form_id': r['form_id'], 'user_id': r['user_id'],
            'form_version': r['form_version']}


@router.post('/{edict_id}/{rota}/mappings/versions/{version}/')
def create_form_mapping(edict_id: int, rota: str, version: int, payload: dict,
                        user=Depends(current_user)):
    require_staff(user)
    kind = _kind(rota)
    with engine.begin() as conn, engine_forms.connect() as fconn:
        e = get_edict(conn, edict_id)
        form_id = _form_id_of(e, kind)
        sections, fields = mapping_targets(fconn, form_id, version)
        spec = CANDIDATE_SPEC if kind == 'candidate' else RECOMMENDER_SPEC
        validate_tree(payload, spec, sections, fields)
        mid = conn.execute(
            text('INSERT INTO edict_form_mappings (edict_id, form_type, mapping, is_active, '
                 'form_id, user_id, form_version) '
                 'VALUES (:e, CAST(:t AS form_type_enum), CAST(:m AS jsonb), true, '
                 ':f, :u, :v) RETURNING id'),
            {'e': edict_id, 't': kind, 'm': json.dumps(payload),
             'f': str(form_id), 'u': user['id'], 'v': version}).scalar()
    return {'id': mid, 'edict_id': edict_id, 'form_type': kind, 'user_id': user['id'],
            'is_active': True, 'mapping': payload, 'version': version,
            'form_id': str(form_id)}


@router.get('/{edict_id}/{rota}/mappings')
def get_form_mappings(edict_id: int, rota: str, user=Depends(current_user)):
    kind = _kind(rota)
    with engine.connect() as conn:
        get_edict(conn, edict_id)
        rows = [dict(r) for r in conn.execute(
            text('SELECT * FROM edict_form_mappings WHERE edict_id = :e '
                 'AND form_type = :t ORDER BY id'),
            {'e': edict_id, 't': kind}).mappings().all()]
    return [_mapping_row(r) for r in rows]


@router.put('/{edict_id}/{rota}/mappings/versions/{version}/{mapping_id}')
def update_form_mapping(edict_id: int, rota: str, version: int, mapping_id: int,
                        payload: dict, user=Depends(current_user)):
    require_staff(user)
    kind = _kind(rota)
    with engine.begin() as conn, engine_forms.connect() as fconn:
        e = get_edict(conn, edict_id)
        row = conn.execute(
            text('SELECT id FROM edict_form_mappings WHERE id = :id AND edict_id = :e '
                 'AND form_type = :t AND form_version = :v'),
            {'id': mapping_id, 'e': edict_id, 't': kind, 'v': version}).scalar()
        if not row:
            raise HTTPException(status_code=404, detail='Mapeamento não encontrado')
        form_id = _form_id_of(e, kind)
        sections, fields = mapping_targets(fconn, form_id, version)
        spec = CANDIDATE_SPEC if kind == 'candidate' else RECOMMENDER_SPEC
        validate_tree(payload, spec, sections, fields)
        conn.execute(text('UPDATE edict_form_mappings SET mapping = CAST(:m AS jsonb) '
                          'WHERE id = :id'),
                     {'m': json.dumps(payload), 'id': mapping_id})
    return {'message': 'Mapping updated successfully'}


@router.delete('/{edict_id}/{rota}/mappings/versions/{version}/{mapping_id}')
def delete_form_mapping(edict_id: int, rota: str, version: int, mapping_id: int,
                        user=Depends(current_user)):
    require_staff(user)
    kind = _kind(rota)
    with engine.begin() as conn:
        get_edict(conn, edict_id)
        row = conn.execute(
            text('SELECT id FROM edict_form_mappings WHERE id = :id AND edict_id = :e '
                 'AND form_type = :t AND form_version = :v'),
            {'id': mapping_id, 'e': edict_id, 't': kind, 'v': version}).scalar()
        if not row:
            raise HTTPException(status_code=404, detail='Mapeamento não encontrado')
        conn.execute(text('DELETE FROM edict_form_mappings WHERE id = :id'),
                     {'id': mapping_id})
    return {'message': 'Mapping deleted successfully'}


@router.get('/{edict_id}/{rota}/forms/versions/unmapped')
def get_unmapped_versions(edict_id: int, rota: str, user=Depends(current_user)):
    kind = _kind(rota)
    with engine.connect() as conn, engine_forms.connect() as fconn:
        e = get_edict(conn, edict_id)
        form_id = _form_id_of(e, kind)
        mapped = {r[0] for r in conn.execute(
            text('SELECT form_version FROM edict_form_mappings '
                 'WHERE edict_id = :e AND form_type = :t'),
            {'e': edict_id, 't': kind}).all()}
        versions = {r[0] for r in fconn.execute(
            text('SELECT DISTINCT version FROM form_section WHERE form_id = :f'),
            {'f': form_id}).all()}
    return sorted(versions - mapped)
