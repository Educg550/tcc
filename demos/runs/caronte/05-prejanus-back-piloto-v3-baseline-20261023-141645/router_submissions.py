import base64
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

import forms_service as forms
import submissions_service as service
from auth import ADMIN_ROLES, current_user, require_admin
from config import settings
from db import PrejanusSession
from mailer import send_email

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")


class CommentBody(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LabelBody(BaseModel):
    label: str
    color: str


class PrivateNoteBody(BaseModel):
    note: str


class RequestReesendBody(BaseModel):
    text: str


class StatsBody(BaseModel):
    user_ids: list[int] | None
    stats: str


class BiddingBody(BaseModel):
    bidding: str
    user_id: int | None = None


class EntrySemesterBody(BaseModel):
    semester: str


async def _get_submission_or_404(submission_id: int) -> dict:
    sub = await service.get_submission(submission_id)
    if not sub:
        raise HTTPException(404, "Submission not found")
    return sub


async def _get_edict_of(sub: dict) -> dict:
    edict = await service.get_edict(sub["edict_id"])
    if not edict:
        raise HTTPException(404, "Edict not found")
    return edict


def _require_phase(edict: dict, phase: str):
    if edict["phase"] != phase:
        raise HTTPException(400, f"Operation only allowed in phase {phase}")


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int, include_comments: bool = False, user=Depends(current_user)
):
    sub = await _get_submission_or_404(submission_id)
    return await service.build_detail(sub, user["id"], include_comments)


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(submission_id: int, label: str, filename: str, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    path = await service.find_submission_file(sub, label, filename)
    if not path:
        raise HTTPException(404, "File not found")
    content = path.read_bytes()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- comments ---

@router.post("/submissions/{submission_id}/comments")
async def add_comment(submission_id: int, body: CommentBody, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text(
                    "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
                    "values (:u, :s, :c, coalesce(:ca, now()), coalesce(:ua, now())) returning *"
                ),
                {
                    "u": user["id"],
                    "s": submission_id,
                    "c": body.comment,
                    "ca": body.created_at,
                    "ua": body.updated_at,
                },
            )
        ).mappings().first()
        await db.commit()
    return {
        "id": row.id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": row.comment,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.get("/submissions/{submission_id}/comments")
async def get_activity(submission_id: int, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    events = []
    for c in await service.get_comments(submission_id):
        events.append(
            {
                "user": c["user"],
                "text": c["comment"],
                "type": "comment",
                "created_at": c["created_at"],
            }
        )
    if sub["created_at"]:
        events.append(
            {
                "user": None,
                "text": "Candidatura submetida",
                "type": "submission",
                "created_at": sub["created_at"],
            }
        )
    item = await service.build_submission_item(sub, user["id"])
    for rec in await service.get_recommendations(edict, sub, item["name"], item["email"]):
        events.append(
            {
                "user": {"id": None, "name": rec.get("email", "")},
                "text": "Recomendação submetida",
                "type": "recommendation",
                "created_at": rec.get("submitted_at"),
            }
        )
    accept = await service.build_accept(sub)
    if accept["sent"] == "replied":
        events.append(
            {
                "user": None,
                "text": "Aceite respondido",
                "type": "accept",
                "created_at": accept["submitted_at"],
            }
        )
    events.sort(key=lambda e: e["created_at"] or datetime.min)
    return events


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user=Depends(current_user)):
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text("select id, user_id from comment where id = :i"), {"i": comment_id}
            )
        ).first()
    if not row:
        raise HTTPException(404, "Comment not found")
    if row.user_id != user["id"]:
        raise HTTPException(403, "Only the author can delete this comment")
    async with PrejanusSession() as db:
        await db.execute(text("delete from comment where id = :i"), {"i": comment_id})
        await db.commit()
    return Response(status_code=204)


# --- favorites ---

@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as db:
        existing = (
            await db.execute(
                text(
                    "select 1 from favorites where user_id = :u and submission_id = :s"
                ),
                {"u": user["id"], "s": submission_id},
            )
        ).first()
        if existing:
            raise HTTPException(409, "Favorite already exists")
        await db.execute(
            text(
                "insert into favorites (user_id, submission_id, created_at) "
                "values (:u, :s, now())"
            ),
            {"u": user["id"], "s": submission_id},
        )
        await db.commit()
    return Response(status_code=201)


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(submission_id: int, user=Depends(current_user)):
    async with PrejanusSession() as db:
        existing = (
            await db.execute(
                text(
                    "select 1 from favorites where user_id = :u and submission_id = :s"
                ),
                {"u": user["id"], "s": submission_id},
            )
        ).first()
        if not existing:
            raise HTTPException(404, "Favorite not found")
        await db.execute(
            text(
                "delete from favorites where user_id = :u and submission_id = :s"
            ),
            {"u": user["id"], "s": submission_id},
        )
        await db.commit()
    return Response(status_code=204)


