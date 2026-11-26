from __future__ import annotations

import unicodedata
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import forms_db
from database import FormsSessionLocal
from models import Edict, Favorite, Label, Submission, User, UserEdictSlot


def _norm(s) -> str:
    if not isinstance(s, str):
        s = str(s or "")
    return (
        unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    )


def _find(details: list[dict], *words, exclude=()) -> str | None:
    for d in details:
        t = _norm(d.get("name")) + " " + _norm(d.get("label"))
        if all(w in t for w in words) and not any(x in t for x in exclude):
            v = d.get("value")
            if v is not None and v != "":
                return v
    return None


def _find_bool(details: list[dict], *words) -> bool:
    v = _find(details, *words)
    if v is None:
        return False
    return _norm(v) not in ("", "nao", "no", "false", "0", "nenhuma", "nenhum")


def _int(v) -> int:
    try:
        return int(str(v).strip()[:4])
    except (ValueError, TypeError):
        return 0


def extract_summary(details: list[dict], email: str) -> dict:
    name = _find(details, "nome", exclude=["mae", "pai", "curso", "institu", "recomend", "orientador", "social"])
    return {
        "name": name or "",
        "email": email,
        "phone_number": _find(details, "telefone", "celular") or _find(details, "phone") or "",
        "nationality": _find(details, "nacionalidade") or "",
        "personal_website": _find(details, "website") or _find(details, "site") or "",
        "gender": _find(details, "genero") or _find(details, "sexo") or "",
        "birth_date": _find(details, "nascimento") or "",
        "graduation": {
            "country": _find(details, "pais") or "",
            "course": _find(details, "curso", exclude=["poscomp"]) or "",
            "institution": _find(details, "institu") or "",
            "year": _int(_find(details, "ano", exclude=["poscomp", "nascimento", "ingresso"]) or 0),
        },
        "poscomp": (
            {
                "year": _int(_find(details, "poscomp", "ano") or 0),
                "score": _find(details, "poscomp", "pontu") or _find(details, "poscomp", "nota") or "",
            }
            if _find(details, "poscomp")
            else None
        ),
        "current_occupation": _find(details, "ocupacao") or _find(details, "atualmente") or "",
        "research": {
            "program": _find(details, "programa") or "",
            "semester": _find(details, "semestre") or "",
            "field": {
                "primary": _find(details, "area", exclude=["secund"]) or "",
                "secondary": _find(details, "secund") or "",
            },
            "will_apply_scholarship": _find_bool(details, "bolsa"),
            "dedication_level": _find(details, "dedicacao") or _find(details, "regime") or "",
        },
        "lattes_curriculum": _find(details, "lattes") or "",
        "disabilities": _find_bool(details, "deficien"),
        "ethnicity_race": _find_bool(details, "etnic") or _find_bool(details, "raca"),
    }


async def sync_edict_submissions(db: AsyncSession, edict: Edict) -> None:
    """Cria inscrições locais para candidaturas finalizadas no Forms ainda não registradas."""
    try:
        candidate_form_id = int(edict.candidate_forms)
    except (TypeError, ValueError):
        return
    async with FormsSessionLocal() as fdb:
        responses = await forms_db.get_responses(fdb, candidate_form_id)
        by_response = {}
        for r in responses:
            by_response[r["id"]] = r
        existing = (
            await db.execute(
                select(Submission).where(
                    Submission.edict_id == edict.id,
                    Submission.candidate_form_id.in_([r["id"] for r in responses])
                    if responses
                    else Submission.candidate_form_id < 0,
                )
            )
        ).scalars().all()
        seen = {s.candidate_form_id for s in existing}
        new_subs = []
        for r in responses:
            if r["id"] in seen:
                continue
            s = Submission(
                edict_id=edict.id,
                candidate_form_id=r["id"],
                candidate_form_version=r["form_version"] or 1,
                recommender_form_version=1,
                stats="underreview",
                created_at=datetime.now(timezone.utc),
            )
            db.add(s)
            new_subs.append((s, r))
        await db.flush()

        # associa recomendações às inscrições pelos dados do candidato
        try:
            recommender_form_id = int(edict.recommenders_forms)
        except (TypeError, ValueError):
            recommender_form_id = None
        if recommender_form_id:
            email_to_sub = {}
            for s, r in new_subs:
                if r.get("email"):
                    email_to_sub[r["email"].strip().lower()] = s
            for s in existing:
                resp = by_response.get(s.candidate_form_id)
                if resp and resp.get("email"):
                    email_to_sub[resp["email"].strip().lower()] = s
            recs = await forms_db.get_responses(fdb, recommender_form_id)
            for rec in recs:
                details = await forms_db.get_response_details(fdb, rec["id"])
                target = None
                for d in details:
                    v = (d.get("value") or "").strip().lower()
                    if "@" in v and v in email_to_sub:
                        target = email_to_sub[v]
                        break
                if target is None:
                    continue
                ids = set(target.recommenders_form_ids or [])
                if rec["id"] not in ids:
                    ids.add(rec["id"])
                    target.recommenders_form_ids = sorted(ids)
    await db.commit()


