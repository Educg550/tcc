import json

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text

from auth import current_user, require_admin
from database import Session
from services import forms_service as forms
from services.submissions_service import get_edict, iso

router = APIRouter(tags=["edicts"])

TYPES = {"candidates": "candidate", "recommenders": "recommender"}


def _mapping_json(row):
    return {
        "id": row["id"],
        "edict_id": row["edict_id"],
        "form_type": row["form_type"],
        "user_id": row["user_id"],
        "form_id": row["form_id"],
        "form_version": row["form_version"],
        "mapping": row["mapping"],
        "is_active": row["is_active"],
        "created_at": iso(row["created_at"]),
    }


def _leaves(node):
    if isinstance(node, dict):
        if "section" in node and "field" in node:
            yield node
        for value in node.values():
            yield from _leaves(value)


def _valid_fields(edict, form_type, version):
    form_id = int(
        edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"]
    )
    sections = forms.select_sections(form_id, version)
    field_ids = set()
    for sec in sections:
        for f in forms.get_fields(sec["id"]):
            field_ids.add(f["id"])
    if not field_ids:
        with forms.FormsSession() as s:
            rows = s.execute(
                text("select id from form_field where form_id = :f"), {"f": form_id}
            ).mappings().all()
        field_ids = {r["id"] for r in rows}
    return field_ids


def _validate_tree(tree, valid_ids):
    for leaf in _leaves(tree):
        if leaf.get("field") not in valid_ids:
            raise HTTPException(status_code=422, detail="Invalid section/field reference in mapping")


def _context(edict_id, tipo, version):
    if tipo not in TYPES:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    form_type = TYPES[tipo]
    edict = get_edict(edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    return form_type, edict


@router.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
):
    form_type, edict = _context(edict_id, tipo, version)
    _validate_tree(payload, _valid_fields(edict, form_type, version))
    with Session() as s:
        existing = s.execute(
            text(
                "select id from edict_form_mappings"
                " where edict_id = :e and form_type = :t and form_version = :v"
            ),
            {"e": edict_id, "t": form_type, "v": version},
        ).mappings().first()
        if existing:
            raise HTTPException(status_code=409, detail="Mapping already exists for this version")
        mapping_id = s.execute(
            text(
                "insert into edict_form_mappings"
                " (edict_id, form_type, mapping, is_active, form_id, user_id, form_version)"
                " values (:e, :t, cast(:m as jsonb), true, :f, :u, :v) returning id"
            ),
            {
                "e": edict_id,
                "t": form_type,
                "m": json.dumps(payload),
                "f": str(
                    edict["candidate_forms"] if form_type == "candidate" else edict["recommenders_forms"]
                ),
                "u": user["id"],
                "v": version,
            },
        ).scalar_one()
        row = s.execute(
            text("select * from edict_form_mappings where id = :i"), {"i": mapping_id}
        ).mappings().first()
        s.commit()
    return _mapping_json(row)


@router.get("/edicts/{edict_id}/{tipo}/mappings")
def get_mappings(edict_id: int, tipo: str, user=Depends(current_user)):
    form_type, _ = _context(edict_id, tipo, 1)
    with Session() as s:
        rows = s.execute(
            text(
                "select * from edict_form_mappings"
                " where edict_id = :e and form_type = :t order by form_version"
            ),
            {"e": edict_id, "t": form_type},
        ).mappings().all()
    return [_mapping_json(r) for r in rows]


@router.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    payload: dict = Body(...),
    user=Depends(require_admin),
):
    form_type, edict = _context(edict_id, tipo, version)
    with Session() as s:
        row = s.execute(
            text(
                "select * from edict_form_mappings"
                " where id = :i and edict_id = :e and form_type = :t and form_version = :v"
            ),
            {"i": mapping_id, "e": edict_id, "t": form_type, "v": version},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Mapping not found")
    _validate_tree(payload, _valid_fields(edict, form_type, version))
    with Session() as s:
        s.execute(
            text("update edict_form_mappings set mapping = cast(:m as jsonb) where id = :i"),
            {"m": json.dumps(payload), "i": mapping_id},
        )
        updated = s.execute(
            text("select * from edict_form_mappings where id = :i"), {"i": mapping_id}
        ).mappings().first()
        s.commit()
    return _mapping_json(updated)


@router.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
):
    form_type, _ = _context(edict_id, tipo, version)
    with Session() as s:
        row = s.execute(
            text(
                "select id from edict_form_mappings"
                " where id = :i and edict_id = :e and form_type = :t and form_version = :v"
            ),
            {"i": mapping_id, "e": edict_id, "t": form_type, "v": version},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Mapping not found")
        s.execute(text("delete from edict_form_mappings where id = :i"), {"i": mapping_id})
        s.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
def get_unmapped_versions(edict_id: int, tipo: str, user=Depends(require_admin)):
    form_type, _ = _context(edict_id, tipo, 1)
    column = "candidate_form_version" if form_type == "candidate" else "recommender_form_version"
    query = text(
        f"select distinct s.{column} from submission s where s.edict_id = :e and not exists ("
        " select 1 from edict_form_mappings m where m.edict_id = s.edict_id"
        " and m.form_type = :t and m.form_version = s."
        + column
        + " and m.is_active) order by 1"
    )
    with Session() as s:
        rows = s.execute(query, {"e": edict_id, "t": form_type}).scalars().all()
    return list(rows)
