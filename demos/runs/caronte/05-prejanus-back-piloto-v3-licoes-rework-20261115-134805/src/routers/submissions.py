import uuid
from datetime import datetime, timezone
from pathlib import Path

from babel.dates import format_date
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

from ..auth import STAFF_ROLES, current_user, require_staff
from ..config import settings
from ..db import engine, engine_forms
from ..schemas import (BiddingSchema, CommentSchema, EntrySemesterSchema,
                       LabelInputSchema, PrivateNoteSchema, RequestReesendSchema,
                       StatsSchema)
from ..services import mail
from ..services import submissions as subsvc
from ..services.forms_db import get_response
from ..services.mapping import walk_tree

router = APIRouter(prefix='/submissions', tags=['submissions'])


def get_submission(conn, submission_id: int) -> dict:
    return subsvc.get_submission(conn, submission_id)


def get_edict_of(conn, submission: dict) -> dict:
    return subsvc.get_edict(conn, submission['edict_id'])


def require_phase(conn, submission: dict, phase: str) -> None:
    e = get_edict_of(conn, submission)
    if e['phase'] != phase:
        raise HTTPException(status_code=400,
                            detail=f'Operação disponível apenas na fase {phase}')


def _normalize_semester(value: str) -> str:
    low = (value or '').lower()
    if 'first' in low or 'primeir' in low:
        return 'Primeiro semestre.'
    if 'second' in low or 'segund' in low:
        return 'Segundo semestre.'
    return value


@router.get('/{submission_id}')
def get_details(submission_id: int, include_comments: bool = False,
                user=Depends(current_user)):
    with engine.connect() as conn, engine_forms.connect() as fconn:
        s = get_submission(conn, submission_id)
        summary = subsvc.submission_summary(conn, fconn, s, user['id'])
        fr = get_response(fconn, s['candidate_form_id'])
        form = subsvc.submission_form(fconn, fr) if fr else []
        result = {'summary': summary, 'submission_form': form}
        if include_comments:
            result['comments'] = [dict(r) for r in conn.execute(
                text('SELECT c.id, c.submission_id, c.comment, c.created_at, c.updated_at, '
                     'u.id AS user_id, u.name AS user_name FROM comment c '
                     'JOIN "user" u ON u.id = c.user_id WHERE c.submission_id = :s '
                     'ORDER BY c.id'), {'s': submission_id}).mappings().all()]
    return result


@router.post('/{submission_id}/comments')
def add_comment(submission_id: int, payload: CommentSchema, user=Depends(current_user)):
    with engine.begin() as conn:
        s = get_submission(conn, submission_id)
        require_phase(conn, s, 'avaliacao')
        now = datetime.now(timezone.utc)
        created = payload.created_at or now
        updated = payload.updated_at or created
        row = conn.execute(
            text('INSERT INTO comment (user_id, submission_id, comment, created_at, '
                 'updated_at) VALUES (:u, :s, :c, :cr, :up) RETURNING id, created_at, updated_at'),
            {'u': user['id'], 's': submission_id, 'c': payload.comment,
             'cr': created, 'up': updated}).mappings().first()
    return {'id': row['id'], 'user': {'id': user['id'], 'name': user['name']},
            'submission_id': submission_id, 'comment': payload.comment,
            'created_at': row['created_at'], 'updated_at': row['updated_at']}


@router.get('/{submission_id}/comments')
def get_all_comments(submission_id: int, user=Depends(current_user)):
    with engine.connect() as conn:
        get_submission(conn, submission_id)
        rows = [dict(r) for r in conn.execute(
            text('SELECT c.id, c.submission_id, c.comment, c.created_at, c.updated_at, '
                 'u.id AS user_id, u.name AS user_name FROM comment c '
                 'JOIN "user" u ON u.id = c.user_id WHERE c.submission_id = :s '
                 'ORDER BY c.id'), {'s': submission_id}).mappings().all()]
    return [{'id': r['id'], 'user': {'id': r['user_id'], 'name': r['user_name']},
             'submission_id': r['submission_id'], 'comment': r['comment'],
             'created_at': r['created_at'], 'updated_at': r['updated_at']} for r in rows]


