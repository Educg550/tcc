from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import delete, select
from typing import Literal

import forms_db
import mail
from auth import ADMIN_ROLES, get_current_user, require_admin
from config import settings
from database import FormsSessionLocal, SessionLocal
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
from submission_service import (
    build_submission_form,
    extract_summary,
    submission_payload,
    sync_edict_submissions,
    user_bidding,
)

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")
UPLOADS_ROOT = "/shared/uploads"


class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LabelSchema(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesend(BaseModel):
    text: str


class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: Literal["approved", "refused", "underreview", "waitlist"]


class BiddingSchema(BaseModel):
    bidding: Literal["decline", "available", "interested", "agreed", "interested_scholarship", ""]
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


async def _get_submission(db, submission_id: int) -> tuple[Submission, Edict]:
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    edict = await db.get(Edict, sub.edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return sub, edict


def _require_phase(edict: Edict, phase: str) -> None:
    if edict.phase != phase:
        raise HTTPException(status_code=400, detail=f"Operação disponível apenas na fase {phase}")


@router.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user: User = Depends(get_current_user),
):
    async with SessionLocal() as db:
        edict = await db.get(Edict, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        await sync_edict_submissions(db, edict)
        q = select(Submission).where(Submission.edict_id == edict_id).order_by(Submission.id)
        subs = (await db.execute(q)).scalars().all()
        if stats is not None:
            subs = [s for s in subs if s.stats == stats]
        if only_favorites:
            fav_ids = set(
                (
                    await db.execute(
                        select(Favorite.submission_id).where(Favorite.user_id == user.id)
                    )
                ).scalars().all()
            )
            subs = [s for s in subs if s.id in fav_ids]
        async with FormsSessionLocal() as fdb:
            items = [
                await submission_payload(db, fdb, edict, s, user) for s in subs
            ]
        return {"submissions": items}


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: User = Depends(get_current_user),
):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        async with FormsSessionLocal() as fdb:
            payload = await submission_payload(db, fdb, edict, sub, user)
            note = (
                await db.execute(
                    select(PrivateNote).where(
                        PrivateNote.user_id == user.id,
                        PrivateNote.submission_id == sub.id,
                    )
                )
            ).scalar_one_or_none()
            payload["summary"] = {
                **payload,
                "private_note": note.note if note else "",
                "entry_semester": sub.entry_semester or "",
                "letter_sent": sub.letter_sent,
                "bidding": await user_bidding(db, user.id, sub.id),
            }
            if include_comments:
                payload["summary"]["comments"] = await _comments_list(db, fdb, sub)
            payload["submission_form"] = await build_submission_form(
                fdb,
                edict.candidate_forms,
                sub.candidate_form_version,
                sub.candidate_form_id,
            )
            return {"summary": payload["summary"], "submission_form": payload["submission_form"]}


# ---------- comentários ----------

async def _comments_list(db, fdb, sub: Submission) -> list[dict]:
    items = []
    comments = (
        await db.execute(
            select(Comment).where(Comment.submission_id == sub.id).order_by(Comment.created_at)
        )
    ).scalars().all()
    for c in comments:
        u = await db.get(User, c.user_id)
        items.append(
            {
                "id": c.id,
                "user": {"id": u.id, "name": u.name} if u else None,
                "comment": c.comment,
                "type": "comment",
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
        )
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp and resp.get("submitted_at"):
        items.append(
            {
                "user": {"name": resp.get("email") or ""},
                "comment": "Candidatura enviada",
                "type": "submission",
                "created_at": resp["submitted_at"].isoformat(),
            }
        )
    for rid in sub.recommenders_form_ids or []:
        r = await forms_db.get_response(fdb, rid)
        if r and r.get("submitted_at"):
            items.append(
                {
                    "user": {"name": r.get("email") or ""},
                    "comment": "Recomendação enviada",
                    "type": "recommendation",
                    "created_at": r["submitted_at"].isoformat(),
                }
            )
    if sub.accept_form_id:
        r = await forms_db.get_response(fdb, sub.accept_form_id)
        if r and r.get("submitted_at"):
            items.append(
                {
                    "user": {"name": r.get("email") or ""},
                    "comment": "Aceite respondido",
                    "type": "accept",
                    "created_at": r["submitted_at"].isoformat(),
                }
            )
    items.sort(key=lambda i: i.get("created_at") or "")
    return items


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int, payload: CommentSchema, user: User = Depends(get_current_user)
):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        _require_phase(edict, "avaliacao")
        now = datetime.now(timezone.utc)
        c = Comment(
            user_id=user.id,
            submission_id=submission_id,
            comment=payload.comment,
            created_at=payload.created_at or now,
            updated_at=payload.updated_at or payload.created_at or now,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return {
            "id": c.id,
            "user": {"id": user.id, "name": user.name},
            "submission_id": submission_id,
            "comment": c.comment,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }


@router.get("/submissions/{submission_id}/comments")
async def get_all_comments(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        sub, _ = await _get_submission(db, submission_id)
        async with FormsSessionLocal() as fdb:
            return await _comments_list(db, fdb, sub)


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        c = await db.get(Comment, comment_id)
        if c is None:
            raise HTTPException(status_code=404, detail="Comentário não encontrado")
        if c.user_id != user.id:
            raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
        await db.delete(c)
        await db.commit()
    return Response(status_code=204)


# ---------- favoritos ----------

@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
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
        db.add(
            Favorite(
                user_id=user.id,
                submission_id=sub.id,
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
    return Response(status_code=201)


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        await _get_submission(db, submission_id)
        result = await db.execute(
            delete(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == submission_id
            )
        )
        await db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Favorito não encontrado")
    return Response(status_code=204)


# ---------- etiquetas ----------

@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int, payload: LabelSchema, user: User = Depends(get_current_user)
):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        _require_phase(edict, "avaliacao")
        # atualiza a cor das etiquetas do mesmo autor e rótulo em outras inscrições
        others = (
            await db.execute(
                select(Label).where(
                    Label.user_id == user.id,
                    Label.label == payload.label,
                    Label.context_type == "candidate",
                )
            )
        ).scalars().all()
        for l in others:
            l.color = payload.color
        l = Label(
            user_id=user.id,
            submission_id=submission_id,
            label=payload.label,
            color=payload.color,
            context_type="candidate",
        )
        db.add(l)
        await db.commit()
        await db.refresh(l)
        return {
            "id": l.id,
            "user": {"id": user.id, "name": user.name},
            "submission_id": submission_id,
            "label": l.label,
            "color": l.color,
        }


@router.get("/submissions/{submission_id}/labels")
async def get_labels(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        await _get_submission(db, submission_id)
        rows = (
            await db.execute(
                select(Label)
                .where(Label.user_id == user.id, Label.context_type == "candidate")
                .order_by(Label.id)
            )
        ).scalars().all()
        seen = {}
        for l in rows:
            seen.setdefault((l.label, l.color), l)
        return {
            "labels": [
                {"id": l.id, "label": l.label, "color": l.color} for l in seen.values()
            ]
        }


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        l = await db.get(Label, label_id)
        if l is None:
            raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
        if l.user_id != user.id:
            raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
        await db.delete(l)
        await db.commit()
    return Response(status_code=204)


# ---------- notas privadas ----------

@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int, payload: PrivateNoteSchema, user: User = Depends(get_current_user)
):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        _require_phase(edict, "avaliacao")
        note = (
            await db.execute(
                select(PrivateNote).where(
                    PrivateNote.user_id == user.id,
                    PrivateNote.submission_id == submission_id,
                )
            )
        ).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if note is None:
            note = PrivateNote(
                user_id=user.id,
                submission_id=submission_id,
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


# ---------- visualizações ----------

@router.post("/submissions/{submission_id}/view")
async def register_view(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        await _get_submission(db, submission_id)
        now = datetime.now(timezone.utc)
        today = now.astimezone(SP_TZ).date()
        views = (
            await db.execute(
                select(SubmissionView).where(
                    SubmissionView.user_id == user.id,
                    SubmissionView.submission_id == submission_id,
                )
            )
        ).scalars().all()
        for v in views:
            if v.created_at and v.created_at.astimezone(SP_TZ).date() == today:
                v.updated_at = now
                await db.commit()
                return {"message": "Visualização registrada"}
        db.add(
            SubmissionView(
                user_id=user.id,
                submission_id=submission_id,
                created_at=now,
                updated_at=now,
            )
        )
        await db.commit()
    return {"message": "Visualização registrada"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        await _get_submission(db, submission_id)
        views = (
            await db.execute(
                select(SubmissionView)
                .where(SubmissionView.submission_id == submission_id)
                .order_by(SubmissionView.id)
            )
        ).scalars().all()
        out = []
        for v in views:
            u = await db.get(User, v.user_id)
            out.append(
                {
                    "id": v.id,
                    "user_id": v.user_id,
                    "user": {"id": u.id, "name": u.name} if u else None,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "updated_at": v.updated_at.isoformat() if v.updated_at else None,
                }
            )
        return out


# ---------- seleção e resultado ----------

@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int, payload: StatsSchema, user: User = Depends(get_current_user)
):
    require_admin(user)
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        if not edict.is_open:
            raise HTTPException(status_code=409, detail="Edital encerrado")
        if payload.stats == "approved":
            if not payload.user_ids or len(payload.user_ids) != 1:
                raise HTTPException(status_code=422, detail="Informe exatamente um orientador")
            advisor = await db.get(User, payload.user_ids[0])
            if advisor is None:
                raise HTTPException(status_code=422, detail="Orientador inexistente")
            sub.advisor_id = advisor.id
        sub.stats = payload.stats
        sub.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return f"Submissão marcada como {payload.stats}"


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int, payload: BiddingSchema, user: User = Depends(get_current_user)
):
    target_id = user.id
    if payload.user_id is not None and user.role in ADMIN_ROLES:
        target_id = payload.user_id
    async with SessionLocal() as db:
        await _get_submission(db, submission_id)
        await db.execute(
            delete(Label).where(
                Label.user_id == target_id,
                Label.submission_id == submission_id,
                Label.context_type == "bidding",
            )
        )
        if payload.bidding != "":
            db.add(
                Label(
                    user_id=target_id,
                    submission_id=submission_id,
                    label=payload.bidding,
                    color="",
                    context_type="bidding",
                )
            )
        await db.commit()
    return f"Interesse atualizado para {payload.bidding}"


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int, payload: EntrySemesterSchema, user: User = Depends(get_current_user)
):
    value = payload.semester.strip()
    norm = value.lower()
    if norm in ("first", "primeiro", "primeiro semestre", "1"):
        value = "Primeiro semestre."
    elif norm in ("second", "segundo", "segundo semestre", "2"):
        value = "Segundo semestre."
    async with SessionLocal() as db:
        sub, _ = await _get_submission(db, submission_id)
        sub.entry_semester = value
        sub.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return value


# ---------- anexos ----------

def _find_upload(filename: str) -> str | None:
    candidates = [
        os.path.join(UPLOADS_ROOT, filename),
        os.path.join(UPLOADS_ROOT, "uploads", filename),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    for root, _dirs, files in os.walk(UPLOADS_ROOT):
        if filename in files:
            return os.path.join(root, filename)
    return None


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(submission_id: int, label: str, filename: str, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
    async with FormsSessionLocal() as fdb:
        details = await forms_db.get_response_details(fdb, sub.candidate_form_id)
    target = None
    for d in details:
        if d.get("type") != "File" or not d.get("value"):
            continue
        names = {d.get("name", ""), forms_db._pick(d.get("label"))}
        value = str(d["value"])
        if label in names and (
            value == filename or os.path.basename(value) == filename
        ):
            target = value
            break
    if target is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    path = _find_upload(os.path.basename(target)) or (
        target if os.path.isabs(target) and os.path.isfile(target) else None
    )
    if path is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    from fastapi.responses import FileResponse

    return FileResponse(
        path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{os.path.basename(path)}"'
        },
    )


# ---------- e-mails ----------

@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int, payload: RequestReesend, user: User = Depends(get_current_user)
):
    require_admin(user)
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        _require_phase(edict, "homologacao")
    async with FormsSessionLocal() as fdb:
        resp = await forms_db.get_response(fdb, sub.candidate_form_id)
        if resp is None:
            raise HTTPException(status_code=404, detail="Resposta não encontrada")
        await forms_db.reopen_response(fdb, sub.candidate_form_id)
    link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua inscrição precisa de correção. Motivo: {payload.text}</p>"
        f'<p>Acesse o formulário para corrigir e reenviar: <a href="{link}">{link}</a></p>'
    )
    await asyncio.to_thread(
        mail.send_email,
        resp["email"],
        "Solicitação de correção da inscrição",
        html,
        bcc=[user.email],
    )
    return {
        "message": "Solicitação de correção enviada",
        "email_sent": resp["email"],
    }


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        if sub.stats != "approved":
            raise HTTPException(status_code=400, detail="Candidatura não aprovada")
        if sub.accept_form_id:
            raise HTTPException(status_code=400, detail="Aceite já enviado")
        if not edict.accept_forms:
            raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
    async with FormsSessionLocal() as fdb:
        resp = await forms_db.get_response(fdb, sub.candidate_form_id)
        if resp is None:
            raise HTTPException(status_code=404, detail="Resposta não encontrada")
        details = await forms_db.get_response_details(fdb, sub.candidate_form_id)
        summ = extract_summary(details, resp["email"])
        created = await forms_db.create_accept_response(
            fdb, int(edict.accept_forms), resp["email"], edict.closed_date
        )
    async with SessionLocal() as db:
        sub = await db.get(Submission, submission_id)
        sub.accept_form_id = created["response_id"]
        await db.commit()
        advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    link = f"{settings.base_url.rstrip('/')}/form/{created['shared_token']}"
    html = (
        f"<p>Prezado(a) {summ['name'] or summ['email']},</p>"
        f"<p>Parabéns! Sua candidatura foi aprovada. Preencha o formulário de aceite "
        f"até {edict.closed_date.isoformat()}.</p>"
        f"<p>Dear candidate, your application was approved. Please fill the acceptance "
        f"form until {edict.closed_date.isoformat()}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
    )
    await asyncio.to_thread(
        mail.send_email,
        resp["email"],
        "Formulário de aceite - Programa de Pós-Graduação",
        html,
        cc=[advisor.email] if advisor and advisor.email else None,
    )
    return {
        "message": "Formulário de aceite enviado",
        "email_sent": resp["email"],
    }


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user: User = Depends(get_current_user)):
    async with SessionLocal() as db:
        sub, edict = await _get_submission(db, submission_id)
        if sub.stats != "approved":
            raise HTTPException(status_code=400, detail="Candidatura não aprovada")
        if sub.letter_sent:
            raise HTTPException(status_code=400, detail="Carta já enviada")
        advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    async with FormsSessionLocal() as fdb:
        resp = await forms_db.get_response(fdb, sub.candidate_form_id)
        details = await forms_db.get_response_details(fdb, sub.candidate_form_id)
        summ = extract_summary(details, (resp or {}).get("email") or "")
    email = (resp or {}).get("email") or summ["email"]
    semester = sub.entry_semester or summ["research"]["semester"] or ""
    html = (
        "<html><body>"
        f"<p>Prezado(a) {summ['name'] or email},</p>"
        f"<p>Informamos que sua candidatura ao programa de pós-graduação foi <b>aprovada</b>.</p>"
        f"<p>Orientador(a): {advisor.name if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {edict.year}</p>"
        '<p><img src="cid:signature" alt="Assinatura"></p>'
        "</body></html>"
    )
    await asyncio.to_thread(
        mail.send_email,
        email,
        "Carta de aceite - Programa de Pós-Graduação",
        html,
        cc=[advisor.email] if advisor and advisor.email else None,
        image_path="data/signature.png",
    )
    async with SessionLocal() as db:
        sub = await db.get(Submission, submission_id)
        sub.letter_sent = True
        await db.commit()
    return {"message": "Carta de aceite enviada", "email_sent": email}
