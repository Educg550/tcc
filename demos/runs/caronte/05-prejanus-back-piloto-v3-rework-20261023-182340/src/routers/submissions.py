import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import ADMIN_ROLES, get_current_user, require_admin
from src.config import get_settings
from src.db import get_forms_session, get_session
from src.schemas import (BiddingSchema, CommentSchema, EntrySemesterSchema,
                         LabelSchema, PrivateNoteSchema, RequestReesendSchema,
                         StatsSchema)
from src.services import emails
from src.services import forms as forms_svc
from src.services import submissions as subs

router = APIRouter(prefix='/submissions', tags=['submissions'])
UPLOADS = Path('/shared/uploads')


async def _load(psession: AsyncSession, submission_id: int):
    sub = await subs.get_submission(psession, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail='Submission not found')
    edict = await subs.get_edict(psession, sub['edict_id'])
    return sub, edict


def _require_phase(edict: dict, phase: str = 'avaliacao') -> None:
    if edict['phase'] != phase:
        raise HTTPException(status_code=400, detail=f'Edict is not in {phase}')


def _normalize_semester(value: str) -> str:
    low = value.strip().lower()
    if 'primeiro' in low or 'first' in low:
        return 'Primeiro semestre.'
    if 'segundo' in low or 'second' in low:
        return 'Segundo semestre.'
    return value.strip()


async def _candidate_contact(psession, fsession, edict, sub):
    resp, values, data = await subs.base_data(psession, fsession, edict, sub)
    email = data.get('email') or (resp['email'] if resp else None)
    return resp, data, email


@router.get('/{submission_id}')
async def get_details(submission_id: int, include_comments: bool = False,
                      user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session),
                      fsession: AsyncSession = Depends(get_forms_session)):
    sub, edict = await _load(session, submission_id)
    await subs.sync_edict(session, fsession, edict)
    sub = await subs.get_submission(session, submission_id)
    resp = await subs.get_form_response(fsession, sub['candidate_form_id'])
    out = {
        'summary': await subs.build_summary(session, fsession, edict, sub, user['id']),
        'submission_form': await subs.build_submission_form(fsession, resp) if resp else [],
    }
    if include_comments:
        out['comments'] = await _comments(session, submission_id)
    return out


async def _comments(psession: AsyncSession, submission_id: int) -> list[dict]:
    rows = (await psession.execute(text(
        'SELECT c.id, c.submission_id, c.comment, c.created_at, c.updated_at, '
        'u.id AS uid, u.name FROM comment c JOIN "user" u ON u.id = c.user_id '
        'WHERE c.submission_id = :s ORDER BY c.id'),
        {'s': submission_id})).mappings().all()
    return [{'id': r['id'], 'user': {'id': r['uid'], 'name': r['name']},
             'submission_id': r['submission_id'], 'comment': r['comment'],
             'created_at': r['created_at'].isoformat() if r['created_at'] else None,
             'updated_at': r['updated_at'].isoformat() if r['updated_at'] else None}
            for r in rows]


@router.get('/{submission_id}/comments')
async def get_all_comments(submission_id: int,
                           user: dict = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session),
                           fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    return await _comments(session, submission_id)


@router.post('/{submission_id}/comments')
async def add_comment(submission_id: int, body: CommentSchema,
                      user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session),
                      fsession: AsyncSession = Depends(get_forms_session)):
    _, edict = await _load(session, submission_id)
    _require_phase(edict, 'avaliacao')
    created = body.created_at or datetime.now(timezone.utc)
    updated = body.updated_at or created
    row = (await session.execute(text(
        'INSERT INTO comment (user_id, submission_id, comment, created_at, updated_at) '
        'VALUES (:u, :s, :c, :cr, :up) RETURNING id, created_at, updated_at'),
        {'u': user['id'], 's': submission_id, 'c': body.comment,
         'cr': created, 'up': updated})).first()
    await session.commit()
    return {'id': row[0], 'user': {'id': user['id'], 'name': user['name']},
            'submission_id': submission_id, 'comment': body.comment,
            'created_at': row[1].isoformat(), 'updated_at': row[2].isoformat()}


@router.delete('/comments/{comment_id}', status_code=204)
async def remove_comment(comment_id: int,
                         user: dict = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)):
    row = (await session.execute(
        text('SELECT id, user_id FROM comment WHERE id = :i'),
        {'i': comment_id})).first()
    if row is None:
        raise HTTPException(status_code=404, detail='Comment not found')
    if row[1] != user['id']:
        raise HTTPException(status_code=403, detail='Cannot delete this comment')
    await session.execute(text('DELETE FROM comment WHERE id = :i'), {'i': comment_id})
    await session.commit()


