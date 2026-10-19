import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ADMIN_ROLES, get_current_user
from config import settings
from database import get_db, get_forms_db
from services import forms_service, mailer
from services import submission_builder as sb

router = APIRouter(tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")
UPLOADS_DIR = Path("/shared/uploads")


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
    stats: str


class BiddingSchema(BaseModel):
    bidding: str
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


async def _get_submission_or_404(db: AsyncSession, submission_id: int):
    sub = await sb.get_submission(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _edict_of(db: AsyncSession, sub: dict):
    edict = await sb.get_edict(db, sub["edict_id"])
    if not edict:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict


# ---------------------------------------------------------------------------
# Detalhe e anexos
# ---------------------------------------------------------------------------


@router.get("/submissions/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    item = await sb.build_submission_view(db, fdb, edict, sub, user)

    note = await db.execute(
        text(
            "select note from private_note where user_id = :uid and submission_id = :sid"
        ),
        {"uid": user["id"], "sid": submission_id},
    )
    note_row = note.first()

    summary = dict(item)
    summary["private_note"] = note_row[0] if note_row else ""
    summary["entry_semester"] = sub.get("entry_semester") or ""
    summary["letter_sent"] = sub.get("letter_sent", False)
    summary["bidding"] = await sb.user_bidding(db, user["id"], submission_id)
    try:
        summary["recommendations"] = await sb.build_recommendations(db, fdb, edict, sub)
    except Exception:
        logging.exception("falha ao consultar recomendações da inscrição %s", submission_id)
        summary["recommendations"] = []
    if include_comments:
        summary["comments"] = await _activity(db, fdb, edict, sub)

    # formulário completo com valores
    form_id = sb._to_int(edict.get("candidate_forms"))
    sections_out = []
    if form_id is not None:
        response = await forms_service.get_response(fdb, sub["candidate_form_id"])
        values = (response or {}).get("values") or {}
        sections = await forms_service.select_sections(
            fdb, form_id, sub["candidate_form_version"]
        )
        for section in sections:
            title = section.get("title") or {}
            fields = await forms_service.select_fields(
                fdb, section["id"], sub["candidate_form_version"]
            )
            for field in fields:
                field["value"] = values.get(field["id"])
            sections_out.append(
                {
                    "id": section["id"],
                    "title": title.get("pt") or title.get("en") or "",
                    "position": section["position"],
                    "fields": fields,
                }
            )
    return {"summary": summary, "submission_form": sections_out}


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    form_id = sb._to_int(edict.get("candidate_forms"))
    if form_id is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    response = await forms_service.get_response(fdb, sub["candidate_form_id"])
    values = (response or {}).get("values") or {}
    sections = await forms_service.select_sections(
        fdb, form_id, sub["candidate_form_version"]
    )
    value = None
    for section in sections:
        for field in await forms_service.select_fields(
            fdb, section["id"], sub["candidate_form_version"]
        ):
            if field["name"] == label:
                value = values.get(field["id"])
                break
        if value is not None:
            break
    if not value or os.path.basename(value) != filename:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    path = _locate_upload(value)
    if path is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, media_type="application/pdf", filename=filename)


def _locate_upload(value: str):
    candidate = (UPLOADS_DIR / value).resolve()
    try:
        candidate.relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    name = os.path.basename(value)
    for root, _dirs, files in os.walk(UPLOADS_DIR):
        if name in files:
            return Path(root) / name
    return None


# ---------------------------------------------------------------------------
# Comentários e atividade
# ---------------------------------------------------------------------------


async def _activity(db: AsyncSession, fdb: AsyncSession, edict: dict, sub: dict):
    events = []
    rows = await db.execute(
        text(
            "select c.id, c.comment, c.created_at, u.id as uid, u.name as uname "
            "from comment c join \"user\" u on u.id = c.user_id "
            "where c.submission_id = :sid order by c.created_at, c.id"
        ),
        {"sid": sub["id"]},
    )
    for row in rows:
        events.append(
            {
                "user": {"id": row.uid, "name": row.uname},
                "text": row.comment,
                "type": "comment",
                "created_at": row.created_at,
            }
        )

    try:
        response = await forms_service.get_response(fdb, sub["candidate_form_id"])
        if response and response.get("submitted_at"):
            mapping = await sb.get_mapping(
                db, edict["id"], "candidate", sub["candidate_form_version"]
            )
            data = sb.build_summary_data(
                mapping.get("mapping") if mapping else {}, response["values"]
            )
            events.append(
                {
                    "user": {"id": None, "name": data.get("name") or ""},
                    "text": "Candidatura enviada",
                    "type": "submission",
                    "created_at": response["submitted_at"],
                }
            )
    except Exception:
        logging.exception("falha ao consultar evento de candidatura %s", sub["id"])

    recommender_form_id = sb._to_int(edict.get("recommenders_forms"))
    ids = sub.get("recommender_form_ids") or []
    if isinstance(ids, str):
        import json as _json

        ids = _json.loads(ids or "[]")
    try:
        if recommender_form_id is not None and ids:
            rec_responses = await forms_service.get_form_responses(fdb, recommender_form_id)
            for response_id in ids:
                meta = rec_responses.get(response_id)
                if meta and meta.get("submitted_at"):
                    events.append(
                        {
                            "user": {"id": None, "name": meta.get("email") or ""},
                            "text": "Recomendação enviada",
                            "type": "recommendation",
                            "created_at": meta["submitted_at"],
                        }
                    )
    except Exception:
        logging.exception("falha ao consultar recomendações da inscrição %s", sub["id"])

    try:
        if sub.get("accept_form_id"):
            accept = await forms_service.get_response(fdb, sub["accept_form_id"])
            if accept and accept.get("submitted_at"):
                events.append(
                    {
                        "user": {"id": None, "name": accept.get("email") or ""},
                        "text": "Aceite respondido",
                        "type": "accept",
                        "created_at": accept["submitted_at"],
                    }
                )
    except Exception:
        logging.exception("falha ao consultar aceite da inscrição %s", sub["id"])

    events.sort(key=lambda e: (e["created_at"] is None, e["created_at"]))
    return events


@router.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    if edict["phase"] != "avaliacao":
        raise HTTPException(status_code=400, detail="Fora da fase de avaliação")
    now = datetime.now(timezone.utc)
    row = await db.execute(
        text(
            "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
            "values (:uid, :sid, :comment, :created, :updated) "
            "returning id, user_id, submission_id, comment, created_at, updated_at"
        ),
        {
            "uid": user["id"],
            "sid": submission_id,
            "comment": payload.comment,
            "created": payload.created_at or now,
            "updated": payload.updated_at or now,
        },
    )
    await db.commit()
    data = dict(row.first()._mapping)
    return {
        "id": data["id"],
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": data["submission_id"],
        "comment": data["comment"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }


@router.get("/submissions/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    return await _activity(db, fdb, edict, sub)


@router.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(
    comment_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        text("select id, user_id from comment where id = :cid"), {"cid": comment_id}
    )
    row = row.first()
    if not row:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if row.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Somente o autor pode excluir")
    await db.execute(text("delete from comment where id = :cid"), {"cid": comment_id})
    await db.commit()
    return None


# ---------------------------------------------------------------------------
# Favoritos, etiquetas, notas, visualizações
# ---------------------------------------------------------------------------


@router.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    try:
        await db.execute(
            text(
                "insert into favorites (user_id, submission_id, created_at) "
                "values (:uid, :sid, now())"
            ),
            {"uid": user["id"], "sid": submission_id},
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Favorito já existe")
    return {"message": "Favorito criado"}


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    row = await db.execute(
        text(
            "select 1 from favorites where user_id = :uid and submission_id = :sid"
        ),
        {"uid": user["id"], "sid": submission_id},
    )
    if not row.first():
        raise HTTPException(status_code=404, detail="Favorito não existe")
    await db.execute(
        text("delete from favorites where user_id = :uid and submission_id = :sid"),
        {"uid": user["id"], "sid": submission_id},
    )
    await db.commit()
    return None


@router.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    row = await db.execute(
        text(
            "insert into labels (user_id, submission_id, label, color, context_type) "
            "values (:uid, :sid, :label, :color, 'candidate') "
            "returning id, user_id, submission_id, label, color"
        ),
        {
            "uid": user["id"],
            "sid": submission_id,
            "label": payload.label,
            "color": payload.color,
        },
    )
    await db.execute(
        text(
            "update labels set color = :color where user_id = :uid and label = :label "
            "and coalesce(context_type, 'candidate') = 'candidate'"
        ),
        {"uid": user["id"], "label": payload.label, "color": payload.color},
    )
    await db.commit()
    data = dict(row.first()._mapping)
    return {
        "id": data["id"],
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": data["submission_id"],
        "label": data["label"],
        "color": data["color"],
    }


@router.get("/submissions/{submission_id}/labels")
async def get_label(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    rows = await db.execute(
        text(
            "select min(id) as id, label, max(color) as color from labels "
            "where user_id = :uid and coalesce(context_type, 'candidate') = 'candidate' "
            "group by label order by id"
        ),
        {"uid": user["id"]},
    )
    return {"labels": [dict(r._mapping) for r in rows]}


@router.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(
    label_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        text("select id, user_id from labels where id = :lid"), {"lid": label_id}
    )
    row = row.first()
    if not row:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if row.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Somente o autor pode excluir")
    await db.execute(text("delete from labels where id = :lid"), {"lid": label_id})
    await db.commit()
    return None


@router.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    row = await db.execute(
        text(
            "select id from private_note where user_id = :uid and submission_id = :sid"
        ),
        {"uid": user["id"], "sid": submission_id},
    )
    if row.first():
        await db.execute(
            text(
                "update private_note set note = :note, updated_at = now() "
                "where user_id = :uid and submission_id = :sid"
            ),
            {"note": payload.note, "uid": user["id"], "sid": submission_id},
        )
    else:
        await db.execute(
            text(
                "insert into private_note (user_id, submission_id, note, created_at) "
                "values (:uid, :sid, :note, now())"
            ),
            {"uid": user["id"], "sid": submission_id, "note": payload.note},
        )
    await db.commit()
    return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
async def register_view(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    today = datetime.now(SP_TZ).date()
    row = await db.execute(
        text(
            "select id from submission_view where user_id = :uid and submission_id = :sid "
            "and (created_at at time zone 'America/Sao_Paulo')::date = :d"
        ),
        {"uid": user["id"], "sid": submission_id, "d": today},
    )
    if not row.first():
        await db.execute(
            text(
                "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                "values (:uid, :sid, now(), now())"
            ),
            {"uid": user["id"], "sid": submission_id},
        )
        await db.commit()
    return {"message": "Visualização registrada"}


@router.get("/submissions/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    rows = await db.execute(
        text(
            "select v.id, v.user_id, u.name, v.created_at, v.updated_at from submission_view v "
            'join "user" u on u.id = v.user_id where v.submission_id = :sid order by v.created_at'
        ),
        {"sid": submission_id},
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user": {"id": r.user_id, "name": r.name},
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Seleção, interesses e semestre
# ---------------------------------------------------------------------------


@router.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital encerrado")
    if payload.stats not in ("approved", "refused", "underreview", "waitlist"):
        raise HTTPException(status_code=422, detail="Situação inválida")
    advisor_id = None
    if payload.stats == "approved":
        user_ids = payload.user_ids or []
        if len(user_ids) != 1:
            raise HTTPException(status_code=422, detail="Aprovação exige um orientador")
        advisor = await sb.get_user(db, user_ids[0])
        if not advisor:
            raise HTTPException(status_code=404, detail="Orientador não encontrado")
        advisor_id = advisor["id"]
    await db.execute(
        text(
            "update submission set stats = :stats, advisor_id = :advisor, updated_at = now() "
            "where id = :sid"
        ),
        {"stats": payload.stats, "advisor": advisor_id, "sid": submission_id},
    )
    await db.commit()
    return payload.stats


@router.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    valid = {
        "decline",
        "available",
        "interested",
        "agreed",
        "interested_scholarship",
        "",
    }
    if payload.bidding not in valid:
        raise HTTPException(status_code=422, detail="Interesse inválido")
    target_id = user["id"]
    if payload.user_id is not None and user["role"] in ADMIN_ROLES:
        target_id = payload.user_id
    await db.execute(
        text(
            "delete from labels where user_id = :uid and submission_id = :sid "
            "and context_type = 'bidding'"
        ),
        {"uid": target_id, "sid": submission_id},
    )
    if payload.bidding != "":
        await db.execute(
            text(
                "insert into labels (user_id, submission_id, label, color, context_type) "
                "values (:uid, :sid, :label, '', 'bidding')"
            ),
            {"uid": target_id, "sid": submission_id, "label": payload.bidding},
        )
    await db.commit()
    return payload.bidding


@router.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    raw = (payload.semester or "").strip().lower()
    if "primeiro" in raw or "first" in raw:
        semester = "Primeiro semestre."
    elif "segundo" in raw or "second" in raw:
        semester = "Segundo semestre."
    else:
        semester = payload.semester
    await db.execute(
        text(
            "update submission set entry_semester = :semester, updated_at = now() where id = :sid"
        ),
        {"semester": semester, "sid": submission_id},
    )
    await db.commit()
    return semester


# ---------------------------------------------------------------------------
# Comunicação: correção, aceite e carta
# ---------------------------------------------------------------------------


async def _candidate_summary(db, fdb, edict, sub):
    response = await forms_service.get_response(fdb, sub["candidate_form_id"])
    values = (response or {}).get("values") or {}
    mapping = await sb.get_mapping(db, edict["id"], "candidate", sub["candidate_form_version"])
    return sb.build_summary_data(mapping.get("mapping") if mapping else {}, values)


@router.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    if edict["phase"] != "homologacao":
        raise HTTPException(status_code=400, detail="Fora da fase de homologação")
    candidate = await _candidate_summary(db, fdb, edict, sub)
    email = candidate.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Candidato sem e-mail")

    await forms_service.reopen_response(fdb, sub["candidate_form_id"])
    response = await forms_service.get_response(fdb, sub["candidate_form_id"])
    token = (response or {}).get("token") or ""
    link = f"{settings.base_url}/form/{token}"
    html = (
        f"<p>Prezado(a) {candidate.get('name') or ''},</p>"
        f"<p>Sua candidatura precisa de correção:</p>"
        f"<p>{payload.text}</p>"
        f'<p>Acesse o formulário em: <a href="{link}">{link}</a></p>'
    )
    mailer.send_email(email, "Solicitação de correção de candidatura", html, bcc=user["email"])
    return {
        "message": "Solicitação de correção enviada",
        "email_sent": email,
    }


@router.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub.get("accept_form_id"):
        raise HTTPException(status_code=400, detail="Aceite já enviado")
    accept_form_id = sb._to_int(edict.get("accept_forms"))
    if accept_form_id is None:
        raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")

    candidate = await _candidate_summary(db, fdb, edict, sub)
    email = candidate.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Candidato sem e-mail")
    form = await forms_service.get_form(fdb, accept_form_id)
    shared = await forms_service.create_shared_response(
        fdb, accept_form_id, email, edict["closed_date"], (form or {}).get("version") or 1
    )
    await db.execute(
        text(
            "update submission set accept_form_id = :afid, updated_at = now() where id = :sid"
        ),
        {"afid": shared["response_id"], "sid": submission_id},
    )
    await db.commit()

    link = f"{settings.base_url}/form/{shared['shared_token']}"
    html = (
        f"<p>Caro(a) {candidate.get('name') or ''},</p>"
        f"<p>Parabéns! Sua candidatura foi aprovada. Preencha o formulário de aceite "
        f"até {edict['closed_date']}.</p>"
        f'<p><a href="{link}">{link}</a></p>'
        f"<p>Dear candidate, your application was approved. Please fill the acceptance "
        f"form until {edict['closed_date']} at the link above.</p>"
    )
    cc = None
    if sub.get("advisor_id"):
        advisor = await sb.get_user(db, sub["advisor_id"])
        if advisor:
            cc = advisor["email"]
    mailer.send_email(email, "Formulário de aceite", html, cc=cc)
    return {"message": "Formulário de aceite enviado", "email_sent": email}


@router.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fdb: AsyncSession = Depends(get_forms_db),
):
    sub = await _get_submission_or_404(db, submission_id)
    edict = await _edict_of(db, sub)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Candidatura não aprovada")
    if sub.get("letter_sent"):
        raise HTTPException(status_code=400, detail="Carta já enviada")

    candidate = await _candidate_summary(db, fdb, edict, sub)
    email = candidate.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Candidato sem e-mail")
    advisor = None
    if sub.get("advisor_id"):
        advisor = await sb.get_user(db, sub["advisor_id"])
    semester = sub.get("entry_semester") or ""
    html = (
        f"<p>Caro(a) {candidate.get('name') or ''},</p>"
        f"<p>Informamos que sua candidatura ao programa de pós-graduação foi aprovada.</p>"
        f"<p>Orientador(a): {advisor['name'] if advisor else '-'}</p>"
        f"<p>Ingresso: {semester} Ano: {edict['year']}</p>"
        f'<p><img src="cid:signature" alt="Assinatura"></p>'
    )
    mailer.send_email(
        email,
        "Carta de aceite",
        html,
        cc=advisor["email"] if advisor else None,
        image_path="data/signature.png",
    )
    await db.execute(
        text("update submission set letter_sent = true, updated_at = now() where id = :sid"),
        {"sid": submission_id},
    )
    await db.commit()
    return {"message": "Carta de aceite enviada", "email_sent": email}
