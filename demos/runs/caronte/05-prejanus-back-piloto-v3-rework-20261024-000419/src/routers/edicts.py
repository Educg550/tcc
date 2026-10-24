"""Rotas de editais: CRUD, fases, mapeamentos, vagas e relatórios."""
import json
import os

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from ..auth import require_admin, require_user
from ..db import get_db, get_forms_db
from ..schemas import (
    AdvancePhaseEdictSchema,
    CloseEdictSchema,
    EditEdictDateSchema,
    EditEdictSchema,
    InsertEdictSchema,
    SectionsDocument,
    SlotsSchema,
)
from ..services import reports
from ..services.forms_integration import (
    form_phase_for,
    form_versions,
    set_form_phase,
    validate_mapping_tree,
)
from ..services.mailer import send_letter_email
from ..services.submissions import (
    build_submission_item,
    get_edict,
    sync_edict_submissions,
)

router = APIRouter(tags=["edicts"])

PHASE_DATES = (
    ("inscricoes", "date_application"),
    ("avaliacao", "date_verification"),
    ("homologacao", "date_evaluation"),
    ("encerrado", "date_closed"),
)


def _require_edict(db, edict_id):
    edict = get_edict(db, edict_id)
    if edict is None:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def _validate_dates(body) -> None:
    if not (
        body.date_application <= body.date_verification
        <= body.date_evaluation <= body.date_closed
    ):
        raise HTTPException(status_code=400, detail="Datas fora de ordem")


def _insert_phases(db, edict_id, body) -> None:
    for phase, attr in PHASE_DATES:
        db.execute(
            text("INSERT INTO edict_phase (edict_id, closed_date, phase) "
                 "VALUES (:e, :d, :p)"),
            {"e": edict_id, "d": getattr(body, attr), "p": phase},
        )


def _update_phases(db, edict_id, body) -> None:
    for phase, attr in PHASE_DATES:
        db.execute(
            text("UPDATE edict_phase SET closed_date = :d "
                 "WHERE edict_id = :e AND phase = :p"),
            {"e": edict_id, "d": getattr(body, attr), "p": phase},
        )


@router.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    path = reports.pop_ready(job_id, "pdf")
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"content-disposition": "inline"},
        background=BackgroundTask(_remove_file, path),
    )


@router.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    path = reports.pop_ready(job_id, "csv")
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path,
        media_type="text/csv",
        headers={"content-disposition": "inline"},
        background=BackgroundTask(_remove_file, path),
    )


def _remove_file(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


@router.get("/edicts")
def get_all_edicts(
    type: str | None = Query(default=None),
    is_open: bool | None = Query(default=None),
    user=Depends(require_user),
    db=Depends(get_db),
):
    query = "SELECT id, title, year, semester, type, is_open FROM edict WHERE true"
    params: dict = {}
    if type is not None:
        query += " AND type = :t"
        params["t"] = type
    if is_open is not None:
        query += " AND is_open = :o"
        params["o"] = is_open
    query += " ORDER BY closed_date DESC, id DESC"
    rows = db.execute(text(query), params).mappings().all()
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
def create_edict(body: InsertEdictSchema, user=Depends(require_admin), db=Depends(get_db)):
    _validate_dates(body)
    edict_id = db.execute(
        text("INSERT INTO edict (title, description, candidate_forms, recommenders_forms, "
             "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
             "VALUES (:t, :d, :c, :r, :cd, :y, :s, :ty, 'inscricoes', :o, now(), now(), :u) "
             "RETURNING id"),
        {
            "t": body.title, "d": body.description,
            "c": str(body.candidate_forms), "r": str(body.recommenders_forms),
            "cd": body.date_closed.date(), "y": body.year, "s": body.semester,
            "ty": body.edict_type, "o": body.is_open, "u": user["id"],
        },
    ).scalar()
    _insert_phases(db, edict_id, body)
    db.commit()
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
        "closed_date": body.date_closed.date(),
    }


