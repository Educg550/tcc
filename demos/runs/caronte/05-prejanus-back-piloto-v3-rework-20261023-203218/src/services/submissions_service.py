import json

from fastapi import HTTPException
from sqlalchemy import text

from src.services.forms_service import (
    choose_mapping,
    date_only,
    extract,
    get_edict,
    get_mappings,
    poscomp_or_none,
    response_row,
    response_values,
    to_bool,
)

BIDDING_KEYS = ["decline", "available", "interested", "agreed", "interested_scholarship"]


def _norm(value) -> str:
    return " ".join(str(value or "").lower().split())


async def get_submission(db, submission_id: int) -> dict | None:
    result = await db.execute(text("SELECT * FROM submission WHERE id = :i"), {"i": submission_id})
    row = result.first()
    return dict(row._mapping) if row else None


async def submission_context(db, fdb, edict: dict, sub: dict):
    values = await response_values(fdb, sub["candidate_form_id"])
    response = await response_row(fdb, sub["candidate_form_id"])
    mappings = await get_mappings(db, edict["id"], "candidate")
    mapping = choose_mapping(mappings, response["form_version"] if response else None)
    data = extract(mapping["mapping"] if mapping else None, values)
    return data, response, values


async def sync_edict(db, fdb, edict: dict) -> None:
    edict_id = edict["id"]
    form_id = int(edict["candidate_forms"])
    rec_form_id = int(edict["recommenders_forms"] or 0)

    result = await fdb.execute(
        text(
            "SELECT id, form_version FROM form_response "
            "WHERE form_id = :f AND submitted_at IS NOT NULL"
        ),
        {"f": form_id},
    )
    responses = [dict(r._mapping) for r in result]
    result = await db.execute(
        text("SELECT id, candidate_form_id FROM submission WHERE edict_id = :e"), {"e": edict_id}
    )
    subs = [dict(r._mapping) for r in result]
    have = {s["candidate_form_id"] for s in subs}

    rec_mappings = await get_mappings(db, edict_id, "recommender")
    rec_version = max((m["form_version"] for m in rec_mappings), default=1)

    for response in responses:
        if response["id"] in have:
            continue
        result = await db.execute(
            text(
                "INSERT INTO submission(edict_id, candidate_form_id, recommender_form_ids, "
                "stats, recommender_form_version, candidate_form_version, created_at, updated_at) "
                "VALUES(:e, :c, CAST('[]' AS json), 'underreview', :rv, :cv, now(), now()) RETURNING id"
            ),
            {
                "e": edict_id,
                "c": response["id"],
                "rv": rec_version,
                "cv": response["form_version"],
            },
        )
        subs.append({"id": result.scalar(), "candidate_form_id": response["id"]})

    if not rec_form_id or not subs:
        return

    cand_mappings = await get_mappings(db, edict_id, "candidate")
    identities: dict[str, int] = {}
    for sub in subs:
        values = await response_values(fdb, sub["candidate_form_id"])
        response = await response_row(fdb, sub["candidate_form_id"])
        mapping = choose_mapping(cand_mappings, response["form_version"] if response else None)
        data = extract(mapping["mapping"] if mapping else None, values)
        name = _norm(data.get("name"))
        email = _norm(data.get("email") or (response["email"] if response else ""))
        if name:
            identities.setdefault(name, sub["id"])
        if email:
            identities.setdefault(email, sub["id"])

    result = await fdb.execute(
        text(
            "SELECT id FROM form_response "
            "WHERE form_id = :f AND submitted_at IS NOT NULL"
        ),
        {"f": rec_form_id},
    )
    for (rec_id,) in result:
        values = await response_values(fdb, rec_id)
        target = None
        for value in values.values():
            key = _norm(value)
            if key in identities:
                target = identities[key]
                break
        if target is None:
            continue
        result = await db.execute(
            text("SELECT recommenders_form_ids FROM submission WHERE id = :i"), {"i": target}
        )
        row = result.first()
        current = list(row[0] or []) if row else []
        if rec_id not in current:
            current.append(rec_id)
            await db.execute(
                text(
                    "UPDATE submission SET recommenders_form_ids = CAST(:j AS json) "
                    "WHERE id = :i"
                ),
                {"j": json.dumps(current), "i": target},
            )


async def is_favorite(db, user_id: int, submission_id: int) -> bool:
    result = await db.execute(
        text(
            "SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s"
        ),
        {"u": user_id, "s": submission_id},
    )
    return result.first() is not None


async def user_labels(db, submission_id: int, user_id: int) -> list[dict]:
    result = await db.execute(
        text(
            "SELECT id, label, color FROM labels "
            "WHERE submission_id = :s AND user_id = :u AND context_type = 'candidate' "
            "ORDER BY id"
        ),
        {"s": submission_id, "u": user_id},
    )
    return [dict(r._mapping) for r in result]