async def get_user_labels(db: AsyncSession, user_id: int, submission_id: int) -> list[dict]:
    rows = (
        await db.execute(
            select(Label).where(
                Label.user_id == user_id,
                Label.submission_id == submission_id,
                Label.context_type == "candidate",
            )
        )
    ).scalars().all()
    return [{"id": l.id, "label": l.label, "color": l.color} for l in rows]


async def get_bidding_users(db: AsyncSession, edict_id: int, submission_id: int) -> dict:
    rows = (
        await db.execute(
            select(Label).where(
                Label.submission_id == submission_id, Label.context_type == "bidding"
            )
        )
    ).scalars().all()
    data: dict[str, list[dict]] = {}
    for l in rows:
        user = await db.get(User, l.user_id)
        if user is None:
            continue
        slot = (
            await db.execute(
                select(UserEdictSlot).where(
                    UserEdictSlot.user_id == l.user_id,
                    UserEdictSlot.edict_id == edict_id,
                )
            )
        ).scalar_one_or_none()
        data.setdefault(l.label, []).append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "slots": str(slot.slots) if slot and slot.slots is not None else "0",
            }
        )
    return data


async def accept_info(fdb: AsyncSession, sub: Submission) -> dict:
    if not sub.accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms_db.get_response(fdb, sub.accept_form_id)
    if resp is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    if not resp.get("submitted_at"):
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    details = await forms_db.get_response_details(fdb, sub.accept_form_id)
    accept_val = (
        _find(details, "aceit")
        or _find(details, "decision")
        or _find(details, "sim")
        or ""
    )
    comments = _find(details, "observa") or _find(details, "comment") or ""
    return {
        "sent": "replied",
        "accept": accept_val,
        "comments": comments,
        "submitted_at": resp["submitted_at"].isoformat() if resp.get("submitted_at") else None,
    }


async def user_bidding(db: AsyncSession, user_id: int, submission_id: int) -> str:
    rows = (
        await db.execute(
            select(Label).where(
                Label.user_id == user_id,
                Label.submission_id == submission_id,
                Label.context_type == "bidding",
            )
        )
    ).scalars().all()
    return rows[-1].label if rows else ""


async def submission_payload(
    db: AsyncSession, fdb: AsyncSession, edict: Edict, sub: Submission, user: User
) -> dict:
    resp = await forms_db.get_response(fdb, sub.candidate_form_id)
    details = await forms_db.get_response_details(fdb, sub.candidate_form_id)
    email = (resp or {}).get("email") or ""
    summary = extract_summary(details, email)
    fav = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id, Favorite.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    accept = await accept_info(fdb, sub)
    payload = {
        **summary,
        "id": sub.id,
        "token": str((resp or {}).get("token") or ""),
        "stats": sub.stats,
        "is_favorite": fav is not None,
        "advisor": (
            {"id": advisor.id, "name": advisor.name, "email": advisor.email}
            if advisor
            else None
        ),
        "bidding_users": {"data": await get_bidding_users(db, edict.id, sub.id)},
        "labels": await get_user_labels(db, user.id, sub.id),
        "accept": accept,
    }
    return payload


async def build_submission_form(
    fdb: AsyncSession, form_id: int, version: int, response_id: int
) -> list[dict]:
    try:
        form_id = int(form_id)
    except (TypeError, ValueError):
        return []
    sections = await forms_db.select_sections(fdb, form_id, version)
    values = await forms_db.get_response_values(fdb, response_id)
    out = []
    for sec in sections:
        fields = await forms_db.get_fields(fdb, sec["id"], version=version)
        out.append(
            {
                "id": sec["id"],
                "title": forms_db._pick(sec["title"]),
                "description": forms_db._pick(sec["description"]),
                "position": sec["position"],
                "fields": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": forms_db._pick(f["label"]),
                        "type": f["type"],
                        "prefix": f["prefix"],
                        "position": f["position"],
                        "required": f["required"],
                        "value": values.get(f["id"]),
                    }
                    for f in fields
                ],
            }
        )
    return out
