"""Rotas de inscrições (submissões)."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import text

from auth.session import CurrentUser, get_current_user
from config import UPLOADS_DIR
from database import get_db, get_forms_db
from schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelInputSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from services import forms_service, mail, submissions as subs_service

router = APIRouter(prefix="/submissions", tags=["submissions"])


async def _get_submission(db, submission_id: int) -> dict:
    sub = await subs_service.get_submission_row(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _get_edict(db, edict_id: int) -> dict:
    row = (
        await db.execute(text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id})
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return dict(row)


async def _require_phase(db, sub: dict, phase: str) -> None:
    edict = await _get_edict(db, sub["edict_id"])
    if edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Ação permitida apenas na fase {phase}")


async def _require_open(db, sub: dict) -> None:
    edict = await _get_edict(db, sub["edict_id"])
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital encerrado")


def _comment_dict(row) -> dict:
    return {
        "id": row["id"],
        "user": {"id": row["user_id"], "name": row["user_name"]},
        "submission_id": row["submission_id"],
        "comment": row["comment"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


COMMENT_SELECT = (
    "SELECT c.id, c.user_id, c.submission_id, c.comment, c.created_at, c.updated_at, "
    'u.name AS user_name FROM comment c JOIN "user" u ON u.id = c.user_id '
    "WHERE c.submission_id = :s ORDER BY c.id"
)


@router.delete("/label/{label_id}")
async def remove_label(label_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    row = (
        await db.execute(text("SELECT id, user_id FROM labels WHERE id = :i"), {"i": label_id})
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if row.user_id != user.id:
        raise HTTPException(status_code=403, detail="Etiqueta de outro usuário")
    await db.execute(text("DELETE FROM labels WHERE id = :i"), {"i": label_id})
    await db.commit()
    return Response(status_code=204)


@router.delete("/comments/{comment_id}")
async def remove_comment(comment_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    row = (
        await db.execute(text("SELECT id, user_id FROM comment WHERE id = :i"), {"i": comment_id})
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if row.user_id != user.id:
        raise HTTPException(status_code=403, detail="Comentário de outro usuário")
    await db.execute(text("DELETE FROM comment WHERE id = :i"), {"i": comment_id})
    await db.commit()
    return Response(status_code=204)


@router.get("/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    edict = await _get_edict(db, sub["edict_id"])
    detail = await subs_service.build_detail(db, fdb, sub, edict, user.id)
    if include_comments:
        rows = (await db.execute(text(COMMENT_SELECT), {"s": submission_id})).mappings().all()
        detail["comments"] = [_comment_dict(r) for r in rows]
    return detail


@router.get("/{submission_id}/comments")
async def get_all_comments(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_submission(db, submission_id)
    rows = (await db.execute(text(COMMENT_SELECT), {"s": submission_id})).mappings().all()
    return [_comment_dict(r) for r in rows]


@router.post("/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_phase(db, sub, "avaliacao")
    row = (
        await db.execute(
            text(
                "INSERT INTO comment(user_id, submission_id, comment, created_at, updated_at) "
                "VALUES (:u, :s, :c, COALESCE(:ca, now()), COALESCE(:ua, :ca, now())) "
                "RETURNING id, user_id, submission_id, comment, created_at, updated_at"
            ),
            {
                "u": user.id,
                "s": submission_id,
                "c": payload.comment,
                "ca": payload.created_at,
                "ua": payload.updated_at,
            },
        )
    ).mappings().first()
    await db.commit()
    d = dict(row)
    return {
        "id": d["id"],
        "user": {"id": user.id, "name": user.name},
        "submission_id": d["submission_id"],
        "comment": d["comment"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


@router.get("/{submission_id}/labels")
async def get_label(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            text(
                "SELECT DISTINCT ON (label) id, label, color FROM labels "
                "WHERE user_id = :u ORDER BY label, id"
            ),
            {"u": user.id},
        )
    ).mappings().all()
    return {"labels": [dict(r) for r in rows]}


@router.post("/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_phase(db, sub, "avaliacao")
    row = (
        await db.execute(
            text(
                "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
                "VALUES (:u, :s, :l, :c, 'candidate') RETURNING id"
            ),
            {"u": user.id, "s": submission_id, "l": payload.label, "c": payload.color},
        )
    ).scalar()
    await db.execute(
        text("UPDATE labels SET color = :c WHERE user_id = :u AND label = :l"),
        {"c": payload.color, "u": user.id, "l": payload.label},
    )
    await db.commit()
    return {
        "id": row,
        "user": {"id": user.id, "name": user.name},
        "submission_id": submission_id,
        "label": payload.label,
        "color": payload.color,
    }


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_phase(db, sub, "avaliacao")
    await db.execute(
        text(
            "INSERT INTO private_note(user_id, submission_id, note, created_at) "
            "VALUES (:u, :s, :n, now()) "
            "ON CONFLICT (user_id, submission_id) DO UPDATE SET note = :n, updated_at = now()"
        ),
        {"u": user.id, "s": submission_id, "n": payload.note},
    )
    await db.commit()
    return {"note": payload.note}


@router.post("/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    sub = await _get_submission(db, submission_id)
    await _require_phase(db, sub, "avaliacao")
    await db.execute(
        text(
            "INSERT INTO favorites(user_id, submission_id, created_at) VALUES (:u, :s, now()) "
            "ON CONFLICT (user_id, submission_id) DO NOTHING"
        ),
        {"u": user.id, "s": submission_id},
    )
    await db.commit()
    return "Favorito registrado"


@router.delete("/{submission_id}/favorites")
async def remove_favorite(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_submission(db, submission_id)
    await db.execute(
        text("DELETE FROM favorites WHERE user_id = :u AND submission_id = :s"),
        {"u": user.id, "s": submission_id},
    )
    await db.commit()
    return "Favorito removido"


@router.post("/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    target_id = user.id
    if payload.user_id is not None and user.is_admin:
        target_id = payload.user_id
    await db.execute(
        text(
            "DELETE FROM labels WHERE user_id = :u AND submission_id = :s "
            "AND context_type = 'bidding'"
        ),
        {"u": target_id, "s": submission_id},
    )
    if payload.bidding.value:
        await db.execute(
            text(
                "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
                "VALUES (:u, :s, :l, '#000000', 'bidding')"
            ),
            {"u": target_id, "s": submission_id, "l": payload.bidding.value},
        )
    await db.commit()
    return "Interesse registrado"


@router.post("/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_open(db, sub)
    advisor = sub["advisor_id"]
    if payload.user_ids:
        advisor = payload.user_ids[0]
    await db.execute(
        text("UPDATE submission SET stats = :st, advisor_id = :a, updated_at = now() WHERE id = :i"),
        {"st": payload.stats.value, "a": advisor, "i": submission_id},
    )
    await db.commit()
    return "Decisão registrada"


def _normalize_semester(value: str) -> str:
    low = value.strip().lower()
    if "segundo" in low or "second" in low:
        return "Segundo semestre."
    if "primeiro" in low or "first" in low:
        return "Primeiro semestre."
    return value


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_open(db, sub)
    normalized = _normalize_semester(payload.semester)
    await db.execute(
        text("UPDATE submission SET entry_semester = :e, updated_at = now() WHERE id = :i"),
        {"e": normalized, "i": submission_id},
    )
    await db.commit()
    return "Semestre de ingresso registrado"


@router.post("/{submission_id}/view")
async def register_view(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_submission(db, submission_id)
    existing = (
        await db.execute(
            text(
                "SELECT id FROM submission_view WHERE user_id = :u AND submission_id = :s "
                "AND created_at::date = current_date"
            ),
            {"u": user.id, "s": submission_id},
        )
    ).scalar()
    if existing:
        await db.execute(
            text("UPDATE submission_view SET updated_at = now() WHERE id = :i"), {"i": existing}
        )
    else:
        await db.execute(
            text(
                "INSERT INTO submission_view(user_id, submission_id, created_at, updated_at) "
                "VALUES (:u, :s, now(), now())"
            ),
            {"u": user.id, "s": submission_id},
        )
    await db.commit()
    return "Visualização registrada"


@router.get("/{submission_id}/view")
async def get_submission_views(
    submission_id: int, user=Depends(get_current_user), db=Depends(get_db)
):
    await _get_submission(db, submission_id)
    rows = (
        await db.execute(
            text(
                "SELECT sv.id, sv.created_at, sv.updated_at, u.id AS user_id, u.name AS user_name "
                "FROM submission_view sv JOIN \"user\" u ON u.id = sv.user_id "
                "WHERE sv.submission_id = :s ORDER BY sv.id"
            ),
            {"s": submission_id},
        )
    ).mappings().all()
    return [
        {
            "id": r["id"],
            "user": {"id": r["user_id"], "name": r["user_name"]},
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    response_ids = [sub["candidate_form_id"]] + list(sub["recommenders_form_ids"] or [])
    if sub["accept_form_id"]:
        response_ids.append(sub["accept_form_id"])
    response_ids = [r for r in response_ids if r]
    rows = []
    if response_ids:
        id_list = ",".join(str(int(r)) for r in response_ids)
        rows = (
            await fdb.execute(
                text(
                    "SELECT f.name, r.value FROM responses r "
                    "JOIN form_field f ON f.id = r.field_id "
                    f"WHERE r.response_id IN ({id_list}) AND f.type = 'File'"
                )
            )
        ).all()
    if not any(name == label and value == filename for name, value in rows):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    if "/" in filename or ".." in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Arquivo inválido")
    path = Path(UPLOADS_DIR) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, filename=filename)


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    await _require_phase(db, sub, "homologacao")
    edict = await _get_edict(db, sub["edict_id"])
    resp, _values, data = await subs_service.get_candidate_data(db, fdb, sub, edict)
    if not resp:
        raise HTTPException(status_code=404, detail="Resposta do candidato não encontrada")
    await fdb.execute(
        text("UPDATE form_response SET current_section = 0 WHERE id = :i"), {"i": resp["id"]}
    )
    await fdb.commit()
    mail.send_correction_email(data["name"] or "", data["email"], resp["token"], payload.text)
    return {"message": "Correção solicitada", "email_sent": data["email"]}


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Inscrição não aprovada")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Formulário de aceite já enviado")
    edict = await _get_edict(db, sub["edict_id"])
    if not edict.get("accept_forms"):
        raise HTTPException(status_code=404, detail="Edital sem formulário de aceite")
    resp, _values, data = await subs_service.get_candidate_data(db, fdb, sub, edict)
    if not resp:
        raise HTTPException(status_code=404, detail="Resposta do candidato não encontrada")
    accept_form = int(edict["accept_forms"])
    shared_id = (
        await fdb.execute(
            text(
                "INSERT INTO form_shared(form_id, unique_answers, is_public, token, created_at, "
                "expiration_at) VALUES (:f, true, false, :t, now(), :exp) RETURNING id"
            ),
            {"f": accept_form, "t": str(uuid.uuid4()), "exp": edict["closed_date"]},
        )
    ).scalar()
    accept_response_id = (
        await fdb.execute(
            text(
                "INSERT INTO form_response(form_id, shared_id, user_id, email, token, "
                "current_section, submitted_at, metadata, form_version) "
                "VALUES (:f, :sid, NULL, :email, :t, 0, NULL, '{}'::jsonb, "
                "COALESCE((SELECT max(version) FROM form_section WHERE form_id = :f), "
                "(SELECT max(version) FROM form_field WHERE form_id = :f), 1)) RETURNING id"
            ),
            {"f": accept_form, "sid": shared_id, "email": data["email"], "t": str(uuid.uuid4())},
        )
    ).scalar()
    await db.execute(
        text("UPDATE submission SET accept_form_id = :a, updated_at = now() WHERE id = :i"),
        {"a": accept_response_id, "i": submission_id},
    )
    await db.commit()
    await fdb.commit()
    cc = None
    if sub.get("advisor_id"):
        cc = (
            await db.execute(
                text('SELECT email FROM "user" WHERE id = :i'), {"i": sub["advisor_id"]}
            )
        ).scalar()
    accept_resp = await forms_service.get_response(fdb, accept_response_id)
    mail.send_accept_email(
        data["name"] or "", data["email"], accept_resp["token"], edict["closed_date"], cc=cc
    )
    return {"message": "Formulário de aceite enviado", "email_sent": data["email"]}


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _get_submission(db, submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Inscrição não aprovada")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Carta já enviada")
    edict = await _get_edict(db, sub["edict_id"])
    resp, _values, data = await subs_service.get_candidate_data(db, fdb, sub, edict)
    await db.execute(
        text("UPDATE submission SET letter_sent = true, updated_at = now() WHERE id = :i"),
        {"i": submission_id},
    )
    await db.commit()
    mail.send_letter_email(data["name"] or "", data["email"])
    return {"message": "Carta de aprovação enviada", "email_sent": data["email"]}
