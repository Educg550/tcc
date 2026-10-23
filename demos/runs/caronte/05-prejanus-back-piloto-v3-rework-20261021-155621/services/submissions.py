"""Sincronização Forms -> PreJanus e construção das candidaturas."""
import json

from sqlalchemy import text

from services import forms_service

BID_KEYS = ["decline", "available", "interested", "agreed", "interested_scholarship"]

FALSE_WORDS = {"", "false", "no", "nao", "não", "0", "nenhum", "nenhuma", "nada"}


def to_int(v):
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def to_bool(v) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() not in FALSE_WORDS


def is_leaf(v) -> bool:
    return isinstance(v, dict) and set(v.keys()) == {"section", "field"}


def apply_mapping(tree: dict, values: dict[int, str]) -> dict:
    result: dict = {}

    def walk(node, target):
        for key, val in node.items():
            if val is None:
                continue
            if is_leaf(val):
                target[key] = values.get(val["field"])
            elif isinstance(val, dict):
                walk(val, target.setdefault(key, {}))
            else:
                target[key] = val

    walk(tree, result)
    return result


def build_candidate_data(mapped: dict) -> dict:
    grad = mapped.get("graduation") or {}
    research = mapped.get("research") or {}
    field = research.get("field") or {}
    poscomp = mapped.get("poscomp") or None
    return {
        "name": mapped.get("name"),
        "email": mapped.get("email"),
        "phone_number": mapped.get("phone_number"),
        "nationality": mapped.get("nationality"),
        "personal_website": mapped.get("personal_website"),
        "gender": mapped.get("gender"),
        "birth_date": mapped.get("birth_date"),
        "graduation": {
            "country": grad.get("country"),
            "course": grad.get("course"),
            "institution": grad.get("institution"),
            "year": to_int(grad.get("year")),
        },
        "poscomp": (
            {"year": to_int(poscomp.get("year")), "score": str(poscomp.get("score"))}
            if poscomp
            else None
        ),
        "current_occupation": mapped.get("current_occupation"),
        "research": {
            "program": research.get("program"),
            "semester": research.get("semester"),
            "field": {"primary": field.get("primary"), "secondary": field.get("secondary")},
            "will_apply_scholarship": to_bool(research.get("will_apply_scholarship")),
            "dedication_level": research.get("dedication_level"),
        },
        "lattes_curriculum": mapped.get("lattes_curriculum"),
        "disabilities": to_bool(mapped.get("disabilities")),
        "ethnicity_race": to_bool(mapped.get("ethnicity_race")),
    }


def _collect_strings(obj, out: set):
    if isinstance(obj, str):
        out.add(obj)
    elif isinstance(obj, list):
        for item in obj:
            _collect_strings(item, out)
    elif isinstance(obj, dict):
        for value in obj.values():
            _collect_strings(value, out)


def response_identifiers(resp: dict, values: dict[int, str]) -> set:
    ids = {resp["token"], str(resp["id"])}
    if resp.get("email"):
        ids.add(resp["email"])
    for v in values.values():
        if v:
            ids.add(v)
    _collect_strings(resp.get("metadata") or {}, ids)
    ids.discard("")
    return ids


async def get_submission_row(db, submission_id: int) -> dict | None:
    row = (
        await db.execute(
            text(
                "SELECT id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, "
                "recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, "
                "recommender_form_version, candidate_form_version FROM submission WHERE id = :i"
            ),
            {"i": submission_id},
        )
    ).mappings().first()
    return dict(row) if row else None


async def find_or_create_submission(db, edict_id: int, resp: dict) -> dict:
    row = (
        await db.execute(
            text(
                "SELECT id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, "
                "recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, "
                "recommender_form_version, candidate_form_version FROM submission "
                "WHERE edict_id = :e AND candidate_form_id = :c"
            ),
            {"e": edict_id, "c": resp["id"]},
        )
    ).mappings().first()
    if row:
        return dict(row)
    row = (
        await db.execute(
            text(
                "INSERT INTO submission(edict_id, created_at, updated_at, candidate_form_id, "
                "recommenders_form_ids, stats, recommender_form_version, candidate_form_version) "
                "VALUES (:e, now(), now(), :c, '[]'::json, 'underreview', :rv, :cv) "
                "RETURNING id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, "
                "recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, "
                "recommender_form_version, candidate_form_version"
            ),
            {"e": edict_id, "c": resp["id"], "rv": resp["form_version"], "cv": resp["form_version"]},
        )
    ).mappings().first()
    return dict(row)