# --- labels ---

@router.post("/submissions/{submission_id}/labels")
async def add_label(submission_id: int, body: LabelBody, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "update labels set color = :c where user_id = :u and label = :l "
                "and context_type = 'candidate'"
            ),
            {"c": body.color, "u": user["id"], "l": body.label},
        )
        row = (
            await db.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color, context_type) "
                    "values (:u, :s, :l, :c, 'candidate') returning id"
                ),
                {"u": user["id"], "s": submission_id, "l": body.label, "c": body.color},
            )
        ).first()
        await db.commit()
        label_id = row.id
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": body.label,
    }


@router.get("/submissions/{submission_id}/labels")
async def get_labels(submission_id: int, user=Depends(current_user)):
    await _get_submission_or_404(submission_id)
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select distinct on (label) id, label, color from labels "
                    "where user_id = :u and context_type = 'candidate' order by label, id"
                ),
                {"u": user["id"]},
            )
        ).mappings().all()
    return {"labels": [dict(r) for r in rows]}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user=Depends(current_user)):
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text("select id, user_id from labels where id = :i"), {"i": label_id}
            )
        ).first()
    if not row:
        raise HTTPException(404, "Label not found")
    if row.user_id != user["id"]:
        raise HTTPException(403, "Only the author can delete this label")
    async with PrejanusSession() as db:
        await db.execute(text("delete from labels where id = :i"), {"i": label_id})
        await db.commit()
    return Response(status_code=204)


# --- private notes ---

@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(submission_id: int, body: PrivateNoteBody, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "insert into private_note (user_id, submission_id, note, created_at, updated_at) "
                "values (:u, :s, :n, now(), now()) "
                "on conflict (user_id, submission_id) do update set note = excluded.note, "
                "updated_at = now()"
            ),
            {"u": user["id"], "s": submission_id, "n": body.note},
        )
        await db.commit()
    return {"note": body.note}


# --- views ---

@router.post("/submissions/{submission_id}/view")
async def register_view(submission_id: int, user=Depends(current_user)):
    await _get_submission_or_404(submission_id)
    today = datetime.now(SP_TZ).date()
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select id, created_at from submission_view "
                    "where user_id = :u and submission_id = :s"
                ),
                {"u": user["id"], "s": submission_id},
            )
        ).all()
        found = False
        for r in rows:
            local_day = r.created_at.astimezone(SP_TZ).date() if r.created_at else None
            if local_day == today:
                await db.execute(
                    text("update submission_view set updated_at = now() where id = :i"),
                    {"i": r.id},
                )
                found = True
        if not found:
            await db.execute(
                text(
                    "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                    "values (:u, :s, now(), now())"
                ),
                {"u": user["id"], "s": submission_id},
            )
        await db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
async def get_views(submission_id: int, user=Depends(current_user)):
    await _get_submission_or_404(submission_id)
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select v.id, v.user_id, u.name, v.created_at, v.updated_at "
                    "from submission_view v join \"user\" u on v.user_id = u.id "
                    "where v.submission_id = :s order by v.created_at"
                ),
                {"s": submission_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


# --- selection ---

@router.post("/submissions/{submission_id}/select")
async def select_stats(submission_id: int, body: StatsBody, user=Depends(current_user)):
    require_admin(user)
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    if not edict["is_open"]:
        raise HTTPException(409, "Edict is closed")
    advisor_id = None
    if body.stats == "approved":
        if not body.user_ids or len(body.user_ids) != 1:
            raise HTTPException(422, "Approval requires exactly one advisor")
        advisor = await service.get_user(body.user_ids[0])
        if not advisor:
            raise HTTPException(422, "Advisor does not exist")
        advisor_id = advisor["id"]
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "update submission set stats = :s, advisor_id = coalesce(:a, advisor_id), "
                "updated_at = now() where id = :i"
            ),
            {"s": body.stats, "a": advisor_id, "i": submission_id},
        )
        await db.commit()
    return f"Submission status updated to {body.stats}"


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(submission_id: int, body: BiddingBody, user=Depends(current_user)):
    await _get_submission_or_404(submission_id)
    target_user = user["id"]
    if body.user_id is not None and user["role"] in ADMIN_ROLES:
        target_user = body.user_id
    async with PrejanusSession() as db:
        await db.execute(
            text(
                "delete from labels where user_id = :u and submission_id = :s "
                "and context_type = 'bidding'"
            ),
            {"u": target_user, "s": submission_id},
        )
        if body.bidding:
            await db.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color, context_type) "
                    "values (:u, :s, :l, '', 'bidding')"
                ),
                {"u": target_user, "s": submission_id, "l": body.bidding},
            )
        await db.commit()
    return f"Bidding updated to {body.bidding}"


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(submission_id: int, body: EntrySemesterBody, user=Depends(current_user)):
    await _get_submission_or_404(submission_id)
    low = body.semester.strip().lower()
    if low in ("primeiro", "first", "primeiro semestre", "1", "1o", "1º"):
        semester = "Primeiro semestre."
    elif low in ("segundo", "second", "segundo semestre", "2", "2o", "2º"):
        semester = "Segundo semestre."
    else:
        semester = body.semester
    async with PrejanusSession() as db:
        await db.execute(
            text("update submission set entry_semester = :s, updated_at = now() where id = :i"),
            {"s": semester, "i": submission_id},
        )
        await db.commit()
    return semester


