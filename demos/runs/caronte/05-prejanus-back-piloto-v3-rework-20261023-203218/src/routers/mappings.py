from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from src.auth import get_current_user, require_admin
from src.db import get_db, get_forms_db
from src.services.forms_service import get_edict

router = APIRouter(prefix="/edicts", tags=["edicts"])

ROUTE_TYPE = {"candidates": "candidate", "recommenders": "recommender"}
FORM_COLUMN = {"candidate": "candidate_forms", "recommender": "recommenders_forms"}


def _mapping_row(row: dict) -> dict:
    result = dict(row)
    result["version"] = result["form_version"]
    return result


def _leaves(node: dict) -> list[tuple]:
    leaves = []
    for value in node.values():
        if value is None:
            continue
        if isinstance(value, dict) and set(value) == {"section", "field"}:
            leaves.append((value["section"], value["field"]))
        elif isinstance(value, dict):
            leaves.extend(_leaves(value))
        else:
            raise HTTPException(status_code=422, detail="Invalid mapping node")
    return leaves


async def _edict_and_form(db, edict_id: int, form_type: str):
    edict = await get_edict(db, edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edict not found")
    form_id = int(edict[FORM_COLUMN[form_type]])
    return edict, form_id


async def _validate_mapping(fdb, form_id: int, version: int, payload: dict) -> None:
    result = await fdb.execute(
        text("SELECT id FROM form_section WHERE form_id = :f AND version = :v"),
        {"f": form_id, "v": version},
    )
    sections = [r[0] for r in result]
    if not sections:
        return
    result = await fdb.execute(
        text("SELECT section_id, id FROM form_field WHERE section_id = ANY(:s)"),
        {"s": sections},
    )
    valid = {(r[0], r[1]) for r in result}
    for leaf in _leaves(payload):
        if leaf not in valid:
            raise HTTPException(status_code=422, detail="Invalid mapping reference")


@router.post("/{edict_id}/{rota}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    rota: str,
    version: int,
    payload: dict,
    user=Depends(require_admin),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    if rota not in ROUTE_TYPE:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    form_type = ROUTE_TYPE[rota]
    edict, form_id = await _edict_and_form(db, edict_id, form_type)
    await _validate_mapping(fdb, form_id, version, payload)
    result = await db.execute(
        text("SELECT id FROM edict_form_mappings WHERE edict_id = :e AND form_type = :t "
             "AND form_version = :v"),
        {"e": edict_id, "t": form_type, "v": version},
    )
    if result.first():
        raise HTTPException(status_code=400, detail="Mapping version already exists")
    result = await db.execute(
        text(
            "INSERT INTO edict_form_mappings(edict_id, form_type, mapping, is_active, "
            "created_at, form_id, user_id, form_version) "
            "VALUES(:e, :t, CAST(:m AS jsonb), true, now(), :f, :u, :v) RETURNING *"
        ),
        {
            "e": edict_id,
            "t": form_type,
            "m": _dump(payload),
            "f": str(form_id),
            "u": user["id"],
            "v": version,
        },
    )
    await db.commit()
    return _mapping_row(dict(result.first()._mapping))


@router.get("/{edict_id}/{rota}/mappings")
async def get_mappings_route(
    edict_id: int,
    rota: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if rota not in ROUTE_TYPE:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    result = await db.execute(
        text(
            "SELECT * FROM edict_form_mappings WHERE edict_id = :e AND form_type = :t ORDER BY id"
        ),
        {"e": edict_id, "t": ROUTE_TYPE[rota]},
    )
    return [_mapping_row(dict(r._mapping)) for r in result]


@router.put("/{edict_id}/{rota}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    rota: str,
    version: int,
    mapping_id: int,
    payload: dict,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    if rota not in ROUTE_TYPE:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    result = await db.execute(
        text(
            "UPDATE edict_form_mappings SET mapping = CAST(:m AS jsonb) "
            "WHERE id = :i AND edict_id = :e AND form_type = :t AND form_version = :v RETURNING *"
        ),
        {"m": _dump(payload), "i": mapping_id, "e": edict_id, "t": ROUTE_TYPE[rota], "v": version},
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Mapping not found")
    await db.commit()
    return _mapping_row(dict(row._mapping))


@router.delete("/{edict_id}/{rota}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    rota: str,
    version: int,
    mapping_id: int,
    user=Depends(require_admin),
    db=Depends(get_db),
):
    if rota not in ROUTE_TYPE:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    result = await db.execute(
        text(
            "DELETE FROM edict_form_mappings WHERE id = :i AND edict_id = :e "
            "AND form_type = :t AND form_version = :v RETURNING id"
        ),
        {"i": mapping_id, "e": edict_id, "t": ROUTE_TYPE[rota], "v": version},
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Mapping not found")
    await db.commit()
    return {"message": "Mapping deleted successfully"}


@router.get("/{edict_id}/{rota}/forms/versions/unmapped")
async def get_unmapped_versions(
    edict_id: int,
    rota: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
    fdb=Depends(get_forms_db),
):
    if rota not in ROUTE_TYPE:
        raise HTTPException(status_code=404, detail="Unknown mapping type")
    form_type = ROUTE_TYPE[rota]
    _, form_id = await _edict_and_form(db, edict_id, form_type)
    result = await fdb.execute(
        text("SELECT DISTINCT version FROM form_section WHERE form_id = :f"),
        {"f": form_id},
    )
    versions = {r[0] for r in result}
    result = await db.execute(
        text(
            "SELECT DISTINCT form_version FROM edict_form_mappings "
            "WHERE edict_id = :e AND form_type = :t"
        ),
        {"e": edict_id, "t": form_type},
    )
    mapped = {r[0] for r in result}
    return sorted(versions - mapped)


def _dump(payload: dict) -> str:
    import json

    return json.dumps(payload)
