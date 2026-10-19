"""Editais, fases, mapeamentos e vagas."""
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text as sql_text

from auth import current_user, require_admin
from db import get_db, get_forms_db
from models import Edict, Mapping, Phase, Slot, Submission, User
import forms_db

router = APIRouter()

PHASE_LABELS = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
# Associação vigente no original (não inverter pelos nomes das variáveis):
PHASE_DATE = {
    "inscricoes": "date_application",
    "homologacao": "date_evaluation",
    "avaliacao": "date_verification",
    "encerrado": "date_closed",
}
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
MAPPING_TYPES = {"candidates", "recommenders"}


def _parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _check_dates(d1, d2, d3, d4):
    ds = [_parse_date(d) for d in (d1, d2, d3, d4)]
    if any(d is None for d in ds):
        raise HTTPException(status_code=422, detail="Missing dates")
    if not (ds[0] < ds[1] < ds[2] < ds[3]):
        raise HTTPException(status_code=422, detail="Dates must be in strict chronological order")


def _get_edict(db, edict_id):
    edict = db.get(Edict, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    return edict


def _edict_payload(db, edict, user):
    phases = db.query(Phase).filter(Phase.edict_id == edict.id).order_by(Phase.date).all()
    slot = db.query(Slot).filter(Slot.edict_id == edict.id, Slot.user_id == user.id).first()
    return {
        "id": edict.id,
        "title": edict.title,
        "description": edict.description,
        "year": edict.year,
        "semester": edict.semester,
        "edict_type": edict.edict_type,
        "is_open": edict.is_open,
        "candidate_form_id": edict.candidate_form_id,
        "recommender_form_id": edict.recommender_form_id,
        "accept_form_id": edict.accept_form_id,
        "date_application": edict.date_application,
        "date_verification": edict.date_verification,
        "date_evaluation": edict.date_evaluation,
        "date_closed": edict.date_closed,
        "current_phase_id": edict.current_phase_id,
        "phases": [
            {"id": p.id, "label": p.label, "date": p.date, "edict_id": p.edict_id}
            for p in phases
        ],
        "slots": slot.amount if slot else "0",
    }


@router.get("/edicts")
def list_edicts(type: str | None = None, is_open: bool | None = None,
                user=Depends(current_user), db=Depends(get_db)):
    q = db.query(Edict)
    if type is not None:
        q = q.filter(Edict.edict_type == type)
    if is_open is not None:
        q = q.filter(Edict.is_open == is_open)
    edicts = q.order_by(Edict.date_closed.desc()).all()
    return [
        {
            "id": e.id, "title": e.title, "year": e.year,
            "semester": e.semester, "edict_type": e.edict_type, "is_open": e.is_open,
        }
        for e in edicts
    ]


@router.post("/edicts")
def create_edict(body: dict = Body(...), user=Depends(require_admin), db=Depends(get_db)):
    _check_dates(body.get("date_application"), body.get("date_verification"),
                 body.get("date_evaluation"), body.get("date_closed"))
    edict = Edict(
        title=body.get("title", ""),
        description=body.get("description", ""),
        year=str(body.get("year", "")),
        semester=str(body.get("semester", "")),
        edict_type=body.get("edict_type", ""),
        is_open=bool(body.get("is_open", True)),
        candidate_form_id=str(body.get("candidate_forms", "") or ""),
        recommender_form_id=str(body.get("recommenders_forms", "") or ""),
        author_id=user.id,
        date_application=_parse_date(body.get("date_application")),
        date_verification=_parse_date(body.get("date_verification")),
        date_evaluation=_parse_date(body.get("date_evaluation")),
        date_closed=_parse_date(body.get("date_closed")),
    )
    db.add(edict)
    db.flush()
    current = None
    for label in PHASE_LABELS:
        phase = Phase(edict_id=edict.id, label=label,
                      date=getattr(edict, PHASE_DATE[label]))
        db.add(phase)
        if label == "inscricoes":
            current = phase
    db.flush()
    edict.current_phase_id = current.id
    db.commit()
    return _edict_payload(db, edict, user)


@router.get("/edicts/{edict_id}")
def get_edict(edict_id: str, user=Depends(current_user), db=Depends(get_db)):
    return _edict_payload(db, _get_edict(db, edict_id), user)


@router.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: str, body: dict = Body(...),
               user=Depends(require_admin), db=Depends(get_db)):
    edict = _get_edict(db, edict_id)
    for key in ("title", "description", "edict_type"):
        if key in body:
            setattr(edict, key, body[key])
    if "year" in body:
        edict.year = str(body["year"])
    if "semester" in body:
        edict.semester = str(body["semester"])
    if "is_open" in body:
        edict.is_open = bool(body["is_open"])
    if all(k in body for k in ("date_application", "date_verification", "date_evaluation", "date_closed")):
        _check_dates(body["date_application"], body["date_verification"],
                     body["date_evaluation"], body["date_closed"])
        for key in ("date_application", "date_verification", "date_evaluation", "date_closed"):
            setattr(edict, key, _parse_date(body[key]))
        for p in db.query(Phase).filter(Phase.edict_id == edict.id).all():
            p.date = getattr(edict, PHASE_DATE[p.label])
    db.commit()
    return _edict_payload(db, edict, user)


