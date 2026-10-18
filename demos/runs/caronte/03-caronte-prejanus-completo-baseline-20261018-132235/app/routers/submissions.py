"""Submission routes: details, evaluation, selection and communication."""
import os
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from .. import formsdb
from ..config import settings
from ..db import get_db
from ..mailing import send_email
from ..models import (
    Bidding,
    Comment,
    Edict,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    SubmissionAdvisor,
    SubmissionView,
    User,
)
from ..schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelSchemaInput,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from ..security import require_admin, require_user
from ..summary import (
    answer_values,
    build_item,
    candidate_answer,
    recommendations,
)

router = APIRouter(tags=["submissions"])

try:
    TZ_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
except Exception:  # pragma: no cover - container without tzdata
    TZ_SAO_PAULO = None

BIDDING_VALUES = {
    "decline",
    "available",
    "interested",
    "agreed",
    "interested_scholarship",
    "",
}


def get_submission_or_404(db, submission_id: int) -> Submission:
    sub = db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


def _require_phase(db, sub: Submission, phase: str):
    edict = db.get(Edict, sub.edict_id)
    if edict is None or edict.phase != phase:
        raise HTTPException(
            status_code=400,
            detail=f"Operation only allowed in phase {phase}",
        )
    return edict


def _advisor(db, submission_id: int) -> User | None:
    advisor_id = db.execute(
        select(SubmissionAdvisor.user_id).where(
            SubmissionAdvisor.submission_id == submission_id
        )
    ).scalar_one_or_none()
    return db.get(User, advisor_id) if advisor_id else None


# --- details ----------------------------------------------------------------

@router.get("/submissions/{submission_id}")
def get_details(
    submission_id: int,
    include_comments: bool = False,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    item = build_item(db, edict, sub, user)

    note = (
        db.query(PrivateNote)
        .filter(
            PrivateNote.user_id == user.id,
            PrivateNote.submission_id == sub.id,
        )
        .first()
    )
    bidding = (
        db.query(Bidding)
        .filter(Bidding.user_id == user.id, Bidding.submission_id == sub.id)
        .first()
    )
    summary = dict(item)
    summary.update(
        {
            "private_note": note.note if note else "",
            "bidding": bidding.bidding if bidding else "",
            "semester": sub.entry_semester or "",
            "letter_sent": sub.letter_sent,
            "recommendations": recommendations(edict, sub),
        }
    )

    answer = candidate_answer(edict, sub)
    values = answer_values(answer)
    sections = formsdb.get_sections(int(edict.candidate_form_id), sub.version)
    submission_form = [
        {
            "id": s.get("id"),
            "name": s.get("name"),
            "label": s.get("label") or s.get("name"),
            "position": s.get("position"),
            "fields": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "label": f.get("label") or f.get("name"),
                    "type": f.get("type"),
                    "prefix": f.get("prefix"),
                    "position": f.get("position"),
                    "value": values.get((s.get("id"), f.get("id"))),
                }
                for f in formsdb.get_fields(s.get("id"))
            ],
        }
        for s in sections
    ]
    result = {"summary": summary, "submission_form": submission_form}
    if include_comments:
        result["comments"] = _comments_list(db, sub)
    return result


# --- comments and activity --------------------------------------------------

def _comments_list(db, sub: Submission) -> list[dict]:
    comments = (
        db.query(Comment)
        .filter(Comment.submission_id == sub.id)
        .order_by(Comment.created_at)
        .all()
    )
    result = []
    for c in comments:
        author = db.get(User, c.user_id)
        result.append(
            {
                "id": c.id,
                "author": author.name if author else "",
                "text": c.comment,
                "type": "comment",
                "created_at": c.created_at,
            }
        )
    return result


