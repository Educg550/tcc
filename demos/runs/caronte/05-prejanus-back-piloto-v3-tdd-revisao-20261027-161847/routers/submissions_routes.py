import os
from datetime import date, datetime
from enum import Enum
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text

from auth import ADMIN_ROLES, current_user, require_admin
from config import settings
from database import Session
from mailer import send_email
from services import forms_service as forms
from services.submissions_service import (
    advisor_json,
    candidate_payload,
    get_edict,
    get_submission,
    iso,
    submission_form,
    submission_summary,
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


class StatsEnum(str, Enum):
    approved = "approved"
    refused = "refused"
    underreview = "underreview"
    waitlist = "waitlist"


class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: StatsEnum


class BiddingEnum(str, Enum):
    decline = "decline"
    available = "available"
    interested = "interested"
    agreed = "agreed"
    interested_scholarship = "interested_scholarship"
    empty = ""


class BiddingSchema(BaseModel):
    bidding: BiddingEnum
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


def _require_submission(submission_id):
    sub = get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


def _require_phase(sub, phase):
    edict = get_edict(sub["edict_id"])
    if not edict or edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Operation only allowed in phase {phase}")
    return edict


def _user_name(user_id):
    with Session() as s:
        row = s.execute(
            text('select id, name from "user" where id = :i'), {"i": user_id}
        ).mappings().first()
    return dict(row) if row else None


def _comments_json(submission_id):
    with Session() as s:
        rows = s.execute(
            text("select * from comment where submission_id = :s order by created_at, id"),
            {"s": submission_id},
        ).mappings().all()
    out = []
    for r in rows:
        author = _user_name(r["user_id"])
        out.append(
            {
                "id": r["id"],
                "user": author,
                "submission_id": r["submission_id"],
                "comment": r["comment"],
                "text": r["comment"],
                "created_at": iso(r["created_at"]),
                "updated_at": iso(r["updated_at"]),
            }
        )
    return out


@router.get("/submissions/{submission_id}")
def get_details(submission_id: int, include_comments: bool = False, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    edict = get_edict(sub["edict_id"])
    detail = {
        "summary": submission_summary(sub, edict, user["id"]),
        "submission_form": submission_form(sub),
    }
    if include_comments:
        detail["comments"] = _comments_json(submission_id)
    return detail


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
def get_file(submission_id: int, label: str, filename: str, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    resp = forms.get_response(sub["candidate_form_id"])
    if not resp:
        raise HTTPException(status_code=404, detail="File not found")
    values = {r["field_id"]: r["value"] for r in forms.get_response_values(sub["candidate_form_id"])}
    matched = False
    for sec in forms.select_sections(resp["form_id"], version=sub["candidate_form_version"]):
        for f in forms.get_fields(sec["id"]):
            if f["name"] == label and values.get(f["id"]) == filename:
                matched = True
    if not matched:
        raise HTTPException(status_code=404, detail="File not found")
    path = os.path.realpath(os.path.join(settings.uploads_dir, filename))
    if not path.startswith(os.path.realpath(settings.uploads_dir)) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/submissions/{submission_id}/comments")
def add_comment(submission_id: int, payload: CommentSchema, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    _require_phase(sub, "avaliacao")
    now = datetime.now()
    with Session() as s:
        comment_id = s.execute(
            text(
                "insert into comment (user_id, submission_id, comment, created_at, updated_at)"
                " values (:u, :s, :c, :cr, :up) returning id"
            ),
            {
                "u": user["id"],
                "s": submission_id,
                "c": payload.comment,
                "cr": payload.created_at or now,
                "up": payload.updated_at or payload.created_at or now,
            },
        ).scalar_one()
        s.commit()
    return {
        "id": comment_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": payload.comment,
        "created_at": iso(payload.created_at or now),
        "updated_at": iso(payload.updated_at or payload.created_at or now),
    }


@router.get("/submissions/{submission_id}/comments")
def get_all_comments(submission_id: int, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    edict = get_edict(sub["edict_id"])
    activity = []
    for c in _comments_json(submission_id):
        entry = dict(c)
        entry["type"] = "comment"
        activity.append(entry)
    resp = forms.get_response(sub["candidate_form_id"])
    if resp and resp["submitted_at"]:
        activity.append(
            {
                "type": "submission",
                "user": None,
                "comment": "Candidatura enviada",
                "text": "Candidatura enviada",
                "created_at": iso(resp["submitted_at"]),
            }
        )
    for rid in sub["recommenders_form_ids"] or []:
        r = forms.get_response(rid)
        if r and r["submitted_at"]:
            activity.append(
                {
                    "type": "recommendation",
                    "user": None,
                    "comment": "Recomendacao recebida",
                    "text": "Recomendacao recebida",
                    "created_at": iso(r["submitted_at"]),
                }
            )
    if sub["accept_form_id"]:
        r = forms.get_response(sub["accept_form_id"])
        if r and r["submitted_at"]:
            activity.append(
                {
                    "type": "accept",
                    "user": None,
                    "comment": "Aceite respondido",
                    "text": "Aceite respondido",
                    "created_at": iso(r["submitted_at"]),
                }
            )
    activity.sort(key=lambda e: e.get("created_at") or "")
    return activity


@router.delete("/submissions/comments/{comment_id}", status_code=204)
def remove_comment(comment_id: int, user=Depends(current_user)):
    with Session() as s:
        row = s.execute(
            text("select * from comment where id = :i"), {"i": comment_id}
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Comment not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the author can remove the comment")
        s.execute(text("delete from comment where id = :i"), {"i": comment_id})
        s.commit()
    return None


@router.post("/submissions/{submission_id}/favorites", status_code=201)
def create_favorite(submission_id: int, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    _require_phase(sub, "avaliacao")
    with Session() as s:
        existing = s.execute(
            text("select 1 from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Favorite already exists")
        s.execute(
            text("insert into favorites (user_id, submission_id, created_at) values (:u, :s, now())"),
            {"u": user["id"], "s": submission_id},
        )
        s.commit()
    return "Favorite created"


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
def remove_favorite(submission_id: int, user=Depends(current_user)):
    _require_submission(submission_id)
    with Session() as s:
        existing = s.execute(
            text("select 1 from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id},
        ).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Favorite not found")
        s.execute(
            text("delete from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id},
        )
        s.commit()
    return None


@router.post("/submissions/{submission_id}/labels")
def add_label(submission_id: int, payload: LabelInputSchema, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    _require_phase(sub, "avaliacao")
    with Session() as s:
        existing = s.execute(
            text(
                "select id from labels where user_id = :u and submission_id = :s and label = :l"
                " and coalesce(context_type, 'candidate') = 'candidate'"
            ),
            {"u": user["id"], "s": submission_id, "l": payload.label},
        ).mappings().first()
        if existing:
            label_id = existing["id"]
            s.execute(
                text("update labels set color = :c where id = :i"),
                {"c": payload.color, "i": label_id},
            )
        else:
            label_id = s.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color, context_type)"
                    " values (:u, :s, :l, :c, 'candidate') returning id"
                ),
                {"u": user["id"], "s": submission_id, "l": payload.label, "c": payload.color},
            ).scalar_one()
        s.execute(
            text(
                "update labels set color = :c where user_id = :u and label = :l"
                " and coalesce(context_type, 'candidate') = 'candidate'"
            ),
            {"c": payload.color, "u": user["id"], "l": payload.label},
        )
        s.commit()
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": payload.label,
    }


@router.get("/submissions/{submission_id}/labels")
def get_labels(submission_id: int, user=Depends(current_user)):
    _require_submission(submission_id)
    with Session() as s:
        rows = s.execute(
            text(
                "select distinct on (label) id, label, color from labels"
                " where user_id = :u and coalesce(context_type, 'candidate') = 'candidate'"
                " order by label, id desc"
            ),
            {"u": user["id"]},
        ).mappings().all()
    return {"labels": [{"id": r["id"], "label": r["label"], "color": r["color"]} for r in rows]}


@router.delete("/submissions/label/{label_id}", status_code=204)
def remove_label(label_id: int, user=Depends(current_user)):
    with Session() as s:
        row = s.execute(text("select * from labels where id = :i"), {"i": label_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Label not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the author can remove the label")
        s.execute(text("delete from labels where id = :i"), {"i": label_id})
        s.commit()
    return None


@router.post("/submissions/{submission_id}/private_notes")
def add_or_update_note(submission_id: int, payload: PrivateNoteSchema, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    _require_phase(sub, "avaliacao")
    with Session() as s:
        existing = s.execute(
            text("select id from private_note where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id},
        ).mappings().first()
        if existing:
            s.execute(
                text("update private_note set note = :n, updated_at = now() where id = :i"),
                {"n": payload.note, "i": existing["id"]},
            )
        else:
            s.execute(
                text(
                    "insert into private_note (user_id, submission_id, note, created_at)"
                    " values (:u, :s, :n, now())"
                ),
                {"u": user["id"], "s": submission_id, "n": payload.note},
            )
        s.commit()
    return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
def register_view(submission_id: int, user=Depends(current_user)):
    _require_submission(submission_id)
    today = datetime.now(SP_TZ).date()
    with Session() as s:
        rows = s.execute(
            text("select * from submission_view where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id},
        ).mappings().all()
        seen = any(
            (r["created_at"].astimezone(SP_TZ).date() if r["created_at"] else None) == today
            for r in rows
        )
        if not seen:
            s.execute(
                text(
                    "insert into submission_view (user_id, submission_id, created_at, updated_at)"
                    " values (:u, :s, now(), now())"
                ),
                {"u": user["id"], "s": submission_id},
            )
            s.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
def get_submission_views(submission_id: int, user=Depends(current_user)):
    _require_submission(submission_id)
    with Session() as s:
        rows = s.execute(
            text("select * from submission_view where submission_id = :s order by id"),
            {"s": submission_id},
        ).mappings().all()
    return [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "submission_id": r["submission_id"],
            "created_at": iso(r["created_at"]),
            "updated_at": iso(r["updated_at"]),
        }
        for r in rows
    ]


@router.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(submission_id: int, payload: RequestReesendSchema, user=Depends(require_admin)):
    sub = _require_submission(submission_id)
    edict = _require_phase(sub, "homologacao")
    resp = forms.get_response(sub["candidate_form_id"])
    if not resp:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    forms.reopen_response(resp["id"])
    candidate = candidate_payload(sub, edict, user["id"])
    to_email = candidate["email"] or resp["email"]
    link = f"{settings.base_url}/form/{resp['token']}"
    html = (
        f"<p>Prezado(a) {candidate['name'] or 'candidato(a)'},</p>"
        f"<p>Sua candidatura precisa de correcao. Motivo: {payload.text}</p>"
        f'<p>Acesse o formulario para corrigir e reenviar: <a href="{link}">{link}</a></p>'
    )
    send_email(to_email, "Solicitacao de correcao da candidatura", html, bcc=[user["email"]])
    return {"message": "Resubmission requested", "email_sent": to_email}


@router.post("/submissions/{submission_id}/send-accept")
def send_accept_forms(submission_id: int, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    edict = get_edict(sub["edict_id"])
    if not edict.get("accept_forms"):
        raise HTTPException(status_code=404, detail="Accept form not configured for this edict")
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Accept form already sent")
    candidate = candidate_payload(sub, edict, user["id"])
    resp = forms.get_response(sub["candidate_form_id"])
    to_email = candidate["email"] or ((resp or {}).get("email") or "")
    accept_form_id = int(edict["accept_forms"])
    expiration = edict["closed_date"]
    _, response_id, token = forms.create_accept_form(accept_form_id, to_email, expiration)
    with Session() as s:
        s.execute(
            text("update submission set accept_form_id = :a, updated_at = now() where id = :i"),
            {"a": response_id, "i": submission_id},
        )
        s.commit()
    advisor = advisor_json(sub["advisor_id"])
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    link = f"{settings.base_url}/form/{token}"
    deadline = edict["closed_date"].isoformat() if edict["closed_date"] else ""
    html = (
        f"<p>Prezado(a) {candidate['name'] or 'candidato(a)'},</p>"
        f"<p>Voce foi aprovado(a). Preencha o formulario de aceite ate {deadline}.</p>"
        f"<p>Dear candidate, please fill the acceptance form until {deadline}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
    )
    send_email(to_email, "Formulario de aceite / Acceptance form", html, cc=cc)
    return {"message": "Accept form sent", "email_sent": to_email}


@router.post("/submissions/{submission_id}/send-letter")
def send_accept_letter(submission_id: int, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    edict = get_edict(sub["edict_id"])
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Letter already sent")
    candidate = candidate_payload(sub, edict, user["id"])
    resp = forms.get_response(sub["candidate_form_id"])
    to_email = candidate["email"] or ((resp or {}).get("email") or "")
    advisor = advisor_json(sub["advisor_id"])
    advisor_name = advisor["name"] if advisor else ""
    semester = sub["entry_semester"] or ""
    html = (
        f"<h2>Carta de Aceitacao</h2>"
        f"<p>Prezado(a) {candidate['name'] or 'candidato(a)'},</p>"
        f"<p>Informamos que sua candidatura ao programa de pos-graduacao foi aprovada.</p>"
        f"<p>Orientador: {advisor_name}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict['year']}</p>"
        '<p><img src="cid:signature" alt="Assinatura"></p>'
    )
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    send_email(
        to_email,
        f"Carta de Aceitacao / Acceptance Letter - {candidate['name'] or 'candidato(a)'}",
        html,
        cc=cc,
        images={"signature": "data/signature.png"},
    )
    with Session() as s:
        s.execute(
            text("update submission set letter_sent = true, updated_at = now() where id = :i"),
            {"i": submission_id},
        )
        s.commit()
    return {"message": "Letter sent", "email_sent": to_email}


@router.post("/submissions/{submission_id}/select")
def select_stats(submission_id: int, payload: StatsSchema, user=Depends(require_admin)):
    sub = _require_submission(submission_id)
    edict = get_edict(sub["edict_id"])
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict is closed")
    advisor_id = None
    if payload.stats == StatsEnum.approved:
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(status_code=422, detail="Approval requires exactly one advisor")
        with Session() as s:
            advisor = s.execute(
                text('select id from "user" where id = :i'), {"i": payload.user_ids[0]}
            ).mappings().first()
        if not advisor:
            raise HTTPException(status_code=422, detail="Advisor does not exist")
        advisor_id = payload.user_ids[0]
    with Session() as s:
        if advisor_id is not None:
            s.execute(
                text("update submission set stats = :s, advisor_id = :a, updated_at = now() where id = :i"),
                {"s": payload.stats.value, "a": advisor_id, "i": submission_id},
            )
        else:
            s.execute(
                text("update submission set stats = :s, updated_at = now() where id = :i"),
                {"s": payload.stats.value, "i": submission_id},
            )
        s.commit()
    return payload.stats.value


@router.post("/submissions/{submission_id}/bidding")
def toggle_bidding(submission_id: int, payload: BiddingSchema, user=Depends(current_user)):
    sub = _require_submission(submission_id)
    target_user = user["id"]
    if payload.user_id is not None and user["role"] in ADMIN_ROLES:
        target_user = payload.user_id
    with Session() as s:
        s.execute(
            text(
                "delete from labels where user_id = :u and submission_id = :s"
                " and context_type = 'bidding'"
            ),
            {"u": target_user, "s": submission_id},
        )
        if payload.bidding.value != "":
            s.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color, context_type)"
                    " values (:u, :s, :l, '', 'bidding')"
                ),
                {"u": target_user, "s": submission_id, "l": payload.bidding.value},
            )
        s.commit()
    return payload.bidding.value


@router.post("/submissions/{submission_id}/entry-semester")
def toggle_entry_semester(submission_id: int, payload: EntrySemesterSchema, user=Depends(current_user)):
    _require_submission(submission_id)
    normalized = payload.semester.strip()
    low = normalized.lower()
    if low in ("first", "primeiro", "primeiro semestre", "primeiro semestre.", "1"):
        normalized = "Primeiro semestre."
    elif low in ("second", "segundo", "segundo semestre", "segundo semestre.", "2"):
        normalized = "Segundo semestre."
    with Session() as s:
        s.execute(
            text("update submission set entry_semester = :s, updated_at = now() where id = :i"),
            {"s": normalized, "i": submission_id},
        )
        s.commit()
    return normalized


