import datetime as dt
import os
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_db as forms_db
from auth import ADMIN_ROLES, get_current_user
from config import settings
from db import get_db, get_forms_db
from mailer import send_email
from models import (
    Comment,
    Edict,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    SubmissionView,
    User,
)
from schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelInputSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from services import submissions_data

router = APIRouter(prefix="/submissions", tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")

BIDDING_VALUES = {
    "decline",
    "available",
    "interested",
    "agreed",
    "interested_scholarship",
    "",
}


async def _get_submission(db: AsyncSession, submission_id: int) -> Submission:
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _get_edict(db: AsyncSession, submission: Submission) -> Edict:
    edict = await db.get(Edict, submission.edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


@router.get("/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    detail = await submissions_data.build_detail(db, fdb, sub, edict, user)
    if include_comments:
        detail["comments"] = await _comments_activity(db, fdb, sub)
    return detail


# ---------------------------------------------------------------------------
# Comentários
# ---------------------------------------------------------------------------


async def _comments_activity(db: AsyncSession, fdb: AsyncSession, sub: Submission):
    comments = (
        await db.execute(
            select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
        )
    ).scalars().all()
    items = []
    for c in comments:
        author = await db.get(User, c.user_id)
        items.append(
            {
                "id": c.id,
                "user": {"id": author.id, "name": author.name} if author else None,
                "submission_id": c.submission_id,
                "comment": c.comment,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "type": "comment",
            }
        )
    event_id = -1
    if sub.created_at:
        items.append(
            {
                "id": event_id,
                "user": None,
                "comment": "Candidatura registrada",
                "created_at": sub.created_at,
                "type": "submission",
            }
        )
        event_id -= 1
    for rid in sub.recommenders_form_ids or []:
        resp = await forms_db.get_response(fdb, rid)
        if resp and resp.get("submitted_at"):
            items.append(
                {
                    "id": event_id,
                    "user": None,
                    "comment": f"Recomendação recebida de {resp.get('email') or ''}",
                    "created_at": resp["submitted_at"],
                    "type": "recommendation",
                }
            )
            event_id -= 1
    if sub.accept_form_id:
        resp = await forms_db.get_response(fdb, sub.accept_form_id)
        if resp and resp.get("submitted_at"):
            items.append(
                {
                    "id": event_id,
                    "user": None,
                    "comment": "Formulário de aceite respondido",
                    "created_at": resp["submitted_at"],
                    "type": "accept",
                }
            )
            event_id -= 1
    def _sort_key(item):
        value = item["created_at"]
        if value is None:
            return dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return value

    items.sort(key=_sort_key)
    return items


@router.get("/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    return await _comments_activity(db, fdb, sub)


@router.post("/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    if edict.phase != "avaliacao":
        raise HTTPException(status_code=400, detail="Comentários permitidos apenas na fase de avaliação")
    now = dt.datetime.now(dt.timezone.utc)
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=payload.comment,
        created_at=payload.created_at or now,
        updated_at=payload.updated_at or payload.created_at or now,
    )
    db.add(comment)
    await db.commit()
    return {
        "id": comment.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": comment.submission_id,
        "comment": comment.comment,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@router.delete("/comments/{comment_id}")
async def remove_comment(
    comment_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
    await db.delete(comment)
    await db.commit()
    return {"message": "Comentário removido"}


# ---------------------------------------------------------------------------
# Etiquetas
# ---------------------------------------------------------------------------


@router.post("/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    label = Label(
        user_id=user.id,
        submission_id=sub.id,
        label=payload.label,
        color=payload.color,
        context_type="candidate",
    )
    db.add(label)
    others = (
        await db.execute(
            select(Label).where(
                Label.user_id == user.id,
                Label.label == payload.label,
                Label.submission_id != sub.id,
                (Label.context_type.is_(None)) | (Label.context_type == "candidate"),
            )
        )
    ).scalars().all()
    for other in others:
        other.color = payload.color
    await db.commit()
    return {
        "id": label.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": label.submission_id,
        "label": label.label,
        "color": label.color,
    }


@router.get("/{submission_id}/labels")
async def get_labels(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            select(Label)
            .where(
                Label.user_id == user.id,
                (Label.context_type.is_(None)) | (Label.context_type == "candidate"),
            )
            .order_by(Label.id)
        )
    ).scalars().all()
    by_label: dict[str, Label] = {}
    for row in rows:
        by_label[row.label] = row
    return {
        "labels": [
            {"id": row.id, "label": row.label, "color": row.color}
            for row in by_label.values()
        ]
    }


@router.delete("/label/{label_id}")
async def remove_label(
    label_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if label.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
    await db.delete(label)
    await db.commit()
    return {"message": "Etiqueta removida"}


# ---------------------------------------------------------------------------
# Notas privadas
# ---------------------------------------------------------------------------


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user.id,
                PrivateNote.submission_id == sub.id,
            )
        )
    ).scalar_one_or_none()
    now = dt.datetime.now(dt.timezone.utc)
    if note is None:
        note = PrivateNote(
            user_id=user.id,
            submission_id=sub.id,
            note=payload.note,
            created_at=now,
            updated_at=now,
        )
        db.add(note)
    else:
        note.note = payload.note
        note.updated_at = now
    await db.commit()
    return {"note": note.note}


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------


@router.post("/{submission_id}/favorites")
async def create_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    existing = await db.get(Favorite, (user.id, sub.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Favorito já registrado")
    db.add(Favorite(user_id=user.id, submission_id=sub.id, created_at=dt.datetime.now(dt.timezone.utc)))
    await db.commit()
    return "Favorito registrado"


@router.delete("/{submission_id}/favorites")
async def remove_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    existing = await db.get(Favorite, (user.id, sub.id))
    if existing is None:
        raise HTTPException(status_code=404, detail="Favorito não registrado")
    await db.delete(existing)
    await db.commit()
    return "Favorito removido"


# ---------------------------------------------------------------------------
# Seleção, interesse e semestre
# ---------------------------------------------------------------------------


@router.post("/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edital encerrado")
    if payload.stats not in ("approved", "refused", "underreview", "waitlist"):
        raise HTTPException(status_code=422, detail="Situação inválida")
    if payload.stats != "underreview" and user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    if payload.stats == "approved":
        user_ids = payload.user_ids or []
        if len(user_ids) != 1:
            raise HTTPException(status_code=400, detail="Aprovação exige um único orientador")
        advisor = await db.get(User, user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=400, detail="Orientador inexistente")
        sub.advisor_id = advisor.id
    sub.stats = payload.stats
    sub.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    return sub.stats


@router.post("/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    if payload.bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Interesse inválido")
    target_id = user.id
    if payload.user_id is not None and user.role in ADMIN_ROLES:
        target_id = payload.user_id
    existing = (
        await db.execute(
            select(Label).where(
                Label.user_id == target_id,
                Label.submission_id == sub.id,
                Label.context_type == "bidding",
            )
        )
    ).scalar_one_or_none()
    if payload.bidding == "":
        if existing is not None:
            await db.delete(existing)
            await db.commit()
        return "Interesse removido"
    if existing is not None:
        existing.label = payload.bidding
    else:
        db.add(
            Label(
                user_id=target_id,
                submission_id=sub.id,
                label=payload.bidding,
                color="",
                context_type="bidding",
            )
        )
    await db.commit()
    return payload.bidding


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    text = (payload.semester or "").strip().lower()
    if "primeiro" in text or "first" in text:
        semester = "Primeiro semestre."
    elif "segundo" in text or "second" in text:
        semester = "Segundo semestre."
    else:
        semester = payload.semester
    sub.entry_semester = semester
    sub.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    return semester


# ---------------------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------------------


def _find_upload(value: str, filename: str) -> str | None:
    base = "/shared/uploads"
    candidates = [
        value if value.startswith("/") else os.path.join(base, value),
        os.path.join(base, filename),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate) and os.path.basename(candidate) == os.path.basename(filename):
            return candidate
    for root, _dirs, files in os.walk(base):
        if os.path.basename(filename) in files:
            return os.path.join(root, os.path.basename(filename))
    return None


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp is None:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    fields = await forms_db.get_all_fields(fdb, resp["form_id"])
    field = next((f for f in fields if f["name"] == label), None)
    if field is None:
        raise HTTPException(status_code=404, detail="Campo não encontrado")
    values = await forms_db.get_values(fdb, sub.candidate_form_id)
    value = values.get(field["id"])
    if not value or os.path.basename(value) != os.path.basename(filename):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    path = _find_upload(value, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Visualizações
# ---------------------------------------------------------------------------


@router.post("/{submission_id}/view")
async def register_view(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    today = dt.datetime.now(SP_TZ).date()
    views = (
        await db.execute(
            select(SubmissionView).where(
                SubmissionView.user_id == user.id,
                SubmissionView.submission_id == sub.id,
            )
        )
    ).scalars().all()
    for view in views:
        created = view.created_at
        if created is not None and created.astimezone(SP_TZ).date() == today:
            view.updated_at = dt.datetime.now(dt.timezone.utc)
            await db.commit()
            return {"message": "Visualização já registrada"}
    db.add(
        SubmissionView(
            user_id=user.id,
            submission_id=sub.id,
            created_at=dt.datetime.now(dt.timezone.utc),
            updated_at=dt.datetime.now(dt.timezone.utc),
        )
    )
    await db.commit()
    return {"message": "Visualização registrada"}


@router.get("/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    views = (
        await db.execute(
            select(SubmissionView)
            .where(SubmissionView.submission_id == sub.id)
            .order_by(SubmissionView.created_at)
        )
    ).scalars().all()
    out = []
    for view in views:
        author = await db.get(User, view.user_id)
        out.append(
            {
                "id": view.id,
                "user": {"id": author.id, "name": author.name} if author else None,
                "submission_id": view.submission_id,
                "created_at": view.created_at,
                "updated_at": view.updated_at,
            }
        )
    return out


# ---------------------------------------------------------------------------
# E-mails e efeitos no Forms
# ---------------------------------------------------------------------------


async def _candidate_email(db: AsyncSession, fdb: AsyncSession, sub: Submission, edict: Edict) -> str | None:
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    email = (resp or {}).get("email")
    if email:
        return email
    cand_mappings = await submissions_data.load_mappings(db, edict.id, "candidate")
    values = await forms_db.get_values(fdb, sub.candidate_form_id)
    leaves = submissions_data._leaves_for_version(
        cand_mappings, sub.candidate_form_version
    )
    from services import mappings as mappings_svc

    return mappings_svc.get_value(leaves, values, "email")


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp is None:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    await forms_db.reopen_response(fdb, sub.candidate_form_id)
    email = await _candidate_email(db, fdb, sub, edict) or ""
    link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
    html = (
        "<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua inscrição precisa de correção. Motivo: {payload.text}</p>"
        f'<p>Acesse o formulário para corrigir e reenviar: <a href="{link}">{link}</a></p>'
    )
    sent = send_email(
        email, "Solicitação de correção de inscrição", html, bcc=[user.email]
    )
    if not sent:
        raise HTTPException(
            status_code=500,
            detail=f"Nenhum destinatário disponível (candidato={email!r}, solicitante={user.email!r})",
        )
    return {
        "message": "Solicitação de correção enviada",
        "email_sent": sent[0],
    }


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    if not edict.accept_forms:
        raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
    if sub.accept_form_id:
        raise HTTPException(status_code=400, detail="Aceite já enviado")

    email = await _candidate_email(db, fdb, sub, edict)
    if not email:
        raise HTTPException(status_code=400, detail="E-mail do candidato indisponível")
    shared = await forms_db.create_shared(fdb, int(edict.accept_forms), edict.closed_date)
    response = await forms_db.create_response(
        fdb, int(edict.accept_forms), shared["id"], email
    )
    sub.accept_form_id = response["id"]
    sub.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    link = f"{settings.base_url.rstrip('/')}/form/{shared['token']}"
    cand_mappings = await submissions_data.load_mappings(db, edict.id, "candidate")
    values = await forms_db.get_values(fdb, sub.candidate_form_id)
    leaves = submissions_data._leaves_for_version(cand_mappings, sub.candidate_form_version)
    from services import mappings as mappings_svc

    name = mappings_svc.get_value(leaves, values, "name") or "candidato(a)"
    html = (
        f"<p>Prezado(a) {name},</p>"
        "<p>Parabéns! Sua candidatura foi aprovada. Para confirmar sua matrícula, "
        f"preencha o formulário de aceite até {edict.closed_date}.</p>"
        f'<p>Dear candidate, congratulations! Your application was approved. '
        f"Please fill the acceptance form until {edict.closed_date}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
    )
    send_email(
        email,
        "Formulário de aceite / Acceptance form",
        html,
        cc=[advisor.email] if advisor and advisor.email else None,
    )
    return {
        "message": "Formulário de aceite enviado",
        "email_sent": email,
    }


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub)
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Carta já enviada")

    email = await _candidate_email(db, fdb, sub, edict)
    if not email:
        raise HTTPException(status_code=400, detail="E-mail do candidato indisponível")
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    semester = sub.entry_semester or f"{edict.semester}º semestre"
    signature = os.path.join("data", "signature.png")
    signature_html = ""
    if os.path.exists(signature):
        signature_html = f'<p><img src="file://{signature}" alt="Assinatura" height="80"></p>'
    html = (
        "<h2>Carta de Aceite / Acceptance Letter</h2>"
        f"<p>Comunicamos que sua candidatura ao programa de pós-graduação foi aprovada.</p>"
        f"<p>Orientador(a): {advisor.name if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict.year}</p>"
        f"{signature_html}"
    )
    send_email(
        email,
        "Carta de aceite / Acceptance letter",
        html,
        cc=[advisor.email] if advisor and advisor.email else None,
    )
    sub.letter_sent = True
    sub.updated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    return {
        "message": "Carta de aceite enviada",
        "email_sent": email,
    }
