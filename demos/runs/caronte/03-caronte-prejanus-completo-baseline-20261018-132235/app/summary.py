"""Shared logic to summarize submissions from Forms answers and mappings."""
from datetime import datetime

from sqlalchemy import select

from . import formsdb
from .models import (
    Bidding,
    Edict,
    Favorite,
    Label,
    Slot,
    Submission,
    SubmissionAdvisor,
    User,
)


def flatten_tree(tree: dict, prefix: str = "") -> dict[str, dict | None]:
    """Flatten a mapping tree into {dotted.path: leaf-or-None}."""
    flat: dict[str, dict | None] = {}
    if not isinstance(tree, dict):
        return flat
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if (
            isinstance(value, dict)
            and "section" in value
            and "field" in value
            and len(value) == 2
        ):
            flat[path] = value
        elif value is None:
            flat[path] = None
        elif isinstance(value, dict):
            flat.update(flatten_tree(value, path))
        else:
            flat[path] = None
    return flat


def find_leaf(flat: dict, *names: str) -> dict | None:
    """Find a mapping leaf whose path ends with any of the given names."""
    lowered = [n.lower() for n in names]
    for path, leaf in flat.items():
        tail = path.lower().split(".")[-1]
        if leaf is not None and tail in lowered:
            return leaf
    return None


def mapping_tree(db, edict_id: int, form_type: str, version: int) -> dict:
    from .models import FormMapping

    mapping = (
        db.query(FormMapping)
        .filter(
            FormMapping.edict_id == edict_id,
            FormMapping.form_type == form_type,
            FormMapping.version == version,
            FormMapping.active.is_(True),
        )
        .first()
    )
    return mapping.tree if mapping else {}


def candidate_answer(edict: Edict, sub: Submission) -> dict | None:
    """The Forms answer of a candidate submission."""
    answer = formsdb.get_answer_by_token(sub.token)
    if answer is None:
        answers = formsdb.get_answers(
            int(edict.candidate_form_id), email=sub.email, version=sub.version
        )
        answer = answers[0] if answers else None
    return answer


def answer_values(answer: dict | None) -> dict[tuple[int, int], str]:
    if not answer:
        return {}
    return formsdb.get_answer_values(answer.get("id"))


def _value(values: dict, leaf: dict | None) -> object:
    if leaf is None:
        return None
    return values.get((leaf.get("section"), leaf.get("field")))


def _mapped(flat: dict, values: dict, *names) -> object:
    return _value(values, find_leaf(flat, *names))


def _as_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _as_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "yes", "1", "sim")


def _as_int(value, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _as_date(value):
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def advisor_user(db, submission_id: int) -> User | None:
    advisor_id = db.execute(
        select(SubmissionAdvisor.user_id).where(
            SubmissionAdvisor.submission_id == submission_id
        )
    ).scalar_one_or_none()
    if advisor_id is None:
        return None
    return db.get(User, advisor_id)


def accept_status(db, edict: Edict, sub: Submission) -> dict:
    """Accept invitation status: not_sent, sent or replied."""
    if sub.accept_form_id is None:
        return {"sent": "not_sent", "accept": None, "comments": None,
                "submitted_at": None}
    answer = formsdb.get_answer(sub.accept_form_id)
    values = formsdb.answer_values(sub.accept_form_id)
    submitted = answer is not None and (
        answer.get("current_state") in ("completed", "finalized")
        or answer.get("submitted_at") is not None
    )
    if not submitted:
        return {"sent": "sent", "accept": None, "comments": None,
                "submitted_at": None}
    accept = None
    comments = None
    if answer:
        for field_id, value in values.items():
            text = _as_str(value).lower()
            if "accept" in text or "aceit" in text or value in ("yes", "sim"):
                accept = _as_str(value)
            if "comment" in text or "observ" in text:
                comments = _as_str(value)
    return {
        "sent": "replied",
        "accept": accept,
        "comments": comments,
        "submitted_at": answer.get("submitted_at") if answer else None,
    }


def bidding_users(db, edict_id: int, submission_id: int) -> dict:
    """Biddings of a submission grouped by bidding value."""
    rows = (
        db.query(Bidding, User)
        .join(User, Bidding.user_id == User.id)
        .filter(Bidding.submission_id == submission_id)
        .all()
    )
    data: dict[str, list[dict]] = {}
    for bidding, user in rows:
        slot = (
            db.query(Slot)
            .filter(Slot.edict_id == edict_id, Slot.user_id == user.id)
            .first()
        )
        data.setdefault(bidding.bidding or "", []).append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "slots": slot.amount if slot else "0",
            }
        )
    return {"data": data}