# --- emails and Forms effects ---

@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(submission_id: int, body: RequestReesendBody, user=Depends(current_user)):
    require_admin(user)
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    _require_phase(edict, "homologacao")
    resp = await forms.get_response_row(sub["candidate_form_id"])
    if not resp:
        raise HTTPException(404, "Candidate response not found")
    await forms.reopen_response(sub["candidate_form_id"])
    link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua inscrição requer correção. Motivo: {body.text}</p>"
        f'<p>Acesse o formulário para corrigir e reenviar: <a href="{link}">{link}</a></p>'
    )
    send_email(
        resp["email"],
        "Solicitação de correção da candidatura",
        html,
        bcc=[user["email"]],
    )
    return {"message": "Resubmission requested", "email_sent": resp["email"]}


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await _get_edict_of(sub)
    if not edict.get("accept_forms"):
        raise HTTPException(404, "Accept form not configured for this edict")
    if sub["stats"] != "approved":
        raise HTTPException(400, "Submission is not approved")
    if sub.get("accept_form_id"):
        raise HTTPException(400, "Accept form already sent")
    accept_form_id = int(edict["accept_forms"])
    form = await forms.get_form(accept_form_id)
    if not form:
        raise HTTPException(404, "Accept form not found")
    item = await service.build_submission_item(sub, user["id"])
    candidate_email = item["email"]
    candidate_name = item["name"]
    shared_id, _ = await forms.create_shared(accept_form_id, edict["closed_date"])
    response_id, token = await forms.create_response(
        accept_form_id, shared_id, candidate_email, form["version"] or 1
    )
    async with PrejanusSession() as db:
        await db.execute(
            text("update submission set accept_form_id = :a, updated_at = now() where id = :i"),
            {"a": response_id, "i": submission_id},
        )
        await db.commit()
    link = f"{settings.base_url.rstrip('/')}/form/{token}"
    deadline = edict["closed_date"]
    html = (
        f"<p>Caro(a) {candidate_name},</p>"
        f"<p>Parabéns! Sua candidatura foi aprovada. Preencha o formulário de aceite "
        f"até {deadline}.</p>"
        f"<p>Dear {candidate_name}, congratulations! Your application was approved. "
        f"Please fill the acceptance form by {deadline}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
    )
    cc = []
    if sub.get("advisor_id"):
        advisor = await service.get_user(sub["advisor_id"])
        if advisor and advisor["email"]:
            cc.append(advisor["email"])
    send_email(candidate_email, "Formulário de aceite / Acceptance form", html, cc=cc)
    return {"message": "Accept form sent", "email_sent": candidate_email}


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user=Depends(current_user)):
    sub = await _get_submission_or_404(submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(400, "Submission is not approved")
    if sub.get("letter_sent"):
        raise HTTPException(400, "Letter already sent")
    edict = await _get_edict_of(sub)
    item = await service.build_submission_item(sub, user["id"])
    candidate_email = item["email"]
    advisor = await service.get_user(sub["advisor_id"]) if sub.get("advisor_id") else None
    semester = sub.get("entry_semester") or ""
    signature_html = ""
    sig = Path("data/signature.png")
    if sig.exists():
        b64 = base64.b64encode(sig.read_bytes()).decode()
        signature_html = f'<p><img src="data:image/png;base64,{b64}" alt="Assinatura"/></p>'
    html = (
        f"<h2>Carta de Aceitação</h2>"
        f"<p>Prezado(a) {item['name']},</p>"
        f"<p>Informamos que sua candidatura ao programa de pós-graduação foi aprovada.</p>"
        f"<p>Identificação: {item['name']} ({candidate_email})</p>"
        f"<p>Orientador: {advisor['name'] if advisor else ''}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict['year']}</p>"
        f"{signature_html}"
    )
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    send_email(candidate_email, "Carta de Aceitação", html, cc=cc)
    async with PrejanusSession() as db:
        await db.execute(
            text("update submission set letter_sent = true, updated_at = now() where id = :i"),
            {"i": submission_id},
        )
        await db.commit()
    return {"message": "Acceptance letter sent", "email_sent": candidate_email}