@router.get('/{submission_id}/labels')
async def get_labels(submission_id: int,
                     user: dict = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session),
                     fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    rows = (await session.execute(text(
        "SELECT DISTINCT ON (label) id, label, color FROM labels "
        "WHERE user_id = :u AND context_type = 'candidate' ORDER BY label, id DESC"),
        {'u': user['id']})).mappings().all()
    return {'labels': [dict(r) for r in rows]}


@router.post('/{submission_id}/labels')
async def add_label(submission_id: int, body: LabelSchema,
                    user: dict = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session),
                    fsession: AsyncSession = Depends(get_forms_session)):
    _, edict = await _load(session, submission_id)
    _require_phase(edict, 'avaliacao')
    await session.execute(text(
        "UPDATE labels SET color = :c WHERE user_id = :u AND label = :l "
        "AND context_type = 'candidate'"),
        {'c': body.color, 'u': user['id'], 'l': body.label})
    row = (await session.execute(text(
        "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
        "VALUES (:u, :s, :l, :c, 'candidate') RETURNING id"),
        {'u': user['id'], 's': submission_id, 'l': body.label,
         'c': body.color})).first()
    await session.commit()
    return {'id': row[0], 'user': {'id': user['id'], 'name': user['name']},
            'submission_id': submission_id, 'label': body.label}


@router.delete('/label/{label_id}', status_code=204)
async def remove_label(label_id: int,
                       user: dict = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)):
    row = (await session.execute(
        text('SELECT id, user_id FROM labels WHERE id = :i'),
        {'i': label_id})).first()
    if row is None:
        raise HTTPException(status_code=404, detail='Label not found')
    if row[1] != user['id']:
        raise HTTPException(status_code=403, detail='Cannot delete this label')
    await session.execute(text('DELETE FROM labels WHERE id = :i'), {'i': label_id})
    await session.commit()


@router.post('/{submission_id}/private_notes')
async def add_or_update_note(submission_id: int, body: PrivateNoteSchema,
                             user: dict = Depends(get_current_user),
                             session: AsyncSession = Depends(get_session),
                             fsession: AsyncSession = Depends(get_forms_session)):
    _, edict = await _load(session, submission_id)
    _require_phase(edict, 'avaliacao')
    await session.execute(text(
        'INSERT INTO private_note (user_id, submission_id, note, created_at, updated_at) '
        'VALUES (:u, :s, :n, now(), now()) '
        'ON CONFLICT (user_id, submission_id) DO UPDATE SET note = :n, updated_at = now()'),
        {'u': user['id'], 's': submission_id, 'n': body.note})
    await session.commit()
    return {'note': body.note}


@router.post('/{submission_id}/favorites', status_code=201)
async def create_favorite(submission_id: int,
                          user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session),
                          fsession: AsyncSession = Depends(get_forms_session)):
    _, edict = await _load(session, submission_id)
    _require_phase(edict, 'avaliacao')
    await session.execute(text(
        'INSERT INTO favorites (user_id, submission_id, created_at) '
        'VALUES (:u, :s, now()) ON CONFLICT (user_id, submission_id) DO NOTHING'),
        {'u': user['id'], 's': submission_id})
    await session.commit()
    return {'message': 'Favorite created'}


@router.delete('/{submission_id}/favorites')
async def remove_favorite(submission_id: int,
                          user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session),
                          fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    await session.execute(text(
        'DELETE FROM favorites WHERE user_id = :u AND submission_id = :s'),
        {'u': user['id'], 's': submission_id})
    await session.commit()
    return {'message': 'Favorite removed'}


@router.post('/{submission_id}/view')
async def register_view(submission_id: int,
                        user: dict = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session),
                        fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    row = (await session.execute(text(
        'SELECT id FROM submission_view WHERE user_id = :u AND submission_id = :s '
        'AND created_at::date = current_date'),
        {'u': user['id'], 's': submission_id})).first()
    if row:
        await session.execute(text(
            'UPDATE submission_view SET updated_at = now() WHERE id = :i'),
            {'i': row[0]})
    else:
        await session.execute(text(
            'INSERT INTO submission_view (user_id, submission_id, created_at, updated_at) '
            'VALUES (:u, :s, now(), now())'),
            {'u': user['id'], 's': submission_id})
    await session.commit()
    return {'message': 'View registered'}