async def sync_edict_submissions(db, fdb, edict: dict) -> list[dict]:
    """Cria/atualiza as inscrições do edital a partir das respostas do Forms.

    Retorna lista de {'submission', 'response', 'values', 'data'}.
    """
    cand_form = to_int(edict.get("candidate_forms"))
    rec_form = to_int(edict.get("recommenders_forms"))
    cand_mappings = await forms_service.fetch_mappings(db, edict["id"], "candidate")
    rec_mappings = (
        await forms_service.fetch_mappings(db, edict["id"], "recommender") if rec_form else []
    )
    responses = await forms_service.get_responses_for_form(fdb, cand_form) if cand_form else []
    values_map = await forms_service.get_values_for_responses(fdb, [r["id"] for r in responses])
    recs = await forms_service.get_responses_for_form(fdb, rec_form) if rec_form else []
    rec_values = await forms_service.get_values_for_responses(fdb, [r["id"] for r in recs])
    rec_identifiers = {
        r["id"]: response_identifiers(r, rec_values.get(r["id"], {})) for r in recs
    }

    synced = []
    for resp in responses:
        values = values_map.get(resp["id"], {})
        mapping = forms_service.choose_mapping(cand_mappings, resp["form_version"])
        mapped = apply_mapping(mapping["mapping"], values) if mapping else {}
        data = build_candidate_data(mapped)
        sub = await find_or_create_submission(db, edict["id"], resp)
        cand_ids = {resp["token"], str(resp["id"])}
        for v in (data["name"], data["email"]):
            if v:
                cand_ids.add(v)
        rec_ids = [rid for rid, ids in rec_identifiers.items() if ids & cand_ids]
        if (sub["recommenders_form_ids"] or []) != rec_ids:
            await db.execute(
                text("UPDATE submission SET recommenders_form_ids = :r, updated_at = now() WHERE id = :i"),
                {"r": json.dumps(rec_ids), "i": sub["id"]},
            )
            sub["recommenders_form_ids"] = rec_ids
        synced.append({"submission": sub, "response": resp, "values": values, "data": data})
    await db.commit()
    return synced


async def build_accept(fdb, sub: dict) -> dict:
    if not sub.get("accept_form_id"):
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms_service.get_response(fdb, sub["accept_form_id"])
    if not resp:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    vals = await forms_service.get_values_by_field_name(fdb, resp["id"])
    return {
        "sent": "replied" if resp["submitted_at"] else "sent",
        "accept": vals.get("accept"),
        "comments": vals.get("comments"),
        "submitted_at": resp["submitted_at"],
    }


async def build_listing_item(db, fdb, edict: dict, entry: dict, user_id: int | None) -> dict:
    sub, resp, data = entry["submission"], entry["response"], entry["data"]
    is_favorite = False
    if user_id is not None:
        is_favorite = (
            await db.execute(
                text("SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s"),
                {"u": user_id, "s": sub["id"]},
            )
        ).first() is not None
    labels = []
    if user_id is not None:
        rows = (
            await db.execute(
                text(
                    "SELECT id, label, color FROM labels "
                    "WHERE user_id = :u AND submission_id = :s AND context_type = 'candidate' "
                    "ORDER BY id"
                ),
                {"u": user_id, "s": sub["id"]},
            )
        ).mappings().all()
        labels = [dict(r) for r in rows]
    bidding_rows = (
        await db.execute(
            text(
                'SELECT l.label, u.id, u.name, u.email, sl.slots FROM labels l '
                'JOIN "user" u ON u.id = l.user_id '
                "LEFT JOIN user_edict_slots sl ON sl.user_id = u.id AND sl.edict_id = :e "
                "WHERE l.submission_id = :s AND l.context_type = 'bidding' ORDER BY l.id"
            ),
            {"e": edict["id"], "s": sub["id"]},
        )
    ).mappings().all()
    bidding_data = {k: [] for k in BID_KEYS}
    for b in bidding_rows:
        bidding_data.setdefault(b["label"], []).append(
            {
                "id": b["id"],
                "name": b["name"],
                "email": b["email"],
                "slots": str(b["slots"]) if b["slots"] is not None else None,
            }
        )
    advisor = None
    if sub.get("advisor_id"):
        arow = (
            await db.execute(
                text('SELECT id, name, email FROM "user" WHERE id = :i'), {"i": sub["advisor_id"]}
            )
        ).mappings().first()
        if arow:
            advisor = dict(arow)
    accept = await build_accept(fdb, sub)
    return {
        "id": sub["id"],
        "token": resp["token"],
        "name": data["name"],
        "email": data["email"],
        "phone_number": data["phone_number"],
        "nationality": data["nationality"],
        "personal_website": data["personal_website"],
        "gender": data["gender"],
        "advisor": advisor,
        "birth_date": data["birth_date"],
        "graduation": data["graduation"],
        "poscomp": data["poscomp"],
        "current_occupation": data["current_occupation"],
        "research": data["research"],
        "lattes_curriculum": data["lattes_curriculum"],
        "stats": sub["stats"],
        "is_favorite": is_favorite,
        "bidding_users": {"data": bidding_data},
        "labels": labels,
        "disabilities": data["disabilities"],
        "ethnicity_race": data["ethnicity_race"],
        "accept": accept,
    }


