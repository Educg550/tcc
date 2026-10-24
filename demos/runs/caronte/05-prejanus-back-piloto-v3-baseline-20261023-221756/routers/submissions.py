import json
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text

import forms_service as forms
import submissions_service as service
from config import settings
from db import FormsSession, PrejanusSession
from mailer import send_email
from schemas import (BiddingSchema, CommentSchema, EntrySemesterSchema, LabelSchema,
                     PrivateNoteSchema, RequestReesendSchema, StatsSchema)
from security import ADMIN_ROLES, get_current_user, require_admin

router = APIRouter(prefix="/submissions", tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")


async def _get_context(submission_id: int):
    async with PrejanusSession() as ps:
        sub = await service.get_submission(ps, submission_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")
        edict = await service.get_edict(ps, sub["edict_id"])
    return sub, edict


def _require_phase(edict, phase):
    if edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Operation only allowed in phase {phase}")


@router.get("/{submission_id}")
async def get_details(submission_id: int, include_comments: bool = False,
                       user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            summary = await service.build_detail(ps, fs, edict, sub, user["id"], include_comments)
            submission_form = await service.build_submission_form(fs, sub)
    return {"summary": summary, "submission_form": submission_form}


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(submission_id: int, label: str, filename: str,
                   user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    async with FormsSession() as fs:
        row = (await fs.execute(text(
            "select f.id, r.value from form_field f join responses r on r.field_id = f.id "
            "where r.response_id = :rid and f.name = :label and f.type = 'File'"),
            {"rid": sub["candidate_form_id"], "label": label})).mappings().first()
        if not row:
            row = (await fs.execute(text(
                "select f.id, r.value from form_field f join responses r on r.field_id = f.id "
                "where r.response_id = :rid and f.type = 'File' "
                "and coalesce(f.label->>'pt', '') = :label"),
                {"rid": sub["candidate_form_id"], "label": label})).mappings().first()
    if not row or row["value"] != filename:
        raise HTTPException(status_code=404, detail="File not found")
    matches = [p for p in Path("/shared/uploads").rglob(filename) if p.is_file()]
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(matches[0], media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/{submission_id}/comments")
async def add_comment(submission_id: int, body: CommentSchema, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    _require_phase(edict, "avaliacao")
    created_at = body.created_at or datetime.now(timezone.utc)
    updated_at = body.updated_at or created_at
    async with PrejanusSession() as s:
        comment_id = (await s.execute(text(
            "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
            "values (:u, :s, :c, :cr, :up) returning id"),
            {"u": user["id"], "s": submission_id, "c": body.comment,
             "cr": created_at, "up": updated_at})).scalar()
        await s.commit()
    return {"id": comment_id, "user": {"id": user["id"], "name": user["name"]},
            "submission_id": submission_id, "comment": body.comment,
            "created_at": created_at, "updated_at": updated_at}


@router.get("/{submission_id}/comments")
async def get_all_comments(submission_id: int, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            comments = await service.list_comments(ps, submission_id)
            activity = [{"user": c["user"], "text": c["comment"], "type": "comment",
                         "created_at": c["created_at"]} for c in comments]
            cand = await forms.get_response(sub["candidate_form_id"])
            if cand and cand.get("submitted_at"):
                payload = await service.candidate_payload(ps, fs, edict, sub)
                activity.append({"user": {"id": None, "name": payload["name"]},
                                 "text": "Candidatura enviada", "type": "submission",
                                 "created_at": cand["submitted_at"]})
            for rec in await service.get_recommendations(ps, fs, edict, sub):
                activity.append({"user": {"id": None, "name": rec["name"]},
                                 "text": rec["text"] or "Recomendação enviada",
                                 "type": "recommendation", "created_at": rec["submitted_at"]})
            if sub.get("accept_form_id"):
                acc = await forms.get_response(sub["accept_form_id"])
                if acc and acc.get("submitted_at"):
                    activity.append({"user": {"id": None, "name": None},
                                     "text": "Formulário de aceite respondido",
                                     "type": "accept", "created_at": acc["submitted_at"]})
    def _sort_key(entry):
        dt = entry["created_at"]
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    activity.sort(key=_sort_key)
    return activity


@router.delete("/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        row = (await s.execute(text("select * from comment where id = :i"), {"i": comment_id})).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Comment not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the author can delete this comment")
        await s.execute(text("delete from comment where id = :i"), {"i": comment_id})
        await s.commit()
    return None


@router.post("/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as s:
        existing = (await s.execute(text(
            "select 1 from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id})).scalar()
        if existing:
            raise HTTPException(status_code=409, detail="Favorite already exists")
        await s.execute(text(
            "insert into favorites (user_id, submission_id, created_at) values (:u, :s, now())"),
            {"u": user["id"], "s": submission_id})
        await s.commit()
    return "Favorite created"


@router.delete("/{submission_id}/favorites", status_code=204)
async def remove_favorite(submission_id: int, user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        existing = (await s.execute(text(
            "select 1 from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id})).scalar()
        if not existing:
            raise HTTPException(status_code=404, detail="Favorite not found")
        await s.execute(text(
            "delete from favorites where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id})
        await s.commit()
    return None


@router.post("/{submission_id}/labels")
async def add_label(submission_id: int, body: LabelSchema, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as s:
        label_id = (await s.execute(text(
            "insert into labels (user_id, submission_id, label, color, context_type) "
            "values (:u, :s, :l, :c, 'candidate') returning id"),
            {"u": user["id"], "s": submission_id, "l": body.label, "c": body.color})).scalar()
        await s.execute(text(
            "update labels set color = :c where user_id = :u and label = :l "
            "and context_type = 'candidate'"),
            {"c": body.color, "u": user["id"], "l": body.label})
        await s.commit()
    return {"id": label_id, "user": {"id": user["id"], "name": user["name"]},
            "submission_id": submission_id, "label": body.label}


@router.get("/{submission_id}/labels")
async def get_labels(submission_id: int, user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        rows = (await s.execute(text(
            "select distinct on (label) id, label, color from labels "
            "where user_id = :u and (context_type = 'candidate' or context_type is null) "
            "order by label, id desc"),
            {"u": user["id"]})).mappings().all()
    return {"labels": [{"id": r["id"], "label": r["label"], "color": r["color"]} for r in rows]}


@router.delete("/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user=Depends(get_current_user)):
    async with PrejanusSession() as s:
        row = (await s.execute(text("select * from labels where id = :i"), {"i": label_id})).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Label not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the author can delete this label")
        await s.execute(text("delete from labels where id = :i"), {"i": label_id})
        await s.commit()
    return None


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(submission_id: int, body: PrivateNoteSchema,
                             user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    _require_phase(edict, "avaliacao")
    async with PrejanusSession() as s:
        existing = (await s.execute(text(
            "select id from private_note where user_id = :u and submission_id = :s"),
            {"u": user["id"], "s": submission_id})).scalar()
        if existing:
            await s.execute(text(
                "update private_note set note = :n, updated_at = now() where id = :i"),
                {"n": body.note, "i": existing})
        else:
            await s.execute(text(
                "insert into private_note (user_id, submission_id, note, created_at) "
                "values (:u, :s, :n, now())"),
                {"u": user["id"], "s": submission_id, "n": body.note})
        await s.commit()
    return {"note": body.note}


@router.post("/{submission_id}/view")
async def register_view(submission_id: int, user=Depends(get_current_user)):
    await _get_context(submission_id)
    today = datetime.now(SP_TZ).date()
    async with PrejanusSession() as s:
        existing = (await s.execute(text(
            "select 1 from submission_view where user_id = :u and submission_id = :s "
            "and (created_at at time zone 'America/Sao_Paulo')::date = :d"),
            {"u": user["id"], "s": submission_id, "d": today})).scalar()
        if not existing:
            await s.execute(text(
                "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                "values (:u, :s, now(), now())"),
                {"u": user["id"], "s": submission_id})
        await s.commit()
    return {"message": "View registered"}


@router.get("/{submission_id}/view")
async def get_submission_views(submission_id: int, user=Depends(get_current_user)):
    await _get_context(submission_id)
    async with PrejanusSession() as s:
        rows = (await s.execute(text(
            "select v.id, v.created_at, v.updated_at, u.id as uid, u.name as uname "
            'from submission_view v join "user" u on u.id = v.user_id '
            "where v.submission_id = :s order by v.created_at"),
            {"s": submission_id})).mappings().all()
    return [{"id": r["id"], "user": {"id": r["uid"], "name": r["uname"]},
             "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]


@router.post("/{submission_id}/select")
async def select_stats(submission_id: int, body: StatsSchema, user=Depends(require_admin)):
    sub, edict = await _get_context(submission_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict is closed")
    advisor_id = None
    if body.stats == "approved":
        if not body.user_ids or len(body.user_ids) != 1:
            raise HTTPException(status_code=400, detail="Approval requires exactly one advisor")
        async with PrejanusSession() as s:
            advisor_id = (await s.execute(text(
                'select id from "user" where id = :i'), {"i": body.user_ids[0]})).scalar()
        if advisor_id is None:
            raise HTTPException(status_code=400, detail="Advisor does not exist")
    async with PrejanusSession() as s:
        await s.execute(text(
            "update submission set stats = :st, advisor_id = :a, updated_at = now() where id = :i"),
            {"st": body.stats, "a": advisor_id, "i": submission_id})
        await s.commit()
    return body.stats


@router.post("/{submission_id}/bidding")
async def toggle_bidding(submission_id: int, body: BiddingSchema, user=Depends(get_current_user)):
    await _get_context(submission_id)
    target_user = user["id"]
    if body.user_id is not None and user["role"] in ADMIN_ROLES:
        target_user = body.user_id
    async with PrejanusSession() as s:
        await s.execute(text(
            "delete from labels where user_id = :u and submission_id = :s and context_type = 'bidding'"),
            {"u": target_user, "s": submission_id})
        if body.bidding != "":
            await s.execute(text(
                "insert into labels (user_id, submission_id, label, color, context_type) "
                "values (:u, :s, :l, '', 'bidding')"),
                {"u": target_user, "s": submission_id, "l": body.bidding})
        await s.commit()
    return body.bidding


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(submission_id: int, body: EntrySemesterSchema,
                               user=Depends(get_current_user)):
    await _get_context(submission_id)
    value = (body.semester or "").strip().lower()
    if "primeiro" in value or "first" in value:
        semester = "Primeiro semestre."
    elif "segundo" in value or "second" in value:
        semester = "Segundo semestre."
    else:
        semester = body.semester
    async with PrejanusSession() as s:
        await s.execute(text(
            "update submission set entry_semester = :sem, updated_at = now() where id = :i"),
            {"sem": semester, "i": submission_id})
        await s.commit()
    return semester


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(submission_id: int, body: RequestReesendSchema,
                             user=Depends(require_admin)):
    sub, edict = await _get_context(submission_id)
    _require_phase(edict, "homologacao")
    async with FormsSession() as fs:
        cand = await forms.get_response(sub["candidate_form_id"])
        await forms.reopen_response(sub["candidate_form_id"])
    link = f"{settings.BASE_URL}/form/{cand['token']}"
    html = (f"<p>Prezado(a) candidato(a),</p>"
            f"<p>Sua candidatura precisa de correção. Motivo: {body.text}</p>"
            f"<p>Acesse o formulário para corrigir e reenviar: <a href=\"{link}\">{link}</a></p>")
    send_email("Solicitação de correção da candidatura", html, [cand["email"]],
               bcc=[user["email"]])
    return {"message": "Resubmission requested", "email_sent": cand["email"]}


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    if not edict.get("accept_forms"):
        raise HTTPException(status_code=404, detail="Accept form not configured for this edict")
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub.get("accept_form_id"):
        raise HTTPException(status_code=400, detail="Accept form already sent")
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            payload = await service.candidate_payload(ps, fs, edict, sub)
            cand = await forms.get_response(sub["candidate_form_id"])
            advisor = await service.advisor_info(ps, sub)
            _, response_id, token = await forms.create_accept_share(
                int(edict["accept_forms"]), cand["email"], edict["closed_date"])
            await ps.execute(text(
                "update submission set accept_form_id = :a, updated_at = now() where id = :i"),
                {"a": response_id, "i": submission_id})
            await ps.commit()
    link = f"{settings.BASE_URL}/form/{token}"
    deadline = edict["closed_date"]
    html = (
        f"<p>Caro(a) {payload['name']},</p>"
        f"<p>Parabéns! Sua candidatura foi aprovada. Preencha o formulário de aceite até "
        f"{deadline}.</p>"
        f"<p><a href=\"{link}\">{link}</a></p>"
        f"<hr/><p>Dear {payload['name']},</p>"
        f"<p>Congratulations! Your application was approved. Please fill the acceptance form "
        f"by {deadline}.</p>"
        f"<p><a href=\"{link}\">{link}</a></p>"
    )
    send_email("Formulário de aceite / Acceptance form", html, [cand["email"]],
               cc=[advisor["email"]] if advisor else None)
    return {"message": "Accept form sent", "email_sent": cand["email"]}


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user=Depends(get_current_user)):
    sub, edict = await _get_context(submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub.get("letter_sent"):
        raise HTTPException(status_code=400, detail="Letter already sent")
    async with PrejanusSession() as ps:
        async with FormsSession() as fs:
            payload = await service.candidate_payload(ps, fs, edict, sub)
            advisor = await service.advisor_info(ps, sub)
            cand = await forms.get_response(sub["candidate_form_id"])
    semester = sub.get("entry_semester") or payload["research"]["semester"]
    html = (
        f"<h2>Carta de Aceitação</h2>"
        f"<p>Prezado(a) {payload['name']},</p>"
        f"<p>Informamos que sua candidatura ao programa de pós-graduação foi <b>aprovada</b>.</p>"
        f"<p>Orientador(a): {advisor['name'] if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict['year']}</p>"
        f'<p><img src="cid:signature" alt="Assinatura"/></p>'
    )
    send_email("Carta de Aceitação", html, [cand["email"]],
               cc=[advisor["email"]] if advisor else None,
               inline_images={"signature": "data/signature.png"})
    async with PrejanusSession() as s:
        await s.execute(text(
            "update submission set letter_sent = true, updated_at = now() where id = :i"),
            {"i": submission_id})
        await s.commit()
    return {"message": "Acceptance letter sent", "email_sent": cand["email"]}