def _activity_list(db, sub: Submission, edict: Edict) -> list[dict]:
    events = _comments_list(db, sub)
    answer = candidate_answer(edict, sub)
    if answer and answer.get("submitted_at"):
        events.append(
            {
                "author": sub.name,
                "text": "Candidatura finalizada",
                "type": "submission",
                "created_at": answer.get("submitted_at"),
            }
        )
    for rec in recommendations(edict, sub):
        events.append(
            {
                "author": rec.get("email") or "",
                "text": "Recomendação recebida",
                "type": "recommendation",
                "created_at": rec.get("submitted_at"),
            }
        )
    if sub.accept_form_id is not None:
        accept_answer = formsdb.get_answer(sub.accept_form_id)
        if accept_answer and accept_answer.get("submitted_at"):
            events.append(
                {
                    "author": sub.name,
                    "text": "Resposta de aceite enviada",
                    "type": "accept",
                    "created_at": accept_answer.get("submitted_at"),
                }
            )
    events.sort(key=lambda e: e.get("created_at") or datetime.min)
    return events


@router.post("/submissions/{submission_id}/comments")
def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    now = datetime.utcnow()
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=payload.comment,
        created_at=payload.created_at or now,
        updated_at=payload.updated_at or payload.created_at or now,
    )
    db.add(comment)
    db.commit()
    return {
        "id": comment.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": sub.id,
        "comment": comment.comment,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


@router.get("/submissions/{submission_id}/comments")
def get_all_comments(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    return _activity_list(db, sub, edict)


@router.delete("/submissions/comments/{comment_id}", status_code=204)
def remove_comment(
    comment_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(comment)
    db.commit()


# --- favorites ---------------------------------------------------------------

@router.post("/submissions/{submission_id}/favorites", status_code=201)
def create_favorite(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id, Favorite.submission_id == sub.id
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Favorite already exists")
    db.add(Favorite(user_id=user.id, submission_id=sub.id,
                    created_at=datetime.utcnow()))
    db.commit()
    return "Favorite created successfully"


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
def remove_favorite(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    get_submission_or_404(db, submission_id)
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id, Favorite.submission_id == submission_id
        )
        .first()
    )
    if favorite is None:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()


# --- labels ------------------------------------------------------------------

@router.post("/submissions/{submission_id}/labels")
def add_label(
    submission_id: int,
    payload: LabelSchemaInput,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    label = Label(
        user_id=user.id,
        submission_id=sub.id,
        label=payload.label,
        color=payload.color,
        context="candidate",
        created_at=datetime.utcnow(),
    )
    db.add(label)
    db.flush()
    # Refresh the color of the same author/label in other submissions,
    # preserving other authors and bidding-context labels.
    others = (
        db.query(Label)
        .filter(
            Label.user_id == user.id,
            Label.label == payload.label,
            Label.context == "candidate",
            Label.id != label.id,
        )
        .all()
    )
    for other in others:
        other.color = payload.color
    db.commit()
    return {
        "id": label.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": sub.id,
        "label": label.label,
    }


@router.get("/submissions/{submission_id}/labels")
def get_label(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    get_submission_or_404(db, submission_id)
    labels = (
        db.query(Label)
        .filter(Label.user_id == user.id)
        .order_by(Label.id)
        .all()
    )
    seen: dict[str, dict] = {}
    for label in labels:
        if label.label not in seen:
            seen[label.label] = {
                "id": label.id,
                "label": label.label,
                "color": label.color,
            }
    return {"labels": list(seen.values())}


@router.delete("/submissions/label/{label_id}", status_code=204)
def remove_label(
    label_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    label = db.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if label.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(label)
    db.commit()


# --- private notes -----------------------------------------------------------

@router.post("/submissions/{submission_id}/private_notes")
def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    note = (
        db.query(PrivateNote)
        .filter(
            PrivateNote.user_id == user.id,
            PrivateNote.submission_id == sub.id,
        )
        .first()
    )
    now = datetime.utcnow()
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
    db.commit()
    return {"note": note.note}


# --- views -------------------------------------------------------------------

@router.post("/submissions/{submission_id}/view")
def register_view(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    now = datetime.now(TZ_SAO_PAULO) if TZ_SAO_PAULO else datetime.utcnow()
    today = now.date()
    existing = (
        db.query(SubmissionView)
        .filter(
            SubmissionView.user_id == user.id,
            SubmissionView.submission_id == sub.id,
            SubmissionView.view_date == today,
        )
        .first()
    )
    if existing is None:
        db.add(
            SubmissionView(
                user_id=user.id,
                submission_id=sub.id,
                view_date=today,
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
def get_submission_views(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    get_submission_or_404(db, submission_id)
    views = (
        db.query(SubmissionView)
        .filter(SubmissionView.submission_id == submission_id)
        .order_by(SubmissionView.id)
        .all()
    )
    return [
        {
            "user": (
                {"id": u.id, "name": u.name}
                if (u := db.get(User, v.user_id))
                else None
            ),
            "date": v.view_date,
        }
        for v in views
    ]


# --- selection and bidding ---------------------------------------------------

@router.post("/submissions/{submission_id}/select")
def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    if edict is None or not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict is closed")
    if payload.stats == "approved":
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="Approval requires exactly one advisor",
            )
        advisor = db.get(User, payload.user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=400, detail="Advisor not found")
        existing = (
            db.query(SubmissionAdvisor)
            .filter(SubmissionAdvisor.submission_id == sub.id)
            .first()
        )
        if existing is not None:
            existing.user_id = advisor.id
        else:
            db.add(
                SubmissionAdvisor(
                    submission_id=sub.id,
                    user_id=advisor.id,
                    created_at=datetime.utcnow(),
                )
            )
    sub.stats = payload.stats
    db.commit()
    return f"Submission marked as {payload.stats}"


@router.post("/submissions/{submission_id}/bidding")
def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    if payload.bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Invalid bidding")
    target_id = payload.user_id if payload.user_id else user.id
    if payload.user_id and payload.user_id != user.id and user.role not in (
        "administrator",
        "secretary",
        "coordinator",
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    bidding = (
        db.query(Bidding)
        .filter(
            Bidding.user_id == target_id, Bidding.submission_id == sub.id
        )
        .first()
    )
    now = datetime.utcnow()
    if bidding is None:
        bidding = Bidding(
            user_id=target_id,
            submission_id=sub.id,
            bidding=payload.bidding,
            created_at=now,
            updated_at=now,
        )
        db.add(bidding)
    else:
        bidding.bidding = payload.bidding
        bidding.updated_at = now
    db.commit()
    return f"Bidding updated to {payload.bidding}"


@router.post("/submissions/{submission_id}/entry-semester")
def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    semester = payload.semester.strip()
    normalized = semester.lower()
    if normalized in ("primeiro", "first", "primeiro semestre"):
        sub.entry_semester = "Primeiro semestre."
    elif normalized in ("segundo", "second", "segundo semestre"):
        sub.entry_semester = "Segundo semestre."
    else:
        sub.entry_semester = payload.semester
    db.commit()
    return sub.entry_semester


# --- files -------------------------------------------------------------------

@router.get("/submissions/{submission_id}/files/{label}/{filename}")
def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    answer = candidate_answer(edict, sub)
    values = answer_values(answer)
    found = None
    for section in formsdb.get_sections(int(edict.candidate_form_id), sub.version):
        for field in formsdb.get_fields(section.get("id")):
            field_label = field.get("label") or field.get("name")
            if field_label == label:
                value = values.get((section.get("id"), field.get("id")))
                if value:
                    found = str(value)
                    break
        if found:
            break
    if found is None:
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.basename(found) != filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = Path(settings.UPLOADS_DIR) / found
    if not path.exists():
        matches = [
            p
            for p in Path(settings.UPLOADS_DIR).rglob(os.path.basename(found))
            if p.is_file()
        ]
        if not matches:
            raise HTTPException(status_code=404, detail="File not found")
        path = matches[0]
    # Never serve files outside the uploads directory.
    uploads_root = Path(settings.UPLOADS_DIR).resolve()
    if not str(path.resolve()).startswith(str(uploads_root)):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        str(path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- e-mail communication ----------------------------------------------------

def _signature_images() -> dict[str, bytes]:
    images = {}
    sig = Path(settings.SIGNATURE_FILE)
    if sig.exists():
        images["signature"] = sig.read_bytes()
    return images


@router.post("/submissions/{submission_id}/send-accept")
def send_accept_forms(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission not approved")
    if not edict.accept_form_id:
        raise HTTPException(status_code=404, detail="Accept form not configured")
    if sub.accept_form_id is not None:
        raise HTTPException(status_code=400, detail="Accept already sent")

    token = uuid.uuid4().hex
    formsdb.create_share(
        int(edict.accept_form_id),
        token,
        expires_at=edict.closed_date,
        single_answer=True,
        private=True,
    )
    answer_id = formsdb.create_answer(
        int(edict.accept_form_id), sub.email, token
    )
    sub.accept_form_id = answer_id
    db.commit()

    advisor = _advisor(db, sub.id)
    deadline = edict.closed_date.strftime("%d/%m/%Y") if edict.closed_date else ""
    link = f"{settings.BASE_URL.rstrip('/')}/form/{token}"
    html = (
        f"<p>Prezado(a) {sub.name},</p>"
        f"<p>Parabéns! Sua candidatura foi aprovada no edital "
        f"{edict.title}.</p>"
        f"<p>Dear {sub.name},</p>"
        f"<p>Congratulations! Your application was approved.</p>"
        f"<p>Prazo / Deadline: {deadline}</p>"
        f"<p>Formulário de aceite / Accept form: "
        f'<a href="{link}">{link}</a></p>'
    )
    send_email(
        to=[sub.email],
        subject="Formulário de aceite / Accept form",
        html=html,
        cc=[advisor.email] if advisor and advisor.email else None,
    )
    return {
        "message": "Accept form sent successfully",
        "email_sent": sub.email,
    }


@router.post("/submissions/{submission_id}/send-letter")
def send_accept_letter(
    submission_id: int,
    user=Depends(require_user),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = db.get(Edict, sub.edict_id)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Submission not approved")
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Letter already sent")

    advisor = _advisor(db, sub.id)
    semester = sub.entry_semester or ""
    html = (
        f"<p>Prezado(a) {sub.name},</p>"
        "<p>Communicamos que sua candidatura foi aprovada no programa de "
        f"pós-graduação referente ao edital {edict.title}.</p>"
        f"<p>Orientador(a): {advisor.name if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict.year}</p>"
        '<img src="cid:signature" alt="Assinatura"/>'
    )
    send_email(
        to=[sub.email],
        subject="Carta de aceite / Acceptance letter",
        html=html,
        cc=[advisor.email] if advisor and advisor.email else None,
        images=_signature_images(),
    )
    sub.letter_sent = True
    db.commit()
    return {
        "message": "Accept letter sent successfully",
        "email_sent": sub.email,
    }


@router.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    sub = get_submission_or_404(db, submission_id)
    edict = _require_phase(db, sub, "homologacao")
    answer = candidate_answer(edict, sub)
    if answer is None:
        raise HTTPException(status_code=404, detail="Submission answer not found")
    formsdb.reopen_answer(answer.get("id"))
    token = answer.get("token") or sub.token
    link = f"{settings.BASE_URL.rstrip('/')}/form/{token}"
    html = (
        f"<p>Prezado(a) {sub.name},</p>"
        "<p>Sua candidatura precisa de correções antes de seguir com o "
        "processo seletivo.</p>"
        f"<p>Motivo: {payload.text}</p>"
        f'<p>Link para correção: <a href="{link}">{link}</a></p>'
    )
    send_email(
        to=[sub.email],
        subject="Solicitação de correção da candidatura",
        html=html,
        bcc=[user.email] if user.email else None,
    )
    return {
        "message": "Resubmission requested successfully",
        "email_sent": sub.email,
    }