@router.post("/edicts/{edict_id}/edit-date")
def edit_date(edict_id: str, body: dict = Body(...),
              user=Depends(require_admin), db=Depends(get_db)):
    edict = _get_edict(db, edict_id)
    new_date = _parse_date(body.get("closed_date"))
    edict.date_closed = new_date
    for p in db.query(Phase).filter(Phase.edict_id == edict.id, Phase.label == "encerrado").all():
        p.date = new_date
    db.commit()
    return {"closed_date": new_date}


@router.post("/edicts/{edict_id}/advance-phase")
def advance_phase(edict_id: str, body: dict = Body(...),
                  user=Depends(require_admin), db=Depends(get_db), fs=Depends(get_forms_db)):
    edict = _get_edict(db, edict_id)
    phase = db.get(Phase, body.get("id"))
    if not phase or phase.edict_id != edict.id:
        raise HTTPException(status_code=404, detail="Phase not found")
    edict.current_phase_id = phase.id
    db.commit()
    # propaga a fase ao formulário de candidatura no Forms
    forms_db.set_form_phase(fs, edict.candidate_form_id, FORMS_PHASE[phase.label])
    return {"id": phase.id, "label": phase.label}


@router.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: str, body: dict = Body(default=None),
                user=Depends(require_admin), db=Depends(get_db)):
    edict = _get_edict(db, edict_id)
    if not edict.is_open:
        raise HTTPException(status_code=409, detail="Edict already closed")
    edict.is_open = False
    db.commit()
    return {"message": "Edict closed successfully"}


@router.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: str, user=Depends(require_admin), db=Depends(get_db)):
    edict = _get_edict(db, edict_id)
    db.delete(edict)
    db.commit()
    return {"message": "Edict removed successfully"}


# ---------------------------------------------------------------- mapeamentos


def _mapping_payload(m):
    return {
        "id": m.id, "edict_id": m.edict_id, "type": m.type,
        "author_id": m.author_id, "version": m.version,
        "tree": m.tree, "active": m.active,
    }


def _leaves(tree):
    if tree is None:
        return []
    if isinstance(tree, dict) and set(tree) == {"section", "field"}:
        return [tree]
    out = []
    for v in tree.values():
        out.extend(_leaves(v))
    return out


def _validate_tree(fs, form_id, tree):
    sections = forms_db.select_sections(fs, form_id, None)
    valid = set()
    for s in sections:
        for f in forms_db.section_fields(fs, s["id"]):
            valid.add((str(s["id"]), str(f["id"])))
    for leaf in _leaves(tree):
        if (str(leaf["section"]), str(leaf["field"])) not in valid:
            raise HTTPException(status_code=422, detail="Invalid section/field reference")


