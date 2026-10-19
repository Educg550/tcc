import base64
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user, require_admin
from config import settings
from database import get_db
from models import Comment, Edict, Favorite, Label, PrivateNote, Submission, SubmissionView, User
from schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelInputSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
import services.forms_service as forms_service
import services.mailer as mailer
import services.submissions_service as submissions_service

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")


async def _get_submission(db: AsyncSession, submission_id: int) -> Submission:
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


async def _get_edict_for(db: AsyncSession, sub: Submission) -> Edict:
    edict = await db.get(Edict, sub.edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def _require_phase(edict: Edict, phase: str):
    if edict.phase != phase:
        raise HTTPException(status_code=400, detail=f"Operation only allowed in phase {phase}")


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    context = await submissions_service.load_submission_context(db, edict, sub)
    summary = await submissions_service.build_submission_item(db, edict, sub, user, context)
    response = context["response"]
    summary["access_email"] = response["email"] if response else ""
    summary["recommendations"] = await submissions_service.build_recommendations(sub)
    summary["interest"] = await submissions_service.user_bidding(db, sub, user.id)
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.submission_id == sub.id, PrivateNote.user_id == user.id
            )
        )
    ).scalars().first()
    summary["private_note"] = note.note if note else ""
    summary["entry_semester"] = sub.entry_semester or summary["research"].get("semester", "")
    summary["letter_sent"] = sub.letter_sent
    if include_comments:
        comments = (
            await db.execute(
                select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
            )
        ).scalars().all()
        summary["comments"] = [
            {
                "id": c.id,
                "user": {"id": c.user_id, "name": (await db.get(User, c.user_id)).name},
                "submission_id": c.submission_id,
                "comment": c.comment,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in comments
        ]
    submission_form = await submissions_service.build_submission_form(sub, context)
    return {"summary": summary, "submission_form": submission_form}


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    response = await forms_service.get_response(sub.candidate_form_id)
    if response is None:
        raise HTTPException(status_code=404, detail="File not found")
    fields = await forms_service.get_form_fields(response["form_id"])
    answers = (await forms_service.get_answers([response["id"]])).get(response["id"], {})
    target = None
    for field in fields:
        labels = field["label"] if isinstance(field["label"], dict) else {}
        names = {field["name"], labels.get("pt"), labels.get("en")}
        if label in names:
            target = field
            break
    if target is None:
        raise HTTPException(status_code=404, detail="File not found")
    value = answers.get(target["id"])
    if value != filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = submissions_service.find_upload(filename, str(response["token"]))
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    _require_phase(edict, "avaliacao")
    now = datetime.now(timezone.utc)
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=payload.comment,
        created_at=payload.created_at or now,
        updated_at=payload.updated_at or payload.created_at or now,
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    events = []
    comments = (
        await db.execute(
            select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
        )
    ).scalars().all()
    for c in comments:
        author = await db.get(User, c.user_id)
        events.append(
            {
                "user": {"id": c.user_id, "name": author.name if author else ""},
                "text": c.comment,
                "type": "comment",
                "created_at": c.created_at,
            }
        )
    response = await forms_service.get_response(sub.candidate_form_id)
    if response is not None:
        if response["submitted_at"] is not None:
            events.append(
                {
                    "user": None,
                    "text": "Candidatura enviada",
                    "type": "submission",
                    "created_at": response["submitted_at"],
                }
            )
    for rec in await submissions_service.build_recommendations(sub):
        events.append(
            {
                "user": None,
                "text": f"Recomendação recebida de {rec['email']}",
                "type": "recommendation",
                "created_at": rec["submitted_at"],
            }
        )
    if sub.accept_form_id:
        accept = await submissions_service.accept_status(sub)
        if accept["sent"] == "replied":
            events.append(
                {
                    "user": None,
                    "text": "Aceite respondido",
                    "type": "accept",
                    "created_at": accept["submitted_at"],
                }
            )
        else:
            events.append(
                {
                    "user": None,
                    "text": "Formulário de aceite enviado",
                    "type": "accept",
                    "created_at": sub.updated_at,
                }
            )
    events.sort(key=lambda e: e["created_at"] or datetime.min.replace(tzinfo=timezone.utc))
    return events


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this comment")
    await db.delete(comment)
    await db.commit()


@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    _require_phase(edict, "avaliacao")
    existing = await db.get(Favorite, {"user_id": user.id, "submission_id": sub.id})
    if existing is not None:
        raise HTTPException(status_code=409, detail="Favorite already exists")
    db.add(Favorite(user_id=user.id, submission_id=sub.id, created_at=datetime.now(timezone.utc)))
    await db.commit()
    return "Favorite created successfully"


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    existing = await db.get(Favorite, {"user_id": user.id, "submission_id": sub.id})
    if existing is None:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.delete(existing)
    await db.commit()


@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    _require_phase(edict, "avaliacao")
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            select(Label)
            .where(Label.user_id == user.id, Label.context_type == "candidate")
            .order_by(Label.id)
        )
    ).scalars().all()
    seen = set()
    labels = []
    for row in rows:
        if row.label in seen:
            continue
        seen.add(row.label)
        labels.append({"id": row.id, "label": row.label, "color": row.color})
    return {"labels": labels}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if label.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this label")
    await db.delete(label)
    await db.commit()


@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    _require_phase(edict, "avaliacao")
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.submission_id == sub.id, PrivateNote.user_id == user.id
            )
        )
    ).scalars().first()
    now = datetime.now(timezone.utc)
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
    return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