@router.delete('/comments/{comment_id}', status_code=204)
def remove_comment(comment_id: int, user=Depends(current_user)):
    with engine.begin() as conn:
        row = conn.execute(text('SELECT user_id FROM comment WHERE id = :i'),
                           {'i': comment_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='Comentário não encontrado')
        if row['user_id'] != user['id']:
            raise HTTPException(status_code=403, detail='Sem permissão')
        conn.execute(text('DELETE FROM comment WHERE id = :i'), {'i': comment_id})
    return Response(status_code=204)


@router.post('/{submission_id}/labels')
def add_label(submission_id: int, payload: LabelInputSchema, user=Depends(current_user)):
    with engine.begin() as conn:
        s = get_submission(conn, submission_id)
        require_phase(conn, s, 'avaliacao')
        conn.execute(
            text("UPDATE labels SET color = :c WHERE user_id = :u AND label = :l "
                 "AND context_type = 'candidate'"),
            {'c': payload.color, 'u': user['id'], 'l': payload.label})
        existing = conn.execute(
            text("SELECT id FROM labels WHERE user_id = :u AND submission_id = :s "
                 "AND label = :l AND context_type = 'candidate'"),
            {'u': user['id'], 's': submission_id, 'l': payload.label}).scalar()
        if existing:
            label_id = existing
            conn.execute(text('UPDATE labels SET color = :c WHERE id = :i'),
                         {'c': payload.color, 'i': label_id})
        else:
            label_id = conn.execute(
                text('INSERT INTO labels (user_id, submission_id, label, color, '
                     "context_type) VALUES (:u, :s, :l, :c, 'candidate') RETURNING id"),
                {'u': user['id'], 's': submission_id, 'l': payload.label,
                 'c': payload.color}).scalar()
    return {'id': label_id, 'user': {'id': user['id'], 'name': user['name']},
            'submission_id': submission_id, 'label': payload.label}


@router.get('/{submission_id}/labels')
def get_labels(submission_id: int, user=Depends(current_user)):
    with engine.connect() as conn:
        get_submission(conn, submission_id)
        rows = [dict(r) for r in conn.execute(
            text("SELECT DISTINCT ON (label) id, label, color FROM labels "
                 "WHERE user_id = :u AND context_type = 'candidate' "
                 'ORDER BY label, id DESC'), {'u': user['id']}).mappings().all()]
    return {'labels': [{'id': r['id'], 'label': r['label'], 'color': r['color']}
                       for r in rows]}


@router.delete('/label/{label_id}', status_code=204)
def remove_label(label_id: int, user=Depends(current_user)):
    with engine.begin() as conn:
        row = conn.execute(text('SELECT user_id FROM labels WHERE id = :i'),
                           {'i': label_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='Etiqueta não encontrada')
        if row['user_id'] != user['id']:
            raise HTTPException(status_code=403, detail='Sem permissão')
        conn.execute(text('DELETE FROM labels WHERE id = :i'), {'i': label_id})
    return Response(status_code=204)


@router.post('/{submission_id}/private_notes')
def add_or_update_note(submission_id: int, payload: PrivateNoteSchema,
                       user=Depends(current_user)):
    with engine.begin() as conn:
        s = get_submission(conn, submission_id)
        require_phase(conn, s, 'avaliacao')
        existing = conn.execute(
            text('SELECT id FROM private_note WHERE user_id = :u AND submission_id = :s'),
            {'u': user['id'], 's': submission_id}).scalar()
        if existing:
            conn.execute(text('UPDATE private_note SET note = :n, updated_at = now() '
                              'WHERE id = :i'), {'n': payload.note, 'i': existing})
        else:
            conn.execute(
                text('INSERT INTO private_note (user_id, submission_id, note, created_at) '
                     'VALUES (:u, :s, :n, now())'),
                {'u': user['id'], 's': submission_id, 'n': payload.note})
    return {'note': payload.note}


@router.post('/{submission_id}/favorites')
def create_favorite(submission_id: int, response: Response, user=Depends(current_user)):
    with engine.begin() as conn:
        s = get_submission(conn, submission_id)
        require_phase(conn, s, 'avaliacao')
        exists = conn.execute(
            text('SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s'),
            {'u': user['id'], 's': submission_id}).first()
        if not exists:
            conn.execute(
                text('INSERT INTO favorites (user_id, submission_id, created_at) '
                     'VALUES (:u, :s, now())'),
                {'u': user['id'], 's': submission_id})
            response.status_code = 201
    return 'Favorito registrado'


@router.delete('/{submission_id}/favorites')
def remove_favorite(submission_id: int, user=Depends(current_user)):
    with engine.begin() as conn:
        get_submission(conn, submission_id)
        conn.execute(text('DELETE FROM favorites WHERE user_id = :u AND submission_id = :s'),
                     {'u': user['id'], 's': submission_id})
    return 'Favorito removido'


@router.post('/{submission_id}/view')
def register_view(submission_id: int, user=Depends(current_user)):
    with engine.begin() as conn:
        get_submission(conn, submission_id)
        existing = conn.execute(
            text('SELECT id FROM submission_view WHERE user_id = :u '
                 'AND submission_id = :s AND created_at::date = current_date'),
            {'u': user['id'], 's': submission_id}).scalar()
        if existing:
            conn.execute(text('UPDATE submission_view SET updated_at = now() WHERE id = :i'),
                         {'i': existing})
        else:
            conn.execute(
                text('INSERT INTO submission_view (user_id, submission_id, created_at, '
                     'updated_at) VALUES (:u, :s, now(), now())'),
                {'u': user['id'], 's': submission_id})
    return {'message': 'Visualização registrada'}


@router.get('/{submission_id}/view')
def get_submission_views(submission_id: int, user=Depends(current_user)):
    with engine.connect() as conn:
        get_submission(conn, submission_id)
        rows = [dict(r) for r in conn.execute(
            text('SELECT v.id, v.created_at, v.updated_at, u.id AS user_id, u.name AS user_name '
                 'FROM submission_view v JOIN "user" u ON u.id = v.user_id '
                 'WHERE v.submission_id = :s ORDER BY v.id'), {'s': submission_id}).mappings().all()]
    return [{'id': r['id'], 'user': {'id': r['user_id'], 'name': r['user_name']},
             'created_at': r['created_at'], 'updated_at': r['updated_at']} for r in rows]


@router.post('/{submission_id}/select')
def select_stats(submission_id: int, payload: StatsSchema, user=Depends(current_user)):
    require_staff(user)
    with engine.begin() as conn:
        s = get_submission(conn, submission_id)
        e = get_edict_of(conn, s)
        if not e['is_open']:
            raise HTTPException(status_code=409, detail='Edital encerrado')
        params = {'st': payload.stats, 'i': submission_id}
        q = 'UPDATE submission SET stats = :st'
        if payload.user_ids:
            q += ', advisor_id = :a'
            params['a'] = payload.user_ids[0]
        conn.execute(text(q + ' WHERE id = :i'), params)
    return 'Situação atualizada'


@router.post('/{submission_id}/entry-semester')
def toggle_entry_semester(submission_id: int, payload: EntrySemesterSchema,
                          user=Depends(current_user)):
    semester = _normalize_semester(payload.semester)
    with engine.begin() as conn:
        get_submission(conn, submission_id)
        conn.execute(text('UPDATE submission SET entry_semester = :s, updated_at = now() '
                          'WHERE id = :i'), {'s': semester, 'i': submission_id})
    return 'Semestre de ingresso atualizado'


@router.post('/{submission_id}/bidding')
def toggle_bidding(submission_id: int, payload: BiddingSchema, user=Depends(current_user)):
    target = user['id']
    if payload.user_id and user['role'] in STAFF_ROLES:
        target = payload.user_id
    with engine.begin() as conn:
        get_submission(conn, submission_id)
        conn.execute(
            text("DELETE FROM labels WHERE user_id = :u AND submission_id = :s "
                 "AND context_type = 'bidding'"),
            {'u': target, 's': submission_id})
        if payload.bidding:
            conn.execute(
                text('INSERT INTO labels (user_id, submission_id, label, color, context_type) '
                     "VALUES (:u, :s, :l, '#000000', 'bidding')"),
                {'u': target, 's': submission_id, 'l': payload.bidding})
    return 'Interesse atualizado'


@router.get('/{submission_id}/files/{label}/{filename}')
def get_file(submission_id: int, label: str, filename: str, user=Depends(current_user)):
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail='Nome de arquivo inválido')
    with engine.connect() as conn, engine_forms.connect() as fconn:
        s = get_submission(conn, submission_id)
        row = fconn.execute(
            text('SELECT 1 FROM responses r JOIN form_field f ON f.id = r.field_id '
                 'WHERE r.response_id = :rid AND f.name = :label AND r.value = :fn'),
            {'rid': s['candidate_form_id'], 'label': label, 'fn': filename}).first()
        if not row:
            raise HTTPException(status_code=404, detail='Arquivo não encontrado')
    path = Path('/shared/uploads') / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail='Arquivo não encontrado')
    data = path.read_bytes()
    return Response(data, media_type='application/pdf',
                    headers={'content-disposition': f'attachment; filename="{filename}"'})