async def bidding_users(db, submission_id: int) -> dict:
    result = await db.execute(
        text(
            "SELECT l.label, u.id, u.name, u.email FROM labels l "
            'JOIN "user" u ON u.id = l.user_id '
            "WHERE l.submission_id = :s AND l.context_type = 'bidding'"
        ),
        {"s": submission_id},
    )
    data = {key: [] for key in BIDDING_KEYS}
    for label, uid, name, email in result:
        if label in data:
            data[label].append({"id": uid, "name": name, "email": email})
    return data


async def accept_info(fdb, sub: dict) -> dict:
    empty = {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if not sub["accept_form_id"]:
        return empty
    result = await fdb.execute(
        text("SELECT submitted_at FROM form_response WHERE id = :i"),
        {"i": sub["accept_form_id"]},
    )
    row = result.first()
    if not row:
        return empty
    result = await fdb.execute(
        text(
            "SELECT f.name, r.value FROM responses r "
            "JOIN form_field f ON f.id = r.field_id WHERE r.response_id = :i"
        ),
        {"i": sub["accept_form_id"]},
    )
    fields = {name: value for name, value in result}
    return {
        "sent": "replied" if row[0] else "sent",
        "accept": fields.get("accept"),
        "comments": fields.get("comments"),
        "submitted_at": row[0],
    }


async def recommenders_info(db, fdb, edict: dict, sub: dict) -> list[dict]:
    mappings = await get_mappings(db, edict["id"], "recommender")
    output = []
    for rec_id in sub["recommenders_form_ids"] or []:
        response = await response_row(fdb, rec_id)
        if not response:
            continue
        values = await response_values(fdb, rec_id)
        mapping = choose_mapping(mappings, response["form_version"])
        data = extract(mapping["mapping"] if mapping else None, values)
        data["sent"] = response["submitted_at"] is not None
        output.append(data)
    return output


async def get_private_note(db, user_id: int, submission_id: int) -> str:
    result = await db.execute(
        text(
            "SELECT note FROM private_note WHERE user_id = :u AND submission_id = :s"
        ),
        {"u": user_id, "s": submission_id},
    )
    row = result.first()
    return row[0] if row else ""


async def build_submission_dict(db, fdb, edict: dict, sub: dict, user: dict) -> dict:
    data, response, _ = await submission_context(db, fdb, edict, sub)
    email = data.get("email") or (response["email"] if response else "") or ""
    advisor = None
    if sub["advisor_id"]:
        result = await db.execute(
            text('SELECT id, name, email FROM "user" WHERE id = :i'), {"i": sub["advisor_id"]}
        )
        row = result.first()
        if row:
            advisor = {"id": row[0], "name": row[1], "email": row[2]}
    return {
        "id": sub["id"],
        "token": response["token"] if response else "",
        "name": data.get("name") or "",
        "email": email,
        "phone_number": data.get("phone_number") or "",
        "nationality": data.get("nationality") or "",
        "personal_website": data.get("personal_website") or "",
        "gender": data.get("gender") or "",
        "advisor": advisor,
        "birth_date": date_only(data.get("birth_date")),
        "graduation": data.get("graduation") or {},
        "poscomp": poscomp_or_none(data),
        "current_occupation": data.get("current_occupation"),
        "research": data.get("research") or {},
        "lattes_curriculum": data.get("lattes_curriculum") or "",
        "stats": sub["stats"],
        "is_favorite": await is_favorite(db, user["id"], sub["id"]),
        "bidding_users": {"data": await bidding_users(db, sub["id"])},
        "labels": await user_labels(db, sub["id"], user["id"]),
        "disabilities": to_bool(data.get("disabilities")),
        "ethnicity_race": to_bool(data.get("ethnicity_race")),
        "accept": await accept_info(fdb, sub),
    }


async def comments_list(db, submission_id: int) -> list[dict]:
    result = await db.execute(
        text(
            "SELECT c.id, c.submission_id, c.comment, c.created_at, c.updated_at, "
            'u.id AS user_id, u.name AS user_name '
            "FROM comment c JOIN \"user\" u ON u.id = c.user_id "
            "WHERE c.submission_id = :s ORDER BY c.id"
        ),
        {"s": submission_id},
    )
    return [
        {
            "id": r["id"],
            "user": {"id": r["user_id"], "name": r["user_name"]},
            "submission_id": r["submission_id"],
            "comment": r["comment"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in result
    ]


async def require_phase(db, submission: dict, phase: str = "avaliacao") -> dict:
    edict = await get_edict(db, submission["edict_id"])
    if not edict or edict["phase"] != phase:
        raise HTTPException(status_code=400, detail=f"Operation only allowed in {phase}")
    return edict
