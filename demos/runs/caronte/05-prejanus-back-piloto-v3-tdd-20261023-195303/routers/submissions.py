import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text
from typing import Literal

from auth import ADMIN_ROLES, get_current_user, require_admin
from config import settings
from database import FormsSession, PrejanusSession
from services import forms_service, mailer
from services.common import get_edict, get_submission, get_user_row, parse_form_ids
from services.submission_data import (
    build_submission,
    build_submission_form,
    build_summary,
)

router = APIRouter(tags=["submissions"])

TZ = ZoneInfo("America/Sao_Paulo")
UPLOADS = Path("/shared/uploads")


class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LabelSchema(BaseModel):
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
    bidding: Literal["decline", "available", "interested", "agreed", "interested_scholarship", ""]
    user_id: int | None = None


class EntrySemesterSchema(BaseModel):
    semester: str


def _require_phase(ps, submission, phase):
    edict = get_edict(ps, submission["edict_id"])
    if edict is None or edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Operação disponível apenas na fase {phase}")


@router.get("/submissions/{submission_id}")
def get_details(submission_id: int, include_comments: bool = False, user=Depends(get_current_user)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        edict = get_edict(ps, sub["edict_id"])
        return {
            "summary": build_summary(ps, fs, sub, edict, user["id"], include_comments=include_comments),
            "submission_form": build_submission_form(fs, sub),
        }


@router.get("/submissions/{submission_id}/comments")
def get_all_comments(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        events = []
        rows = ps.execute(
            text(
                'select c.*, u.name as user_name from comment c join "user" u on u.id = c.user_id '
                "where c.submission_id=:s order by c.created_at, c.id"
            ),
            {"s": submission_id},
        ).mappings().all()
        for r in rows:
            events.append(
                {
                    "id": r["id"],
                    "user": {"id": r["user_id"], "name": r["user_name"]},
                    "comment": r["comment"],
                    "type": "comment",
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
            )
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        if resp and resp["submitted_at"]:
            events.append(
                {
                    "type": "submission",
                    "user": None,
                    "comment": None,
                    "created_at": resp["submitted_at"].isoformat(),
                }
            )
        rec_ids = sub["recommenders_form_ids"] or []
        if isinstance(rec_ids, str):
            rec_ids = json.loads(rec_ids)
        for rid in rec_ids:
            rec = forms_service.get_form_response(fs, rid)
            if rec and rec["submitted_at"]:
                events.append(
                    {
                        "type": "recommendation",
                        "user": None,
                        "comment": None,
                        "created_at": rec["submitted_at"].isoformat(),
                    }
                )
        if sub["accept_form_id"]:
            acc = forms_service.get_form_response(fs, sub["accept_form_id"])
            if acc and acc["submitted_at"]:
                events.append(
                    {
                        "type": "accept",
                        "user": None,
                        "comment": None,
                        "created_at": acc["submitted_at"].isoformat(),
                    }
                )
        events.sort(key=lambda e: e.get("created_at") or "")
        return events


@router.post("/submissions/{submission_id}/comments")
def add_comment(submission_id: int, payload: CommentSchema, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        _require_phase(ps, sub, "avaliacao")
        now = datetime.now(TZ)
        created = payload.created_at or now
        updated = payload.updated_at or created
        comment_id = ps.execute(
            text(
                "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
                "values (:u, :s, :c, :cr, :up) returning id"
            ),
            {"u": user["id"], "s": submission_id, "c": payload.comment, "cr": created, "up": updated},
        ).scalar()
        ps.commit()
        return {
            "id": comment_id,
            "user": {"id": user["id"], "name": user["name"]},
            "submission_id": submission_id,
            "comment": payload.comment,
            "created_at": created.isoformat(),
            "updated_at": updated.isoformat(),
        }


@router.delete("/submissions/comments/{comment_id}", status_code=204)
def remove_comment(comment_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        row = ps.execute(
            text("select * from comment where id=:i"), {"i": comment_id}
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Comentário não encontrado")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Apenas o autor pode excluir o comentário")
        ps.execute(text("delete from comment where id=:i"), {"i": comment_id})
        ps.commit()
        return Response(status_code=204)


@router.post("/submissions/{submission_id}/favorites", status_code=201)
def create_favorite(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        _require_phase(ps, sub, "avaliacao")
        existing = ps.execute(
            text("select 1 from favorites where user_id=:u and submission_id=:s"),
            {"u": user["id"], "s": submission_id},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Favorito já registrado")
        ps.execute(
            text("insert into favorites (user_id, submission_id, created_at) values (:u, :s, now())"),
            {"u": user["id"], "s": submission_id},
        )
        ps.commit()
        return "Favorito criado"


@router.delete("/submissions/{submission_id}/favorites", status_code=204)
def remove_favorite(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        existing = ps.execute(
            text("select 1 from favorites where user_id=:u and submission_id=:s"),
            {"u": user["id"], "s": submission_id},
        ).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Favorito não encontrado")
        ps.execute(
            text("delete from favorites where user_id=:u and submission_id=:s"),
            {"u": user["id"], "s": submission_id},
        )
        ps.commit()
        return Response(status_code=204)


@router.post("/submissions/{submission_id}/labels")
def add_label(submission_id: int, payload: LabelSchema, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        _require_phase(ps, sub, "avaliacao")
        label_id = ps.execute(
            text(
                "insert into labels (user_id, submission_id, label, color, context_type) "
                "values (:u, :s, :l, :c, 'candidate') returning id"
            ),
            {"u": user["id"], "s": submission_id, "l": payload.label, "c": payload.color},
        ).scalar()
        ps.execute(
            text(
                "update labels set color=:c where user_id=:u and label=:l and context_type='candidate'"
            ),
            {"c": payload.color, "u": user["id"], "l": payload.label},
        )
        ps.commit()
        return {
            "id": label_id,
            "user": {"id": user["id"], "name": user["name"]},
            "submission_id": submission_id,
            "label": payload.label,
        }


@router.get("/submissions/{submission_id}/labels")
def get_label(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        rows = ps.execute(
            text(
                "select distinct on (label) id, label, color from labels "
                "where user_id=:u and context_type='candidate' order by label, id desc"
            ),
            {"u": user["id"]},
        ).mappings().all()
        return {"labels": [{"id": r["id"], "label": r["label"], "color": r["color"]} for r in rows]}


@router.delete("/submissions/label/{label_id}", status_code=204)
def remove_label(label_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        row = ps.execute(text("select * from labels where id=:i"), {"i": label_id}).mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
        if row["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Apenas o autor pode excluir a etiqueta")
        ps.execute(text("delete from labels where id=:i"), {"i": label_id})
        ps.commit()
        return Response(status_code=204)


@router.post("/submissions/{submission_id}/private_notes")
def add_or_update_note(submission_id: int, payload: PrivateNoteSchema, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        _require_phase(ps, sub, "avaliacao")
        existing = ps.execute(
            text("select id from private_note where user_id=:u and submission_id=:s"),
            {"u": user["id"], "s": submission_id},
        ).first()
        if existing:
            ps.execute(
                text("update private_note set note=:n, updated_at=now() where id=:i"),
                {"n": payload.note, "i": existing[0]},
            )
        else:
            ps.execute(
                text(
                    "insert into private_note (user_id, submission_id, note, created_at) "
                    "values (:u, :s, :n, now())"
                ),
                {"u": user["id"], "s": submission_id, "n": payload.note},
            )
        ps.commit()
        return {"note": payload.note}


@router.post("/submissions/{submission_id}/view")
def register_view(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        today = datetime.now(TZ).date()
        existing = ps.execute(
            text(
                "select id from submission_view where user_id=:u and submission_id=:s "
                "and (created_at at time zone 'America/Sao_Paulo')::date = :d"
            ),
            {"u": user["id"], "s": submission_id, "d": today},
        ).first()
        if not existing:
            ps.execute(
                text(
                    "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                    "values (:u, :s, now(), now())"
                ),
                {"u": user["id"], "s": submission_id},
            )
            ps.commit()
        return {"message": "Visualização registrada"}


@router.get("/submissions/{submission_id}/view")
def get_submission_views(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        rows = ps.execute(
            text(
                'select v.*, u.name as user_name from submission_view v join "user" u on u.id = v.user_id '
                "where v.submission_id=:s order by v.created_at"
            ),
            {"s": submission_id},
        ).mappings().all()
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "user": {"id": r["user_id"], "name": r["user_name"]},
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ]


@router.post("/submissions/{submission_id}/select")
def select_stats(submission_id: int, payload: StatsSchema, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        if user["role"] not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
        edict = get_edict(ps, sub["edict_id"])
        if edict is not None and not edict["is_open"]:
            raise HTTPException(status_code=409, detail="Edital encerrado")
        advisor_id = sub["advisor_id"]
        if payload.stats == "approved":
            if not payload.user_ids or len(payload.user_ids) != 1:
                raise HTTPException(status_code=400, detail="Aprovação exige exatamente um orientador")
            advisor = get_user_row(ps, payload.user_ids[0])
            if advisor is None:
                raise HTTPException(status_code=400, detail="Orientador não encontrado")
            advisor_id = advisor["id"]
        ps.execute(
            text("update submission set stats=:s, advisor_id=:a, updated_at=now() where id=:i"),
            {"s": payload.stats, "a": advisor_id, "i": submission_id},
        )
        ps.commit()
        return "Situação da inscrição atualizada"


@router.post("/submissions/{submission_id}/bidding")
def toggle_bidding(submission_id: int, payload: BiddingSchema, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        target = user["id"]
        if payload.user_id is not None and user["role"] in ("administrator", "secretary", "coordinator"):
            target = payload.user_id
        if payload.bidding == "":
            ps.execute(
                text(
                    "delete from labels where user_id=:u and submission_id=:s and context_type='bidding'"
                ),
                {"u": target, "s": submission_id},
            )
        else:
            existing = ps.execute(
                text(
                    "select id from labels where user_id=:u and submission_id=:s and context_type='bidding'"
                ),
                {"u": target, "s": submission_id},
            ).first()
            if existing:
                ps.execute(
                    text("update labels set label=:l where id=:i"),
                    {"l": payload.bidding, "i": existing[0]},
                )
            else:
                ps.execute(
                    text(
                        "insert into labels (user_id, submission_id, label, color, context_type) "
                        "values (:u, :s, :l, '', 'bidding')"
                    ),
                    {"u": target, "s": submission_id, "l": payload.bidding},
                )
        ps.commit()
        return "Interesse atualizado"


@router.post("/submissions/{submission_id}/entry-semester")
def toggle_entry_semester(submission_id: int, payload: EntrySemesterSchema, user=Depends(get_current_user)):
    raw = (payload.semester or "").strip()
    low = raw.lower()
    if low in ("first", "primeiro", "primeiro semestre", "primeiro semestre.", "1"):
        value = "Primeiro semestre."
    elif low in ("second", "segundo", "segundo semestre", "segundo semestre.", "2"):
        value = "Segundo semestre."
    else:
        value = raw
    with PrejanusSession() as ps:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        ps.execute(
            text("update submission set entry_semester=:s, updated_at=now() where id=:i"),
            {"s": value, "i": submission_id},
        )
        ps.commit()
        return "Semestre de ingresso atualizado"


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
def get_file(submission_id: int, label: str, filename: str, user=Depends(get_current_user)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        if resp is None:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        values = forms_service.get_values(fs, sub["candidate_form_id"])
        field = None
        for f in forms_service.get_all_fields(fs, resp["form_id"]):
            if f["name"] == label and values.get(f["id"]):
                field = f
                break
        if field is None:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        value = values.get(field["id"])
        if not value:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        base = os.path.basename(str(value))
        if base != filename:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        candidates = [UPLOADS / str(value), UPLOADS / base]
        target = None
        for candidate in candidates:
            if candidate.is_file() and str(candidate.resolve()).startswith(str(UPLOADS.resolve())):
                target = candidate
                break
        if target is None and UPLOADS.is_dir():
            for root, _dirs, files in os.walk(UPLOADS):
                if base in files:
                    candidate = Path(root) / base
                    if str(candidate.resolve()).startswith(str(UPLOADS.resolve())):
                        target = candidate
                        break
        if target is None:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        data = target.read_bytes()
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(submission_id: int, payload: RequestReesendSchema, user=Depends(require_admin)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        _require_phase(ps, sub, "homologacao")
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        if resp is None:
            raise HTTPException(status_code=404, detail="Resposta de candidatura não encontrada")
        fs.execute(text("select update_form_response_section(:i, 0)"), {"i": resp["id"]})
        fs.execute(
            text("update form_response set submitted_at=null where id=:i"), {"i": resp["id"]}
        )
        fs.commit()
        link = f"{settings.base_url.rstrip('/')}/form/{resp['token']}"
        html = mailer.resubmission_email("", payload.text, link)
        try:
            sent_to = mailer.send_email(resp["email"], "Solicitação de correção de candidatura", html, bcc=[user["email"]])
        except Exception:
            raise HTTPException(status_code=500, detail="Falha no envio do e-mail")
        return {"message": "Solicitação de correção enviada", "email_sent": sent_to}


@router.post("/submissions/{submission_id}/send-accept")
def send_accept_forms(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        if sub["stats"] != "approved":
            raise HTTPException(status_code=400, detail="Candidatura não aprovada")
        edict = get_edict(ps, sub["edict_id"])
        accept_form_ids = parse_form_ids(edict["accept_forms"] if edict else None)
        if not accept_form_ids:
            raise HTTPException(status_code=404, detail="Formulário de aceite não configurado")
        if sub["accept_form_id"]:
            raise HTTPException(status_code=400, detail="Aceite já enviado")
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        candidate_email = resp["email"] if resp else None
        shared_id = fs.execute(
            text(
                "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
                "values (:f, true, false, :t, now(), :e) returning id"
            ),
            {"f": accept_form_ids[0], "t": uuid.uuid4(), "e": edict["closed_date"]},
        ).scalar()
        response_id = fs.execute(
            text(
                "insert into form_response (form_id, shared_id, email, token, current_section, form_version) "
                "values (:f, :sh, :e, :t, 0, 1) returning id"
            ),
            {"f": accept_form_ids[0], "sh": shared_id, "e": candidate_email, "t": uuid.uuid4()},
        ).scalar()
        fs.commit()
        ps.execute(
            text("update submission set accept_form_id=:a, updated_at=now() where id=:i"),
            {"a": response_id, "i": submission_id},
        )
        ps.commit()
        shared = fs.execute(
            text("select token from form_shared where id=:i"), {"i": shared_id}
        ).scalar()
        link = f"{settings.base_url.rstrip('/')}/form/{shared}"
        deadline = edict["closed_date"].isoformat() if edict["closed_date"] else ""
        html = mailer.accept_form_email("", deadline, link)
        cc = []
        if sub["advisor_id"]:
            advisor = get_user_row(ps, sub["advisor_id"])
            if advisor and advisor["email"]:
                cc = [advisor["email"]]
        try:
            sent_to = mailer.send_email(candidate_email, "Formulário de aceite / Acceptance form", html, cc=cc)
        except Exception:
            raise HTTPException(status_code=500, detail="Falha no envio do e-mail")
        return {"message": "Formulário de aceite enviado", "email_sent": sent_to}


@router.post("/submissions/{submission_id}/send-letter")
def send_accept_letter(submission_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps, FormsSession() as fs:
        sub = get_submission(ps, submission_id)
        if sub is None:
            raise HTTPException(status_code=404, detail="Inscrição não encontrada")
        if sub["stats"] != "approved":
            raise HTTPException(status_code=400, detail="Candidatura não aprovada")
        if sub["letter_sent"]:
            raise HTTPException(status_code=400, detail="Carta já enviada")
        edict = get_edict(ps, sub["edict_id"])
        summary = build_summary(ps, fs, sub, edict, user["id"])
        candidate_name = summary.get("name") or ""
        advisor = get_user_row(ps, sub["advisor_id"]) if sub["advisor_id"] else None
        advisor_name = advisor["name"] if advisor else ""
        semester = sub["entry_semester"] or ""
        year = edict["year"] if edict else ""
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        candidate_email = summary.get("email") or (resp["email"] if resp else None)
        html = mailer.acceptance_letter_html(candidate_name, advisor_name, semester, year)
        cc = [advisor["email"]] if advisor and advisor["email"] else []
        try:
            sent_to = mailer.send_email(candidate_email, "Carta de aceite", html, cc=cc)
        except Exception:
            raise HTTPException(status_code=500, detail="Falha no envio do e-mail")
        ps.execute(
            text("update submission set letter_sent=true, updated_at=now() where id=:i"),
            {"i": submission_id},
        )
        ps.commit()
        return {"message": "Carta de aceite enviada", "email_sent": sent_to}