def _mapping_type(tipo):
    if tipo not in MAPPING_TYPES:
        raise HTTPException(status_code=404, detail="Mapping type not found")
    return tipo


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
def create_mapping(edict_id: str, tipo: str, version: str, body: dict = Body(...),
                   user=Depends(require_admin), db=Depends(get_db), fs=Depends(get_forms_db)):
    tipo = _mapping_type(tipo)
    edict = _get_edict(db, edict_id)
    existing = db.query(Mapping).filter(
        Mapping.edict_id == edict_id, Mapping.type == tipo, Mapping.version == str(version)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Mapping already exists")
    form_id = edict.candidate_form_id if tipo == "candidates" else edict.recommender_form_id
    _validate_tree(fs, form_id, body)
    m = Mapping(edict_id=edict_id, type=tipo, version=str(version),
                author_id=user.id, tree=body, active=True)
    db.add(m)
    db.commit()
    return _mapping_payload(m)


@router.get("/edicts/{edict_id}/{tipo}/mappings")
def list_mappings(edict_id: str, tipo: str, user=Depends(current_user), db=Depends(get_db)):
    tipo = _mapping_type(tipo)
    _get_edict(db, edict_id)
    ms = db.query(Mapping).filter(Mapping.edict_id == edict_id, Mapping.type == tipo).all()
    return [_mapping_payload(m) for m in ms]


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def update_mapping(edict_id: str, tipo: str, version: str, mapping_id: str,
                   body: dict = Body(...), user=Depends(require_admin),
                   db=Depends(get_db), fs=Depends(get_forms_db)):
    tipo = _mapping_type(tipo)
    edict = _get_edict(db, edict_id)
    m = db.get(Mapping, mapping_id)
    if not m or m.edict_id != edict_id or m.type != tipo or m.version != str(version):
        raise HTTPException(status_code=404, detail="Mapping not found")
    form_id = edict.candidate_form_id if tipo == "candidates" else edict.recommender_form_id
    _validate_tree(fs, form_id, body)
    m.tree = body
    db.commit()
    return _mapping_payload(m)


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def delete_mapping(edict_id: str, tipo: str, version: str, mapping_id: str,
                    user=Depends(require_admin), db=Depends(get_db)):
    tipo = _mapping_type(tipo)
    m = db.get(Mapping, mapping_id)
    if not m or m.edict_id != edict_id or m.type != tipo or m.version != str(version):
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(m)
    db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
def unmapped_versions(edict_id: str, tipo: str, user=Depends(current_user), db=Depends(get_db)):
    tipo = _mapping_type(tipo)
    _get_edict(db, edict_id)
    subs = db.query(Submission).filter(Submission.edict_id == edict_id).all()
    versions = {s.form_version for s in subs}
    mapped = {
        m.version for m in db.query(Mapping).filter(
            Mapping.edict_id == edict_id, Mapping.type == tipo).all()
    }
    return sorted(v for v in versions if v not in mapped)


# ---------------------------------------------------------------------- vagas

@router.post("/edicts/{edict_id}/slots")
def set_slots(edict_id: str, body: dict = Body(...),
              user=Depends(current_user), db=Depends(get_db)):
    _get_edict(db, edict_id)
    amount = str(body.get("amount", "")).strip()
    if amount == "":
        amount = "0"
    else:
        try:
            value = int(amount)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid amount")
        amount = str(value) if value > 0 else "0"
    slot = db.query(Slot).filter(Slot.edict_id == edict_id, Slot.user_id == user.id).first()
    if slot:
        slot.amount = amount
    else:
        slot = Slot(edict_id=edict_id, user_id=user.id, amount=amount)
        db.add(slot)
    db.commit()
    return {"amount": amount}
