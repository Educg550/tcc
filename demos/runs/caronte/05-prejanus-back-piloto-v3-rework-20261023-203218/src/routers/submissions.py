import uuid
from datetime import datetime, timezone
from pathlib import Path

from babel.dates import format_date
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import text

from src.auth import get_current_user, is_admin
from src.config import settings
from src.db import get_db, get_forms_db
from src.schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from src.services.forms_service import (
    date_only,
    get_edict,
    poscomp_or_none,
    response_row,
    sections_of,
    fields_of_section,
    response_values,
)
from src.services.mailer import send_email
from src.services.submissions_service import (
    accept_info,
    build_submission_dict,
    comments_list,
    get_private_note,
    get_submission,
    recommenders_info,
    require_phase,
    submission_context,
    user_labels,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])

UPLOADS = Path("/shared/uploads")


async def _load_submission(db, submission_id: int) -> dict:
    sub = await get_submission(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


@router.delete("/comments/{comment_id}")
async def remove_comment(
    comment_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, user_id FROM comment WHERE id = :i"), {"i": comment_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Comment not found")
    if row[1] != user["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete another user's comment")
    await db.execute(text("DELETE FROM comment WHERE id = :i"), {"i": comment_id})
    await db.commit()
    return Response(status_code=204)


@router.delete("/label/{label_id}")
async def remove_label(
    label_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, user_id FROM labels WHERE id = :i"), {"i": label_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Label not found")
    if row[1] != user["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete another user's label")
    await db.execute(text("DELETE FROM labels WHERE id = :i"), {"i": label_id})
    await db.commit()
    return Response(status_code=204)


@router.get("/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _load_submission(db, submission_id)
    edict = await get_edict(db, sub["edict_id"])
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    data, response, values = await submission_context(db, fdb, edict, sub)
    summary = {
        "id": sub["id"],
        "name": data.get("name") or "",
        "email": data.get("email") or (response["email"] if response else ""),
        "stats": sub["stats"],
        "letter_sent": sub["letter_sent"],
        "private_note": await get_private_note(db, user["id"], sub["id"]),
        "graduation": data.get("graduation") or {},
        "research": data.get("research") or {},
        "entry_semester": sub["entry_semester"] or "",
        "birth_date": date_only(data.get("birth_date")),
        "poscomp": poscomp_or_none(data),
        "recommenders": await recommenders_info(db, fdb, edict, sub),
        "labels": await user_labels(db, sub["id"], user["id"]),
        "accept": await accept_info(fdb, sub),
    }
    submission_form = []
    if response:
        for section in await sections_of(fdb, response["form_id"], response["form_version"]):
            section = dict(section)
            section["fields"] = await fields_of_section(fdb, section["id"])
            for field in section["fields"]:
                field["value"] = values.get(field["id"])
            submission_form.append(section)
    result = {"summary": summary, "submission_form": submission_form}
    if include_comments:
        result["comments"] = await comments_list(db, sub["id"])
    return result


@router.get("/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    return await comments_list(db, submission_id)


@router.post("/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    body: CommentSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _load_submission(db, submission_id)
    await require_phase(db, sub, "avaliacao")
    now = datetime.now(timezone.utc)
    result = await db.execute(
        text(
            "INSERT INTO comment(user_id, submission_id, comment, created_at, updated_at) "
            "VALUES(:u, :s, :c, :ca, :ua) RETURNING id, created_at, updated_at"
        ),
        {
            "u": user["id"],
            "s": submission_id,
            "c": body.comment,
            "ca": body.created_at or now,
            "ua": body.updated_at or body.created_at or now,
        },
    )
    row = result.first()
    await db.commit()
    return {
        "id": row[0],
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": body.comment,
        "created_at": row[1],
        "updated_at": row[2],
    }


@router.post("/{submission_id}/favorites", status_code=201)
async def create_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _load_submission(db, submission_id)
    await require_phase(db, sub, "avaliacao")
    await db.execute(
        text(
            "INSERT INTO favorites(user_id, submission_id, created_at) "
            "VALUES(:u, :s, now()) ON CONFLICT DO NOTHING"
        ),
        {"u": user["id"], "s": submission_id},
    )
    await db.commit()
    return "Favorite created"


@router.delete("/{submission_id}/favorites")
async def remove_favorite(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    await db.execute(
        text("DELETE FROM favorites WHERE user_id = :u AND submission_id = :s"),
        {"u": user["id"], "s": submission_id},
    )
    await db.commit()
    return "Favorite removed"


@router.get("/{submission_id}/labels")
async def get_label(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    result = await db.execute(
        text(
            "SELECT DISTINCT ON (label) id, label, color FROM labels "
            "WHERE user_id = :u AND context_type = 'candidate' ORDER BY label, id"
        ),
        {"u": user["id"]},
    )
    return {"labels": [dict(r._mapping) for r in result]}


@router.post("/{submission_id}/labels")
async def add_label(
    submission_id: int,
    body: LabelSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _load_submission(db, submission_id)
    await require_phase(db, sub, "avaliacao")
    await db.execute(
        text(
            "UPDATE labels SET color = :c WHERE user_id = :u AND label = :l "
            "AND context_type = 'candidate'"
        ),
        {"c": body.color, "u": user["id"], "l": body.label},
    )
    result = await db.execute(
        text(
            "SELECT id FROM labels WHERE user_id = :u AND submission_id = :s "
            "AND label = :l AND context_type = 'candidate'"
        ),
        {"u": user["id"], "s": submission_id, "l": body.label},
    )
    row = result.first()
    if row:
        label_id = row[0]
    else:
        result = await db.execute(
            text(
                "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
                "VALUES(:u, :s, :l, :c, 'candidate') RETURNING id"
            ),
            {"u": user["id"], "s": submission_id, "l": body.label, "c": body.color},
        )
        label_id = result.scalar()
    await db.commit()
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": body.label,
    }


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    body: PrivateNoteSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _load_submission(db, submission_id)
    await require_phase(db, sub, "avaliacao")
    await db.execute(
        text(
            "INSERT INTO private_note(user_id, submission_id, note, created_at, updated_at) "
            "VALUES(:u, :s, :n, now(), now()) "
            "ON CONFLICT (user_id, submission_id) DO UPDATE SET note = :n, updated_at = now()"
        ),
        {"u": user["id"], "s": submission_id, "n": body.note},
    )
    await db.commit()
    return {"note": body.note}


@router.post("/{submission_id}/view")
async def register_view(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    result = await db.execute(
        text(
            "SELECT id FROM submission_view WHERE user_id = :u AND submission_id = :s "
            "AND created_at::date = current_date"
        ),
        {"u": user["id"], "s": submission_id},
    )
    row = result.first()
    if row:
        await db.execute(
            text("UPDATE submission_view SET updated_at = now() WHERE id = :i"), {"i": row[0]}
        )
    else:
        await db.execute(
            text(
                "INSERT INTO submission_view(user_id, submission_id, created_at, updated_at) "
                "VALUES(:u, :s, now(), now())"
            ),
            {"u": user["id"], "s": submission_id},
        )
    await db.commit()
    return {"message": "View registered"}


@router.get("/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    result = await db.execute(
        text(
            "SELECT v.created_at, v.updated_at, u.id, u.name, u.email "
            "FROM submission_view v JOIN \"user\" u ON u.id = v.user_id "
            "WHERE v.submission_id = :s ORDER BY v.id"
        ),
        {"s": submission_id},
    )
    return [
        {
            "user": {"id": r[2], "name": r[3], "email": r[4]},
            "created_at": r[0],
            "updated_at": r[1],
        }
        for r in result
    ]


@router.post("/{submission_id}/select")
async def select_stats(
    submission_id: int,
    body: StatsSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    sub = await _load_submission(db, submission_id)
    edict = await get_edict(db, sub["edict_id"])
    if edict and not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict is closed")
    advisor = body.user_ids[0] if body.user_ids else None
    await db.execute(
        text("UPDATE submission SET stats = :s, advisor_id = :a, updated_at = now() WHERE id = :i"),
        {"s": body.stats.value, "a": advisor, "i": submission_id},
    )
    await db.commit()
    return "Selection updated"


@router.post("/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    body: BiddingSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    target = user["id"]
    if body.user_id and is_admin(user):
        target = body.user_id
    await db.execute(
        text(
            "DELETE FROM labels WHERE user_id = :u AND submission_id = :s "
            "AND context_type = 'bidding'"
        ),
        {"u": target, "s": submission_id},
    )
    if body.bidding.value:
        await db.execute(
            text(
                "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
                "VALUES(:u, :s, :l, '#000000', 'bidding')"
            ),
            {"u": target, "s": submission_id, "l": body.bidding.value},
        )
    await db.commit()
    return "Bidding updated"


def _normalize_semester(semester: str) -> str:
    lowered = semester.lower()
    if "segundo" in lowered or "second" in lowered:
        return "Segundo semestre."
    if "primeiro" in lowered or "first" in lowered:
        return "Primeiro semestre."
    return semester


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    body: EntrySemesterSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    await _load_submission(db, submission_id)
    normalized = _normalize_semester(body.semester)
    await db.execute(
        text("UPDATE submission SET entry_semester = :s, updated_at = now() WHERE id = :i"),
        {"s": normalized, "i": submission_id},
    )
    await db.commit()
    return "Entry semester updated"


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    if "/" in filename or ".." in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid file")
    sub = await _load_submission(db, submission_id)
    result = await fdb.execute(
        text(
            "SELECT r.value FROM responses r JOIN form_field f ON f.id = r.field_id "
            "WHERE r.response_id = :r AND f.name = :n AND r.value = :v"
        ),
        {"r": sub["candidate_form_id"], "n": label, "v": filename},
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="File not found")
    path = UPLOADS / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    body: RequestReesendSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _load_submission(db, submission_id)
    edict = await get_edict(db, sub["edict_id"])
    if not edict or edict["phase"] != "homologacao":
        raise HTTPException(status_code=400, detail="Operation only allowed in homologacao")
    response = await response_row(fdb, sub["candidate_form_id"])
    if not response:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    data, _, _ = await submission_context(db, fdb, edict, sub)
    candidate_email = data.get("email") or response["email"]
    await fdb.execute(
        text("SELECT id FROM update_form_response_section(:i, 0)"),
        {"i": sub["candidate_form_id"]},
    )
    await fdb.execute(
        text("UPDATE form_response SET submitted_at = NULL WHERE id = :i"),
        {"i": sub["candidate_form_id"]},
    )
    await fdb.commit()
    link = f"{settings.BASE_URL}/form/{response['token']}"
    send_email(
        candidate_email,
        "Solicitação de correção de inscrição",
        f"{body.text}\n\n{link}\n",
        bcc=user["email"],
    )
    return {
        "message": "Resubmission requested",
        "email_sent": candidate_email,
    }


@router.post("/{submission_id}/send-accept")
async def send_accept_forms(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _load_submission(db, submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    edict = await get_edict(db, sub["edict_id"])
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    if not edict["accept_forms"]:
        raise HTTPException(status_code=404, detail="No accept form configured")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Accept form already sent")
    form_id = int(edict["accept_forms"])
    data, response, _ = await submission_context(db, fdb, edict, sub)
    if not response:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    candidate_email = data.get("email") or response["email"]
    candidate_name = data.get("name") or ""
    expiration = edict["closed_date"]
    token = uuid.uuid4()
    result = await fdb.execute(
        text(
            "INSERT INTO form_shared(form_id, unique_answers, is_public, token, created_at, "
            "expiration_at) VALUES(:f, true, false, :t, now(), :exp) RETURNING id"
        ),
        {"f": form_id, "t": token, "exp": expiration},
    )
    shared_id = result.scalar()
    result = await fdb.execute(
        text("SELECT version FROM form WHERE id = :f"), {"f": form_id}
    )
    version = result.scalar() or 1
    response_token = uuid.uuid4()
    result = await fdb.execute(
        text(
            "INSERT INTO form_response(form_id, shared_id, email, token, current_section, "
            "submitted_at, metadata, form_version) "
            "VALUES(:f, :sh, :e, :t, 0, NULL, CAST('{}' AS jsonb), :v) RETURNING id"
        ),
        {"f": form_id, "sh": shared_id, "e": candidate_email, "t": response_token, "v": version},
    )
    accept_id = result.scalar()
    await db.execute(
        text("UPDATE submission SET accept_form_id = :a WHERE id = :i"),
        {"a": accept_id, "i": submission_id},
    )
    await db.commit()
    await fdb.commit()
    advisor_email = None
    if sub["advisor_id"]:
        result = await db.execute(
            text('SELECT email FROM "user" WHERE id = :i'), {"i": sub["advisor_id"]}
        )
        row = result.first()
        if row:
            advisor_email = row[0]
    link = f"{settings.BASE_URL}/form/{response_token}"
    date_pt = format_date(expiration, format="long", locale="pt")
    date_en = format_date(expiration, format="long", locale="en")
    send_email(
        candidate_email,
        "Formulário de aceite",
        (
            f"Prezado(a) {candidate_name},\n\n"
            "Sua inscrição foi aprovada. Preencha o formulário de aceite no link abaixo:\n"
            f"{link}\n\n"
            f"Prazo: {date_pt} ({date_en})\n"
        ),
        cc=advisor_email,
    )
    return {"message": "Accept form sent", "email_sent": candidate_email}


@router.post("/{submission_id}/send-letter")
async def send_accept_letter(
    submission_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    sub = await _load_submission(db, submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Letter already sent")
    edict = await get_edict(db, sub["edict_id"])
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    data, response, _ = await submission_context(db, fdb, edict, sub)
    candidate_email = data.get("email") or (response["email"] if response else "")
    send_email(
        candidate_email,
        "Carta de aprovação",
        "Sua inscrição foi aprovada. Segue a carta de aprovação.\n",
    )
    await db.execute(
        text("UPDATE submission SET letter_sent = true, updated_at = now() WHERE id = :i"),
        {"i": submission_id},
    )
    await db.commit()
    return {"message": "Accept letter sent", "email_sent": candidate_email}
