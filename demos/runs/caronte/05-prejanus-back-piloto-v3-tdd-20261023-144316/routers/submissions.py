import json
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import services.forms_db as forms_db
import services.submissions as submissions
from auth import ADMIN_ROLES, get_current_user
from config import settings
from database import SessionLocal
from services.mailer import send_email
from services.mappings import resolve_mapping

router = APIRouter(tags=["submissions"])


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
    user_ids: list[int] | None
    stats: Literal["approved", "refused", "underreview", "waitlist"]


class BiddingSchema(BaseModel):
    bidding: Literal[
        "decline", "available", "interested", "agreed", "interested_scholarship", ""
    ]
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


async def _get_submission_or_404(submission_id: int) -> dict:
    sub = await submissions.get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _phase_of(sub: dict) -> str:
    edict = await submissions.get_edict(sub["edict_id"])
    return edict["phase"] if edict else ""


def _require_phase(phase: str, expected: str = "avaliacao") -> None:
    if phase != expected:
        raise HTTPException(
            status_code=400, detail=f"Operação disponível apenas na fase {expected}"
        )


def _user_brief(user: dict | None) -> dict | None:
    if not user:
        return None
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


async def _resolved_candidate(sub: dict, edict: dict):
    fr = await forms_db.get_response(sub["candidate_form_id"])
    values = await forms_db.get_response_values(sub["candidate_form_id"])
    mapping = await submissions.get_mapping(
        edict["id"], "candidate", sub["candidate_form_version"]
    )
    resolved = resolve_mapping(mapping, values) if mapping else {}
    return fr, values, (resolved or {})


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: dict = Depends(get_current_user),
):
    edict = await submissions.get_edict(edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    if edict["candidate_forms"] is None:
        return {"submissions": []}
    responses = await forms_db.get_submitted_responses(int(edict["candidate_forms"]))
    ctx = await submissions.edict_context(edict_id, user["id"])
    recommendations = await submissions.load_recommendations(edict)
    bidding_users = submissions._bidding_users(ctx["labels"], ctx["slots"])
    items = []
    for fr in responses:
        sub = await submissions.ensure_submission(edict_id, fr.id, fr.form_version)
        if stats is not None and sub["stats"] != stats:
            continue
        if only_favorites and sub["id"] not in ctx["favorites"]:
            continue
        _, values, resolved = await _resolved_candidate(sub, edict)
        fields = submissions.build_summary_fields(resolved)
        await submissions.associate_recommendations(
            sub, fields["name"], fields["email"], recommendations
        )
        advisor = (
            await submissions.get_user(sub["advisor_id"]) if sub["advisor_id"] else None
        )
        accept = await submissions.accept_info(sub["accept_form_id"])
        items.append(
            {
                **fields,
                "email": fields["email"] or (fr.email or ""),
                "id": sub["id"],
                "token": str(fr.token),
                "advisor": _user_brief(advisor),
                "stats": sub["stats"],
                "is_favorite": sub["id"] in ctx["favorites"],
                "bidding_users": bidding_users,
                "labels": submissions._submission_labels(ctx["labels"], sub["id"]),
                "accept": accept,
            }
        )
    return {"submissions": items}


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: dict = Depends(get_current_user),
):
    sub = await _get_submission_or_404(submission_id)
    edict = await submissions.get_edict(sub["edict_id"])
    fr, values, resolved = await _resolved_candidate(sub, edict)
    if not fr:
        raise HTTPException(status_code=404, detail="Resposta não encontrada")
    fields = submissions.build_summary_fields(resolved)
    recommendations = await submissions.load_recommendations(edict)
    recs = await submissions.associate_recommendations(
        sub, fields["name"], fields["email"], recommendations
    )
    advisor = (
        await submissions.get_user(sub["advisor_id"]) if sub["advisor_id"] else None
    )
    accept = await submissions.accept_info(sub["accept_form_id"])

    async with SessionLocal() as s:
        note_row = await s.execute(
            text(
                "select note from private_note where user_id = :u and submission_id = :s"
            ),
            {"u": user["id"], "s": submission_id},
        )
        note = note_row.fetchone()
        fav_row = await s.execute(
            text(
                "select 1 from favorites where user_id = :u and submission_id = :s"
            ),
            {"u": user["id"], "s": submission_id},
        )
        is_favorite = fav_row.fetchone() is not None
        sub_labels = await s.execute(
            text(
                "select id, label, color from labels where submission_id = :s"
                " and coalesce(context_type, 'candidate') <> 'bidding'"
            ),
            {"s": submission_id},
        )
        labels = [
            {"id": r.id, "label": r.label, "color": r.color}
            for r in sub_labels.fetchall()
        ]
        my_bidding = await s.execute(
            text(
                "select label from labels where user_id = :u and submission_id = :s"
                " and context_type = 'bidding' order by id desc limit 1"
            ),
            {"u": user["id"], "s": submission_id},
        )
        bidding_row = my_bidding.fetchone()

    summary = {
        **fields,
        "email": fields["email"] or (fr.email or ""),
        "access_email": fr.email,
        "id": sub["id"],
        "token": str(fr.token),
        "recommendations": recs,
        "stats": sub["stats"],
        "is_favorite": is_favorite,
        "labels": labels,
        "bidding": bidding_row.label if bidding_row else "",
        "private_note": note.note if note else "",
        "accept": accept,
        "semester": sub["entry_semester"]
        or fields["research"]["semester"],
        "entry_semester": sub["entry_semester"],
        "letter_sent": sub["letter_sent"],
        "advisor": _user_brief(advisor),
    }
    if include_comments:
        summary["comments"] = await _comments_payload(submission_id)

    form_id = int(edict["candidate_forms"]) if edict["candidate_forms"] is not None else 0
    submission_form = await submissions.build_submission_form(
        form_id, sub["candidate_form_version"], values
    )
    return {"summary": summary, "submission_form": submission_form}


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user: dict = Depends(get_current_user),
):
    sub = await _get_submission_or_404(submission_id)
    fr = await forms_db.get_response(sub["candidate_form_id"])
    if not fr:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    values = await forms_db.get_response_values(sub["candidate_form_id"])
    fields = await submissions.all_form_fields(fr.form_id, sub["candidate_form_version"])
    field = next(
        (f for f in fields if f["type"] == "File" and f["name"] == label), None
    )
    if field is None:
        field = next(
            (f for f in fields if f["type"] == "File" and f["label"] == label), None
        )
    if field is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    value = values.get(field["id"])
    if not value or os.path.basename(value) != filename:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    uploads = Path(settings.uploads_dir)
    candidates = []
    if "/" in value:
        candidates.append(uploads / value)
    candidates.extend(
        [
            uploads / str(fr.token) / filename,
            uploads / str(fr.id) / filename,
            uploads / str(fr.form_id) / str(fr.id) / filename,
            uploads / filename,
        ]
    )
    for path in candidates:
        if path.is_file():
            content = path.read_bytes()
            return Response(
                content=content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                },
            )
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