@router.post('/{submission_id}/reesend_submission')
def reesend_submission(submission_id: int, payload: RequestReesendSchema,
                       user=Depends(current_user)):
    require_staff(user)
    with engine.connect() as conn, engine_forms.connect() as fconn:
        s = get_submission(conn, submission_id)
        require_phase(conn, s, 'homologacao')
        fr = get_response(fconn, s['candidate_form_id'])
        if not fr:
            raise HTTPException(status_code=404, detail='Formulário não encontrado')
        with engine_forms.begin() as ftconn:
            ftconn.execute(text('SELECT * FROM update_form_response_section(:r, 0)'),
                           {'r': fr['id']})
        email = fr['email']
        link = f"{settings.base_url}/form/{fr['token']}"
        mail.send_email(
            email, 'Correção de inscrição',
            f"{payload.text}\n\nAcesse o formulário para corrigir sua inscrição:\n{link}\n",
            bcc=[user['email']])
    return {'message': 'Solicitação de correção enviada', 'email_sent': email}


@router.post('/{submission_id}/send-accept')
def send_accept_forms(submission_id: int, user=Depends(current_user)):
    with engine.connect() as conn, engine_forms.connect() as fconn:
        s = get_submission(conn, submission_id)
        if s['stats'] != 'approved':
            raise HTTPException(status_code=400, detail='Inscrição não aprovada')
        if s['accept_form_id']:
            raise HTTPException(status_code=400, detail='Formulário de aceite já enviado')
        e = get_edict_of(conn, s)
        if not e['accept_forms']:
            raise HTTPException(status_code=404, detail='Formulário de aceite não configurado')
        form_id = int(e['accept_forms'])
        fr = get_response(fconn, s['candidate_form_id'])
        if not fr:
            raise HTTPException(status_code=404, detail='Formulário não encontrado')
        email = fr['email']
        mappings = {r[0]: r[1] for r in conn.execute(
            text('SELECT form_version, mapping FROM edict_form_mappings '
                 'WHERE edict_id = :e AND form_type = \'candidate\''),
            {'e': e['id']}).all()}
        mapping = subsvc._mapping_for(mappings, fr['form_version'])
        from ..services.forms_db import response_values
        name = walk_tree(mapping or {}, response_values(fconn, fr['id'])).get('name')
        with engine_forms.begin() as ftconn:
            shared_id = ftconn.execute(
                text('INSERT INTO form_shared (form_id, unique_answers, is_public, token, '
                     'created_at, expiration_at) '
                     'VALUES (:f, true, false, :t, now(), :exp) RETURNING id'),
                {'f': form_id, 't': str(uuid.uuid4()), 'exp': e['closed_date']}).scalar()
            version = ftconn.execute(
                text('SELECT max(version) FROM form_section WHERE form_id = :f'),
                {'f': form_id}).scalar() or 1
            resp = ftconn.execute(
                text('INSERT INTO form_response (form_id, shared_id, email, token, '
                     "current_section, submitted_at, metadata, form_version) "
                     "VALUES (:f, :sh, :e, :t, 0, NULL, '{}'::jsonb, :v) "
                     'RETURNING id, token'),
                {'f': form_id, 'sh': shared_id, 'e': email, 't': str(uuid.uuid4()),
                 'v': version}).mappings().first()
        with engine.begin() as conn2:
            conn2.execute(text('UPDATE submission SET accept_form_id = :a WHERE id = :i'),
                          {'a': resp['id'], 'i': submission_id})
        advisor = subsvc.user_by_id(conn, s['advisor_id'])
        deadline = e['closed_date']
        link = f"{settings.base_url}/form/{resp['token']}"
        body = (f"Olá, {name or email}!\n\n"
                f"Sua inscrição foi aprovada. Preencha o formulário de aceite até "
                f"{format_date(deadline, format='long', locale='pt')} "
                f"({format_date(deadline, format='long', locale='en')}):\n{link}\n")
        mail.send_email(email, 'Formulário de aceite',
                        body, cc=[advisor['email']] if advisor and advisor.get('email') else None)
    return {'message': 'Formulário de aceite enviado', 'email_sent': email}


@router.post('/{submission_id}/send-letter')
def send_accept_letter(submission_id: int, user=Depends(current_user)):
    with engine.connect() as conn, engine_forms.connect() as fconn:
        s = get_submission(conn, submission_id)
        if s['stats'] != 'approved':
            raise HTTPException(status_code=400, detail='Inscrição não aprovada')
        if s['letter_sent']:
            raise HTTPException(status_code=400, detail='Carta já enviada')
        fr = get_response(fconn, s['candidate_form_id'])
        email = fr['email'] if fr else None
        if not email:
            raise HTTPException(status_code=404, detail='Formulário não encontrado')
        mail.send_email(email, 'Carta de aprovação',
                        'Sua inscrição foi aprovada. Parabéns!\n')
        with engine.begin() as conn2:
            conn2.execute(text('UPDATE submission SET letter_sent = true WHERE id = :i'),
                          {'i': submission_id})
    return {'message': 'Carta de aprovação enviada', 'email_sent': email}
