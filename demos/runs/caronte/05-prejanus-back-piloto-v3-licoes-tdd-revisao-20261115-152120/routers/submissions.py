import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from deps import ADMIN_ROLES, get_current_user, get_db, get_forms_db, require_admin
from models import Comment, Edict, Favorite, Label, PrivateNote, Submission, \
    SubmissionView, User
from services import forms_db, mailer
from services.mapping import extract_candidate, extract_recommender
from services.submissions import (
    build_submission_form,
    build_summary,
    get_mapping,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])

UPLOADS_DIR = "/shared/uploads"
SP_TZ = ZoneInfo("America/Sao_Paulo")


async def _load_submission(db: AsyncSession, submission_id: int):
    sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    edict = await db.get(Edict, sub.edict_id)
    return sub, edict


def _require_phase(edict: Edict, phase: str):
    if edict.phase != phase:
        raise HTTPException(
            status_code=400,
            detail=f"Operação disponível apenas na fase {phase}",
        )


async def _candidate_data(fdb: AsyncSession, sub: Submission):
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp is None:
        raise HTTPException(status_code=404, detail="Resposta do candidato não encontrada")
    data = await forms_db.get_response_data(fdb, resp["id"])
    return resp, data


@router.get("/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    resp, data = await _candidate_data(fdb, sub)
    summary = await build_summary(db, fdb, edict, sub, resp, data, user)
    submission_form = await build_submission_form(
        fdb, edict.candidate_forms, sub.candidate_form_version, resp["id"]
    )
    out = {"summary": summary, "submission_form": submission_form}
    if include_comments:
        comments = (
            await db.execute(
                select(Comment)
                .where(Comment.submission_id == sub.id)
                .order_by(Comment.created_at)
            )
        ).scalars().all()
        out["comments"] = [
            {
                "id": c.id,
                "user": {"id": c.user_id, "name": None},
                "submission_id": c.submission_id,
                "comment": c.comment,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in comments
        ]
    return out


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    sub, _edict = await _load_submission(db, submission_id)
    _resp, data = await _candidate_data(fdb, sub)
    field = None
    for f in data["fields"].values():
        if f["name"] == label and str(f["type"]).lower() == "file":
            field = f
            break
    if field is None or data["values"].get(field["id"]) != filename:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    root = Path(UPLOADS_DIR)
    if not root.is_dir():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    for dirpath, _dirnames, filenames in os.walk(root):
        if filename in filenames:
            path = Path(dirpath) / filename
            resolved = path.resolve()
            if UPLOADS_DIR not in str(resolved):
                raise HTTPException(status_code=404, detail="Arquivo não encontrado")
            return FileResponse(
                resolved, media_type="application/pdf", filename=filename
            )
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


# ------------------------------------------------------------------ comentários

class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@router.post("/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    body: CommentSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    _require_phase(edict, "avaliacao")
    comment = Comment(
        user_id=user.id,
        submission_id=sub.id,
        comment=body.comment,
        created_at=body.created_at or datetime.now(SP_TZ),
        updated_at=body.updated_at,
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


@router.get("/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    sub, _edict = await _load_submission(db, submission_id)
    events = []
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    if resp is not None and resp.get("submitted_at"):
        data = await forms_db.get_response_data(fdb, resp["id"])
        cand = extract_candidate(None, data["values"], data["fields"])
        events.append(
            {
                "id": None,
                "user": {"id": None, "name": cand["name"]},
                "type": "submission",
                "comment": "Candidatura submetida",
                "created_at": resp["submitted_at"],
            }
        )
    rec_mapping = await get_mapping(db, sub.edict_id, "recommender")
    for rid in sub.recommender_form_ids or []:
        rec = await forms_db.get_response(fdb, rid)
        if rec is None or not rec.get("submitted_at"):
            continue
        rdata = await forms_db.get_response_data(fdb, rid)
        ext = extract_recommender(
            rec_mapping.mapping if rec_mapping else None,
            rdata["values"],
            rdata["fields"],
            rec["email"],
        )
        events.append(
            {
                "id": None,
                "user": {"id": None, "name": ext["recommender_name"]},
                "type": "recommendation",
                "comment": "Recomendação recebida",
                "created_at": rec["submitted_at"],
            }
        )
    if sub.accept_form_id:
        acc = await forms_db.get_response(fdb, sub.accept_form_id)
        if acc is not None and acc.get("submitted_at"):
            events.append(
                {
                    "id": None,
                    "user": {"id": None, "name": None},
                    "type": "accept",
                    "comment": "Formulário de aceite respondido",
                    "created_at": acc["submitted_at"],
                }
            )
    comments = (
        await db.execute(
            select(Comment)
            .where(Comment.submission_id == sub.id)
            .order_by(Comment.created_at)
        )
    ).scalars().all()
    for c in comments:
        author = await db.get(User, c.user_id)
        events.append(
            {
                "id": c.id,
                "user": {"id": c.user_id, "name": author.name if author else None},
                "type": "comment",
                "comment": c.comment,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
        )
    def _sort_key(event):
        dt = event["created_at"]
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    events.sort(key=_sort_key)
    return events


@router.delete("/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
    await db.delete(comment)
    await db.commit()
    return None


# -------------------------------------------------------------------- favoritos

@router.post("/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    _require_phase(edict, "avaliacao")
    existing = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == sub.id
            )
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Favorito já registrado")
    db.add(
        Favorite(user_id=user.id, submission_id=sub.id, created_at=datetime.now(SP_TZ))
    )
    await db.commit()
    return "Favorito registrado com sucesso"


@router.delete("/{submission_id}/favorites", status_code=204)
async def remove_favorite(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == submission_id
            )
        )
    ).scalars().first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
    await db.delete(existing)
    await db.commit()
    return None


# -------------------------------------------------------------------- etiquetas

class LabelInputSchema(BaseModel):
    label: str
    color: str


@router.post("/{submission_id}/labels")
async def add_label(
    submission_id: int,
    body: LabelInputSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    _require_phase(edict, "avaliacao")
    label = Label(
        user_id=user.id,
        submission_id=sub.id,
        label=body.label,
        color=body.color,
        context_type="candidate",
    )
    db.add(label)
    await db.flush()
    others = (
        await db.execute(
            select(Label).where(
                Label.user_id == user.id,
                Label.label == body.label,
                Label.context_type == "candidate",
            )
        )
    ).scalars().all()
    for other in others:
        other.color = body.color
    await db.commit()
    return {
        "id": label.id,
        "user": {"id": user.id, "name": user.name},
        "submission_id": sub.id,
        "label": label.label,
        "color": label.color,
    }


@router.get("/{submission_id}/labels")
async def get_labels(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_submission(db, submission_id)
    rows = (
        await db.execute(
            select(Label)
            .where(Label.user_id == user.id, Label.context_type == "candidate")
            .order_by(Label.id)
        )
    ).scalars().all()
    catalog: dict[str, Label] = {}
    for row in rows:
        catalog[row.label] = row
    return {
        "labels": [
            {"id": row.id, "label": row.label, "color": row.color}
            for row in catalog.values()
        ]
    }


@router.delete("/label/{label_id}", status_code=204)
async def remove_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if label.user_id != user.id:
        raise HTTPException(status_code=403, detail="Apenas o autor pode excluir")
    await db.delete(label)
    await db.commit()
    return None


# --------------------------------------------------------------- notas privadas

class PrivateNoteSchema(BaseModel):
    note: str


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    body: PrivateNoteSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    _require_phase(edict, "avaliacao")
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user.id,
                PrivateNote.submission_id == sub.id,
            )
        )
    ).scalars().first()
    if note is None:
        note = PrivateNote(
            user_id=user.id,
            submission_id=sub.id,
            note=body.note,
            created_at=datetime.now(SP_TZ),
        )
        db.add(note)
    else:
        note.note = body.note
        note.updated_at = datetime.now(SP_TZ)
    await db.commit()
    return {"note": note.note}


# --------------------------------------------------------------- visualizações

@router.post("/{submission_id}/view")
async def register_view(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, _edict = await _load_submission(db, submission_id)
    today = datetime.now(SP_TZ).date()
    views = (
        await db.execute(
            select(SubmissionView).where(
                SubmissionView.user_id == user.id,
                SubmissionView.submission_id == sub.id,
            )
        )
    ).scalars().all()
    exists_today = any(
        v.created_at and v.created_at.astimezone(SP_TZ).date() == today
        for v in views
    )
    if not exists_today:
        db.add(
            SubmissionView(
                user_id=user.id,
                submission_id=sub.id,
                created_at=datetime.now(SP_TZ),
                updated_at=datetime.now(SP_TZ),
            )
        )
        await db.commit()
    return {"message": "Visualização registrada"}


@router.get("/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_submission(db, submission_id)
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
                "user": {"id": v.user_id, "name": u.name if u else None},
                "user_id": v.user_id,
                "created_at": v.created_at,
                "updated_at": v.updated_at,
            }
        )
    return out


# -------------------------------------------------------------------- seleção

class StatsSchema(BaseModel):
    user_ids: list[int] | None
    stats: str


@router.post("/{submission_id}/select")
async def select_stats(
    submission_id: int,
    body: StatsSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    sub, edict = await _load_submission(db, submission_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edital encerrado")
    if body.stats == "approved":
        if not isinstance(body.user_ids, list) or len(body.user_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="Aprovação exige exatamente um orientador",
            )
        advisor = await db.get(User, body.user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=404, detail="Orientador não encontrado")
        sub.advisor_id = advisor.id
    sub.stats = body.stats
    sub.updated_at = datetime.now(SP_TZ)
    await db.commit()
    return f"Situação atualizada para {body.stats}"


BIDDING_VALUES = (
    "decline",
    "available",
    "interested",
    "agreed",
    "interested_scholarship",
    "",
)


class BiddingSchema(BaseModel):
    bidding: str
    user_id: int | None = None


@router.post("/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    body: BiddingSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Valor de interesse inválido")
    sub, _edict = await _load_submission(db, submission_id)
    target_id = user.id
    if user.role in ADMIN_ROLES and body.user_id is not None:
        target_id = body.user_id
    await db.execute(
        sa_delete(Label).where(
            Label.submission_id == sub.id,
            Label.user_id == target_id,
            Label.context_type == "bidding",
        )
    )
    if body.bidding != "":
        db.add(
            Label(
                user_id=target_id,
                submission_id=sub.id,
                label=body.bidding,
                color="",
                context_type="bidding",
            )
        )
    await db.commit()
    return f"Interesse atualizado para {body.bidding or 'vazio'}"


class EntrySemesterSchema(BaseModel):
    semester: str


def _normalize_semester(value: str) -> str:
    raw = (value or "").strip().lower()
    if raw in ("first", "primeiro", "1", "1o", "1º"):
        return "Primeiro semestre."
    if raw in ("second", "segundo", "2", "2o", "2º"):
        return "Segundo semestre."
    return value


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    body: EntrySemesterSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub, _edict = await _load_submission(db, submission_id)
    sub.entry_semester = _normalize_semester(body.semester)
    sub.updated_at = datetime.now(SP_TZ)
    await db.commit()
    return sub.entry_semester


# ------------------------------------------------------------------ comunicação

class RequestReesendSchema(BaseModel):
    text: str


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    body: RequestReesendSchema,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(require_admin),
):
    sub, edict = await _load_submission(db, submission_id)
    _require_phase(edict, "homologacao")
    resp, data = await _candidate_data(fdb, sub)
    await forms_db.reopen_response(fdb, resp["id"])
    link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
    mapping = await get_mapping(db, edict.id, "candidate", sub.candidate_form_version)
    if mapping is None:
        mapping = await get_mapping(db, edict.id, "candidate")
    cand = extract_candidate(
        mapping.mapping if mapping else None, data["values"], data["fields"]
    )
    to = cand["email"] or resp["email"] or ""
    mailer.send_resubmission(to=to, bcc=user.email or "", text=body.text, link=link)
    return {
        "message": "Solicitação de correção enviada",
        "email_sent": to,
    }


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    if not edict.accept_forms:
        raise HTTPException(
            status_code=404, detail="Formulário de aceite não configurado"
        )
    if sub.stats != "approved":
        raise HTTPException(
            status_code=400, detail="Candidatura não aprovada"
        )
    resp, data = await _candidate_data(fdb, sub)
    mapping = await get_mapping(db, edict.id, "candidate", sub.candidate_form_version)
    if mapping is None:
        mapping = await get_mapping(db, edict.id, "candidate")
    cand = extract_candidate(
        mapping.mapping if mapping else None, data["values"], data["fields"]
    )
    to = cand["email"] or resp["email"] or ""
    if sub.accept_form_id:
        return {
            "message": "Formulário de aceite já enviado",
            "email_sent": to,
        }
    accept_form_id = int(edict.accept_forms)
    form = await forms_db.get_form(fdb, accept_form_id)
    created = await forms_db.create_shared_response(
        fdb,
        accept_form_id,
        to,
        datetime.combine(edict.closed_date, datetime.max.time())
        if edict.closed_date
        else None,
        form_version=form["version"] if form else 1,
    )
    sub.accept_form_id = created["response_id"]
    sub.updated_at = datetime.now(SP_TZ)
    await db.commit()
    link = f"{settings.base_url.rstrip('/')}/form/{created['token']}"
    cc = []
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor and advisor.email:
            cc.append(advisor.email)
    mailer.send_accept_form(
        to=to,
        cc=cc,
        name=cand["name"] or to,
        deadline=edict.closed_date.isoformat() if edict.closed_date else "—",
        link=link,
    )
    return {
        "message": "Formulário de aceite enviado",
        "email_sent": to,
    }


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
    user: User = Depends(get_current_user),
):
    sub, edict = await _load_submission(db, submission_id)
    if sub.stats != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub.letter_sent:
        raise HTTPException(status_code=400, detail="Carta já enviada")
    resp, data = await _candidate_data(fdb, sub)
    mapping = await get_mapping(db, edict.id, "candidate", sub.candidate_form_version)
    if mapping is None:
        mapping = await get_mapping(db, edict.id, "candidate")
    cand = extract_candidate(
        mapping.mapping if mapping else None, data["values"], data["fields"]
    )
    to = cand["email"] or resp["email"] or ""
    advisor_name = ""
    cc = []
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor:
            advisor_name = advisor.name
            if advisor.email:
                cc.append(advisor.email)
    semester = sub.entry_semester or cand["research"]["semester"] or ""
    signature = None
    sig_path = Path("data/signature.png")
    if sig_path.is_file():
        signature = sig_path.read_bytes()
    mailer.send_accept_letter(
        to=to,
        cc=cc,
        name=cand["name"] or to,
        advisor=advisor_name,
        semester=semester,
        year=edict.year,
        signature=signature,
    )
    sub.letter_sent = True
    sub.updated_at = datetime.now(SP_TZ)
    await db.commit()
    return {
        "message": "Carta de aceite enviada",
        "email_sent": to,
    }
