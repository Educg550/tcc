from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from auth import current_user, require_admin
from database import Session
from services import forms_service as forms
from services.submissions_service import get_edict, list_submissions

router = APIRouter(tags=["edicts"])

PHASES = ("inscricoes", "homologacao", "avaliacao", "encerrado")
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class EditEdictDateSchema(BaseModel):
    closed_date: date


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


def _check_dates(d1, d2, d3, d4):
    if not (d1 < d2 < d3 < d4):
        raise HTTPException(status_code=422, detail="Dates must be in strict chronological order")


def _user_slots(user_id, edict_id):
    with Session() as s:
        row = s.execute(
            text("select slots from user_edict_slots where user_id = :u and edict_id = :e"),
            {"u": user_id, "e": edict_id},
        ).mappings().first()
    return str(row["slots"]) if row and row["slots"] is not None else "0"


def _phases_json(edict_id):
    with Session() as s:
        rows = s.execute(
            text("select * from edict_phase where edict_id = :e order by id"),
            {"e": edict_id},
        ).mappings().all()
    return [
        {
            "id": r["id"],
            "closed_date": r["closed_date"].isoformat() if r["closed_date"] else None,
            "phase": r["phase"],
        }
        for r in rows
    ]


def _edict_detail(edict, user_id):
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": str(edict["candidate_forms"] or ""),
        "recommender_form_id": str(edict["recommenders_forms"] or ""),
        "description": edict["description"] or "",
        "closed_date": edict["closed_date"].isoformat() if edict["closed_date"] else None,
        "created_at": edict["created_at"].isoformat() if edict["created_at"] else None,
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"].isoformat() if edict["updated_at"] else None,
        "phase": edict["phase"],
        "phases": _phases_json(edict["id"]),
        "slots": _user_slots(user_id, edict["id"]),
    }


def _require_edict(edict_id):
    edict = get_edict(edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


@router.get("/edicts")
def get_all_edicts(
    type: str | None = None,
    is_open: bool | None = None,
    user=Depends(current_user),
):
    query = "select * from edict where true"
    params = {}
    if type is not None:
        query += " and type = :t"
        params["t"] = type
    if is_open is not None:
        query += " and is_open = :o"
        params["o"] = is_open
    query += " order by closed_date desc, id desc"
    with Session() as s:
        rows = s.execute(text(query), params).mappings().all()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "year": r["year"],
            "semester": r["semester"],
            "edict_type": r["type"],
            "is_open": r["is_open"],
        }
        for r in rows
    ]


@router.post("/edicts")
def create_edict(payload: InsertEdictSchema, user=Depends(require_admin)):
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    with Session() as s:
        edict_id = s.execute(
            text(
                "insert into edict (title, description, candidate_forms, recommenders_forms,"
                " closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id)"
                " values (:t, :d, :cf, :rf, :cd, :y, :se, :ty, 'inscricoes', :io, now(), now(), :u)"
                " returning id"
            ),
            {
                "t": payload.title,
                "d": payload.description,
                "cf": str(payload.candidate_forms),
                "rf": str(payload.recommenders_forms),
                "cd": payload.date_closed.date(),
                "y": payload.year,
                "se": payload.semester,
                "ty": payload.edict_type,
                "io": payload.is_open,
                "u": user["id"],
            },
        ).scalar_one()
        for phase, dt in (
            ("inscricoes", payload.date_application),
            ("homologacao", payload.date_evaluation),
            ("avaliacao", payload.date_verification),
            ("encerrado", payload.date_closed),
        ):
            s.execute(
                text("insert into edict_phase (edict_id, closed_date, phase) values (:e, :d, :p)"),
                {"e": edict_id, "d": dt.date(), "p": phase},
            )
        s.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": payload.date_application.isoformat(),
        "date_verification": payload.date_verification.isoformat(),
        "date_evaluation": payload.date_evaluation.isoformat(),
        "date_closed": payload.date_closed.isoformat(),
        "id": edict_id,
        "closed_date": payload.date_closed.isoformat(),
    }


@router.get("/edicts/{edict_id}")
def get_edict_by_id(edict_id: int, user=Depends(current_user)):
    return _edict_detail(_require_edict(edict_id), user["id"])


