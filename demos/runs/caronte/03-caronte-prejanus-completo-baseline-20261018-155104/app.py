import asyncio
import csv
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response as FastResponse
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from itsdangerous import URLSafeTimedSerializer
from oauthlib.oauth1 import Client as OAuth1Client
from pydantic import BaseModel
from sqlalchemy import delete, select

import forms as formsdb
from db import (
    Bidding,
    Comment,
    Edict,
    Favorite,
    Label,
    Mapping,
    Phase,
    PrivateNote,
    SessionLocal,
    Slot,
    Submission,
    SubmissionView,
    User,
    init_db,
    new_id,
)
from settings import settings

app = FastAPI(title="PreJanus Back", version="2.0.0")

_origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

serializer = URLSafeTimedSerializer(settings.secret_key)
SESSION_COOKIE = "session"
SESSION_MAX_AGE = 8 * 3600
ADMIN_ROLES = {"administrator", "secretary", "coordinator"}
PHASE_LABELS = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
BIDDING_VALUES = {
    "decline",
    "available",
    "interested",
    "agreed",
    "interested_scholarship",
    "",
}

WHITELIST: set[str] = set()
JOBS: dict[str, dict] = {}

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.smtp_user or "",
    MAIL_PASSWORD=settings.smtp_password or "",
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


@app.on_event("startup")
async def startup() -> None:
    await init_db()
    global WHITELIST
    path = Path(settings.nusp_whitelist_path)
    if path.exists():
        WHITELIST = {
            line.strip() for line in path.read_text().splitlines() if line.strip()
        }


# ---------------------------------------------------------------- sessions


def load_session(request: Request) -> dict:
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        return {}
    try:
        data = serializer.loads(raw, max_age=SESSION_MAX_AGE)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def set_session(response: Response, data: dict) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        serializer.dumps(data),
        max_age=SESSION_MAX_AGE,
        samesite="lax",
        secure=True,
    )


async def get_user(request: Request) -> User:
    data = load_session(request)
    uid = data.get("user_id")
    if not uid:
        raise HTTPException(401, "Not authenticated")
    async with SessionLocal() as db:
        user = await db.get(User, uid)
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return user


def require_admin(user: User) -> None:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Administrative role required")


def user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }


# ---------------------------------------------------------------- helpers


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def check_chronological(dates: list[Any]) -> None:
    """The four edict dates must be in strict chronological order."""
    parsed = [parse_dt(v) for v in dates]
    for a, b in zip(parsed, parsed[1:]):
        if not a < b:
            raise HTTPException(422, "Dates must be in strict chronological order")


async def get_edict(edict_id: str) -> Edict:
    async with SessionLocal() as db:
        edict = await db.get(Edict, edict_id)
    if edict is None:
        raise HTTPException(404, "Edict not found")
    return edict


async def get_submission(submission_id: str) -> Submission:
    async with SessionLocal() as db:
        sub = await db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "Submission not found")
    return sub


async def current_phase_label(edict: Edict) -> str:
    if edict.current_phase_id is None:
        return "inscricoes"
    async with SessionLocal() as db:
        phase = await db.get(Phase, edict.current_phase_id)
    return phase.label if phase else "inscricoes"


async def get_mapping(edict_id: str, tipo: str, version: int) -> Mapping | None:
    async with SessionLocal() as db:
        res = await db.execute(
            select(Mapping).where(
                Mapping.edict_id == edict_id,
                Mapping.type == tipo,
                Mapping.version == version,
                Mapping.active.is_(True),
            )
        )
        return res.scalar_one_or_none()


def apply_tree(tree: Any, answers: dict[str, Any]) -> Any:
    """Resolve a mapping tree against {field_id: value} answers."""
    if tree is None:
        return None
    if isinstance(tree, dict):
        if set(tree.keys()) >= {"section", "field"}:
            return answers.get(str(tree["field"]))
        return {k: apply_tree(v, answers) for k, v in tree.items()}
    if isinstance(tree, list):
        return [apply_tree(v, answers) for v in tree]
    return tree


async def validate_tree(tree: Any, form_id: str, version: int) -> None:
    if isinstance(tree, dict):
        if set(tree.keys()) >= {"section", "field"}:
            sections = await formsdb.get_sections(form_id, version)
            sec_ids = {s["id"] for s in sections}
            if str(tree["section"]) not in sec_ids:
                raise HTTPException(422, "Invalid section reference")
            fields = await formsdb.get_fields(str(tree["section"]))
            if str(tree["field"]) not in {f["id"] for f in fields}:
                raise HTTPException(422, "Invalid field reference")
            return
        for v in tree.values():
            await validate_tree(v, form_id, version)
    elif isinstance(tree, list):
        for v in tree:
            await validate_tree(v, form_id, version)


async def ensure_submissions(edict: Edict) -> None:
    """Create local submission rows for finished candidate responses."""
    if not edict.candidate_form_id:
        return
    responses = [
        r for r in await formsdb.get_responses(edict.candidate_form_id) if r["finished"]
    ]
    async with SessionLocal() as db:
        for resp in responses:
            existing = (
                await db.execute(
                    select(Submission).where(Submission.response_id == resp["id"])
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    Submission(
                        id=new_id(),
                        edict_id=edict.id,
                        response_id=resp["id"],
                        version=resp["version"],
                        email=resp["email"],
                    )
                )
        await db.commit()


async def accept_status(sub: Submission) -> str:
    if not sub.accept_form_id:
        return "not_sent"
    answers = await formsdb.get_answers(sub.accept_form_id)
    return "replied" if answers else "sent"


async def send_mail(
    subject: str, recipients: list[str], html: str, cc: list[str] | None = None, bcc: list[str] | None = None
) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        html=html,
        cc=cc or [],
        bcc=bcc or [],
    )
    await FastMail(mail_config).send_message(message)


# ---------------------------------------------------------------- root


@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


# ---------------------------------------------------------------- auth


@app.get("/auth/login")
async def auth_login(request: Request) -> dict:
    if settings.app_env == "local" and settings.dev_user_id:
        async with SessionLocal() as db:
            user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(500, "DEV_USER_ID does not match an existing user")
        return user_dict(user)
    data = load_session(request)
    if data.get("user_id"):
        async with SessionLocal() as db:
            user = await db.get(User, data["user_id"])
        if user is not None:
            return user_dict(user)
    raise HTTPException(401, "Not authenticated")