async def get_candidate_data(db, fdb, sub: dict, edict: dict) -> tuple[dict | None, dict, dict]:
    """Resposta, valores e dados mapeados da candidatura."""
    resp = await forms_service.get_response(fdb, sub["candidate_form_id"])
    if not resp:
        return None, {}, build_candidate_data({})
    values = await forms_service.get_response_values(fdb, resp["id"])
    mappings = await forms_service.fetch_mappings(db, edict["id"], "candidate")
    mapping = forms_service.choose_mapping(mappings, resp["form_version"])
    mapped = apply_mapping(mapping["mapping"], values) if mapping else {}
    return resp, values, build_candidate_data(mapped)


async def build_recommenders(db, fdb, sub: dict, edict: dict) -> list[dict]:
    mappings = await forms_service.fetch_mappings(db, edict["id"], "recommender")
    out = []
    for rid in sub.get("recommenders_form_ids") or []:
        resp = await forms_service.get_response(fdb, rid)
        if not resp:
            continue
        values = await forms_service.get_response_values(fdb, rid)
        mapping = forms_service.choose_mapping(mappings, resp["form_version"])
        mapped = apply_mapping(mapping["mapping"], values) if mapping else {}
        sent = bool(resp["submitted_at"]) or bool((resp.get("metadata") or {}).get("sent"))
        out.append(
            {
                "fullname": mapped.get("fullname"),
                "rating": mapped.get("rating"),
                "affiliation": mapped.get("affiliation"),
                "sent": sent,
            }
        )
    return out


async def build_detail(db, fdb, sub: dict, edict: dict, user_id: int | None) -> dict:
    resp, values, data = await get_candidate_data(db, fdb, sub, edict)
    private_note = ""
    labels = []
    if user_id is not None:
        note = (
            await db.execute(
                text("SELECT note FROM private_note WHERE user_id = :u AND submission_id = :s"),
                {"u": user_id, "s": sub["id"]},
            )
        ).scalar()
        private_note = note or ""
        rows = (
            await db.execute(
                text(
                    "SELECT id, label, color FROM labels "
                    "WHERE user_id = :u AND submission_id = :s AND context_type = 'candidate' "
                    "ORDER BY id"
                ),
                {"u": user_id, "s": sub["id"]},
            )
        ).mappings().all()
        labels = [dict(r) for r in rows]
    recommenders = await build_recommenders(db, fdb, sub, edict)
    accept = await build_accept(fdb, sub)
    summary = {
        "id": sub["id"],
        "name": data["name"],
        "email": data["email"],
        "stats": sub["stats"],
        "letter_sent": sub["letter_sent"],
        "private_note": private_note,
        "graduation": data["graduation"],
        "research": data["research"],
        "entry_semester": sub["entry_semester"],
        "poscomp": data["poscomp"],
        "recommenders": recommenders,
        "labels": labels,
        "accept": accept,
    }
    submission_form = []
    if resp:
        sections = await forms_service.get_sections(fdb, resp["form_id"], resp["form_version"])
        for section in sections:
            fields = await forms_service.get_fields_for_section(fdb, section["id"])
            for f in fields:
                f["value"] = values.get(f["id"])
            section["fields"] = fields
            submission_form.append(section)
    return {"summary": summary, "submission_form": submission_form}