@router.get('/{submission_id}/view')
async def get_views(submission_id: int,
                    user: dict = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session),
                    fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    rows = (await session.execute(text(
        'SELECT v.id, v.created_at, v.updated_at, u.id AS uid, u.name, u.email '
        'FROM submission_view v JOIN "user" u ON u.id = v.user_id '
        'WHERE v.submission_id = :s ORDER BY v.id'),
        {'s': submission_id})).mappings().all()
    return [{'id': r['id'],
             'user': {'id': r['uid'], 'name': r['name'], 'email': r['email']},
             'created_at': r['created_at'].isoformat() if r['created_at'] else None,
             'updated_at': r['updated_at'].isoformat() if r['updated_at'] else None}
            for r in rows]


@router.post('/{submission_id}/select')
async def select_stats(submission_id: int, body: StatsSchema,
                       user: dict = Depends(require_admin),
                       session: AsyncSession = Depends(get_session),
                       fsession: AsyncSession = Depends(get_forms_session)):
    sub, edict = await _load(session, submission_id)
    if not edict['is_open']:
        raise HTTPException(status_code=409, detail='Edict is closed')
    if body.stats == 'approved' and body.user_ids:
        await session.execute(text(
            'UPDATE submission SET stats = :st, advisor_id = :a, updated_at = now() '
            'WHERE id = :i'),
            {'st': body.stats.value, 'a': body.user_ids[0], 'i': submission_id})
    else:
        await session.execute(text(
            'UPDATE submission SET stats = :st, updated_at = now() WHERE id = :i'),
            {'st': body.stats.value, 'i': submission_id})
    await session.commit()
    return {'message': f'Submission marked as {body.stats.value}'}


@router.post('/{submission_id}/bidding')
async def toggle_bidding(submission_id: int, body: BiddingSchema,
                         user: dict = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session),
                         fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    target = user['id']
    if body.user_id and user['role'] in ADMIN_ROLES:
        target = body.user_id
    await session.execute(text(
        "DELETE FROM labels WHERE user_id = :u AND submission_id = :s "
        "AND context_type = 'bidding'"),
        {'u': target, 's': submission_id})
    if body.bidding.value:
        await session.execute(text(
            "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
            "VALUES (:u, :s, :l, '#000000', 'bidding')"),
            {'u': target, 's': submission_id, 'l': body.bidding.value})
    await session.commit()
    return {'message': 'Bidding updated'}


@router.post('/{submission_id}/entry-semester')
async def toggle_entry_semester(submission_id: int, body: EntrySemesterSchema,
                                user: dict = Depends(require_admin),
                                session: AsyncSession = Depends(get_session),
                                fsession: AsyncSession = Depends(get_forms_session)):
    await _load(session, submission_id)
    normalized = _normalize_semester(body.semester)
    await session.execute(text(
        'UPDATE submission SET entry_semester = :n, updated_at = now() WHERE id = :i'),
        {'n': normalized, 'i': submission_id})
    await session.commit()
    return {'semester': normalized}


@router.get('/{submission_id}/files/{label}/{filename}')
async def get_file(submission_id: int, label: str, filename: str,
                   user: dict = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session),
                   fsession: AsyncSession = Depends(get_forms_session)):
    sub, _ = await _load(session, submission_id)
    row = (await fsession.execute(text(
        "SELECT r.value FROM responses r JOIN form_field f ON f.id = r.field_id "
        "WHERE r.response_id = :rid AND f.name = :label AND f.type = 'File' "
        'AND r.value = :fn'),
        {'rid': sub['candidate_form_id'], 'label': label, 'fn': filename})).first()
    if not row or '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=404, detail='File not found')
    path = UPLOADS / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail='File not found')
    content = path.read_bytes()
    return Response(content, media_type='application/pdf',
                    headers={'Content-Disposition':
                             f'attachment; filename="{filename}"'})


@router.post('/{submission_id}/reesend_submission')
async def reesend_submission(submission_id: int, body: RequestReesendSchema,
                             user: dict = Depends(require_admin),
                             session: AsyncSession = Depends(get_session),
                             fsession: AsyncSession = Depends(get_forms_session)):
    sub, edict = await _load(session, submission_id)
    if edict['phase'] != 'homologacao':
        raise HTTPException(status_code=400, detail='Edict is not in homologacao')
    resp, data, email = await _candidate_contact(session, fsession, edict, sub)
    if not resp or not email:
        raise HTTPException(status_code=404, detail='Candidate response not found')
    await fsession.execute(text(
        'UPDATE form_response SET current_section = 0 WHERE id = :i'), {'i': resp['id']})
    await fsession.commit()
    settings = get_settings()
    link = f"{settings.base_url}/form/{resp['token']}"
    body_text = (f"{body.text}\n\n"
                 f"Acesse o formulário para corrigir sua inscrição:\n{link}\n")
    emails.send(email, 'Solicitação de correção de inscrição', body_text,
                bcc=user['email'])
    return {'message': 'Resubmission requested', 'email_sent': email}