@router.get("/edicts/{edict_id}")
def get_edict_by_id(edict_id: int, user=Depends(require_user), db=Depends(get_db)):
    edict = _require_edict(db, edict_id)
    phases = db.execute(
        text("SELECT id, closed_date, phase FROM edict_phase WHERE edict_id = :e ORDER BY id"),
        {"e": edict_id},
    ).mappings().all()
    slots = db.execute(
        text("SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e"),
        {"u": user["id"], "e": edict_id},
    ).scalar()
    return {
        "id": edict["id"],
        "title": edict["title"],
        "candidate_form_id": edict["candidate_forms"],
        "recommender_form_id": edict["recommenders_forms"],
        "description": edict["description"],
        "closed_date": edict["closed_date"],
        "created_at": edict["created_at"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "is_open": edict["is_open"],
        "updated_at": edict["updated_at"],
        "phase": edict["phase"],
        "phases": [
            {"id": p["id"], "closed_date": p["closed_date"], "phase": p["phase"]}
            for p in phases
        ],
        "slots": str(slots) if slots is not None else "0",
    }


@router.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: int, body: EditEdictSchema,
               user=Depends(require_admin), db=Depends(get_db)):
    _require_edict(db, edict_id)
    _validate_dates(body)
    db.execute(
        text("UPDATE edict SET title = :t, description = :d, year = :y, semester = :s, "
             "type = :ty, closed_date = :cd, updated_at = now() WHERE id = :i"),
        {
            "t": body.title, "d": body.description, "y": int(body.year),
            "s": int(body.semester), "ty": body.edict_type,
            "cd": body.date_closed.date(), "i": edict_id,
        },
    )
    _update_phases(db, edict_id, body)
    db.commit()
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


@router.post("/edicts/{edict_id}/edit-date")
def edit_edict_date(edict_id: int, body: EditEdictDateSchema,
                    user=Depends(require_admin), db=Depends(get_db)):
    _require_edict(db, edict_id)
    db.execute(
        text("UPDATE edict SET closed_date = :d, updated_at = now() WHERE id = :i"),
        {"d": body.closed_date, "i": edict_id},
    )
    db.execute(
        text("UPDATE edict_phase SET closed_date = :d "
             "WHERE edict_id = :e AND phase = 'encerrado'"),
        {"d": body.closed_date, "e": edict_id},
    )
    db.commit()
    return {"closed_date": body.closed_date.isoformat()}


@router.post("/edicts/{edict_id}/advance-phase")
def advance_edict(edict_id: int, body: AdvancePhaseEdictSchema,
                  user=Depends(require_admin), db=Depends(get_db),
                  fdb=Depends(get_forms_db)):
    _require_edict(db, edict_id)
    phase = db.execute(
        text("SELECT id, phase FROM edict_phase WHERE id = :i AND edict_id = :e"),
        {"i": body.id, "e": edict_id},
    ).mappings().first()
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    db.execute(
        text("UPDATE edict SET phase = :p, updated_at = now() WHERE id = :i"),
        {"p": phase["phase"], "i": edict_id},
    )
    db.commit()
    form_phase = form_phase_for(phase["phase"])
    edict = get_edict(db, edict_id)
    for column in ("candidate_forms", "recommenders_forms", "accept_forms"):
        value = edict[column]
        if value:
            try:
                set_form_phase(fdb, int(value), form_phase)
            except ValueError:
                pass
    return {"id": phase["id"], "label": phase["phase"]}


@router.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: int, user=Depends(require_admin), db=Depends(get_db)):
    _require_edict(db, edict_id)
    db.execute(text("DELETE FROM edict WHERE id = :i"), {"i": edict_id})
    db.commit()
    return {"message": "Edict deleted successfully"}


@router.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: int, body: CloseEdictSchema,
                user=Depends(require_admin), db=Depends(get_db)):
    edict = _require_edict(db, edict_id)
    if not edict["is_open"]:
        raise HTTPException(status_code=409, detail="Edict already closed")
    db.execute(
        text("UPDATE edict SET is_open = false, updated_at = now() WHERE id = :i"),
        {"i": edict_id},
    )
    db.commit()
    if body.send_approval_letter:
        approved = db.execute(
            text("SELECT s.id, u.email, u.name FROM submission s "
                 'JOIN "user" u ON u.id = s.advisor_id '
                 "WHERE s.edict_id = :e AND s.stats = 'approved' AND NOT s.letter_sent"),
            {"e": edict_id},
        ).mappings().all()
        for row in approved:
            send_letter_email(row["email"], row["name"])
            db.execute(
                text("UPDATE submission SET letter_sent = true WHERE id = :i"),
                {"i": row["id"]},
            )
        db.commit()
    return {"message": "Edict closed"}