class OAuthBody(BaseModel):
    oauth_token: Optional[str] = None
    oauth_verifier: Optional[str] = None


@app.post("/auth/login/senhaunica")
async def senhaunica(request: Request, response: Response, body: OAuthBody) -> dict:
    sess = load_session(request)
    key, secret = (
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
    )
    if not body.oauth_token:
        client = OAuth1Client(key, secret)
        uri, headers, _ = client.sign(settings.senhaunica_request_token_url)
        r = requests.post(uri, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(500, "Failed to obtain request token")
        data = dict(
            p.split("=", 1) for p in r.text.split("&") if "=" in p
        )
        sess["request_token"] = data.get("oauth_token")
        sess["request_secret"] = data.get("oauth_token_secret")
        set_session(response, sess)
        return {
            "redirect_to": (
                f"{settings.senhaunica_authorize_url}?oauth_token={data.get('oauth_token')}"
            )
        }
    if not sess.get("request_secret"):
        raise HTTPException(401, "Missing request token secret")
    client = OAuth1Client(
        key,
        secret,
        resource_owner_key=body.oauth_token,
        resource_owner_secret=sess["request_secret"],
        verifier=body.oauth_verifier,
    )
    uri, headers, _ = client.sign(settings.senhaunica_access_token_url)
    r = requests.post(uri, headers=headers)
    if r.status_code >= 400:
        raise HTTPException(500, "Failed to exchange access token")
    tok = dict(p.split("=", 1) for p in r.text.split("&") if "=" in p)
    client2 = OAuth1Client(
        key,
        secret,
        resource_owner_key=tok.get("oauth_token"),
        resource_owner_secret=tok.get("oauth_token_secret"),
    )
    uri2, headers2, _ = client2.sign(settings.senhaunica_user_data_url)
    r2 = requests.get(uri2, headers=headers2)
    if r2.status_code >= 400:
        raise HTTPException(500, "Failed to fetch user data")
    info = r2.json()
    nusp = str(info.get("nusp") or info.get("codpes") or "")
    if WHITELIST and nusp not in WHITELIST:
        raise HTTPException(401, "NUSP not in whitelist")
    email = info.get("email") or info.get("emailUsp") or ""
    name = info.get("name") or info.get("nome") or ""
    async with SessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                id=new_id(), name=name, email=email, nusp=nusp, role="teacher"
            )
            db.add(user)
            await db.commit()
        sess["user_id"] = user.id
    set_session(response, sess)
    return user_dict(user)


# ---------------------------------------------------------------- forms


@app.get("/forms")
async def list_forms(
    year: Optional[str] = None, notice: Optional[str] = None
) -> list[dict]:
    return await formsdb.list_forms(year, notice)


@app.get("/forms/{form_id}")
async def get_form(form_id: str, version: Optional[int] = None) -> dict:
    return await formsdb.get_form(form_id, version)


@app.get("/forms/{form_id}/sections")
async def get_sections(form_id: str, version: Optional[int] = None) -> list[dict]:
    return await formsdb.get_sections(form_id, version)


@app.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_fields(form_id: str, section_id: str) -> list[dict]:
    return await formsdb.get_fields(section_id)


# ---------------------------------------------------------------- edicts


class EdictIn(BaseModel):
    title: str
    description: str = ""
    year: str
    semester: str
    edict_type: str
    is_open: bool = True
    candidate_forms: Any = None
    recommenders_forms: Any = None
    date_application: str
    date_verification: str
    date_evaluation: str
    date_closed: str


def edict_dict(edict: Edict) -> dict:
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
        "date_application": edict.date_application.isoformat() if edict.date_application else None,
        "date_verification": edict.date_verification.isoformat() if edict.date_verification else None,
        "date_evaluation": edict.date_evaluation.isoformat() if edict.date_evaluation else None,
        "date_closed": edict.date_closed.isoformat() if edict.date_closed else None,
        "confirmation_deadline": edict.confirmation_deadline.isoformat() if edict.confirmation_deadline else None,
        "send_approval_letter": edict.send_approval_letter,
    }


@app.get("/edicts")
async def list_edicts(
    type: Optional[str] = None, is_open: Optional[bool] = None
) -> list[dict]:
    async with SessionLocal() as db:
        q = select(Edict)
        if type is not None:
            q = q.where(Edict.edict_type == type)
        if is_open is not None:
            q = q.where(Edict.is_open == is_open)
        q = q.order_by(Edict.date_closed.desc())
        edicts = (await db.execute(q)).scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "year": e.year,
            "semester": e.semester,
            "edict_type": e.edict_type,
            "is_open": e.is_open,
        }
        for e in edicts
    ]


@app.get("/edicts/{edict_id}")
async def get_edict_detail(
    edict_id: str, user: User = Depends(get_user)
) -> dict:
    edict = await get_edict(edict_id)
    async with SessionLocal() as db:
        phases = (
            await db.execute(
                select(Phase).where(Phase.edict_id == edict_id).order_by(Phase.position)
            )
        ).scalars().all()
        slot = (
            await db.execute(
                select(Slot).where(Slot.edict_id == edict_id, Slot.user_id == user.id)
            )
        ).scalar_one_or_none()
    data = edict_dict(edict)
    data["phases"] = [
        {"id": p.id, "label": p.label, "position": p.position} for p in phases
    ]
    data["slots"] = slot.amount if slot else "0"
    data["current_phase"] = await current_phase_label(edict)
    return data


