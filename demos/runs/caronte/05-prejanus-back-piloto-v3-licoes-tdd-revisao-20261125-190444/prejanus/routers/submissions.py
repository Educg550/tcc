import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import forms_db, mailer, submissions_service
from prejanus.config import settings
from prejanus.db import get_db, get_forms_db
from prejanus.deps import ADMIN_ROLES, get_current_user
from prejanus.models import (
    Comment,
    Edict,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    SubmissionView,
    User,
)

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")


class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LabelInputSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class StatsSchema(BaseModel):
    user_ids: list[int] | None = None
    stats: str


class BiddingSchema(BaseModel):
    bidding: str
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


async def _get_submission(db: AsyncSession, submission_id: int) -> Submission:
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _get_edict_of(db: AsyncSession, sub: Submission) -> Edict:
    edict = await db.get(Edict, sub.edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


def _require_phase(edict: Edict, phase: str):
    if edict.phase != phase:
        raise HTTPException(status_code=400, detail=f"Operação disponível apenas na fase {phase}")


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    items = await submissions_service.list_submissions(db, fdb, edict, user)
    if stats is not None:
        items = [i for i in items if i["stats"] == stats]
    if only_favorites:
        items = [i for i in items if i["is_favorite"]]
    return {"submissions": items}


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    summary = await submissions_service.submission_summary(db, fdb, edict, sub, user)
    if include_comments:
        rows = (
            await db.execute(
                select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
            )
        ).scalars().all()
        users = {u.id: u for u in (await db.execute(select(User).where(User.id.in_({c.user_id for c in rows})))).scalars().all()} if rows else {}
        summary["comments"] = [
            {
                "id": c.id,
                "user": {"id": users[c.user_id].id, "name": users[c.user_id].name} if c.user_id in users else None,
                "comment": c.comment,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in rows
        ]
    form = await submissions_service.build_submission_form(fdb, edict, sub)
    return {"summary": summary, "submission_form": form}


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    form = await submissions_service.build_submission_form(fdb, edict, sub)
    found = None
    for section in form:
        for field in section.get("fields", []):
            if (field.get("label") == label or field.get("name") == label) and field.get("value") == filename:
                found = field
                break
        if found:
            break
    if found is None:
        raise HTTPException(status_code=404, detail="Arquivo não pertence a esta candidatura")
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    token = str(resp.get("token")) if resp else ""
    path = _find_upload(token, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, media_type="application/pdf", filename=filename)


def _find_upload(token: str, filename: str) -> str | None:
    base = "/shared/uploads"
    if not os.path.isdir(base) or "/" in filename or filename in ("", ".", ".."):
        return None
    matches = []
    for root, _dirs, files in os.walk(base):
        if filename in files:
            matches.append(os.path.join(root, filename))
    if not matches:
        return None
    for m in matches:
        if token and token in m:
            return m
    return matches[0]


# ---------------------------------------------------------------------------
# Comentários e atividade


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    body: CommentSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    _require_phase(edict, "avaliacao")
    now = datetime.now(timezone.utc)
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=body.comment,
        created_at=body.created_at or now,
        updated_at=body.updated_at or body.created_at or now,
    )
    db.add(comment)
    await db.commit()
    return {
        "id": comment.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": sub.id,
        "comment": comment.comment,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


def _as_utc(dt):
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/submissions/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    rows = (
        await db.execute(
            select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
        )
    ).scalars().all()
    user_ids = {c.user_id for c in rows}
    users = {}
    if user_ids:
        for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all():
            users[u.id] = u
    activity = []
    for c in rows:
        u = users.get(c.user_id)
        activity.append(
            {
                "id": c.id,
                "user": {"id": u.id, "name": u.name} if u else None,
                "comment": c.comment,
                "text": c.comment,
                "type": "comment",
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
        )
    # eventos de candidatura, recomendações e aceite
    cand_resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if cand_resp and cand_resp.get("submitted_at"):
        activity.append(
            {
                "id": f"submission-{sub.id}",
                "user": {"id": 0, "name": "Candidato"},
                "text": "Candidatura submetida",
                "type": "submission",
                "created_at": cand_resp["submitted_at"],
            }
        )
    for rec in await submissions_service.get_recommendations(db, fdb, edict, sub):
        activity.append(
            {
                "id": f"recommendation-{rec['id']}",
                "user": {"id": 0, "name": rec["name"] or rec["email"]},
                "text": "Recomendação recebida",
                "type": "recommendation",
                "created_at": rec["submitted_at"],
            }
        )
    if sub.accept_form_id:
        acc_resp = await forms_db.get_response(fdb, sub.accept_form_id)
        if acc_resp and acc_resp.get("submitted_at"):
            activity.append(
                {
                    "id": f"accept-{sub.accept_form_id}",
                    "user": {"id": 0, "name": "Candidato"},
                    "text": "Aceite respondido",
                    "type": "accept",
                    "created_at": acc_resp["submitted_at"],
                }
            )
    activity.sort(key=lambda a: _as_utc(a["created_at"]))
    return activity


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir o comentário")
    await db.delete(comment)
    await db.commit()


# ---------------------------------------------------------------------------
# Favoritos


@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    _require_phase(edict, "avaliacao")
    existing = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Favorito já registrado")
    db.add(Favorite(user_id=user.id, submission_id=sub.id, created_at=datetime.now(timezone.utc)))
    await db.commit()
    return "Favorite created"


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    existing = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="Favorito não registrado")
    await db.delete(existing)
    await db.commit()


# ---------------------------------------------------------------------------
# Etiquetas


@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int,
    body: LabelInputSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    _require_phase(edict, "avaliacao")
    label = Label(
        user_id=user.id,
        submission_id=sub.id,
        label=body.label,
        color=body.color,
        context_type="candidate",
    )
    db.add(label)
    # atualiza a cor das etiquetas do mesmo autor e rótulo em outras inscrições
    rows = (
        await db.execute(
            select(Label).where(
                Label.user_id == user.id,
                Label.label == body.label,
                Label.context_type == "candidate",
            )
        )
    ).scalars().all()
    for row in rows:
        row.color = body.color
    await db.commit()
    return {
        "id": label.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": sub.id,
        "label": label.label,
    }


@router.get("/submissions/{submission_id}/labels")
async def get_label(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission(db, submission_id)
    rows = await db.execute(
        text(
            "select distinct on (label) id, label, color from labels"
            " where user_id = :u and (context_type is null or context_type = 'candidate')"
            " order by label, id"
        ),
        {"u": user.id},
    )
    return {"labels": [{"id": r[0], "label": r[1], "color": r[2]} for r in rows.all()]}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(
    label_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if label.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir a etiqueta")
    await db.delete(label)
    await db.commit()


# ---------------------------------------------------------------------------
# Notas privadas


@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    body: PrivateNoteSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    _require_phase(edict, "avaliacao")
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user.id, PrivateNote.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if note is None:
        note = PrivateNote(
            user_id=user.id,
            submission_id=sub.id,
            note=body.note,
            created_at=now,
            updated_at=now,
        )
        db.add(note)
    else:
        note.note = body.note
        note.updated_at = now
    await db.commit()
    return {"note": note.note}


# ---------------------------------------------------------------------------
# Visualizações


@router.post("/submissions/{submission_id}/view")
async def register_view(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    today = datetime.now(SP_TZ).date()
    existing = (
        await db.execute(
            select(SubmissionView).where(
                SubmissionView.user_id == user.id,
                SubmissionView.submission_id == sub.id,
                text("(created_at at time zone 'America/Sao_Paulo')::date = :d"),
            ),
            {"d": today},
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if existing is None:
        db.add(SubmissionView(user_id=user.id, submission_id=sub.id, created_at=now, updated_at=now))
    else:
        existing.updated_at = now
    await db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            select(SubmissionView).where(SubmissionView.submission_id == submission_id)
        )
    ).scalars().all()
    user_ids = {v.user_id for v in rows}
    users = {}
    if user_ids:
        for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all():
            users[u.id] = u
    return [
        {
            "id": v.id,
            "user": {"id": users[v.user_id].id, "name": users[v.user_id].name} if v.user_id in users else None,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
        }
        for v in rows
    ]


# ---------------------------------------------------------------------------
# Seleção e interesses


@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int,
    body: StatsSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edital encerrado")
    if body.stats == "approved":
        if not body.user_ids or len(body.user_ids) != 1:
            raise HTTPException(status_code=400, detail="Aprovação exige um único orientador")
        advisor = await db.get(User, body.user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=400, detail="Orientador inexistente")
        sub.advisor_id = advisor.id
    sub.stats = body.stats
    await db.commit()
    return body.stats


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    body: BiddingSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    target_id = user.id
    if body.user_id is not None and user.role in ADMIN_ROLES:
        target_id = body.user_id
    existing = (
        await db.execute(
            select(Label).where(
                Label.user_id == target_id,
                Label.submission_id == sub.id,
                Label.context_type == "bidding",
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Label(
                user_id=target_id,
                submission_id=sub.id,
                label=body.bidding,
                color="",
                context_type="bidding",
            )
        )
    else:
        existing.label = body.bidding
    await db.commit()
    return body.bidding


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    body: EntrySemesterSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    value = body.semester.strip()
    low = value.lower()
    if low in ("first", "primeiro", "primeiro semestre", "1", "primeiro semestre."):
        value = "Primeiro semestre."
    elif low in ("second", "segundo", "segundo semestre", "2", "segundo semestre."):
        value = "Segundo semestre."
    sub.entry_semester = value
    await db.commit()
    return value


# ---------------------------------------------------------------------------
# E-mails


async def _candidate_email(db: AsyncSession, fdb: AsyncSession, sub: Submission, edict: Edict) -> str:
    summary = await submissions_service.submission_summary(db, fdb, edict, sub, User(id=0, name="", email="", role=""))
    email = summary.get("email") or ""
    if email:
        return email
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    return (resp or {}).get("email") or ""


@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    body: RequestReesendSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    _require_phase(edict, "homologacao")
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp is None:
        raise HTTPException(status_code=404, detail="Resposta de candidatura não encontrada")
    await forms_db.update_response_section(fdb, sub.candidate_form_id, 0)
    to = resp.get("email") or await _candidate_email(db, fdb, sub, edict)
    link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua candidatura precisa de correção. Motivo:</p>"
        f"<p>{body.text}</p>"
        f"<p>Para corrigir e reenviar, acesse: <a href=\"{link}\">{link}</a></p>"
    )
    plain = (
        f"Prezado(a) candidato(a),\n\n"
        f"Sua candidatura precisa de correção. Motivo:\n\n"
        f"{body.text}\n\n"
        f"Para corrigir e reenviar, acesse: {link}\n"
    )
    await asyncio.to_thread(
        mailer.send_email,
        to,
        "Solicitação de correção de candidatura",
        html,
        bcc=user.email,
        plain=plain,
    )
    return {"message": "Solicitação de correção enviada", "email_sent": to}


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub.accept_form_id:
        raise HTTPException(status_code=400, detail="Formulário de aceite já enviado")
    try:
        accept_form = int(str(edict.accept_forms))
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
    form = await forms_db.get_form(fdb, accept_form)
    if form is None:
        raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
    to = await _candidate_email(db, fdb, sub, edict)
    expiration = (
        datetime.combine(edict.closed_date, datetime.min.time()) if edict.closed_date else None
    )
    shared = await forms_db.create_shared(fdb, accept_form, expiration)
    response = await forms_db.create_response(
        fdb, accept_form, shared["id"], to, form.get("version") or 1
    )
    sub.accept_form_id = response["id"]
    await db.commit()

    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    link = f"{settings.base_url.rstrip('/')}/form/{response['token']}"
    deadline = edict.closed_date.isoformat() if edict.closed_date else ""
    html = (
        f"<p>Parabéns! Sua candidatura foi aprovada.</p>"
        f"<p>Caro(a) candidato(a), confirme sua aceitação até <b>{deadline}</b> "
        f"preenchendo o formulário de aceite: <a href=\"{link}\">{link}</a></p>"
        f"<p>Dear candidate, please confirm your acceptance by <b>{deadline}</b> "
        f"using this form: <a href=\"{link}\">{link}</a></p>"
    )
    await asyncio.to_thread(
        mailer.send_email,
        to,
        "Formulário de aceite / Acceptance form",
        html,
        cc=advisor.email if advisor else None,
    )
    return {"message": "Formulário de aceite enviado", "email_sent": to}


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Carta já enviada")
    summary = await submissions_service.submission_summary(db, fdb, edict, sub, user)
    to = summary.get("email") or ""
    if not to:
        resp = await forms_db.get_response(fdb, sub.candidate_form_id)
        to = (resp or {}).get("email") or ""
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    semester = summary.get("entry_semester") or ""
    signature = ""
    try:
        import base64

        with open("data/signature.png", "rb") as fh:
            signature = base64.b64encode(fh.read()).decode()
    except OSError:
        pass
    sig_html = (
        f'<p><img src="data:image/png;base64,{signature}" alt="Assinatura"/></p>' if signature else ""
    )
    html = (
        f"<p>Prezado(a) <b>{summary.get('name') or 'candidato(a)'}</b>,</p>"
        f"<p>Informamos que sua candidatura ao programa de pós-graduação foi <b>aprovada</b>.</p>"
        f"<p>Orientador(a): <b>{advisor.name if advisor else '-'}</b></p>"
        f"<p>Semestre de ingresso: <b>{semester}</b></p>"
        f"<p>Ano de ingresso: <b>{edict.year}</b></p>"
        f"<p>Cordialmente,</p>{sig_html}"
    )
    await asyncio.to_thread(
        mailer.send_email,
        to,
        "Carta de aceite",
        html,
        cc=advisor.email if advisor else None,
    )
    sub.letter_sent = True
    await db.commit()
    return {"message": "Carta de aceite enviada", "email_sent": to}