@router.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: int, payload: EditEdictSchema, user=Depends(require_admin)):
    _require_edict(edict_id)
    _check_dates(
        payload.date_application,
        payload.date_verification,
        payload.date_evaluation,
        payload.date_closed,
    )
    try:
        year = int(payload.year)
        semester = int(payload.semester)
    except ValueError:
        raise HTTPException(status_code=422, detail="year and semester must be integers")
    with Session() as s:
        s.execute(
            text(
                "update edict set title = :t, description = :d, year = :y, semester = :se,"
                " type = :ty, closed_date = :cd, updated_at = now() where id = :i"
            ),
            {
                "t": payload.title,
                "d": payload.description,
                "y": year,
                "se": semester,
                "ty": payload.edict_type,
                "cd": payload.date_closed.date(),
                "i": edict_id,
            },
        )
        for phase, dt in (
            ("inscricoes", payload.date_application),
            ("homologacao", payload.date_evaluation),
            ("avaliacao", payload.date_verification),
            ("encerrado", payload.date_closed),
        ):
            s.execute(
                text("update edict_phase set closed_date = :d where edict_id = :e and phase = :p"),
                {"d": dt.date(), "e": edict_id, "p": phase},
            )
        s.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": payload.date_application.isoformat(),
        "date_verification": payload.date_verification.isoformat(),
        "date_evaluation": payload.date_evaluation.isoformat(),
        "date_closed": payload.date_closed.isoformat(),
    }


@router.post("/edicts/{edict_id}/edit-date")
def edit_edict_date(edict_id: int, payload: EditEdictDateSchema, user=Depends(require_admin)):
    _require_edict(edict_id)
    with Session() as s:
        s.execute(
            text("update edict set closed_date = :d, updated_at = now() where id = :i"),
            {"d": payload.closed_date, "i": edict_id},
        )
        s.execute(
            text("update edict_phase set closed_date = :d where edict_id = :e and phase = 'encerrado'"),
            {"d": payload.closed_date, "e": edict_id},
        )
        s.commit()
    return {"closed_date": payload.closed_date.isoformat()}


@router.post("/edicts/{edict_id}/advance-phase")
def advance_phase(edict_id: int, payload: AdvancePhaseEdictSchema, user=Depends(require_admin)):
    edict = _require_edict(edict_id)
    with Session() as s:
        row = s.execute(
            text("select * from edict_phase where id = :i and edict_id = :e"),
            {"i": payload.id, "e": edict_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Phase not found")
    with Session() as s:
        s.execute(
            text("update edict set phase = :p, updated_at = now() where id = :i"),
            {"p": row["phase"], "i": edict_id},
        )
        s.commit()
    try:
        forms.set_form_phase(int(edict["candidate_forms"]), FORMS_PHASE[row["phase"]])
    except (TypeError, ValueError):
        pass
    return {"id": row["id"], "label": row["phase"]}


@router.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: int, payload: CloseEdictSchema, user=Depends(require_admin)):
    edict = _require_edict(edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict already closed")
    with Session() as s:
        s.execute(
            text("update edict set is_open = false, updated_at = now() where id = :i"),
            {"i": edict_id},
        )
        s.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: int, user=Depends(require_admin)):
    _require_edict(edict_id)
    with Session() as s:
        s.execute(text("delete from edict where id = :i"), {"i": edict_id})
        s.commit()
    return {"message": "Edict removed successfully"}


@router.post("/edicts/{edict_id}/slots")
def set_user_slots(edict_id: int, payload: SlotsSchema, user=Depends(current_user)):
    _require_edict(edict_id)
    amount = payload.amount.strip()
    if amount == "":
        amount = "0"
    try:
        value = int(amount)
    except ValueError:
        raise HTTPException(status_code=422, detail="amount must be an integer")
    if value < 0:
        value = 0
    with Session() as s:
        existing = s.execute(
            text("select id from user_edict_slots where user_id = :u and edict_id = :e"),
            {"u": user["id"], "e": edict_id},
        ).mappings().first()
        if existing:
            s.execute(
                text("update user_edict_slots set slots = :s where id = :i"),
                {"s": value, "i": existing["id"]},
            )
        else:
            s.execute(
                text("insert into user_edict_slots (user_id, edict_id, slots) values (:u, :e, :s)"),
                {"u": user["id"], "e": edict_id, "s": value},
            )
        s.commit()
    return {"amount": str(value)}


@router.get("/edicts/{edict_id}/submissions")
def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(current_user),
):
    edict = _require_edict(edict_id)
    return {"submissions": list_submissions(edict, user["id"], stats=stats, only_favorites=only_favorites)}