@app.post("/edicts")
async def create_edict(
    body: EdictIn, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    check_chronological(
        [
            body.date_application,
            body.date_verification,
            body.date_evaluation,
            body.date_closed,
        ]
    )
    edict_id = new_id()
    edict = Edict(
        id=edict_id,
        title=body.title,
        description=body.description,
        year=str(body.year),
        semester=str(body.semester),
        edict_type=body.edict_type,
        is_open=body.is_open,
        candidate_form_id=(
            str(body.candidate_forms)
            if body.candidate_forms is not None
            else None
        ),
        recommender_form_id=(
            str(body.recommenders_forms)
            if body.recommenders_forms is not None
            else None
        ),
        author_id=user.id,
        date_application=parse_dt(body.date_application),
        date_verification=parse_dt(body.date_verification),
        date_evaluation=parse_dt(body.date_evaluation),
        date_closed=parse_dt(body.date_closed),
    )
    async with SessionLocal() as db:
        db.add(edict)
        await db.flush()
        phase_ids = {}
        for pos, label in enumerate(PHASE_LABELS):
            phase = Phase(id=new_id(), edict_id=edict_id, label=label, position=pos)
            db.add(phase)
            phase_ids[label] = phase.id
        edict.current_phase_id = phase_ids["inscricoes"]
        await db.commit()
    return {"id": edict_id, **edict_dict(edict)}


class EdictEdit(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    semester: Optional[str] = None
    edict_type: Optional[str] = None
    is_open: Optional[bool] = None
    date_application: Optional[str] = None
    date_verification: Optional[str] = None
    date_evaluation: Optional[str] = None
    date_closed: Optional[str] = None


@app.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: str, body: EdictEdit, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    edict = await get_edict(edict_id)
    dates = [
        body.date_application or edict.date_application,
        body.date_verification or edict.date_verification,
        body.date_evaluation or edict.date_evaluation,
        body.date_closed or edict.date_closed,
    ]
    check_chronological(dates)
    async with SessionLocal() as db:
        for field in (
            "title",
            "description",
            "year",
            "semester",
            "edict_type",
            "is_open",
        ):
            value = getattr(body, field)
            if value is not None:
                setattr(edict, field, value)
        edict.date_application = parse_dt(dates[0])
        edict.date_verification = parse_dt(dates[1])
        edict.date_evaluation = parse_dt(dates[2])
        edict.date_closed = parse_dt(dates[3])
        db.add(edict)
        await db.commit()
    return edict_dict(edict)


class EditDate(BaseModel):
    closed_date: str


@app.post("/edicts/{edict_id}/edit-date")
async def edit_date(
    edict_id: str, body: EditDate, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    edict = await get_edict(edict_id)
    edict.date_closed = parse_dt(body.closed_date)
    async with SessionLocal() as db:
        db.add(edict)
        await db.commit()
    return {"closed_date": body.closed_date}


class AdvancePhase(BaseModel):
    id: str


@app.post("/edicts/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: str, body: AdvancePhase, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    edict = await get_edict(edict_id)
    async with SessionLocal() as db:
        phase = await db.get(Phase, body.id)
    if phase is None or phase.edict_id != edict_id:
        raise HTTPException(404, "Phase not found")
    edict.current_phase_id = phase.id
    async with SessionLocal() as db:
        db.add(edict)
        await db.commit()
    if edict.candidate_form_id:
        await formsdb.set_form_phase(
            edict.candidate_form_id, PHASE_TO_FORMS[phase.label]
        )
    return {"id": phase.id, "label": phase.label}


class CloseBody(BaseModel):
    confirmation_deadline: Optional[str] = None
    send_approval_letter: bool = False


@app.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: str, body: CloseBody, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    edict = await get_edict(edict_id)
    if not edict.is_open:
        raise HTTPException(409, "Edict already closed")
    edict.is_open = False
    edict.send_approval_letter = body.send_approval_letter
    if body.confirmation_deadline:
        edict.confirmation_deadline = parse_dt(body.confirmation_deadline)
    async with SessionLocal() as db:
        db.add(edict)
        await db.commit()
    return {"id": edict.id, "is_open": False}


@app.delete("/edicts/{edict_id}/remove")
async def remove_edict(
    edict_id: str, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    await get_edict(edict_id)
    async with SessionLocal() as db:
        sub_ids = [
            s.id
            for s in (
                await db.execute(
                    select(Submission).where(Submission.edict_id == edict_id)
                )
            ).scalars().all()
        ]
        for sid in sub_ids:
            for model in (Comment, Favorite, Label, PrivateNote, SubmissionView, Bidding):
                await db.execute(delete(model).where(model.submission_id == sid))
        await db.execute(delete(Submission).where(Submission.edict_id == edict_id))
        await db.execute(delete(Phase).where(Phase.edict_id == edict_id))
        await db.execute(delete(Mapping).where(Mapping.edict_id == edict_id))
        await db.execute(delete(Slot).where(Slot.edict_id == edict_id))
        await db.execute(delete(Edict).where(Edict.id == edict_id))
        await db.commit()
    return {"message": "Edict removed successfully"}


# ---------------------------------------------------------------- mappings


async def _mapping_form_id(edict: Edict, tipo: str) -> str | None:
    return (
        edict.candidate_form_id
        if tipo == "candidates"
        else edict.recommender_form_id
    )


def mapping_dict(m: Mapping) -> dict:
    return {
        "id": m.id,
        "edict_id": m.edict_id,
        "type": m.type,
        "author_id": m.author_id,
        "form_id": m.form_id,
        "version": m.version,
        "tree": m.tree,
        "active": m.active,
    }


@app.post(
    "/edicts/{edict_id}/{tipo}/mappings/versions/{version}/"
)
async def create_mapping(
    edict_id: str,
    tipo: str,
    version: int,
    tree: dict,
    user: User = Depends(get_user),
) -> dict:
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Unknown mapping type")
    require_admin(user)
    edict = await get_edict(edict_id)
    form_id = await _mapping_form_id(edict, tipo)
    if form_id:
        await validate_tree(tree, form_id, version)
    if await get_mapping(edict_id, tipo, version) is not None:
        raise HTTPException(409, "Mapping already exists")
    mapping = Mapping(
        id=new_id(),
        edict_id=edict_id,
        type=tipo,
        version=version,
        author_id=user.id,
        form_id=form_id,
        tree=tree,
        active=True,
    )
    async with SessionLocal() as db:
        db.add(mapping)
        await db.commit()
    return mapping_dict(mapping)


@app.get("/edicts/{edict_id}/{tipo}/mappings")
async def list_mappings(
    edict_id: str, tipo: str, user: User = Depends(get_user)
) -> list[dict]:
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Unknown mapping type")
    await get_edict(edict_id)
    async with SessionLocal() as db:
        mappings = (
            await db.execute(
                select(Mapping).where(
                    Mapping.edict_id == edict_id, Mapping.type == tipo
                )
            )
        ).scalars().all()
    return [mapping_dict(m) for m in mappings]


@app.put(
    "/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}"
)
async def update_mapping(
    edict_id: str,
    tipo: str,
    version: int,
    mapping_id: str,
    tree: dict,
    user: User = Depends(get_user),
) -> dict:
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Unknown mapping type")
    require_admin(user)
    edict = await get_edict(edict_id)
    async with SessionLocal() as db:
        mapping = await db.get(Mapping, mapping_id)
    if (
        mapping is None
        or mapping.edict_id != edict_id
        or mapping.type != tipo
        or mapping.version != version
    ):
        raise HTTPException(404, "Mapping not found")
    form_id = await _mapping_form_id(edict, tipo)
    if form_id:
        await validate_tree(tree, form_id, version)
    mapping.tree = tree
    async with SessionLocal() as db:
        db.add(mapping)
        await db.commit()
    return mapping_dict(mapping)


@app.delete(
    "/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}"
)
async def delete_mapping(
    edict_id: str,
    tipo: str,
    version: int,
    mapping_id: str,
    user: User = Depends(get_user),
) -> dict:
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Unknown mapping type")
    require_admin(user)
    await get_edict(edict_id)
    async with SessionLocal() as db:
        mapping = await db.get(Mapping, mapping_id)
    if (
        mapping is None
        or mapping.edict_id != edict_id
        or mapping.type != tipo
        or mapping.version != version
    ):
        raise HTTPException(404, "Mapping not found")
    async with SessionLocal() as db:
        await db.delete(mapping)
        await db.commit()
    return {"message": "Mapping deleted successfully"}


@app.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def unmapped_versions(
    edict_id: str, tipo: str, user: User = Depends(get_user)
) -> list[dict]:
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Unknown mapping type")
    await get_edict(edict_id)
    async with SessionLocal() as db:
        versions = {
            s.version
            for s in (
                await db.execute(
                    select(Submission).where(Submission.edict_id == edict_id)
                )
            ).scalars().all()
        }
        mapped = {
            m.version
            for m in (
                await db.execute(
                    select(Mapping).where(
                        Mapping.edict_id == edict_id, Mapping.type == tipo
                    )
                )
            ).scalars().all()
        }
    return [{"version": v} for v in sorted(versions - mapped)]


# ---------------------------------------------------------------- submissions


@app.get("/edicts/{edict_id}/submissions")
async def list_submissions(
    edict_id: str,
    stats: Optional[str] = None,
    only_favorites: bool = False,
    user: User = Depends(get_user),
) -> dict:
    edict = await get_edict(edict_id)
    await ensure_submissions(edict)
    async with SessionLocal() as db:
        subs = (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict_id)
            )
        ).scalars().all()
        favs = {
            f.submission_id
            for f in (
                await db.execute(
                    select(Favorite).where(Favorite.user_id == user.id)
                )
            ).scalars().all()
        }
        labels = (
            await db.execute(
                select(Label).where(
                    Label.submission_id.in_([s.id for s in subs] or [""]),
                    Label.user_id == user.id,
                )
            )
        ).scalars().all()
        biddings = (
            await db.execute(
                select(Bidding).where(Bidding.user_id == user.id)
            )
        ).scalars().all()
        users = {
            u.id: u
            for u in (
                await db.execute(select(User))
            ).scalars().all()
        }
    labels_by_sub: dict[str, list[dict]] = {}
    for lab in labels:
        labels_by_sub.setdefault(lab.submission_id, []).append(
            {"id": lab.id, "label": lab.label, "color": lab.color}
        )
    bidding_by_sub = {b.submission_id: b.bidding for b in biddings}
    result = []
    for sub in subs:
        if stats is not None and sub.stats != stats:
            continue
        if only_favorites and sub.id not in favs:
            continue
        answers = await formsdb.get_answers(sub.response_id)
        mapping = await get_mapping(edict_id, "candidates", sub.version)
        data = apply_tree(mapping.tree, answers) if mapping else {}
        advisor = users.get(sub.advisor_id)
        result.append(
            {
                "id": sub.id,
                "edict_id": sub.edict_id,
                "email": sub.email,
                "version": sub.version,
                "stats": sub.stats,
                "advisor": advisor.name if advisor else None,
                "advisor_id": sub.advisor_id,
                "entry_semester": sub.entry_semester,
                "favorite": sub.id in favs,
                "labels": labels_by_sub.get(sub.id, []),
                "bidding": bidding_by_sub.get(sub.id, ""),
                "accept": await accept_status(sub),
                "letter_sent": sub.letter_sent,
                "data": data,
            }
        )
    return {"submissions": result}


@app.get("/submissions/{submission_id}")
async def submission_detail(
    submission_id: str,
    include_comments: bool = False,
    user: User = Depends(get_user),
) -> dict:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    answers = await formsdb.get_answers(sub.response_id)
    mapping = await get_mapping(sub.edict_id, "candidates", sub.version)
    summary = {
        "id": sub.id,
        "edict_id": sub.edict_id,
        "email": sub.email,
        "stats": sub.stats,
        "entry_semester": sub.entry_semester,
        "letter_sent": sub.letter_sent,
        "accept": await accept_status(sub),
        "data": apply_tree(mapping.tree, answers) if mapping else {},
    }
    async with SessionLocal() as db:
        fav = (
            await db.execute(
                select(Favorite).where(
                    Favorite.user_id == user.id,
                    Favorite.submission_id == sub.id,
                )
            )
        ).scalar_one_or_none()
        labs = (
            await db.execute(
                select(Label).where(
                    Label.user_id == user.id,
                    Label.submission_id == sub.id,
                )
            )
        ).scalars().all()
        note = (
            await db.execute(
                select(PrivateNote).where(
                    PrivateNote.user_id == user.id,
                    PrivateNote.submission_id == sub.id,
                )
            )
        ).scalar_one_or_none()
        advisor = (
            await db.get(User, sub.advisor_id) if sub.advisor_id else None
        )
    summary["favorite"] = fav is not None
    summary["labels"] = [
        {"id": l.id, "label": l.label, "color": l.color} for l in labs
    ]
    summary["private_note"] = note.note if note else ""
    summary["advisor"] = advisor.name if advisor else None
    if include_comments:
        summary["comments"] = await _activity(sub)
    # recommendations linked to this candidate
    recommendations = []
    if edict.recommender_form_id:
        for resp in await formsdb.get_responses(edict.recommender_form_id):
            values = [str(v) for v in (await formsdb.get_answers(resp["id"])).values()]
            if sub.email and sub.email in values:
                recommendations.append(
                    {
                        "id": resp["id"],
                        "email": resp["email"],
                        "version": resp["version"],
                        "finished": resp["finished"],
                    }
                )
    summary["recommendations"] = recommendations
    # full form: every section and field, with values
    submission_form = await formsdb.get_form(
        sub.response_id and edict.candidate_form_id or edict.candidate_form_id,
        sub.version,
    )
    for section in submission_form.get("sections", []):
        for field in section["fields"]:
            field["value"] = answers.get(field["id"])
    return {"summary": summary, "submission_form": submission_form}


async def _activity(sub: Submission) -> list[dict]:
    events: list[dict] = []
    async with SessionLocal() as db:
        comments = (
            await db.execute(
                select(Comment).where(Comment.submission_id == sub.id)
            )
        ).scalars().all()
        users = {u.id: u for u in (await db.execute(select(User))).scalars().all()}
    for c in comments:
        author = users.get(c.user_id)
        events.append(
            {
                "type": "comment",
                "user": author.name if author else None,
                "user_id": c.user_id,
                "text": c.text,
                "date": c.created_at.isoformat(),
            }
        )
    resp = await formsdb.get_responses(sub.response_id)
    events.append(
        {
            "type": "submission",
            "user": sub.email,
            "user_id": sub.email,
            "text": "Candidatura enviada",
            "date": str(resp.get("created_at", "")) if resp else "",
        }
    )
    if sub.accept_form_id:
        events.append(
            {
                "type": "accept",
                "user": sub.email,
                "user_id": sub.email,
                "text": "Formulário de aceite enviado",
                "date": "",
            }
        )
    events.sort(key=lambda e: e["date"] or "")
    return events


@app.get("/submissions/{submission_id}/comments")
async def get_comments(
    submission_id: str, user: User = Depends(get_user)
) -> list[dict]:
    sub = await get_submission(submission_id)
    return await _activity(sub)


@app.get("/submissions/{submission_id}/files/{label}/{filename}")
async def download_file(
    submission_id: str, label: str, filename: str, user: User = Depends(get_user)
):
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if not edict.candidate_form_id:
        raise HTTPException(404, "File not found")
    answers = await formsdb.get_answers(sub.response_id)
    sections = await formsdb.get_sections(edict.candidate_form_id, sub.version)
    found = None
    for section in sections:
        for field in await formsdb.get_fields(section["id"]):
            if field["label"] == label or field["name"] == label:
                value = answers.get(field["id"])
                if isinstance(value, str) and value == filename:
                    found = value
    if found is None:
        raise HTTPException(404, "File not found")
    path = Path(settings.uploads_dir) / found
    if not path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------- comments


class CommentBody(BaseModel):
    comment: str
    created_at: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@app.post("/submissions/{submission_id}/comments")
async def create_comment(
    submission_id: str, body: CommentBody, user: User = Depends(get_user)
) -> dict:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if (await current_phase_label(edict)) != "avaliacao":
        raise HTTPException(400, "Comments are only allowed in the evaluation phase")
    comment = Comment(
        id=new_id(),
        submission_id=submission_id,
        user_id=user.id,
        text=body.comment,
        created_at=parse_dt(body.created_at) if body.created_at else datetime.now(),
        start_date=parse_dt(body.start_date) if body.start_date else None,
        end_date=parse_dt(body.end_date) if body.end_date else None,
    )
    async with SessionLocal() as db:
        db.add(comment)
        await db.commit()
    return {
        "id": comment.id,
        "user_id": comment.user_id,
        "submission_id": comment.submission_id,
        "comment": comment.text,
        "created_at": comment.created_at.isoformat(),
        "start_date": comment.start_date.isoformat() if comment.start_date else None,
        "end_date": comment.end_date.isoformat() if comment.end_date else None,
    }


@app.delete("/submissions/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: str, response: Response, user: User = Depends(get_user)
) -> Response:
    async with SessionLocal() as db:
        comment = await db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(403, "Only the author may delete this comment")
    async with SessionLocal() as db:
        await db.delete(comment)
        await db.commit()
    response.status_code = 204
    return response


# ---------------------------------------------------------------- favorites


@app.post("/submissions/{submission_id}/favorites", status_code=201)
async def add_favorite(
    submission_id: str, response: Response, user: User = Depends(get_user)
) -> Response:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if (await current_phase_label(edict)) != "avaliacao":
        raise HTTPException(400, "Favorites are only allowed in the evaluation phase")
    async with SessionLocal() as db:
        existing = (
            await db.execute(
                select(Favorite).where(
                    Favorite.user_id == user.id,
                    Favorite.submission_id == submission_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(409, "Favorite already exists")
        db.add(
            Favorite(id=new_id(), user_id=user.id, submission_id=submission_id)
        )
        await db.commit()
    response.status_code = 201
    return response


@app.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(
    submission_id: str, response: Response, user: User = Depends(get_user)
) -> Response:
    async with SessionLocal() as db:
        existing = (
            await db.execute(
                select(Favorite).where(
                    Favorite.user_id == user.id,
                    Favorite.submission_id == submission_id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            raise HTTPException(404, "Favorite not found")
        await db.delete(existing)
        await db.commit()
    response.status_code = 204
    return response


# ---------------------------------------------------------------- labels


class LabelBody(BaseModel):
    label: str
    color: str = ""


@app.post("/submissions/{submission_id}/labels")
async def create_label(
    submission_id: str, body: LabelBody, user: User = Depends(get_user)
) -> dict:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if (await current_phase_label(edict)) != "avaliacao":
        raise HTTPException(400, "Labels are only allowed in the evaluation phase")
    label = Label(
        id=new_id(),
        user_id=user.id,
        submission_id=submission_id,
        label=body.label,
        color=body.color,
        context="candidate",
    )
    async with SessionLocal() as db:
        db.add(label)
        # keep the color of same author + same label consistent across submissions
        others = (
            await db.execute(
                select(Label).where(
                    Label.user_id == user.id,
                    Label.label == body.label,
                    Label.context == "candidate",
                )
            )
        ).scalars().all()
        for other in others:
            other.color = body.color
        await db.commit()
    return {
        "id": label.id,
        "user_id": label.user_id,
        "submission_id": label.submission_id,
        "label": label.label,
        "color": label.color,
    }


@app.get("/submissions/{submission_id}/labels")
async def list_labels(
    submission_id: str, user: User = Depends(get_user)
) -> list[dict]:
    await get_submission(submission_id)
    async with SessionLocal() as db:
        labels = (
            await db.execute(
                select(Label).where(Label.user_id == user.id)
            )
        ).scalars().all()
    seen: dict[str, dict] = {}
    for lab in labels:
        seen.setdefault(
            lab.label, {"id": lab.id, "label": lab.label, "color": lab.color}
        )
    return list(seen.values())


@app.delete("/submissions/label/{label_id}", status_code=204)
async def delete_label(
    label_id: str, response: Response, user: User = Depends(get_user)
) -> Response:
    async with SessionLocal() as db:
        label = await db.get(Label, label_id)
        if label is None:
            raise HTTPException(404, "Label not found")
        if label.user_id != user.id:
            raise HTTPException(403, "Only the author may delete this label")
        await db.delete(label)
        await db.commit()
    response.status_code = 204
    return response


# ---------------------------------------------------------------- private notes


class NoteBody(BaseModel):
    note: str


@app.post("/submissions/{submission_id}/private_notes")
async def upsert_note(
    submission_id: str, body: NoteBody, user: User = Depends(get_user)
) -> dict:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if (await current_phase_label(edict)) != "avaliacao":
        raise HTTPException(400, "Notes are only allowed in the evaluation phase")
    async with SessionLocal() as db:
        note = (
            await db.execute(
                select(PrivateNote).where(
                    PrivateNote.user_id == user.id,
                    PrivateNote.submission_id == submission_id,
                )
            )
        ).scalar_one_or_none()
        if note is None:
            note = PrivateNote(
                id=new_id(),
                user_id=user.id,
                submission_id=submission_id,
                note=body.note,
            )
            db.add(note)
        else:
            note.note = body.note
            db.add(note)
        await db.commit()
    return {"note": body.note}


# ---------------------------------------------------------------- views


TZ_SP = timezone(timedelta(hours=-3))


@app.post("/submissions/{submission_id}/view")
async def register_view(
    submission_id: str, user: User = Depends(get_user)
) -> dict:
    await get_submission(submission_id)
    today = datetime.now(TZ_SP).date()
    async with SessionLocal() as db:
        existing = (
            await db.execute(
                select(SubmissionView).where(
                    SubmissionView.user_id == user.id,
                    SubmissionView.submission_id == submission_id,
                    SubmissionView.view_date == today,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                SubmissionView(
                    id=new_id(),
                    user_id=user.id,
                    submission_id=submission_id,
                    view_date=today,
                )
            )
            await db.commit()
    return {"message": "View registered"}


@app.get("/submissions/{submission_id}/view")
async def list_views(
    submission_id: str, user: User = Depends(get_user)
) -> list[dict]:
    await get_submission(submission_id)
    async with SessionLocal() as db:
        views = (
            await db.execute(
                select(SubmissionView).where(
                    SubmissionView.submission_id == submission_id
                )
            )
        ).scalars().all()
    return [
        {"user_id": v.user_id, "date": v.view_date.isoformat()} for v in views
    ]


# ---------------------------------------------------------------- slots & bidding


class SlotBody(BaseModel):
    amount: str


@app.post("/edicts/{edict_id}/slots")
async def set_slots(
    edict_id: str, body: SlotBody, user: User = Depends(get_user)
) -> dict:
    await get_edict(edict_id)
    text = (body.amount or "").strip()
    if text.startswith("-") or not text:
        amount = "0"
    else:
        try:
            amount = str(int(text))
        except ValueError:
            raise HTTPException(422, "amount must be an integer")
    async with SessionLocal() as db:
        slot = (
            await db.execute(
                select(Slot).where(
                    Slot.edict_id == edict_id, Slot.user_id == user.id
                )
            )
        ).scalar_one_or_none()
        if slot is None:
            slot = Slot(
                id=new_id(), edict_id=edict_id, user_id=user.id, amount=amount
            )
            db.add(slot)
        else:
            slot.amount = amount
            db.add(slot)
        await db.commit()
    return {"amount": amount}


class BiddingBody(BaseModel):
    bidding: str
    user_id: Optional[str] = None


@app.post("/submissions/{submission_id}/bidding")
async def set_bidding(
    submission_id: str, body: BiddingBody, user: User = Depends(get_user)
) -> dict:
    await get_submission(submission_id)
    if body.bidding not in BIDDING_VALUES:
        raise HTTPException(422, "Invalid bidding value")
    target = user.id
    if body.user_id is not None:
        if user.role in ADMIN_ROLES:
            target = body.user_id
        else:
            raise HTTPException(403, "Only administrators may bid for another user")
    async with SessionLocal() as db:
        bidding = (
            await db.execute(
                select(Bidding).where(
                    Bidding.user_id == target,
                    Bidding.submission_id == submission_id,
                )
            )
        ).scalar_one_or_none()
        if bidding is None:
            bidding = Bidding(
                id=new_id(),
                user_id=target,
                submission_id=submission_id,
                bidding=body.bidding,
            )
            db.add(bidding)
        else:
            bidding.bidding = body.bidding
            db.add(bidding)
        await db.commit()
    return {"bidding": body.bidding, "user_id": target}


# ---------------------------------------------------------------- selection


class SelectBody(BaseModel):
    stats: str
    user_ids: Optional[list[str]] = None


@app.post("/submissions/{submission_id}/select")
async def select_submission(
    submission_id: str, body: SelectBody, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if not edict.is_open:
        raise HTTPException(409, "Edict is closed")
    if body.stats not in ("approved", "refused", "underreview", "waitlist"):
        raise HTTPException(422, "Invalid stats value")
    async with SessionLocal() as db:
        if body.stats == "approved":
            if not body.user_ids or len(body.user_ids) != 1:
                raise HTTPException(422, "Approval requires exactly one advisor")
            advisor = await db.get(User, body.user_ids[0])
            if advisor is None:
                raise HTTPException(422, "Advisor not found")
            sub.advisor_id = advisor.id
        sub.stats = body.stats
        db.add(sub)
        await db.commit()
    return {"id": sub.id, "stats": sub.stats, "advisor_id": sub.advisor_id}


class SemesterBody(BaseModel):
    semester: str


@app.post("/submissions/{submission_id}/entry-semester")
async def set_entry_semester(
    submission_id: str, body: SemesterBody, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    sub = await get_submission(submission_id)
    text = body.semester.strip().lower()
    if text in ("first", "primeiro", "primeiro semestre"):
        value = "Primeiro semestre."
    elif text in ("second", "segundo", "segundo semestre"):
        value = "Segundo semestre."
    else:
        value = body.semester
    sub.entry_semester = value
    async with SessionLocal() as db:
        db.add(sub)
        await db.commit()
    return {"semester": value}


# ---------------------------------------------------------------- mail


@app.post("/submissions/{submission_id}/reesend_submission")
async def resend_submission(
    submission_id: str, body: dict, user: User = Depends(get_user)
) -> dict:
    require_admin(user)
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if (await current_phase_label(edict)) != "homologacao":
        raise HTTPException(400, "Correction requests are only allowed in the approval phase")
    text = body.get("text", "")
    await formsdb.reopen_response(sub.response_id)
    token = await formsdb.get_response_token(sub.response_id)
    link = f"{settings.base_url}/form/{token}" if token else settings.base_url
    html = (
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Sua inscrição precisa de correção.</p>"
        f"<p>Motivo: {text}</p>"
        f"<p>Para corrigir e reenviar, acesse: <a href='{link}'>{link}</a></p>"
    )
    await send_mail(
        "[PreJanus] Solicitação de correção da inscrição",
        [sub.email],
        html,
        bcc=[user.email],
    )
    return {
        "message": "Correction request sent",
        "email_sent": True,
    }


@app.post("/submissions/{submission_id}/send-accept")
async def send_accept(
    submission_id: str, user: User = Depends(get_user)
) -> dict:
    sub = await get_submission(submission_id)
    edict = await get_edict(sub.edict_id)
    if not edict.accept_form_id:
        raise HTTPException(404, "Accept form not configured")
    if sub.stats != "approved":
        raise HTTPException(400, "Submission is not approved")
    if sub.accept_form_id:
        raise HTTPException(400, "Accept form already sent")
    token = await formsdb.create_share(
        edict.accept_form_id, sub.email, edict.date_closed
    )
    response_id = await formsdb.create_response(
        edict.accept_form_id, sub.email, 1, token
    )
    sub.accept_form_id = response_id
    async with SessionLocal() as db:
        db.add(sub)
        await db.commit()
    advisor = None
    if sub.advisor_id:
        async with SessionLocal() as db:
            advisor = await db.get(User, sub.advisor_id)
    link = f"{settings.base_url}/form/{token}"
    deadline = (
        edict.date_closed.strftime("%d/%m/%Y") if edict.date_closed else "-"
    )
    html = (
        f"<p>Caro(a) {sub.email},</p>"
        f"<p>Dear candidate,</p>"
        f"<p>Você foi aprovado(a). Preencha o formulário de aceite "
        f"até {deadline}.</p>"
        f"<p>Please fill the acceptance form until {deadline}.</p>"
        f"<p><a href='{link}'>{link}</a></p>"
    )
    await send_mail(
        "[PreJanus] Formulário de aceite / Acceptance form",
        [sub.email],
        html,
        cc=[advisor.email] if advisor else [],
    )
    return {
        "message": "Accept form sent",
        "email_sent": True,
    }


@app.post("/submissions/{submission_id}/send-letter")
async def send_letter(
    submission_id: str, user: User = Depends(get_user)
) -> dict:
    sub = await get_submission(submission_id)
    if sub.stats != "approved":
        raise HTTPException(400, "Submission is not approved")
    if sub.letter_sent:
        raise HTTPException(400, "Letter already sent")
    edict = await get_edict(sub.edict_id)
    advisor = None
    if sub.advisor_id:
        async with SessionLocal() as db:
            advisor = await db.get(User, sub.advisor_id)
    signature = ""
    sig_path = Path(settings.signature_path)
    if sig_path.exists():
        signature = sig_path.read_text()
    html = (
        f"<h2>Carta de Aceite</h2>"
        f"<p>Prezado(a) candidato(a),</p>"
        f"<p>Informamos que sua candidatura foi aprovada no edital "
        f"{edict.title}.</p>"
        f"<p>Orientador: {advisor.name if advisor else '-'}</p>"
        f"<p>Semestre de ingresso: {sub.entry_semester}</p>"
        f"<p>Ano de ingresso: {edict.year}</p>"
        f"{signature}"
    )
    await send_mail(
        "[PreJanus] Carta de aceite",
        [sub.email],
        html,
        cc=[advisor.email] if advisor else [],
    )
    sub.letter_sent = True
    async with SessionLocal() as db:
        db.add(sub)
        await db.commit()
    return {
        "message": "Acceptance letter sent",
        "email_sent": True,
    }


# ---------------------------------------------------------------- reports


class InteractorsBody(BaseModel):
    list_of_advisors: bool = False
    relation: bool = False
    approved: bool = False
    refused: bool = False
    underreview: bool = False
    general_statistics: bool = False
    show_emails: bool = False


async def _interactors(edict_id: str) -> list[User]:
    async with SessionLocal() as db:
        subs = (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict_id)
            )
        ).scalars().all()
        sub_ids = [s.id for s in subs] or [""]
        user_ids: set[str] = set()
        for model in (Comment, Favorite, Label, PrivateNote):
            rows = (
                await db.execute(
                    select(model.user_id).where(model.submission_id.in_(sub_ids))
                )
            ).scalars().all()
            user_ids.update(rows)
        users = [
            u for u in (await db.execute(select(User))).scalars().all()
            if u.id in user_ids
        ]
    return users


@app.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: str,
    body: InteractorsBody,
    mode: str = Query("plain_text"),
    user: User = Depends(get_user),
):
    await get_edict(edict_id)
    if mode != "pdf":
        return [user_dict(u) for u in await _interactors(edict_id)]
    job_id = new_id()
    JOBS[job_id] = {"type": "pdf", "status": "processing", "path": None}
    asyncio.create_task(
        _generate_pdf(job_id, edict_id, body, user.id)
    )
    return {"job_id": job_id, "status": "processing"}


async def _generate_pdf(
    job_id: str, edict_id: str, options: InteractorsBody, author_id: str
) -> None:
    from fpdf import FPDF

    edict = await get_edict(edict_id)
    async with SessionLocal() as db:
        subs = (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict_id)
            )
        ).scalars().all()
        users = {u.id: u for u in (await db.execute(select(User))).scalars().all()}
    finished = [s for s in subs if await formsdb.get_answers(s.response_id)]
    in_progress = [s for s in subs if s not in finished]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.cell(0, 10, text=f"Relatório do Edital {edict.title}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 8, text=f"Ano: {edict.year}", new_x="LMARGIN", new_y="NEXT")
    if options.general_statistics:
        pdf.cell(0, 8, text=f"Candidaturas finalizadas: {len(finished)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, text=f"Candidaturas em preenchimento: {len(in_progress)}", new_x="LMARGIN", new_y="NEXT")
    if options.approved:
        pdf.cell(0, 8, text="Aprovados:", new_x="LMARGIN", new_y="NEXT")
        for s in subs:
            if s.stats == "approved":
                advisor = users.get(s.advisor_id)
                line = f"- {s.email} (orientador: {advisor.name if advisor else '-'})"
                if options.show_emails:
                    line += f" [{s.email}]"
                pdf.cell(0, 8, text=line, new_x="LMARGIN", new_y="NEXT")
    if options.refused:
        pdf.cell(0, 8, text="Reprovados:", new_x="LMARGIN", new_y="NEXT")
        for s in subs:
            if s.stats == "refused":
                pdf.cell(0, 8, text=f"- {s.email}", new_x="LMARGIN", new_y="NEXT")
    if options.underreview:
        pdf.cell(0, 8, text="Em avaliação:", new_x="LMARGIN", new_y="NEXT")
        for s in subs:
            if s.stats == "underreview":
                pdf.cell(0, 8, text=f"- {s.email}", new_x="LMARGIN", new_y="NEXT")
    if options.list_of_advisors:
        pdf.cell(0, 8, text="Orientadores:", new_x="LMARGIN", new_y="NEXT")
        for s in subs:
            if s.advisor_id:
                advisor = users.get(s.advisor_id)
                pdf.cell(0, 8, text=f"- {advisor.name if advisor else s.advisor_id}", new_x="LMARGIN", new_y="NEXT")
    if options.show_emails:
        pdf.cell(0, 8, text="E-mails dos participantes:", new_x="LMARGIN", new_y="NEXT")
        for u in await _interactors(edict_id):
            pdf.cell(0, 8, text=f"- {u.name} <{u.email}>", new_x="LMARGIN", new_y="NEXT")
    logo = Path(settings.logo_path)
    if logo.exists():
        try:
            pdf.image(str(logo), x=170, y=10, w=25)
        except Exception:
            pass
    path = Path(settings.tmp_dir) / f"{job_id}.pdf"
    pdf.output(str(path))
    JOBS[job_id]["status"] = "done"
    JOBS[job_id]["path"] = str(path)


@app.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(
    edict_id: str, user: User = Depends(get_user)
) -> dict:
    await get_edict(edict_id)
    job_id = new_id()
    JOBS[job_id] = {"type": "csv", "status": "processing", "path": None}
    asyncio.create_task(_generate_csv(job_id, edict_id))
    return {"job_id": job_id, "status": "processing"}


async def _generate_csv(job_id: str, edict_id: str) -> None:
    async with SessionLocal() as db:
        subs = (
            await db.execute(
                select(Submission).where(Submission.edict_id == edict_id)
            )
        ).scalars().all()
        sub_ids = [s.id for s in subs] or [""]
        biddings = (
            await db.execute(
                select(Bidding).where(Bidding.submission_id.in_(sub_ids))
            )
        ).scalars().all()
        slots = (
            await db.execute(select(Slot).where(Slot.edict_id == edict_id))
        ).scalars().all()
        users = {u.id: u for u in (await db.execute(select(User))).scalars().all()}
    teachers = sorted({b.user_id for b in biddings})
    teacher_emails = [users[t].email for t in teachers if t in users]
    slot_by_user = {s.user_id: s.amount for s in slots}
    bidding_by_pair = {(b.user_id, b.submission_id): b.bidding for b in biddings}
    sub_by_id = {s.id: s for s in subs}
    path = Path(settings.tmp_dir) / f"{job_id}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["#"] + teacher_emails)
        writer.writerow(["slots"] + [slot_by_user.get(t, "0") for t in teachers])
        for sid, sub in sub_by_id.items():
            writer.writerow(
                [sub.email] + [bidding_by_pair.get((t, sid), "") for t in teachers]
            )
    JOBS[job_id]["status"] = "done"
    JOBS[job_id]["path"] = str(path)


@app.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return await _download(job_id, "pdf", "application/pdf")


@app.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return await _download(job_id, "csv", "text/csv")


async def _download(job_id: str, kind: str, media_type: str):
    job = JOBS.get(job_id)
    if (
        job is None
        or job.get("type") != kind
        or job.get("status") != "done"
        or not job.get("path")
        or not Path(job["path"]).exists()
    ):
        raise HTTPException(404, "Report not found")
    content = Path(job["path"]).read_bytes()
    Path(job["path"]).unlink(missing_ok=True)
    JOBS.pop(job_id, None)
    return FastResponse(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{job_id}.{kind}"'},
    )