def submission_labels(db, user_id: int, submission_id: int) -> list[dict]:
    labels = (
        db.query(Label)
        .filter(Label.user_id == user_id, Label.submission_id == submission_id)
        .order_by(Label.id)
        .all()
    )
    return [{"id": l.id, "label": l.label, "color": l.color} for l in labels]


def is_favorite(db, user_id: int, submission_id: int) -> bool:
    return (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id,
                Favorite.submission_id == submission_id)
        .first()
        is not None
    )


def build_item(db, edict: Edict, sub: Submission, user: User) -> dict:
    """A submission list item, as of the original SubmissionSchema."""
    answer = candidate_answer(edict, sub)
    values = answer_values(answer)
    tree = mapping_tree(db, edict.id, "candidates", sub.version)
    flat = flatten_tree(tree)

    advisor = advisor_user(db, sub.id)
    graduation = {
        "country": _as_str(_mapped(flat, values, "country")),
        "course": _as_str(_mapped(flat, values, "course")),
        "institution": _as_str(_mapped(flat, values, "institution")),
        "year": _as_int(_mapped(flat, values, "graduation_year", "year")),
    }
    poscomp_leaf = find_leaf(flat, "score", "poscomp_score")
    poscomp = None
    if poscomp_leaf is not None:
        poscomp = {
            "year": _as_int(_mapped(flat, values, "poscomp_year")),
            "score": _as_str(_mapped(flat, values, "score", "poscomp_score")),
        }
    research = {
        "program": _as_str(_mapped(flat, values, "program")),
        "semester": _as_str(_mapped(flat, values, "research_semester")),
        "field": {
            "primary": _as_str(_mapped(flat, values, "primary", "primary_field")),
            "secondary": _as_str(
                _mapped(flat, values, "secondary", "secondary_field")
            ),
        },
        "will_apply_scholarship": _as_bool(
            _mapped(flat, values, "will_apply_scholarship", "scholarship")
        ),
        "dedication_level": _as_str(_mapped(flat, values, "dedication_level")),
    }

    return {
        "id": sub.id,
        "token": sub.token,
        "name": sub.name,
        "email": sub.email,
        "phone_number": _as_str(_mapped(flat, values, "phone_number", "phone")),
        "nationality": _as_str(_mapped(flat, values, "nationality")),
        "personal_website": _as_str(_mapped(flat, values, "personal_website")),
        "gender": _as_str(_mapped(flat, values, "gender")),
        "advisor": (
            {"id": advisor.id, "name": advisor.name, "email": advisor.email}
            if advisor
            else None
        ),
        "birth_date": _as_date(_mapped(flat, values, "birth_date", "birth")),
        "graduation": graduation,
        "poscomp": poscomp,
        "current_occupation": _as_str(
            _mapped(flat, values, "current_occupation", "occupation")
        ) or None,
        "research": research,
        "lattes_curriculum": _as_str(_mapped(flat, values, "lattes", "lattes_url")),
        "stats": sub.stats,
        "is_favorite": is_favorite(db, user.id, sub.id),
        "bidding_users": bidding_users(db, edict.id, sub.id),
        "labels": submission_labels(db, user.id, sub.id),
        "disabilities": _as_bool(_mapped(flat, values, "disabilities")),
        "ethnicity_race": _as_bool(_mapped(flat, values, "ethnicity_race", "ethnicity")),
        "accept": accept_status(db, edict, sub),
    }


def recommendations(edict: Edict, sub: Submission) -> list[dict]:
    """Recommendation answers associated with a candidate submission."""
    answers = formsdb.get_answers(int(edict.recommender_form_id))
    result = []
    for answer in answers:
        values = formsdb.answer_values(answer.get("id"))
        if not values:
            continue
        texts = [str(v) for v in values.values()]
        if sub.email in texts or (sub.name and sub.name in texts):
            result.append(
                {
                    "email": answer.get("email"),
                    "submitted_at": answer.get("submitted_at"),
                    "values": values,
                }
            )
    return result