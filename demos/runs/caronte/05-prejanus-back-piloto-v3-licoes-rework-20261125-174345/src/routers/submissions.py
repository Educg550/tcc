import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from ..auth import ADMIN_ROLES, current_user
from ..config import settings
from ..db import fetch, fetch_one, forms_engine, prejanus_engine, run
from ..schemas import (BiddingSchema, CommentSchema, EntrySemesterSchema, LabelSchema,
                       PrivateNoteSchema, RequestReesendSchema, StatsSchema)
from ..services import email_service, forms_service, submissions_service

router = APIRouter(prefix="/submissions", tags=["submissions"])

UPLOADS = Path("/shared/uploads")


async def _get_submission(submission_id: int) -> dict:
    sub = await submissions_service.get_submission(submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return sub


async def _require_phase(sub: dict, phase: str) -> None:
    edict = await submissions_service.get_edict(sub["edict_id"])
    if edict is None or edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Operação disponível apenas na fase {phase}")


@router.get("/{submission_id}")
async def get_details(submission_id: int, include_comments: bool = False,
                      user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    resultado = {
        "summary": await submissions_service.build_summary(sub, user),
        "submission_form": await submissions_service.submission_sections(sub),
    }
    if include_comments:
        resultado["comments"] = await _comments(submission_id)
    return resultado


async def _comments(submission_id: int) -> list[dict]:
    rows = await fetch(
        prejanus_engine,
        'SELECT c.id, c.submission_id, c.comment, c.created_at, c.updated_at, '
        'u.id AS uid, u.name AS uname FROM comment c JOIN "user" u ON u.id=c.user_id '
        "WHERE c.submission_id=:s ORDER BY c.id",
        {"s": submission_id},
    )
    return [{
        "id": r["id"], "user": {"id": r["uid"], "name": r["uname"]},
        "submission_id": r["submission_id"], "comment": r["comment"],
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    } for r in rows]


@router.get("/{submission_id}/comments")
async def get_all_comments(submission_id: int, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    return await _comments(submission_id)


@router.post("/{submission_id}/comments")
async def add_comment(submission_id: int, body: CommentSchema, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    await _require_phase(sub, "avaliacao")
    rows = await run(
        prejanus_engine,
        "INSERT INTO comment (user_id, submission_id, comment, created_at, updated_at) "
        "VALUES (:u, :s, :c, COALESCE(:ca, now()), COALESCE(:ua, now())) "
        "RETURNING id, created_at, updated_at",
        {"u": user["id"], "s": submission_id, "c": body.comment,
         "ca": body.created_at, "ua": body.updated_at or body.created_at},
    )
    return {
        "id": rows[0]["id"], "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id, "comment": body.comment,
        "created_at": rows[0]["created_at"], "updated_at": rows[0]["updated_at"],
    }


@router.delete("/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user: dict = Depends(current_user)):
    row = await fetch_one(
        prejanus_engine, "SELECT user_id FROM comment WHERE id=:i", {"i": comment_id}
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if row["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Comentário de outro usuário")
    await run(prejanus_engine, "DELETE FROM comment WHERE id=:i", {"i": comment_id})
    return Response(status_code=204)


@router.get("/{submission_id}/labels")
async def get_label(submission_id: int, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    rows = await fetch(
        prejanus_engine,
        "SELECT DISTINCT ON (label) id, label, color FROM labels "
        "WHERE user_id=:u AND context_type='candidate' ORDER BY label, id DESC",
        {"u": user["id"]},
    )
    return {"labels": rows}


@router.post("/{submission_id}/labels")
async def add_label(submission_id: int, body: LabelSchema, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    await _require_phase(sub, "avaliacao")
    await run(
        prejanus_engine,
        "UPDATE labels SET color=:c WHERE user_id=:u AND label=:l AND context_type='candidate'",
        {"c": body.color, "u": user["id"], "l": body.label},
    )
    row = await fetch_one(
        prejanus_engine,
        "SELECT id, label FROM labels WHERE user_id=:u AND submission_id=:s AND "
        "context_type='candidate' AND label=:l",
        {"u": user["id"], "s": submission_id, "l": body.label},
    )
    if row:
        await run(
            prejanus_engine, "UPDATE labels SET color=:c WHERE id=:i",
            {"c": body.color, "i": row["id"]},
        )
        label_id = row["id"]
    else:
        rows = await run(
            prejanus_engine,
            "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
            "VALUES (:u, :s, :l, :c, 'candidate') RETURNING id",
            {"u": user["id"], "s": submission_id, "l": body.label, "c": body.color},
        )
        label_id = rows[0]["id"]
    return {
        "id": label_id, "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id, "label": body.label,
    }


@router.delete("/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user: dict = Depends(current_user)):
    row = await fetch_one(
        prejanus_engine, "SELECT user_id FROM labels WHERE id=:i", {"i": label_id}
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
    if row["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Etiqueta de outro usuário")
    await run(prejanus_engine, "DELETE FROM labels WHERE id=:i", {"i": label_id})
    return Response(status_code=204)


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(submission_id: int, body: PrivateNoteSchema,
                             user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    await _require_phase(sub, "avaliacao")
    await run(
        prejanus_engine,
        "INSERT INTO private_note (user_id, submission_id, note, created_at, updated_at) "
        "VALUES (:u, :s, :n, now(), now()) "
        "ON CONFLICT (user_id, submission_id) DO UPDATE SET note=:n, updated_at=now()",
        {"u": user["id"], "s": submission_id, "n": body.note},
    )
    return {"note": body.note}


@router.post("/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    await _require_phase(sub, "avaliacao")
    await run(
        prejanus_engine,
        "INSERT INTO favorites (user_id, submission_id, created_at) VALUES (:u, :s, now()) "
        "ON CONFLICT (user_id, submission_id) DO NOTHING",
        {"u": user["id"], "s": submission_id},
    )
    return "Favorito adicionado"


@router.delete("/{submission_id}/favorites")
async def remove_favorite(submission_id: int, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    await run(
        prejanus_engine,
        "DELETE FROM favorites WHERE user_id=:u AND submission_id=:s",
        {"u": user["id"], "s": submission_id},
    )
    return "Favorito removido"


@router.post("/{submission_id}/view")
async def register_view(submission_id: int, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    existing = await fetch_one(
        prejanus_engine,
        "SELECT id FROM submission_view WHERE user_id=:u AND submission_id=:s "
        "AND created_at::date = current_date",
        {"u": user["id"], "s": submission_id},
    )
    if existing:
        await run(
            prejanus_engine,
            "UPDATE submission_view SET updated_at=now() WHERE id=:i", {"i": existing["id"]},
        )
    else:
        await run(
            prejanus_engine,
            "INSERT INTO submission_view (user_id, submission_id, created_at, updated_at) "
            "VALUES (:u, :s, now(), now())",
            {"u": user["id"], "s": submission_id},
        )
    return {"message": "Visualização registrada"}


@router.get("/{submission_id}/view")
async def get_submission_views(submission_id: int, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    rows = await fetch(
        prejanus_engine,
        'SELECT v.id, v.submission_id, v.created_at, v.updated_at, u.id AS uid, u.name, u.email '
        'FROM submission_view v JOIN "user" u ON u.id=v.user_id '
        "WHERE v.submission_id=:s ORDER BY v.id",
        {"s": submission_id},
    )
    return [{
        "id": r["id"], "user": {"id": r["uid"], "name": r["name"], "email": r["email"]},
        "submission_id": r["submission_id"], "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    } for r in rows]


@router.post("/{submission_id}/select")
async def select_stats(submission_id: int, body: StatsSchema, user: dict = Depends(current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a perfis administrativos")
    sub = await _get_submission(submission_id)
    edict = await submissions_service.get_edict(sub["edict_id"])
    if edict and not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edital fechado")
    advisor = body.user_ids[0] if (body.stats == "approved" and body.user_ids) else None
    await run(
        prejanus_engine,
        "UPDATE submission SET stats=:s, advisor_id=:a, updated_at=now() WHERE id=:i",
        {"s": body.stats.value, "a": advisor, "i": submission_id},
    )
    return "Situação atualizada"


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(submission_id: int, body: EntrySemesterSchema,
                                user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    texto = body.semester.strip().lower()
    if re.search("segundo|second", texto):
        gravado = "Segundo semestre."
    elif re.search("primeiro|first", texto):
        gravado = "Primeiro semestre."
    else:
        gravado = body.semester
    await run(
        prejanus_engine,
        "UPDATE submission SET entry_semester=:s, updated_at=now() WHERE id=:i",
        {"s": gravado, "i": submission_id},
    )
    return "Semestre de ingresso atualizado"


@router.post("/{submission_id}/bidding")
async def toggle_bidding(submission_id: int, body: BiddingSchema, user: dict = Depends(current_user)):
    await _get_submission(submission_id)
    target = user["id"]
    if body.user_id is not None and user["role"] in ADMIN_ROLES:
        target = body.user_id
    await run(
        prejanus_engine,
        "DELETE FROM labels WHERE user_id=:u AND submission_id=:s AND context_type='bidding'",
        {"u": target, "s": submission_id},
    )
    await run(
        prejanus_engine,
        "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
        "VALUES (:u, :s, :l, '#000000', 'bidding')",
        {"u": target, "s": submission_id, "l": body.bidding.value},
    )
    return "Interesse registrado"


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(submission_id: int, body: RequestReesendSchema,
                             user: dict = Depends(current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a perfis administrativos")
    sub = await _get_submission(submission_id)
    await _require_phase(sub, "homologacao")
    resp = await forms_service.get_response(sub["candidate_form_id"])
    if resp is None:
        raise HTTPException(status_code=404, detail="Formulário do candidato não encontrado")
    await forms_service.reset_response_section(resp["id"])
    edict = await submissions_service.get_edict(sub["edict_id"])
    mapped = await submissions_service.candidate_mapped(sub)
    nome = submissions_service._s(mapped.get("name"))
    link = f"{settings.BASE_URL}/form/{resp['token']}"
    email_service.send_correction(edict["title"], nome, resp["email"], body.text, link, user["email"])
    return {"message": "Solicitação de correção enviada", "email_sent": resp["email"]}


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Inscrição não está aprovada")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Formulário de aceite já enviado")
    edict = await submissions_service.get_edict(sub["edict_id"])
    if not edict or not edict["accept_forms"]:
        raise HTTPException(status_code=404, detail="Edital sem formulário de aceite configurado")
    form_id = int(edict["accept_forms"])
    form = await forms_service.get_form(form_id)
    resp = await forms_service.get_response(sub["candidate_form_id"])
    email = resp["email"] if resp else ""
    criado = await forms_service.create_accept_response(
        form_id, email, edict["closed_date"], form["version"] if form else 1
    )
    await run(
        prejanus_engine,
        "UPDATE submission SET accept_form_id=:a, updated_at=now() WHERE id=:i",
        {"a": criado["id"], "i": submission_id},
    )
    mapped = await submissions_service.candidate_mapped(sub)
    nome = submissions_service._s(mapped.get("name"))
    advisor = await submissions_service._advisor(sub)
    link = f"{settings.BASE_URL}/form/{criado['token']}"
    email_service.send_accept(edict["title"], nome, email, link, edict["closed_date"],
                              advisor["email"] if advisor else None)
    return {"message": "Formulário de aceite enviado", "email_sent": email}


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Inscrição não está aprovada")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Carta já enviada")
    edict = await submissions_service.get_edict(sub["edict_id"])
    resp = await forms_service.get_response(sub["candidate_form_id"])
    email = resp["email"] if resp else ""
    mapped = await submissions_service.candidate_mapped(sub)
    email_service.send_letter(edict["title"], submissions_service._s(mapped.get("name")), email)
    await run(
        prejanus_engine,
        "UPDATE submission SET letter_sent=true, updated_at=now() WHERE id=:i",
        {"i": submission_id},
    )
    return {"message": "Carta de aprovação enviada", "email_sent": email}


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(submission_id: int, label: str, filename: str, user: dict = Depends(current_user)):
    sub = await _get_submission(submission_id)
    if "/" in filename or ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
    response_ids = [sub["candidate_form_id"]]
    response_ids += list(sub["recommenders_form_ids"] or [])
    if sub["accept_form_id"]:
        response_ids.append(sub["accept_form_id"])
    row = await fetch_one(
        forms_engine,
        "SELECT r.value FROM responses r JOIN form_field f ON f.id=r.field_id "
        "WHERE f.name=:label AND r.value=:filename AND r.response_id = ANY(:ids) LIMIT 1",
        {"label": label, "filename": filename, "ids": response_ids},
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    caminho = UPLOADS / filename
    if not caminho.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(caminho, media_type="application/pdf", filename=filename)
