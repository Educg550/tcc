import datetime
import os
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import formsdb, mail, subservice
from prejanus.auth import ADMIN_ROLES, get_current_user
from prejanus.config import settings
from prejanus.db import get_db
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
from prejanus.schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelInputSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")


async def _get_submission(db: AsyncSession, submission_id: int) -> Submission:
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "submission not found")
    return sub


async def _get_edict_of(db: AsyncSession, sub: Submission) -> Edict:
    edict = await db.get(Edict, sub.edict_id)
    if edict is None:
        raise HTTPException(404, "edict not found")
    return edict


def _aware(dt: datetime.datetime | None) -> datetime.datetime:
    if dt is None:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    return await subservice.build_detail(db, edict, sub, user.id, include_comments)


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if edict.phase != "avaliacao":
        raise HTTPException(400, "comments are only allowed in the avaliacao phase")
    now = datetime.datetime.now(datetime.timezone.utc)
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=payload.comment,
        created_at=payload.created_at or now,
        updated_at=payload.updated_at or now,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {
        "id": comment.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": comment.submission_id,
        "comment": comment.comment,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@router.get("/submissions/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    events = []
    for comment in await subservice.comments_list(db, sub):
        events.append(
            {
                "id": comment["id"],
                "user": comment["user"],
                "comment": comment["comment"],
                "text": comment["comment"],
                "type": "comment",
                "created_at": comment["created_at"],
            }
        )
    name, _email, resp, _mapped, _values = await subservice.candidate_identity(db, edict, sub)
    if resp and resp["submitted_at"]:
        events.append(
            {
                "user": {"id": None, "name": name},
                "text": "Candidatura enviada",
                "type": "submission",
                "created_at": resp["submitted_at"],
            }
        )
    for rid in sub.recommender_form_ids or []:
        rec = await formsdb.get_response(rid)
        if rec and rec["submitted_at"]:
            events.append(
                {
                    "user": {"id": None, "name": ""},
                    "text": "Recomendacao recebida",
                    "type": "recommendation",
                    "created_at": rec["submitted_at"],
                }
            )
    if sub.accept_form_id:
        accept_resp = await formsdb.get_response(sub.accept_form_id)
        if accept_resp and accept_resp["submitted_at"]:
            events.append(
                {
                    "user": {"id": None, "name": name},
                    "text": "Aceite respondido",
                    "type": "accept",
                    "created_at": accept_resp["submitted_at"],
                }
            )
    events.sort(key=lambda e: _aware(e["created_at"]))
    return events


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "comment not found")
    if comment.user_id != user.id:
        raise HTTPException(403, "only the author can delete this comment")
    await db.delete(comment)
    await db.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(
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
    if existing is not None:
        raise HTTPException(409, "submission is already a favorite")
    db.add(
        Favorite(
            user_id=user.id,
            submission_id=sub.id,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
    )
    await db.commit()
    return "favorite created"


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
        raise HTTPException(404, "favorite not found")
    await db.delete(existing)
    await db.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    user: User = Depends(get_current_user),
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
    await db.flush()
    others = (
        await db.execute(
            select(Label).where(
                Label.user_id == user.id,
                Label.label == payload.label,
                Label.context_type == "candidate",
                Label.id != label.id,
            )
        )
    ).scalars().all()
    for other in others:
        other.color = payload.color
    await db.commit()
    await db.refresh(label)
    return {
        "id": label.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": label.submission_id,
        "label": label.label,
    }


@router.get("/submissions/{submission_id}/labels")
async def get_labels(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            select(Label)
            .where(Label.user_id == user.id, Label.context_type == "candidate")
            .order_by(Label.id.desc())
        )
    ).scalars().all()
    labels = []
    seen = set()
    for row in rows:
        if row.label in seen:
            continue
        seen.add(row.label)
        labels.append({"id": row.id, "label": row.label, "color": row.color})
    return {"labels": labels}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(
    label_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(404, "label not found")
    if label.user_id != user.id:
        raise HTTPException(403, "only the author can delete this label")
    await db.delete(label)
    await db.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    now = datetime.datetime.now(datetime.timezone.utc)
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user.id, PrivateNote.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    if note is None:
        note = PrivateNote(
            user_id=user.id,
            submission_id=sub.id,
            note=payload.note,
            created_at=now,
        )
        db.add(note)
    else:
        note.note = payload.note
        note.updated_at = now
    await db.commit()
    return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
async def register_view(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    today = datetime.datetime.now(SP_TZ).date()
    views = (
        await db.execute(
            select(SubmissionView).where(
                SubmissionView.user_id == user.id,
                SubmissionView.submission_id == sub.id,
            )
        )
    ).scalars().all()
    for view in views:
        if view.created_at and view.created_at.astimezone(SP_TZ).date() == today:
            return {"message": "view already registered"}
    db.add(
        SubmissionView(
            user_id=user.id,
            submission_id=sub.id,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
    )
    await db.commit()
    return {"message": "view registered"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            select(SubmissionView, User)
            .join(User, User.id == SubmissionView.user_id)
            .where(SubmissionView.submission_id == sub.id)
            .order_by(SubmissionView.id)
        )
    ).all()
    return [
        {"user": {"id": u.id, "name": u.name}, "created_at": v.created_at}
        for v, u in rows
    ]


@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Administrative role required")
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if not edict.is_open:
        raise HTTPException(409, "edict is closed")
    if payload.stats == "approved":
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(400, "approval requires exactly one advisor")
        advisor = await db.get(User, payload.user_ids[0])
        if advisor is None:
            raise HTTPException(400, "advisor does not exist")
        sub.advisor_id = advisor.id
    sub.stats = payload.stats
    await db.commit()
    return f"submission marked as {payload.stats}"


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    target_id = user.id
    if payload.user_id is not None and user.role in ADMIN_ROLES:
        target_id = payload.user_id
    existing = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id,
                Label.user_id == target_id,
                Label.context_type == "bidding",
            )
        )
    ).scalars().all()
    for label in existing:
        await db.delete(label)
    if payload.bidding != "":
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
    return "bidding updated"


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    text = payload.semester.strip()
    low = text.lower().rstrip(".")
    if low in ("primeiro", "first", "primeiro semestre", "1"):
        value = "Primeiro semestre."
    elif low in ("segundo", "second", "segundo semestre", "2"):
        value = "Segundo semestre."
    else:
        value = text
    sub.entry_semester = value
    await db.commit()
    return value


def _find_upload_file(filename: str) -> str | None:
    base = os.path.basename(filename)
    candidates = []
    if filename.startswith("/"):
        candidates.append(filename)
    else:
        candidates.append(os.path.join("/shared/uploads", filename))
        candidates.append(os.path.join("/shared/uploads", base))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    for root, _dirs, files in os.walk("/shared/uploads"):
        if base in files:
            return os.path.join(root, base)
    return None


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    values, fields = await formsdb.get_response_data(sub.candidate_form_id)
    field = None
    for f in fields:
        if f["name"] == label or (f["label"] or "").lower() == label.lower():
            field = f
            break
    if field is None:
        raise HTTPException(404, "field not found")
    value = values.get(field["id"])
    if value is None or (
        value != filename
        and not value.endswith("/" + filename)
        and os.path.basename(value) != filename
    ):
        raise HTTPException(404, "file does not match this submission")
    path = _find_upload_file(value)
    if path is None:
        raise HTTPException(404, "file not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Administrative role required")
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if edict.phase != "homologacao":
        raise HTTPException(400, "corrections can only be requested in the homologacao phase")
    name, email, resp, _mapped, _values = await subservice.candidate_identity(db, edict, sub)
    if resp is None:
        raise HTTPException(404, "candidate response not found")
    await formsdb.reopen_response(sub.candidate_form_id)
    link = f"{settings.base_url}/form/{resp['token']}"
    tos = []
    for address in (email, resp["email"]):
        if address and address not in tos:
            tos.append(address)
    html = (
        "<html><body>"
        f"<p>Olá {name},</p>"
        "<p>Sua candidatura precisa de correção. Motivo informado:</p>"
        f"<p>{payload.text}</p>"
        f'<p>Acesse o formulário para corrigir e reenviar: <a href="{link}">{link}</a></p>'
        "</body></html>"
    )
    mail.send_email(tos, "Solicitação de correção da candidatura", html, bcc=[user.email])
    return {
        "message": "correction requested",
        "email_sent": tos[0] if tos else "",
    }


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if not edict.accept_forms:
        raise HTTPException(404, "accept form is not configured for this edict")
    if sub.stats != "approved":
        raise HTTPException(400, "submission is not approved")
    if sub.accept_form_id:
        raise HTTPException(400, "accept form was already sent")
    name, email, resp, _mapped, _values = await subservice.candidate_identity(db, edict, sub)
    tos = []
    for address in (email, resp["email"] if resp else None):
        if address and address not in tos:
            tos.append(address)
    if not tos:
        raise HTTPException(400, "candidate email not available")
    accept_form_id = int(edict.accept_forms)
    form = await formsdb.get_form(accept_form_id)
    shared = await formsdb.create_shared(accept_form_id, edict.closed_date)
    response = await formsdb.create_response(
        accept_form_id, shared["id"], tos[0], (form or {}).get("version") or 1
    )
    sub.accept_form_id = response["id"]
    await db.commit()
    link = f"{settings.base_url}/form/{shared['token']}"
    deadline = edict.closed_date
    html = (
        "<html><body>"
        f"<p>Olá {name},</p>"
        "<p>Parabéns! Sua candidatura foi aprovada. Para confirmar sua aceitação, "
        "preencha o formulário de aceite até " + str(deadline) + ".</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<hr/>"
        "<p>Dear " + name + ",</p>"
        "<p>Congratulations! Your application has been approved. To confirm your "
        "acceptance, please fill in the acceptance form by " + str(deadline) + ".</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "</body></html>"
    )
    cc = []
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor and advisor.email:
            cc.append(advisor.email)
    mail.send_email(tos, "Formulário de aceite / Acceptance form", html, cc=cc)
    return {"message": "accept form sent", "email_sent": tos[0]}


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_of(db, sub)
    if sub.stats != "approved":
        raise HTTPException(400, "submission is not approved")
    if sub.letter_sent:
        raise HTTPException(400, "letter was already sent")
    name, email, resp, mapped, _values = await subservice.candidate_identity(db, edict, sub)
    tos = []
    for address in (email, resp["email"] if resp else None):
        if address and address not in tos:
            tos.append(address)
    if not tos:
        raise HTTPException(400, "candidate email not available")
    advisor_name = ""
    cc = []
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor:
            advisor_name = advisor.name
            if advisor.email:
                cc.append(advisor.email)
    semester = sub.entry_semester or (mapped.get("research") or {}).get("semester") or ""
    html = (
        "<html><body>"
        "<h2>Carta de Aceitação</h2>"
        f"<p>Prezado(a) {name},</p>"
        "<p>Temos o prazer de informar que sua candidatura ao programa de "
        "pós-graduação foi <b>aprovada</b>.</p>"
        f"<p>Orientador(a): {advisor_name}</p>"
        f"<p>Ingresso: {semester} Ano: {edict.year}</p>"
        "<p>Atenciosamente,</p>"
        '<img src="cid:signature" alt="assinatura"/>'
        "</body></html>"
    )
    mail.send_email(
        tos,
        "Carta de Aceitação / Acceptance Letter",
        html,
        cc=cc,
        image_path="data/signature.png",
    )
    sub.letter_sent = True
    await db.commit()
    return {"message": "acceptance letter sent", "email_sent": tos[0]}