async def register_view(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    now = datetime.now(timezone.utc)
    today = now.astimezone(SP_TZ).date()
    views = (
        await db.execute(
            select(SubmissionView).where(
                SubmissionView.submission_id == sub.id, SubmissionView.user_id == user.id
            )
        )
    ).scalars().all()
    for view in views:
        if view.created_at and view.created_at.astimezone(SP_TZ).date() == today:
            view.updated_at = now
            await db.commit()
            return {"message": "View already registered today"}
    db.add(SubmissionView(user_id=user.id, submission_id=sub.id, created_at=now, updated_at=now))
    await db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
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
                "user": {"id": view.user_id, "name": author.name if author else ""},
                "created_at": view.created_at,
                "updated_at": view.updated_at,
            }
        )
    return out


@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict is closed")
    if payload.stats == "approved":
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(status_code=400, detail="Approval requires exactly one advisor")
        advisor = await db.get(User, payload.user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=400, detail="Advisor not found")
        sub.advisor_id = advisor.id
    sub.stats = payload.stats
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return payload.stats


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    from auth import ADMIN_ROLES

    target_id = payload.user_id if (payload.user_id and user.role in ADMIN_ROLES) else user.id
    existing = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id,
                Label.user_id == target_id,
                Label.context_type == "bidding",
            )
        )
    ).scalars().first()
    if existing is None:
        db.add(
            Label(
                user_id=target_id,
                submission_id=sub.id,
                label=payload.bidding,
                color="",
                context_type="bidding",
            )
        )
    else:
        existing.label = payload.bidding
    await db.commit()
    return payload.bidding


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    normalized = payload.semester.strip().lower()
    if normalized in ("primeiro", "first", "primeiro semestre"):
        value = "Primeiro semestre."
    elif normalized in ("segundo", "second", "segundo semestre"):
        value = "Segundo semestre."
    else:
        value = payload.semester
    sub.entry_semester = value
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return value


@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    _require_phase(edict, "homologacao")
    response = await forms_service.get_response(sub.candidate_form_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    await forms_service.reopen_response(response["id"])
    link = f"{settings.base_url.rstrip('/')}/form/{response['token']}"
    body = (
        f"Prezado(a) candidato(a),\n\n"
        f"Sua candidatura precisa de correção antes da homologação.\n\n"
        f"Motivo: {payload.text}\n\n"
        f"Acesse o formulário para corrigir e reenviar: {link}\n"
    )
    email_sent = mailer.send_email(
        subject="Solicitação de correção da candidatura",
        body=body,
        to=response["email"],
        bcc=user.email,
    )
    return {
        "message": "Resubmission requested successfully",
        "email_sent": email_sent,
    }


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    if not edict.accept_forms:
        raise HTTPException(status_code=404, detail="Accept form not configured")
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub.accept_form_id:
        raise HTTPException(status_code=400, detail="Accept form already sent")
    response = await forms_service.get_response(sub.candidate_form_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    accept_form_id = int(edict.accept_forms)
    form = await forms_service.get_form(accept_form_id)
    if form is None:
        raise HTTPException(status_code=404, detail="Accept form not found")
    shared = await forms_service.create_shared(accept_form_id, edict.closed_date)
    created = await forms_service.create_response(
        accept_form_id, shared["id"], response["email"], form["version"]
    )
    sub.accept_form_id = created["id"]
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()

    context = await submissions_service.load_submission_context(db, edict, sub)
    name = context["values"].get("name") or ""
    link = f"{settings.base_url.rstrip('/')}/form/{shared['token']}"
    deadline = edict.closed_date.strftime("%d/%m/%Y") if edict.closed_date else ""
    body_pt = (
        f"Prezado(a) {name},\n\n"
        f"Parabéns! Sua candidatura foi aprovada. Para confirmar seu aceite, preencha o "
        f"formulário de aceite até {deadline} através do link: {link}\n"
    )
    body_en = (
        f"Dear {name},\n\n"
        f"Congratulations! Your application has been approved. To confirm your acceptance, "
        f"please fill the acceptance form by {deadline} at: {link}\n"
    )
    cc = None
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor:
            cc = advisor.email
    email_sent = mailer.send_email(
        subject="Formulário de aceite / Acceptance form",
        body=body_pt + "\n--\n" + body_en,
        to=response["email"],
        cc=cc,
    )
    return {
        "message": "Accept form sent successfully",
        "email_sent": email_sent,
    }


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict_for(db, sub)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Letter already sent")
    response = await forms_service.get_response(sub.candidate_form_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    context = await submissions_service.load_submission_context(db, edict, sub)
    name = context["values"].get("name") or ""
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    advisor_name = advisor.name if advisor else ""
    semester = sub.entry_semester or ""
    year = edict.year
    signature_html = ""
    try:
        with open("data/signature.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        signature_html = f'<p><img src="data:image/png;base64,{encoded}" alt="Assinatura"/></p>'
    except OSError:
        pass
    html = (
        f"<html><body>"
        f"<p>Prezado(a) {name},</p>"
        f"<p>É com satisfação que comunicamos a aprovação de sua candidatura ao programa de "
        f"pós-graduação. Orientador(a): <b>{advisor_name}</b>. Ingresso: {semester} de {year}.</p>"
        f"<p>Atenciosamente,</p>"
        f"{signature_html}"
        f"</body></html>"
    )
    cc = advisor.email if advisor else None
    email_sent = mailer.send_email(
        subject="Carta de aceite",
        body=f"Prezado(a) {name}, sua candidatura foi aprovada. Orientador(a): {advisor_name}. "
        f"Ingresso: {semester} de {year}.",
        to=response["email"],
        cc=cc,
        html=html,
    )
    sub.letter_sent = True
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "message": "Acceptance letter sent successfully",
        "email_sent": email_sent,
    }