async def _comments_payload(submission_id: int) -> list[dict]:
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                'select c.id, c.user_id, c.submission_id, c.comment, c.created_at,'
                ' c.updated_at, u.name from comment c join "user" u on u.id = c.user_id'
                " where c.submission_id = :s order by c.created_at, c.id"
            ),
            {"s": submission_id},
        )
        comments = [
            {
                "id": r.id,
                "user": {"id": r.user_id, "name": r.name},
                "submission_id": r.submission_id,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "author": r.name,
                "text": r.comment,
                "type": "comment",
                "date": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows.fetchall()
        ]
    sub = await submissions.get_submission(submission_id)
    edict = await submissions.get_edict(sub["edict_id"])
    fr = await forms_db.get_response(sub["candidate_form_id"])
    events = []
    if fr and fr.submitted_at:
        events.append(
            {
                "author": fr.email or "",
                "text": "Candidatura enviada",
                "type": "submission",
                "date": fr.submitted_at.isoformat(),
            }
        )
    recommendations = await submissions.load_recommendations(edict)
    _, _, resolved = await _resolved_candidate(sub, edict)
    fields = submissions.build_summary_fields(resolved)
    key = submissions._candidate_key(fields["name"], fields["email"])
    for rec in recommendations.get(key, []):
        events.append(
            {
                "author": rec["name"],
                "text": "Recomendação recebida",
                "type": "recommendation",
                "date": rec["submitted_at"],
            }
        )
    if sub["accept_form_id"]:
        afr = await forms_db.get_response(sub["accept_form_id"])
        if afr and afr.submitted_at:
            events.append(
                {
                    "author": afr.email or "",
                    "text": "Aceite respondido",
                    "type": "accept",
                    "date": afr.submitted_at.isoformat(),
                }
            )
    activity = comments + events
    activity.sort(key=lambda e: e.get("date") or "")
    return activity


@router.get("/submissions/{submission_id}/comments")
async def get_all_comments(
    submission_id: int, user: dict = Depends(get_current_user)
):
    await _get_submission_or_404(submission_id)
    return await _comments_payload(submission_id)


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int, payload: CommentSchema, user: dict = Depends(get_current_user)
):
    sub = await _get_submission_or_404(submission_id)
    _require_phase(await _phase_of(sub))
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "insert into comment (user_id, submission_id, comment, created_at,"
                " updated_at) values (:u, :s, :c, :ca, :ua) returning id, created_at,"
                " updated_at"
            ),
            {
                "u": user["id"],
                "s": submission_id,
                "c": payload.comment,
                "ca": payload.created_at or datetime.utcnow(),
                "ua": payload.updated_at,
            },
        )
        await s.commit()
        r = rows.fetchone()
    return {
        "id": r.id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": payload.comment,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        rows = await s.execute(
            text("select user_id from comment where id = :id"), {"id": comment_id}
        )
        r = rows.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Comentário não encontrado")
        if r.user_id != user["id"]:
            raise HTTPException(status_code=403, detail="Autor divergente")
        await s.execute(text("delete from comment where id = :id"), {"id": comment_id})
        await s.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user: dict = Depends(get_current_user)):
    sub = await _get_submission_or_404(submission_id)
    _require_phase(await _phase_of(sub))
    async with SessionLocal() as s:
        try:
            await s.execute(
                text(
                    "insert into favorites (user_id, submission_id, created_at)"
                    " values (:u, :s, now())"
                ),
                {"u": user["id"], "s": submission_id},
            )
            await s.commit()
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Favorito já registrado")
    return Response(status_code=201, content="Favorite created")


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(submission_id: int, user: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select 1 from favorites where user_id = :u and submission_id = :s"
            ),
            {"u": user["id"], "s": submission_id},
        )
        if not rows.fetchone():
            raise HTTPException(status_code=404, detail="Favorito não encontrado")
        await s.execute(
            text(
                "delete from favorites where user_id = :u and submission_id = :s"
            ),
            {"u": user["id"], "s": submission_id},
        )
        await s.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int, payload: LabelInputSchema, user: dict = Depends(get_current_user)
):
    sub = await _get_submission_or_404(submission_id)
    _require_phase(await _phase_of(sub))
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "insert into labels (user_id, submission_id, label, color,"
                " context_type) values (:u, :s, :l, :c, 'candidate') returning id"
            ),
            {"u": user["id"], "s": submission_id, "l": payload.label, "c": payload.color},
        )
        label_id = rows.fetchone().id
        await s.execute(
            text(
                "update labels set color = :c where user_id = :u and label = :l"
                " and coalesce(context_type, 'candidate') <> 'bidding'"
            ),
            {"u": user["id"], "l": payload.label, "c": payload.color},
        )
        await s.commit()
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": payload.label,
    }


