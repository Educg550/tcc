"""Rotas de candidaturas: detalhes, avaliação, seleção, arquivos e mensagens."""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from starlette.responses import FileResponse

from ..auth import ADMIN_ROLES, require_admin, require_user
from ..db import get_db, get_forms_db
from ..schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from ..services.mailer import send_accept_email, send_letter_email, send_resend_email
from ..services.submissions import (
    build_submission_form,
    build_summary,
    candidate_data,
    get_edict,
    get_submission,
    normalize_semester,
    user_by_id,
)

router = APIRouter(tags=["submissions"])

UPLOADS = Path("/shared/uploads")


def _require_submission(db, submission_id):
    sub = get_submission(db, submission_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


def _require_phase(db, sub, phase):
    edict = get_edict(db, sub["edict_id"])
    if edict is None or edict["phase"] != phase:
        raise HTTPException(
            status_code=400, detail=f"Operação permitida apenas na fase {phase}"
        )
    return edict


def _comment_dict(row):
    return {
        "id": row["id"],
        "user": {"id": row["uid"], "name": row["uname"]},
        "submission_id": row["submission_id"],
        "comment": row["comment"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _comments(db, submission_id):
    rows = db.execute(
        text('SELECT c.*, u.id AS uid, u.name AS uname FROM comment c '
             'JOIN "user" u ON u.id = c.user_id '
             "WHERE c.submission_id = :s ORDER BY c.id"),
        {"s": submission_id},
    ).mappings().all()
    return [_comment_dict(r) for r in rows]


@router.get("/submissions/{submission_id}")
def get_details(submission_id: int, include_comments: bool = Query(default=False),
                user=Depends(require_user), db=Depends(get_db), fdb=Depends(get_forms_db)):
    sub = _require_submission(db, submission_id)
    edict = get_edict(db, sub["edict_id"])
    result = {
        "summary": build_summary(db, fdb, sub, edict, user["id"]),
        "submission_form": build_submission_form(fdb, sub),
    }
    if include_comments:
        result["comments"] = _comments(db, submission_id)
    return result


@router.get("/submissions/{submission_id}/comments")
def get_all_comments(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    return _comments(db, submission_id)


@router.post("/submissions/{submission_id}/comments")
def add_comment(submission_id: int, body: CommentSchema,
                user=Depends(require_user), db=Depends(get_db)):
    sub = _require_submission(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    created_at = body.created_at or datetime.now(timezone.utc)
    updated_at = body.updated_at or created_at
    comment_id = db.execute(
        text("INSERT INTO comment (user_id, submission_id, comment, created_at, updated_at) "
             "VALUES (:u, :s, :c, :ca, :ua) RETURNING id"),
        {"u": user["id"], "s": submission_id, "c": body.comment,
         "ca": created_at, "ua": updated_at},
    ).scalar()
    db.commit()
    return {
        "id": comment_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": body.comment,
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.delete("/submissions/comments/{comment_id}", status_code=204)
def remove_comment(comment_id: int, user=Depends(require_user), db=Depends(get_db)):
    row = db.execute(
        text("SELECT id, user_id FROM comment WHERE id = :i"), {"i": comment_id}
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if row["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.execute(text("DELETE FROM comment WHERE id = :i"), {"i": comment_id})
    db.commit()


@router.get("/submissions/{submission_id}/labels")
def get_label(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    rows = db.execute(
        text("SELECT min(id) AS id, label, color FROM labels "
             "WHERE user_id = :u AND context_type = 'candidate' "
             "GROUP BY label, color ORDER BY label"),
        {"u": user["id"]},
    ).mappings().all()
    return {"labels": [dict(r) for r in rows]}


@router.post("/submissions/{submission_id}/labels")
def add_label(submission_id: int, body: LabelSchema,
              user=Depends(require_user), db=Depends(get_db)):
    sub = _require_submission(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    label_id = db.execute(
        text("INSERT INTO labels (user_id, submission_id, label, color, context_type) "
             "VALUES (:u, :s, :l, :c, 'candidate') RETURNING id"),
        {"u": user["id"], "s": submission_id, "l": body.label, "c": body.color},
    ).scalar()
    db.execute(
        text("UPDATE labels SET color = :c WHERE user_id = :u AND label = :l "
             "AND context_type = 'candidate'"),
        {"c": body.color, "u": user["id"], "l": body.label},
    )
    db.commit()
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": body.label,
        "color": body.color,
    }


@router.delete("/submissions/label/{label_id}", status_code=204)
def remove_label(label_id: int, user=Depends(require_user), db=Depends(get_db)):
    row = db.execute(
        text("SELECT id, user_id FROM labels WHERE id = :i"), {"i": label_id}
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if row["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.execute(text("DELETE FROM labels WHERE id = :i"), {"i": label_id})
    db.commit()


@router.post("/submissions/{submission_id}/private_notes")
def add_or_update_note(submission_id: int, body: PrivateNoteSchema,
                      user=Depends(require_user), db=Depends(get_db)):
    sub = _require_submission(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    existing = db.execute(
        text("SELECT id FROM private_note WHERE user_id = :u AND submission_id = :s"),
        {"u": user["id"], "s": submission_id},
    ).first()
    if existing:
        db.execute(
            text("UPDATE private_note SET note = :n, updated_at = now() WHERE id = :i"),
            {"n": body.note, "i": existing[0]},
        )
    else:
        db.execute(
            text("INSERT INTO private_note (user_id, submission_id, note, created_at) "
                 "VALUES (:u, :s, :n, now())"),
            {"u": user["id"], "s": submission_id, "n": body.note},
        )
    db.commit()
    return {"note": body.note}


@router.post("/submissions/{submission_id}/favorites", status_code=201)
def create_favorite(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    sub = _require_submission(db, submission_id)
    _require_phase(db, sub, "avaliacao")
    try:
        db.execute(
            text("INSERT INTO favorites (user_id, submission_id, created_at) "
                 "VALUES (:u, :s, now())"),
            {"u": user["id"], "s": submission_id},
        )
        db.commit()
    except Exception:
        db.rollback()
    return "Favorite created"


@router.delete("/submissions/{submission_id}/favorites")
def remove_favorite(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    db.execute(
        text("DELETE FROM favorites WHERE user_id = :u AND submission_id = :s"),
        {"u": user["id"], "s": submission_id},
    )
    db.commit()
    return "Favorite removed"


@router.post("/submissions/{submission_id}/view")
def register_view(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    existing = db.execute(
        text("SELECT id FROM submission_view WHERE user_id = :u AND submission_id = :s "
             "AND created_at::date = current_date"),
        {"u": user["id"], "s": submission_id},
    ).first()
    if existing:
        db.execute(
            text("UPDATE submission_view SET updated_at = now() WHERE id = :i"),
            {"i": existing[0]},
        )
    else:
        db.execute(
            text("INSERT INTO submission_view (user_id, submission_id, created_at, updated_at) "
                 "VALUES (:u, :s, now(), now())"),
            {"u": user["id"], "s": submission_id},
        )
    db.commit()
    return {"message": "View registered"}


@router.get("/submissions/{submission_id}/view")
def get_submission_views(submission_id: int, user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    rows = db.execute(
        text('SELECT v.*, u.id AS uid, u.name AS uname, u.email AS uemail '
             "FROM submission_view v JOIN \"user\" u ON u.id = v.user_id "
             "WHERE v.submission_id = :s ORDER BY v.id"),
        {"s": submission_id},
    ).mappings().all()
    return [
        {
            "id": r["id"],
            "user": {"id": r["uid"], "name": r["uname"], "email": r["uemail"]},
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@router.post("/submissions/{submission_id}/bidding")
def toggle_bidding(submission_id: int, body: BiddingSchema,
                   user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    target = user["id"]
    if body.user_id is not None and user["role"] in ADMIN_ROLES:
        target = body.user_id
    db.execute(
        text("DELETE FROM labels WHERE user_id = :u AND submission_id = :s "
             "AND context_type = 'bidding'"),
        {"u": target, "s": submission_id},
    )
    if body.bidding:
        db.execute(
            text("INSERT INTO labels (user_id, submission_id, label, color, context_type) "
                 "VALUES (:u, :s, :l, '', 'bidding')"),
            {"u": target, "s": submission_id, "l": body.bidding.value},
        )
    db.commit()
    return "Bidding updated"


@router.post("/submissions/{submission_id}/select")
def select_stats(submission_id: int, body: StatsSchema,
                 user=Depends(require_admin), db=Depends(get_db)):
    sub = _require_submission(db, submission_id)
    edict = get_edict(db, sub["edict_id"])
    if edict is None or not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict is closed")
    advisor_id = body.user_ids[0] if body.user_ids else sub["advisor_id"]
    db.execute(
        text("UPDATE submission SET stats = :s, advisor_id = :a, updated_at = now() "
             "WHERE id = :i"),
        {"s": body.stats.value, "a": advisor_id, "i": submission_id},
    )
    db.commit()
    return "Submission status updated"


@router.post("/submissions/{submission_id}/entry-semester")
def toggle_entry_semester(submission_id: int, body: EntrySemesterSchema,
                          user=Depends(require_user), db=Depends(get_db)):
    _require_submission(db, submission_id)
    semester = normalize_semester(body.semester)
    db.execute(
        text("UPDATE submission SET entry_semester = :s, updated_at = now() WHERE id = :i"),
        {"s": semester, "i": submission_id},
    )
    db.commit()
    return "Entry semester updated"


@router.get("/submissions/{submission_id}/files/{label}/{filename}")
def get_file(submission_id: int, label: str, filename: str,
             user=Depends(require_user), db=Depends(get_db), fdb=Depends(get_forms_db)):
    sub = _require_submission(db, submission_id)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=404, detail="File not found")
    row = fdb.execute(
        text("SELECT 1 FROM responses r JOIN form_field f ON f.id = r.field_id "
             "WHERE r.response_id = :rid AND f.name = :label AND r.value = :fn"),
        {"rid": sub["candidate_form_id"], "label": label, "fn": filename},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")
    path = UPLOADS / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path), filename=filename)


@router.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(submission_id: int, body: RequestReesendSchema,
                       user=Depends(require_user), db=Depends(get_db),
                       fdb=Depends(get_forms_db)):
    sub = _require_submission(db, submission_id)
    edict = _require_phase(db, sub, "homologacao")
    resp, data = candidate_data(fdb, db, sub, edict)
    if resp is None:
        raise HTTPException(status_code=404, detail="Form response not found")
    fdb.execute(
        text("SELECT * FROM update_form_response_section(:i, 0)"),
        {"i": sub["candidate_form_id"]},
    )
    fdb.commit()
    email = data.get("email") or resp["email"] or ""
    name = data.get("name") or ""
    send_resend_email(email, name, body.text, str(resp["token"]), bcc=[user["email"]])
    return {"message": "Resubmission requested", "email_sent": email}


@router.post("/submissions/{submission_id}/send-accept")
def send_accept_forms(submission_id: int, user=Depends(require_user),
                      db=Depends(get_db), fdb=Depends(get_forms_db)):
    sub = _require_submission(db, submission_id)
    edict = get_edict(db, sub["edict_id"])
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if not edict["accept_forms"]:
        raise HTTPException(status_code=404, detail="Accept form not configured")
    if sub["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Accept form already sent")
    resp, data = candidate_data(fdb, db, sub, edict)
    if resp is None:
        raise HTTPException(status_code=404, detail="Form response not found")
    email = data.get("email") or resp["email"] or ""
    name = data.get("name") or ""
    accept_form = int(edict["accept_forms"])
    shared_id = fdb.execute(
        text("INSERT INTO form_shared (form_id, unique_answers, is_public, token, "
             "created_at, expiration_at) "
             "VALUES (:f, true, false, CAST(:t AS uuid), now(), :exp) RETURNING id"),
        {"f": accept_form, "t": str(uuid.uuid4()), "exp": edict["closed_date"]},
    ).scalar()
    version = fdb.execute(
        text("SELECT version FROM form WHERE id = :f"), {"f": accept_form}
    ).scalar() or 1
    response_id = fdb.execute(
        text("INSERT INTO form_response (form_id, shared_id, email, token, current_section, "
             "submitted_at, metadata, form_version) "
             "VALUES (:f, :s, :e, CAST(:t AS uuid), 0, NULL, '{}'::jsonb, :v) RETURNING id"),
        {"f": accept_form, "s": shared_id, "e": email,
         "t": str(uuid.uuid4()), "v": version},
    ).scalar()
    fdb.commit()
    db.execute(
        text("UPDATE submission SET accept_form_id = :a, updated_at = now() WHERE id = :i"),
        {"a": response_id, "i": submission_id},
    )
    db.commit()
    advisor = user_by_id(db, sub["advisor_id"]) if sub["advisor_id"] else None
    send_accept_email(
        email, name, _accept_token(fdb, response_id), edict["closed_date"],
        cc=[advisor["email"]] if advisor else None,
    )
    return {"message": "Accept form sent", "email_sent": email}


def _accept_token(fdb, response_id) -> str:
    return str(fdb.execute(
        text("SELECT token FROM form_response WHERE id = :i"), {"i": response_id}
    ).scalar())


@router.post("/submissions/{submission_id}/send-letter")
def send_accept_letter(submission_id: int, user=Depends(require_user),
                       db=Depends(get_db), fdb=Depends(get_forms_db)):
    sub = _require_submission(db, submission_id)
    if sub["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if sub["letter_sent"]:
        raise HTTPException(status_code=400, detail="Letter already sent")
    edict = get_edict(db, sub["edict_id"])
    resp, data = candidate_data(fdb, db, sub, edict)
    email = (data.get("email") or (resp or {}).get("email") or "")
    name = data.get("name") or ""
    send_letter_email(email, name)
    db.execute(
        text("UPDATE submission SET letter_sent = true, updated_at = now() WHERE id = :i"),
        {"i": submission_id},
    )
    db.commit()
    return {"message": "Accept letter sent", "email_sent": email}
