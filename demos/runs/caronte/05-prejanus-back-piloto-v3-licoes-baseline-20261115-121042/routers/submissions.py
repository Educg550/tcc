import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user, get_db, get_forms_db, require_admin
from config import SIGNATURE_PATH, UPLOADS_DIR
from schemas import (
    BiddingSchema,
    CommentSchema,
    EntrySemesterSchema,
    LabelInputSchema,
    PrivateNoteSchema,
    RequestReesendSchema,
    StatsSchema,
)
from services import forms_service, mailer, submission_service
from services.mapping_service import resolve_value

router = APIRouter(prefix="/submissions", tags=["submissions"])

SP_TZ = ZoneInfo("America/Sao_Paulo")

BIDDING_VALUES = {"decline", "available", "interested", "agreed", "interested_scholarship", ""}


async def _get_submission_or_404(db: AsyncSession, submission_id: int) -> dict:
    submission = await submission_service.get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


async def _get_edict_of(db: AsyncSession, submission: dict) -> dict:
    edict = await submission_service.get_edict(db, submission["edict_id"])
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def _require_phase(edict: dict, phase: str = "avaliacao"):
    if edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Edict is not in phase {phase}")


@router.get("/{submission_id}")
async def get_details(
    submission_id: int,
    include_comments: bool = False,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    summary = await submission_service.build_summary(db, fs, edict, submission, user)
    summary["labels"] = await submission_service.get_submission_labels(db, submission_id)
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    values = await forms_service.get_response_values(fs, submission["candidate_form_id"])
    form_id = response["form_id"] if response else None
    submission_form = []
    if form_id is not None:
        submission_form = await submission_service.build_submission_form(
            fs, form_id, submission["candidate_form_version"], values
        )
    result = {"summary": summary, "submission_form": submission_form}
    if include_comments:
        result["comments"] = await _activity(db, fs, edict, submission)
    return result


async def _activity(db: AsyncSession, fs: AsyncSession, edict: dict, submission: dict) -> list[dict]:
    events = []
    result = await db.execute(
        text(
            'select c.id, c.user_id, c.comment, c.created_at, c.updated_at, u.name from comment c '
            'join "user" u on u.id = c.user_id where c.submission_id = :sid order by c.created_at'
        ),
        {"sid": submission["id"]},
    )
    for row in result.mappings():
        events.append(
            {
                "id": row["id"],
                "user": {"id": row["user_id"], "name": row["name"]},
                "text": row["comment"],
                "type": "comment",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    if response is not None:
        values = await forms_service.get_response_values(fs, submission["candidate_form_id"])
        mapping_row = await submission_service.get_mapping(
            db, edict["id"], "candidate", submission["candidate_form_version"]
        )
        name = None
        if mapping_row:
            name = resolve_value(mapping_row["mapping"], ("personal", "name"), values)
        events.append(
            {
                "user": {"id": 0, "name": name or response.get("email") or "Candidato"},
                "text": "Candidatura submetida",
                "type": "submission",
                "created_at": response.get("submitted_at"),
            }
        )
    for recommendation in await submission_service.get_recommendations_for_submission(
        db, fs, edict, submission
    ):
        events.append(
            {
                "user": {"id": 0, "name": recommendation.get("name") or recommendation.get("email") or "Recomendador"},
                "text": recommendation.get("text") or "Recomendacao submetida",
                "type": "recommendation",
                "created_at": recommendation.get("submitted_at"),
            }
        )
    accept = await submission_service.get_accept_info(fs, submission)
    if accept.get("sent") == "replied":
        events.append(
            {
                "user": {"id": 0, "name": "Candidato"},
                "text": "Aceite respondido",
                "type": "accept",
                "created_at": accept.get("submitted_at"),
            }
        )
    def _sort_key(value):
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    events.sort(key=lambda e: _sort_key(e.get("created_at")))
    return events


@router.get("/{submission_id}/comments")
async def get_all_comments(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    return await _activity(db, fs, edict, submission)


@router.post("/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    _require_phase(edict)
    now = datetime.now(timezone.utc)
    created_at = payload.created_at or now
    updated_at = payload.updated_at or created_at
    result = await db.execute(
        text(
            "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
            "values (:uid, :sid, :comment, :created_at, :updated_at) returning id"
        ),
        {
            "uid": user["id"],
            "sid": submission_id,
            "comment": payload.comment,
            "created_at": created_at,
            "updated_at": updated_at,
        },
    )
    comment_id = result.scalar_one()
    await db.commit()
    return {
        "id": comment_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": payload.comment,
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.delete("/comments/{comment_id}")
async def remove_comment(
    comment_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("select user_id from comment where id = :id"), {"id": comment_id}
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if row[0] != user["id"]:
        raise HTTPException(status_code=403, detail="Not the comment author")
    await db.execute(text("delete from comment where id = :id"), {"id": comment_id})
    await db.commit()
    return Response(status_code=204)


@router.post("/{submission_id}/favorites")
async def create_favorite(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    _require_phase(edict)
    if await submission_service.is_favorite(db, submission_id, user["id"]):
        raise HTTPException(status_code=409, detail="Favorite already exists")
    await db.execute(
        text("insert into favorites (user_id, submission_id, created_at) values (:uid, :sid, :now)"),
        {"uid": user["id"], "sid": submission_id, "now": datetime.now(timezone.utc)},
    )
    await db.commit()
    return JSONResponse(status_code=201, content="Favorite created successfully")


@router.delete("/{submission_id}/favorites")
async def remove_favorite(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    result = await db.execute(
        text("select 1 from favorites where submission_id = :sid and user_id = :uid"),
        {"sid": submission_id, "uid": user["id"]},
    )
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.execute(
        text("delete from favorites where submission_id = :sid and user_id = :uid"),
        {"sid": submission_id, "uid": user["id"]},
    )
    await db.commit()
    return Response(status_code=204)


@router.post("/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInputSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    _require_phase(edict)
    await db.execute(
        text(
            "update labels set color = :color where user_id = :uid and label = :label "
            "and context_type = 'candidate'"
        ),
        {"color": payload.color, "uid": user["id"], "label": payload.label},
    )
    result = await db.execute(
        text(
            "insert into labels (user_id, submission_id, label, color, context_type) "
            "values (:uid, :sid, :label, :color, 'candidate') returning id"
        ),
        {
            "uid": user["id"],
            "sid": submission_id,
            "label": payload.label,
            "color": payload.color,
        },
    )
    label_id = result.scalar_one()
    await db.commit()
    return {
        "id": label_id,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": payload.label,
        "color": payload.color,
    }


@router.get("/{submission_id}/labels")
async def get_labels(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    result = await db.execute(
        text(
            "select distinct label, min(id) as id, color from labels "
            "where user_id = :uid and context_type = 'candidate' group by label, color order by id"
        ),
        {"uid": user["id"]},
    )
    return {
        "labels": [{"id": r.id, "label": r.label, "color": r.color} for r in result.mappings()]
    }


@router.delete("/label/{label_id}")
async def remove_label(
    label_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("select user_id from labels where id = :id"), {"id": label_id})
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Label not found")
    if row[0] != user["id"]:
        raise HTTPException(status_code=403, detail="Not the label author")
    await db.execute(text("delete from labels where id = :id"), {"id": label_id})
    await db.commit()
    return Response(status_code=204)


@router.post("/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    _require_phase(edict)
    now = datetime.now(timezone.utc)
    existing = await db.execute(
        text("select id from private_note where submission_id = :sid and user_id = :uid"),
        {"sid": submission_id, "uid": user["id"]},
    )
    row = existing.first()
    if row:
        await db.execute(
            text("update private_note set note = :note, updated_at = :now where id = :id"),
            {"note": payload.note, "now": now, "id": row[0]},
        )
    else:
        await db.execute(
            text(
                "insert into private_note (user_id, submission_id, note, created_at) "
                "values (:uid, :sid, :note, :now)"
            ),
            {"uid": user["id"], "sid": submission_id, "note": payload.note, "now": now},
        )
    await db.commit()
    return {"note": payload.note}


@router.post("/{submission_id}/view")
async def register_view(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    now = datetime.now(SP_TZ)
    result = await db.execute(
        text(
            "select id from submission_view where submission_id = :sid and user_id = :uid "
            "and (created_at at time zone 'America/Sao_Paulo')::date = :today"
        ),
        {"sid": submission_id, "uid": user["id"], "today": now.date()},
    )
    if result.first() is None:
        await db.execute(
            text(
                "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                "values (:uid, :sid, :now, :now)"
            ),
            {"uid": user["id"], "sid": submission_id, "now": datetime.now(timezone.utc)},
        )
        await db.commit()
    return {"message": "View registered"}


@router.get("/{submission_id}/view")
async def get_submission_views(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    result = await db.execute(
        text(
            "select v.id, v.user_id, u.name, v.created_at, v.updated_at from submission_view v "
            'join "user" u on u.id = v.user_id where v.submission_id = :sid order by v.created_at'
        ),
        {"sid": submission_id},
    )
    return [
        {
            "id": r.id,
            "user": {"id": r.user_id, "name": r.name},
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in result.mappings()
    ]


@router.post("/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    if payload.bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Invalid bidding value")
    if user["role"] in {"administrator", "secretary", "coordinator"} and payload.user_id is not None:
        target_id = payload.user_id
    else:
        target_id = user["id"]
    await db.execute(
        text(
            "delete from labels where submission_id = :sid and user_id = :uid "
            "and context_type = 'bidding'"
        ),
        {"sid": submission_id, "uid": target_id},
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


@router.post("/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_submission_or_404(db, submission_id)
    semester = payload.semester
    lowered = semester.strip().lower()
    if "primeiro" in lowered or "first" in lowered:
        semester = "Primeiro semestre."
    elif "segundo" in lowered or "second" in lowered:
        semester = "Segundo semestre."
    await db.execute(
        text("update submission set entry_semester = :semester, updated_at = :now where id = :id"),
        {"semester": semester, "now": datetime.now(timezone.utc), "id": submission_id},
    )
    await db.commit()
    return semester


@router.post("/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict is closed")
    if payload.stats not in {"approved", "refused", "underreview", "waitlist"}:
        raise HTTPException(status_code=422, detail="Invalid stats")
    advisor_id = None
    if payload.stats == "approved":
        if not payload.user_ids or len(payload.user_ids) != 1:
            raise HTTPException(status_code=400, detail="Approved requires exactly one advisor")
        advisor = await submission_service.get_advisor(db, payload.user_ids[0])
        if advisor is None:
            raise HTTPException(status_code=404, detail="Advisor not found")
        advisor_id = payload.user_ids[0]
    await db.execute(
        text(
            "update submission set stats = :stats, advisor_id = :advisor, updated_at = :now "
            "where id = :id"
        ),
        {
            "stats": payload.stats,
            "advisor": advisor_id,
            "now": datetime.now(timezone.utc),
            "id": submission_id,
        },
    )
    await db.commit()
    return payload.stats


@router.get("/{submission_id}/files/{label}/{filename}")
async def get_file(
    submission_id: int,
    label: str,
    filename: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    if response is None:
        raise HTTPException(status_code=404, detail="File not found")
    target = None
    fields = await fs.execute(
        text(
            "select f.id, f.label, r.value from form_field f left join responses r "
            "on r.field_id = f.id and r.response_id = :rid where f.form_id = :fid and f.type = 'File'"
        ),
        {"rid": submission["candidate_form_id"], "fid": response["form_id"]},
    )
    for row in fields.mappings():
        labels = row.label or {}
        field_label = labels.get("pt") or labels.get("en") or ""
        if field_label != label:
            continue
        value = row.value
        if value is None:
            continue
        if os.path.basename(value) == filename or value == filename:
            target = value
            break
    if target is None:
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.isabs(target) and target.startswith(UPLOADS_DIR):
        path = target
    else:
        path = _find_upload(os.path.basename(target))
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _find_upload(filename: str) -> str | None:
    for root, _dirs, files in os.walk(UPLOADS_DIR):
        if filename in files:
            return os.path.join(root, filename)
    return None


async def _candidate_email(db: AsyncSession, fs: AsyncSession, edict: dict, submission: dict):
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    if response is None:
        return None
    values = await forms_service.get_response_values(fs, submission["candidate_form_id"])
    mapping_row = await submission_service.get_mapping(
        db, edict["id"], "candidate", submission["candidate_form_version"]
    )
    if mapping_row:
        email = resolve_value(mapping_row["mapping"], ("personal", "email"), values)
        name = resolve_value(mapping_row["mapping"], ("personal", "name"), values)
        if email:
            return email, name
    return response.get("email"), None


@router.post("/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    if edict["phase"] != "homologacao":
        raise HTTPException(status_code=400, detail="Edict is not in phase homologacao")
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    if response is None:
        raise HTTPException(status_code=404, detail="Candidate response not found")
    contact = await _candidate_email(db, fs, edict, submission)
    email = contact[0] if contact else None
    if not email:
        raise HTTPException(status_code=404, detail="Candidate email not found")
    await forms_service.reopen_response(fs, submission["candidate_form_id"])
    link = f"{_base_url()}/form/{response['token']}"
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua candidatura precisa de corre&ccedil;&otilde;es.</p>"
        f"<p>Motivo: {payload.text}</p>"
        f"<p>Acesse o formul&aacute;rio em: <a href=\"{link}\">{link}</a></p>"
    )
    mailer.send_email(
        "Solicitacao de correcao de candidatura",
        html,
        to=email,
        bcc=[user["email"]],
    )
    return {
        "message": "Resubmission requested",
        "email_sent": email,
    }


def _base_url() -> str:
    from config import settings

    return settings.base_url


@router.post("/{submission_id}/send-accept")
async def send_accept(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    if submission["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if submission["accept_form_id"]:
        raise HTTPException(status_code=400, detail="Accept form already sent")
    accept_form_ids = submission_service.parse_form_ids(edict.get("accept_forms"))
    if not accept_form_ids:
        raise HTTPException(status_code=404, detail="Accept form not configured")
    accept_form_id = accept_form_ids[0]
    contact = await _candidate_email(db, fs, edict, submission)
    email = contact[0] if contact else None
    name = contact[1] if contact else None
    if not email:
        raise HTTPException(status_code=404, detail="Candidate email not found")
    shared = await forms_service.create_shared(fs, accept_form_id, edict["closed_date"])
    response = await forms_service.create_response(fs, accept_form_id, shared["id"], email, 1)
    await db.execute(
        text("update submission set accept_form_id = :rid, updated_at = :now where id = :id"),
        {"rid": response["id"], "now": datetime.now(timezone.utc), "id": submission_id},
    )
    await db.commit()
    link = f"{_base_url()}/form/{response['token']}"
    deadline = edict["closed_date"]
    html = (
        f"<p>Caro(a) {name or 'candidato(a)'},</p>"
        f"<p>Parab&eacute;ns! Sua candidatura foi aprovada.</p>"
        f"<p>Dear candidate, congratulations! Your application has been approved.</p>"
        f"<p>Prazo / Deadline: {deadline}</p>"
        f"<p>Formul&aacute;rio de aceite / Acceptance form: <a href=\"{link}\">{link}</a></p>"
    )
    advisor = await submission_service.get_advisor(db, submission.get("advisor_id"))
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    mailer.send_email("Formulario de aceite / Acceptance form", html, to=email, cc=cc)
    return {"message": "Accept form sent", "email_sent": email}


@router.post("/{submission_id}/send-letter")
async def send_letter(
    submission_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    fs: AsyncSession = Depends(get_forms_db),
):
    submission = await _get_submission_or_404(db, submission_id)
    edict = await _get_edict_of(db, submission)
    if submission["stats"] != "approved":
        raise HTTPException(status_code=400, detail="Submission is not approved")
    if submission["letter_sent"]:
        raise HTTPException(status_code=400, detail="Letter already sent")
    contact = await _candidate_email(db, fs, edict, submission)
    email = contact[0] if contact else None
    name = contact[1] if contact else None
    if not email:
        raise HTTPException(status_code=404, detail="Candidate email not found")
    advisor = await submission_service.get_advisor(db, submission.get("advisor_id"))
    advisor_name = advisor["name"] if advisor else ""
    semester = submission.get("entry_semester") or ""
    year = edict["year"]
    html = (
        f"<p>Caro(a) {name or 'candidato(a)'},</p>"
        f"<p>Temos o prazer de informar que sua candidatura ao programa de "
        f"p&oacute;s-gradua&ccedil;&atilde;o foi aprovada.</p>"
        f"<p>Orientador(a): {advisor_name}</p>"
        f"<p>Semestre de ingresso: {semester}</p>"
        f"<p>Ano de ingresso: {year}</p>"
        "<p>Atenciosamente,</p>"
    )
    try:
        import base64

        with open(SIGNATURE_PATH, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        html += f'<p><img src="data:image/png;base64,{encoded}" alt="Assinatura"/></p>'
    except OSError:
        pass
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    mailer.send_email("Carta de aceite / Acceptance letter", html, to=email, cc=cc)
    await db.execute(
        text("update submission set letter_sent = true, updated_at = :now where id = :id"),
        {"now": datetime.now(timezone.utc), "id": submission_id},
    )
    await db.commit()
    return {"message": "Letter sent", "email_sent": email}