@router.get("/submissions/{submission_id}/labels")
async def get_labels(submission_id: int, user: dict = Depends(get_current_user)):
    await _get_submission_or_404(submission_id)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select distinct on (label) id, label, color from labels"
                " where user_id = :u and coalesce(context_type, 'candidate') <> 'bidding'"
                " order by label, id desc"
            ),
            {"u": user["id"]},
        )
        labels = [
            {"id": r.id, "label": r.label, "color": r.color} for r in rows.fetchall()
        ]
    return {"labels": labels}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user: dict = Depends(get_current_user)):
    async with SessionLocal() as s:
        rows = await s.execute(
            text("select user_id from labels where id = :id"), {"id": label_id}
        )
        r = rows.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
        if r.user_id != user["id"]:
            raise HTTPException(status_code=403, detail="Autor divergente")
        await s.execute(text("delete from labels where id = :id"), {"id": label_id})
        await s.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int, payload: PrivateNoteSchema, user: dict = Depends(get_current_user)
):
    sub = await _get_submission_or_404(submission_id)
    _require_phase(await _phase_of(sub))
    async with SessionLocal() as s:
        await s.execute(
            text(
                "insert into private_note (user_id, submission_id, note, created_at)"
                " values (:u, :s, :n, now())"
                " on conflict (user_id, submission_id) do update set note = :n,"
                " updated_at = now()"
            ),
            {"u": user["id"], "s": submission_id, "n": payload.note},
        )
        await s.commit()
    return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