@router.post("/edicts/{edict_id}/slots")
def set_user_slots(edict_id: int, body: SlotsSchema,
                   user=Depends(require_user), db=Depends(get_db)):
    _require_edict(db, edict_id)
    try:
        amount = int(body.amount)
    except (TypeError, ValueError):
        amount = 0
    amount = max(amount, 0)
    db.execute(
        text("INSERT INTO user_edict_slots (user_id, edict_id, slots) "
             "VALUES (:u, :e, :s) "
             "ON CONFLICT (user_id, edict_id) DO UPDATE SET slots = :s"),
        {"u": user["id"], "e": edict_id, "s": amount},
    )
    db.commit()
    return {"amount": str(amount)}


@router.get("/edicts/{edict_id}/submissions")
def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = Query(default=None),
    only_favorites: bool = Query(default=False),
    user=Depends(require_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    edict = _require_edict(db, edict_id)
    sync_edict_submissions(db, fdb, edict)
    query = "SELECT * FROM submission WHERE edict_id = :e"
    params: dict = {"e": edict_id}
    if stats is not None:
        query += " AND stats = :s"
        params["s"] = stats
    if only_favorites:
        query += " AND id IN (SELECT submission_id FROM favorites WHERE user_id = :u)"
        params["u"] = user["id"]
    query += " ORDER BY id"
    subs = db.execute(text(query), params).mappings().all()
    return {
        "submissions": [
            build_submission_item(db, fdb, sub, edict, user["id"]) for sub in subs
        ]
    }


@router.post("/edicts/{edict_id}/interactors_list")
def interactors_list(
    edict_id: int,
    mode: str = Query(default="plain_text"),
    body: SectionsDocument | None = None,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    _require_edict(db, edict_id)
    if mode == "pdf":
        options = body.model_dump() if body else {}
        job_id = reports.start_pdf(edict_id, options)
        return {"status": "processing", "job_id": job_id}
    return reports.interactors_list(db, edict_id)


@router.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(edict_id: int, user=Depends(require_admin), db=Depends(get_db)):
    _require_edict(db, edict_id)
    job_id = reports.start_job("csv", reports.generate_csv, edict_id)
    return {"status": "processing", "job_id": job_id}


def _mapping_form_id(edict, kind: str) -> int:
    column = "candidate_forms" if kind == "candidate" else "recommenders_forms"
    return int(edict[column])


def _create_mapping(db, fdb, edict_id, version, tree, kind, user):
    edict = _require_edict(db, edict_id)
    form_id = _mapping_form_id(edict, kind)
    try:
        validate_mapping_tree(fdb, form_id, version, tree, kind)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    row = db.execute(
        text("INSERT INTO edict_form_mappings "
             "(edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
             "VALUES (:e, CAST(:t AS form_type_enum), CAST(:m AS jsonb), true, :f, :u, :v) "
             "RETURNING id"),
        {
            "e": edict_id, "t": kind, "m": _dump(tree), "f": str(form_id),
            "u": user["id"], "v": version,
        },
    ).mappings().first()
    db.commit()
    return {
        "id": row["id"],
        "edict_id": edict_id,
        "form_type": kind,
        "form_id": str(form_id),
        "user_id": user["id"],
        "is_active": True,
        "mapping": tree,
        "version": version,
    }


def _dump(tree) -> str:
    return json.dumps(tree)


def _list_mappings(db, edict_id, kind):
    _require_edict(db, edict_id)
    rows = db.execute(
        text("SELECT * FROM edict_form_mappings WHERE edict_id = :e "
             "AND form_type = CAST(:t AS form_type_enum) ORDER BY id"),
        {"e": edict_id, "t": kind},
    ).mappings().all()
    return [
        {
            "id": r["id"],
            "edict_id": r["edict_id"],
            "form_type": str(r["form_type"]),
            "form_id": r["form_id"],
            "form_version": r["form_version"],
            "mapping": r["mapping"],
            "is_active": r["is_active"],
            "user_id": r["user_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def _update_mapping(db, fdb, edict_id, version, mapping_id, payload, kind, user):
    _require_edict(db, edict_id)
    row = db.execute(
        text("SELECT id FROM edict_form_mappings WHERE id = :i AND edict_id = :e "
             "AND form_type = CAST(:t AS form_type_enum) AND form_version = :v"),
        {"i": mapping_id, "e": edict_id, "t": kind, "v": version},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    form_id = _mapping_form_id(get_edict(db, edict_id), kind)
    try:
        validate_mapping_tree(fdb, form_id, version, payload, kind)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    db.execute(
        text("UPDATE edict_form_mappings SET mapping = CAST(:m AS jsonb), "
             "is_active = true, user_id = :u WHERE id = :i"),
        {"m": _dump(payload), "u": user["id"], "i": mapping_id},
    )
    db.commit()
    return _mapping_row(db, mapping_id)


def _mapping_row(db, mapping_id):
    r = db.execute(
        text("SELECT * FROM edict_form_mappings WHERE id = :i"), {"i": mapping_id}
    ).mappings().first()
    return {
        "id": r["id"],
        "edict_id": r["edict_id"],
        "form_type": str(r["form_type"]),
        "form_id": r["form_id"],
        "form_version": r["form_version"],
        "mapping": r["mapping"],
        "is_active": r["is_active"],
        "user_id": r["user_id"],
        "created_at": r["created_at"],
    }


def _delete_mapping(db, edict_id, version, mapping_id, kind):
    _require_edict(db, edict_id)
    row = db.execute(
        text("SELECT id FROM edict_form_mappings WHERE id = :i AND edict_id = :e "
             "AND form_type = CAST(:t AS form_type_enum) AND form_version = :v"),
        {"i": mapping_id, "e": edict_id, "t": kind, "v": version},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.execute(
        text("DELETE FROM edict_form_mappings WHERE id = :i"), {"i": mapping_id}
    )
    db.commit()
    return {"message": "Mapping deleted successfully"}


def _unmapped_versions(db, fdb, edict_id, kind):
    edict = _require_edict(db, edict_id)
    form_id = _mapping_form_id(edict, kind)
    versions = set(form_versions(fdb, form_id))
    mapped = {
        r[0] for r in db.execute(
            text("SELECT DISTINCT form_version FROM edict_form_mappings "
                 "WHERE edict_id = :e AND form_type = CAST(:t AS form_type_enum)"),
            {"e": edict_id, "t": kind},
        )
    }
    return sorted(versions - mapped)


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
def create_candidate_mapping(edict_id: int, version: int, tree: dict = Body(...),
                             user=Depends(require_admin), db=Depends(get_db),
                             fdb=Depends(get_forms_db)):
    return _create_mapping(db, fdb, edict_id, version, tree, "candidate", user)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
def create_recommender_mapping(edict_id: int, version: int, tree: dict = Body(...),
                               user=Depends(require_admin), db=Depends(get_db),
                               fdb=Depends(get_forms_db)):
    return _create_mapping(db, fdb, edict_id, version, tree, "recommender", user)


@router.get("/edicts/{edict_id}/candidates/mappings")
def get_candidate_mappings(edict_id: int, user=Depends(require_user), db=Depends(get_db)):
    return _list_mappings(db, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/mappings")
def get_recommender_mappings(edict_id: int, user=Depends(require_user), db=Depends(get_db)):
    return _list_mappings(db, edict_id, "recommender")


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def update_candidate_mapping(edict_id: int, version: int, mapping_id: int,
                             payload: dict = Body(...), user=Depends(require_admin),
                             db=Depends(get_db), fdb=Depends(get_forms_db)):
    return _update_mapping(db, fdb, edict_id, version, mapping_id, payload, "candidate", user)


@router.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def update_recommender_mapping(edict_id: int, version: int, mapping_id: int,
                               payload: dict = Body(...), user=Depends(require_admin),
                               db=Depends(get_db), fdb=Depends(get_forms_db)):
    return _update_mapping(db, fdb, edict_id, version, mapping_id, payload, "recommender", user)


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def delete_candidate_mapping(edict_id: int, version: int, mapping_id: int,
                             user=Depends(require_admin), db=Depends(get_db)):
    return _delete_mapping(db, edict_id, version, mapping_id, "candidate")


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def delete_recommender_mapping(edict_id: int, version: int, mapping_id: int,
                               user=Depends(require_admin), db=Depends(get_db)):
    return _delete_mapping(db, edict_id, version, mapping_id, "recommender")


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
def get_candidates_unmapped_versions(edict_id: int, user=Depends(require_user),
                                     db=Depends(get_db), fdb=Depends(get_forms_db)):
    return _unmapped_versions(db, fdb, edict_id, "candidate")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
def get_recommenders_unmapped_versions(edict_id: int, user=Depends(require_user),
                                       db=Depends(get_db), fdb=Depends(get_forms_db)):
    return _unmapped_versions(db, fdb, edict_id, "recommender")
