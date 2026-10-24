from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from src.auth import get_current_user, require_admin
from src.db import get_db, get_forms_db
from src.schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)
from src.services import reports
from src.services.forms_service import get_edict
from src.services.submissions_service import build_submission_dict, is_favorite, sync_edict

router = APIRouter(prefix="/edicts", tags=["edicts"])

PHASE_DATE_COLUMNS = [
    ("inscricoes", "date_application"),
    ("avaliacao", "date_verification"),
    ("homologacao", "date_evaluation"),
    ("encerrado", "date_closed"),
]
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


@router.get("/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return reports.download(job_id, "application/pdf", ".pdf")


@router.get("/download_csv/{job_id}")
async def download_csv(job_id: str):
    return reports.download(job_id, "text/csv", ".csv")


@router.get("")
async def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    query = "SELECT id, title, year, semester, type AS edict_type, is_open FROM edict WHERE 1=1"
    params = {}
    if type is not None:
        query += " AND type = :type"
        params["type"] = type
    if is_open is not None:
        query += " AND is_open = :is_open"
        params["is_open"] = is_open
    query += " ORDER BY closed_date DESC, id DESC"
    result = await db.execute(text(query), params)
    return [dict(r._mapping) for r in result]


@router.post("")
async def create_edict(
    body: InsertEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    dates = {col: getattr(body, col) for _, col in PHASE_DATE_COLUMNS}
    order = [dates[col] for _, col in PHASE_DATE_COLUMNS]
    if any(order[i] > order[i + 1] for i in range(len(order) - 1)):
        raise HTTPException(status_code=400, detail="Dates out of order")
    result = await db.execute(
        text(
            "INSERT INTO edict(title, description, candidate_forms, recommenders_forms, "
            "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
            "VALUES(:title, :description, :candidate_forms, :recommenders_forms, :closed_date, "
            ":year, :semester, :edict_type, 'inscricoes', :is_open, now(), now(), :user_id) "
            "RETURNING id"
        ),
        {
            "title": body.title,
            "description": body.description,
            "candidate_forms": str(body.candidate_forms),
            "recommenders_forms": str(body.recommenders_forms),
            "closed_date": body.date_closed.date(),
            "year": body.year,
            "semester": body.semester,
            "edict_type": body.edict_type,
            "is_open": body.is_open,
            "user_id": user["id"],
        },
    )
    edict_id = result.scalar()
    for phase, col in PHASE_DATE_COLUMNS:
        await db.execute(
            text("INSERT INTO edict_phase(edict_id, phase, closed_date) VALUES(:e, :p, :d)"),
            {"e": edict_id, "p": phase, "d": dates[col].date()},
        )
    await db.commit()
    return {
        "id": edict_id,
        "title": body.title,
        "description": body.description,
        "year": body.year,
        "semester": body.semester,
        "edict_type": body.edict_type,
        "is_open": body.is_open,
        "candidate_forms": body.candidate_forms,
        "recommenders_forms": body.recommenders_forms,
        "date_application": body.date_application,
        "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation,
        "date_closed": body.date_closed,
        "closed_date": body.date_closed,
    }


@router.get("/{edict_id}")
async def get_edict_by_id(
    edict_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    result = await db.execute(
        text("SELECT id, phase, closed_date::text AS closed_date FROM edict_phase "
             "WHERE edict_id = :e ORDER BY id"),
        {"e": edict_id},
    )
    phases = [dict(r._mapping) for r in result]
    result = await db.execute(
        text("SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e"),
        {"u": user["id"], "e": edict_id},
    )
    row = result.first()
    slots = str(row[0]) if row and row[0] is not None else "0"
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": str(edict["candidate_forms"]),
        "recommender_form_id": str(edict["recommenders_forms"]),
        "description": edict["description"],
        "closed_date": str(edict["closed_date"]) if edict["closed_date"] else None,
        "created_at": edict["created_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": phases,
        "slots": slots,
    }


@router.post("/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    body: EditEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    dates = {col: getattr(body, col) for _, col in PHASE_DATE_COLUMNS}
    order = [dates[col] for _, col in PHASE_DATE_COLUMNS]
    if any(order[i] > order[i + 1] for i in range(len(order) - 1)):
        raise HTTPException(status_code=400, detail="Dates out of order")
    await db.execute(
        text(
            "UPDATE edict SET title = :title, description = :description, year = :year, "
            "semester = :semester, type = :edict_type, closed_date = :closed_date, "
            "updated_at = now() WHERE id = :i"
        ),
        {
            "title": body.title,
            "description": body.description,
            "year": int(body.year),
            "semester": int(body.semester),
            "edict_type": body.edict_type,
            "closed_date": body.date_closed.date(),
            "i": edict_id,
        },
    )
    for phase, col in PHASE_DATE_COLUMNS:
        await db.execute(
            text("UPDATE edict_phase SET closed_date = :d WHERE edict_id = :e AND phase = :p"),
            {"d": dates[col].date(), "e": edict_id, "p": phase},
        )
    await db.commit()
    return {
        "title": body.title,
        "description": body.description,
        "year": body.year,
        "semester": body.semester,
        "edict_type": body.edict_type,
        "date_application": body.date_application,
        "date_verification": body.date_verification,
        "date_evaluation": body.date_evaluation,
        "date_closed": body.date_closed,
    }


@router.post("/{edict_id}/edit-date")
async def edit_edict_date_only(
    edict_id: int,
    body: EditEdictDateSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    await db.execute(
        text("UPDATE edict SET closed_date = :d, updated_at = now() WHERE id = :i"),
        {"d": body.closed_date, "i": edict_id},
    )
    await db.execute(
        text("UPDATE edict_phase SET closed_date = :d WHERE edict_id = :e AND phase = 'encerrado'"),
        {"d": body.closed_date, "e": edict_id},
    )
    await db.commit()
    return {"closed_date": str(body.closed_date)}


@router.post("/{edict_id}/advance-phase")
async def advance_edict(
    edict_id: int,
    body: AdvancePhaseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    result = await db.execute(
        text("SELECT id, phase FROM edict_phase WHERE id = :i AND edict_id = :e"),
        {"i": body.id, "e": edict_id},
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Phase not found")
    phase = row[1]
    await db.execute(
        text("UPDATE edict SET phase = :p, updated_at = now() WHERE id = :i"),
        {"p": phase, "i": edict_id},
    )
    form_id = int(edict["candidate_forms"])
    await fdb.execute(
        text("SELECT id FROM change_form_phase(:f, CAST(:p AS form_phase))"),
        {"f": form_id, "p": FORMS_PHASE[phase]},
    )
    await db.commit()
    await fdb.commit()
    return {"id": body.id, "label": phase}


@router.patch("/{edict_id}/close")
async def close_edict(
    edict_id: int,
    body: CloseEdictSchema,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict already closed")
    await db.execute(
        text("UPDATE edict SET is_open = false, updated_at = now() WHERE id = :i"),
        {"i": edict_id},
    )
    await db.commit()
    return {"message": "Edict closed"}


@router.delete("/{edict_id}/remove")
async def remove_edict(
    edict_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    await db.execute(text("DELETE FROM edict WHERE id = :i"), {"i": edict_id})
    await db.commit()
    return {"message": "Edict removed"}


@router.post("/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    body: SlotsSchema,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    try:
        amount = int(body.amount)
    except (TypeError, ValueError):
        amount = 0
    if amount < 0:
        amount = 0
    await db.execute(
        text(
            "INSERT INTO user_edict_slots(user_id, edict_id, slots) VALUES(:u, :e, :a) "
            "ON CONFLICT (user_id, edict_id) DO UPDATE SET slots = :a"
        ),
        {"u": user["id"], "e": edict_id, "a": amount},
    )
    await db.commit()
    return {"amount": str(amount)}


@router.get("/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    await sync_edict(db, fdb, edict)
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM submission WHERE edict_id = :e ORDER BY id"), {"e": edict_id}
    )
    submissions = []
    for sub in [dict(r._mapping) for r in result]:
        if stats is not None and sub["stats"] != stats:
            continue
        if only_favorites and not await is_favorite(db, user["id"], sub["id"]):
            continue
        submissions.append(await build_submission_dict(db, fdb, edict, sub, user))
    return {"submissions": submissions}


@router.post("/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    sections: SectionsDocument = SectionsDocument(),
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    if mode == "pdf":
        data = await reports.collect_pdf_data(db, fdb, edict, sections.model_dump())
        job_id = reports.start_job("pdf", reports.build_pdf, data)
        return {"job_id": job_id, "status": "processing"}
    return await reports.get_interactors(db, edict_id)


@router.post("/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    data = await reports.collect_csv_data(db, fdb, edict)
    job_id = reports.start_job("csv", reports.build_csv, data)
    return {"job_id": job_id, "status": "processing"}