async def register_view(submission_id: int, user: dict = Depends(get_current_user)):
    await _get_submission_or_404(submission_id)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select 1 from submission_view where user_id = :u and submission_id = :s"
                " and (created_at at time zone 'America/Sao_Paulo')::date ="
                " (now() at time zone 'America/Sao_Paulo')::date"
            ),
            {"u": user["id"], "s": submission_id},
        )
        if not rows.fetchone():
            await s.execute(
                text(
                    "insert into submission_view (user_id, submission_id, created_at,"
                    " updated_at) values (:u, :s, now(), now())"
                ),
                {"u": user["id"], "s": submission_id},
            )
            await s.commit()
    return {"message": "Visualização registrada"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(submission_id: int, user: dict = Depends(get_current_user)):
    await _get_submission_or_404(submission_id)
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                'select v.id, v.created_at, v.updated_at, u.id as uid, u.name'
                " from submission_view v join \"user\" u on u.id = v.user_id"
                " where v.submission_id = :s order by v.created_at, v.id"
            ),
            {"s": submission_id},
        )
        return [
            {
                "id": r.id,
                "user": {"id": r.uid, "name": r.name},
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows.fetchall()
        ]


@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int, payload: StatsSchema, user: dict = Depends(get_current_user)
):
    sub = await _get_submission_or_404(submission_id)
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    edict = await submissions.get_edict(sub["edict_id"])
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital encerrado")
    advisor_id = None
    if payload.stats == "approved":
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(status_code=400, detail="Aprovação exige um orientador")
        advisor = await submissions.get_user(payload.user_ids[0])
        if not advisor:
            raise HTTPException(status_code=400, detail="Orientador inexistente")
        advisor_id = advisor["id"]
    async with SessionLocal() as s:
        if advisor_id is not None:
            await s.execute(
                text(
                    "update submission set stats = :st, advisor_id = :a,"
                    " updated_at = now() where id = :id"
                ),
                {"st": payload.stats, "a": advisor_id, "id": submission_id},
            )
        else:
            await s.execute(
                text(
                    "update submission set stats = :st, updated_at = now()"
                    " where id = :id"
                ),
                {"st": payload.stats, "id": submission_id},
            )
        await s.commit()
    return f"Submission marked as {payload.stats}"


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int, payload: BiddingSchema, user: dict = Depends(get_current_user)
):
    sub = await _get_submission_or_404(submission_id)
    if payload.user_id is not None and user["role"] in ADMIN_ROLES:
        target_id = payload.user_id
    else:
        target_id = user["id"]
    async with SessionLocal() as s:
        await s.execute(
            text(
                "delete from labels where user_id = :u and submission_id = :s"
                " and context_type = 'bidding'"
            ),
            {"u": target_id, "s": submission_id},
        )
        if payload.bidding:
            await s.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color,"
                    " context_type) values (:u, :s, :l, '', 'bidding')"
                ),
                {"u": target_id, "s": submission_id, "l": payload.bidding},
            )
        await s.commit()
    return f"Bidding updated to {payload.bidding}"


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int, payload: EntrySemesterSchema, user: dict = Depends(get_current_user)
):
    await _get_submission_or_404(submission_id)
    semester = payload.semester
    low = semester.strip().lower()
    if low in ("primeiro", "first", "primeiro semestre", "1"):
        semester = "Primeiro semestre."
    elif low in ("segundo", "second", "segundo semestre", "2"):
        semester = "Segundo semestre."
    async with SessionLocal() as s:
        await s.execute(
            text(
                "update submission set entry_semester = :sem, updated_at = now()"
                " where id = :id"
            ),
            {"sem": semester, "id": submission_id},
        )
        await s.commit()
    return f"Entry semester updated to {semester}"