@router.post('/{submission_id}/send-accept')
async def send_accept_forms(submission_id: int,
                            user: dict = Depends(get_current_user),
                            session: AsyncSession = Depends(get_session),
                            fsession: AsyncSession = Depends(get_forms_session)):
    sub, edict = await _load(session, submission_id)
    if sub['stats'] != 'approved':
        raise HTTPException(status_code=400, detail='Submission is not approved')
    if not edict['accept_forms']:
        raise HTTPException(status_code=404, detail='No accept form configured')
    if sub['accept_form_id']:
        raise HTTPException(status_code=400, detail='Accept form already sent')
    accept_form = int(edict['accept_forms'])
    resp, data, email = await _candidate_contact(session, fsession, edict, sub)
    if not resp or not email:
        raise HTTPException(status_code=404, detail='Candidate response not found')
    name = data.get('name') or ''
    phase_row = (await session.execute(text(
        "SELECT closed_date FROM edict_phase WHERE edict_id = :e "
        "AND phase = 'encerrado'"), {'e': edict['id']})).first()
    expiration = None
    if phase_row and phase_row[0]:
        expiration = phase_row[0]
    elif edict['closed_date']:
        expiration = edict['closed_date']
    else:
        expiration = date.today() + timedelta(days=30)
    shared_token, response_token = str(uuid4()), str(uuid4())
    shared = (await fsession.execute(text(
        'INSERT INTO form_shared (form_id, unique_answers, is_public, token, '
        'created_at, expiration_at) VALUES (:f, true, false, :t, now(), :e) '
        'RETURNING id'),
        {'f': accept_form, 't': shared_token, 'e': expiration})).first()
    version = await forms_svc.get_form_version(fsession, accept_form)
    new_id = (await fsession.execute(text(
        'INSERT INTO form_response (form_id, shared_id, email, token, current_section, '
        "submitted_at, metadata, form_version) VALUES (:f, :sh, :e, :t, 0, NULL, "
        "CAST('{}' AS jsonb), :v) RETURNING id"),
        {'f': accept_form, 'sh': shared[0], 'e': email, 't': response_token,
         'v': version})).first()
    await session.execute(text(
        'UPDATE submission SET accept_form_id = :a, updated_at = now() WHERE id = :i'),
        {'a': new_id[0], 'i': submission_id})
    await fsession.commit()
    await session.commit()
    cc = None
    if sub['advisor_id']:
        arow = (await session.execute(
            text('SELECT email FROM "user" WHERE id = :i'),
            {'i': sub['advisor_id']})).first()
        if arow and arow[0]:
            cc = arow[0]
    settings = get_settings()
    link = f"{settings.base_url}/form/{response_token}"
    text = (f"Prezado(a) {name},\n\n"
            f"Você foi aprovado(a) no edital {edict['title']}. Para confirmar a "
            f"aceitação da vaga, preencha o formulário no link abaixo:\n{link}\n\n"
            f"Prazo para confirmação: {emails.format_date_pt(expiration)}\n"
            f"Deadline: {emails.format_date_en(expiration)}\n")
    emails.send(email, 'Formulário de aceite de vaga', text, cc=cc)
    return {'message': 'Accept form sent', 'email_sent': email}


@router.post('/{submission_id}/send-letter')
async def send_accept_letter(submission_id: int,
                             user: dict = Depends(get_current_user),
                             session: AsyncSession = Depends(get_session),
                             fsession: AsyncSession = Depends(get_forms_session)):
    sub, edict = await _load(session, submission_id)
    if sub['stats'] != 'approved':
        raise HTTPException(status_code=400, detail='Submission is not approved')
    if sub['letter_sent']:
        raise HTTPException(status_code=400, detail='Letter already sent')
    resp, data, email = await _candidate_contact(session, fsession, edict, sub)
    if not email:
        raise HTTPException(status_code=404, detail='Candidate response not found')
    name = data.get('name') or ''
    emails.send(email, 'Carta de aprovação',
                f"Prezado(a) {name},\n\nSua inscrição foi aprovada no edital "
                f"{edict['title']}.\n")
    await session.execute(text(
        'UPDATE submission SET letter_sent = true, updated_at = now() WHERE id = :i'),
        {'i': submission_id})
    await session.commit()
    return {'message': 'Letter sent', 'email_sent': email}