@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int, payload: RequestReesendSchema, user: dict = Depends(get_current_user)
):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    sub = await _get_submission_or_404(submission_id)
    _require_phase(await _phase_of(sub), "homologacao")
    fr = await forms_db.get_response(sub["candidate_form_id"])
    if not fr:
        raise HTTPException(status_code=404, detail="Resposta não encontrada")
    await forms_db.reopen_response(fr.id)
    link = f"{settings.base_url}/form/{fr.token}"
    html = (
        "<p>Prezado(a) candidato(a),</p>"
        "<p>Sua candidatura precisa de correção. Motivo:</p>"
        f"<p>{payload.text}</p>"
        f'<p>Acesse o formulário para corrigir e reenviar: <a href="{link}">{link}</a></p>'
    )
    send_email(fr.email or "", "Solicitação de correção da candidatura", html, bcc=user["email"])
    return {
        "message": "Solicitação de correção enviada",
        "email_sent": fr.email or "",
    }


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user: dict = Depends(get_current_user)):
    sub = await _get_submission_or_404(submission_id)
    edict = await submissions.get_edict(sub["edict_id"])
    if not edict.get("accept_forms"):
        raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Aceite já enviado")
    fr = await forms_db.get_response(sub["candidate_form_id"])
    if not fr:
        raise HTTPException(status_code=404, detail="Resposta não encontrada")
    _, _, resolved = await _resolved_candidate(sub, edict)
    fields = submissions.build_summary_fields(resolved)
    candidate_name = fields["name"] or (fr.email or "")
    candidate_email = fr.email or fields["email"]
    form = await forms_db.get_form(int(edict["accept_forms"]))
    shared_id, share_token = await forms_db.create_accept_share(
        int(edict["accept_forms"]), edict["closed_date"]
    )
    response_id, _ = await forms_db.create_accept_response(
        int(edict["accept_forms"]),
        shared_id,
        candidate_email,
        form.version if form else 1,
    )
    async with SessionLocal() as s:
        await s.execute(
            text(
                "update submission set accept_form_id = :a, updated_at = now()"
                " where id = :id"
            ),
            {"a": response_id, "id": submission_id},
        )
        await s.commit()
    link = f"{settings.base_url}/form/{share_token}"
    deadline = edict["closed_date"].isoformat() if edict["closed_date"] else ""
    html = (
        f"<p>Caro(a) {candidate_name},</p>"
        "<p>Parabéns! Sua candidatura foi aprovada. Preencha o formulário"
        f" de aceite até {deadline}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<p>Dear candidate, your application was approved. Please fill the"
        f" acceptance form until {deadline} at the link above.</p>"
    )
    advisor = await submissions.get_user(sub["advisor_id"]) if sub["advisor_id"] else None
    send_email(
        candidate_email,
        "Formulário de aceite / Acceptance form",
        html,
        cc=advisor["email"] if advisor else None,
    )
    return {
        "message": "Formulário de aceite enviado",
        "email_sent": candidate_email,
    }


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user: dict = Depends(get_current_user)):
    sub = await _get_submission_or_404(submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Carta já enviada")
    edict = await submissions.get_edict(sub["edict_id"])
    fr, _, resolved = await _resolved_candidate(sub, edict)
    fields = submissions.build_summary_fields(resolved)
    candidate_name = fields["name"] or (fr.email if fr else "")
    candidate_email = fr.email if fr else fields["email"]
    advisor = await submissions.get_user(sub["advisor_id"]) if sub["advisor_id"] else None
    semester = sub["entry_semester"] or fields["research"]["semester"]
    html = (
        f"<h2>Carta de Aprovação</h2>"
        f"<p>Prezado(a) {candidate_name},</p>"
        "<p>Informamos que sua candidatura ao programa de pós-graduação foi"
        " aprovada.</p>"
        f"<p>Orientador(a): {advisor['name'] if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict['year']}</p>"
    )
    attachments = []
    signature = Path(settings.data_dir) / "signature.png"
    if signature.exists():
        html += f'<p><img src="cid:signature.png" alt="Assinatura"/></p>'
        attachments.append(("signature.png", signature.read_bytes()))
    send_email(
        candidate_email,
        "Carta de aceite / Acceptance letter",
        html,
        cc=advisor["email"] if advisor else None,
        attachments=attachments,
    )
    async with SessionLocal() as s:
        await s.execute(
            text(
                "update submission set letter_sent = true, updated_at = now()"
                " where id = :id"
            ),
            {"id": submission_id},
        )
        await s.commit()
    return {
        "message": "Carta de aceite enviada",
        "email_sent": candidate_email,
    }
