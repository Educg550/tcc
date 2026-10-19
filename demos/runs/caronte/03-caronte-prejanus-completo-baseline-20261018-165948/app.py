"""PreJanus backend (piloto v2)."""
import csv
import json
import os
import smtplib
import uuid
from datetime import datetime, date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

import requests
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fpdf import FPDF
from oauthlib.oauth1 import Client as OAuth1Client
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


class Settings(BaseSettings):
    APP_NAME: str = "PreJanus"
    APP_ENV: str = "production"
    APP_VERSION: str = "0.1.0"
    DB_CONNECTION_STRING: str = "postgresql+psycopg://prejanus:prejanus@localhost/prejanus"
    DB_CONNECTION_STRING_FORMS: str = "postgresql+psycopg://forms:forms@localhost/forms"
    BASE_URL: str = "http://localhost"
    BACKEND_CORS_ORIGINS: str = ""
    SECRET_KEY: str = "insecure-dev-secret"
    DEV_USER_ID: Optional[int] = None
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@prejanus.local"
    SMTP_USE_TLS: bool = False
    SENHAUNICA_OAUTH_HOST: str = "http://localhost"
    SENHAUNICA_REQUEST_TOKEN_RESOURCE: str = "/wsauth/request_token"
    SENHAUNICA_AUTHORIZE_URL: str = "/wsauth/authorize"
    SENHAUNICA_ACCESS_TOKEN_RESOURCE: str = "/wsauth/access_token"
    SENHAUNICA_CALLBACK_ID: str = ""
    SENHAUNICA_CONSUMER_KEY: str = ""
    SENHAUNICA_CONSUMER_SECRET: str = ""


settings = Settings()

BASE_DIR = Path(__file__).parent
UPLOADS_DIR = Path("/shared/uploads")
TMP_DIR = Path("/tmp")

engine = create_async_engine(settings.DB_CONNECTION_STRING)
forms_engine = create_async_engine(settings.DB_CONNECTION_STRING_FORMS)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}
PHASES = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
BIDDING_VALUES = {"decline", "available", "interested", "agreed", "interested_scholarship", ""}

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

if settings.BACKEND_CORS_ORIGINS:
    origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=8 * 3600,
    same_site="lax",
    https_only=True,
)


# ---------------------------------------------------------------- helpers


async def q1(db, sql, **params):
    res = await db.execute(text(sql), params)
    return res.mappings().first()


async def qa(db, sql, **params):
    res = await db.execute(text(sql), params)
    return res.mappings().all()


async def current_user(request: Request) -> dict:
    uid = request.session.get("user_id")
    if uid is None and settings.APP_ENV == "local" and settings.DEV_USER_ID is not None:
        uid = settings.DEV_USER_ID
        request.session["user_id"] = uid
    if uid is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with SessionLocal() as db:
        u = await q1(db, 'select * from "user" where id=:id', id=uid)
    if not u:
        if settings.APP_ENV == "local" and settings.DEV_USER_ID == uid:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not exist")
        raise HTTPException(status_code=401, detail="Not authenticated")
    return dict(u)


async def require_admin(user: dict) -> dict:
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Administrative role required")
    return user


def user_payload(u: dict) -> dict:
    return {"id": u["id"], "name": u["name"], "email": u["email"], "nusp": u.get("nusp"), "role": u["role"]}


def iso(v):
    if v is None:
        return None
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def to_bool(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes", "sim", "on"}


def to_int(v, default=0):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def send_email(to: str, subject: str, html: str, cc=None, bcc=None, inline_images=None) -> None:
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)
    for cid, path in (inline_images or {}).items():
        if Path(path).exists():
            with open(path, "rb") as f:
                img = MIMEImage(f.read())
            img.add_header("Content-ID", "<%s>" % cid)
            msg.attach(img)
    rcpt = [to] + list(cc or []) + list(bcc or [])
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as s:
        if settings.SMTP_USE_TLS:
            s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.sendmail(settings.FROM_EMAIL, rcpt, msg.as_string())


def load_whitelist() -> set:
    p = BASE_DIR / "data" / "nusp_whitelist.txt"
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        for tok in line.split(","):
            if tok.strip():
                out.add(tok.strip())
    return out


# ---------------------------------------------------------------- schemas


class InsertEdictSchema(BaseModel):
    title: str
    description: Optional[str] = None
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


class CommentSchema(BaseModel):
    comment: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LabelInput(BaseModel):
    label: str
    color: str


class PrivateNoteSchema(BaseModel):
    note: str


class RequestReesendSchema(BaseModel):
    text: str


class StatsSchema(BaseModel):
    user_ids: Optional[list[int]] = None
    stats: str


class BiddingSchema(BaseModel):
    bidding: str
    user_id: Optional[int] = None


class EntrySemesterSchema(BaseModel):
    semester: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool = False
    relation: bool = False
    approved: bool = False
    refused: bool = False
    underreview: bool = False
    general_statistics: bool = False
    show_emails: bool = False


# ---------------------------------------------------------------- root


@app.get("/")
async def root():
    return {"message": "Hello World"}


# ---------------------------------------------------------------- auth


@app.get("/auth/login")
async def login(user: dict = Depends(current_user)):
    return user_payload(user)


@app.post("/auth/login/senhaunica")
async def login_senhaunica(request: Request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}
    key = settings.SENHAUNICA_CONSUMER_KEY
    secret = settings.SENHAUNICA_CONSUMER_SECRET
    host = settings.SENHAUNICA_OAUTH_HOST

    if not body.get("oauth_token"):
        url = host + settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE
        client = OAuth1Client(key, secret)
        uri, headers, req_body = client.sign(url, http_method="POST")
        resp = requests.post(uri, headers=dict(headers), data=req_body or None)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Request token failed")
        data = parse_qs(resp.text)
        token = data["oauth_token"][0]
        token_secret = data["oauth_token_secret"][0]
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = token_secret
        redirect_to = "%s?oauth_token=%s&callback_id=%s" % (
            host + settings.SENHAUNICA_AUTHORIZE_URL,
            token,
            settings.SENHAUNICA_CALLBACK_ID,
        )
        return {"redirect_to": redirect_to}

    token = body["oauth_token"]
    verifier = body.get("oauth_verifier")
    token_secret = request.session.get("oauth_token_secret")
    if not token_secret or request.session.get("oauth_token") != token:
        raise HTTPException(status_code=401, detail="Missing request token secret")
    client = OAuth1Client(
        key, secret, resource_owner_key=token, resource_owner_secret=token_secret, verifier=verifier
    )
    url = host + settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE
    uri, headers, req_body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=dict(headers), data=req_body or None)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Access token failed")
    data = parse_qs(resp.text)
    acc_token = data["oauth_token"][0]
    acc_secret = data["oauth_token_secret"][0]
    client = OAuth1Client(key, secret, resource_owner_key=acc_token, resource_owner_secret=acc_secret)
    url = host + "/wsusuario/oauth/usuariousp"
    uri, headers, req_body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=dict(headers), data=req_body or None)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="User info failed")
    info = resp.json()
    nusp = str(info.get("loginUsuario", ""))
    whitelist = load_whitelist()
    if whitelist and nusp not in whitelist:
        raise HTTPException(status_code=403, detail="NUSP not authorized")
    email = info.get("emailPrincipalUsuario")
    name = info.get("nomeUsuario") or email
    async with SessionLocal() as db:
        u = await q1(db, 'select * from "user" where email=:e', e=email)
        if not u:
            await db.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at) '
                    "values (:e, :n, 'teacher', :p, now())"
                ),
                e=email, n=name, p=nusp,
            )
            await db.commit()
            u = await q1(db, 'select * from "user" where email=:e', e=email)
        request.session["user_id"] = u["id"]
    return user_payload(dict(u))


# ---------------------------------------------------------------- forms


async def form_sections(fdb, form_id: int, version: Optional[int] = None):
    if version is None:
        rows = await qa(
            fdb,
            "select * from form_section where form_id=:f and is_active=true order by \"position\"",
            f=form_id,
        )
    elif version == 1:
        rows = await qa(
            fdb,
            'select * from form_section where form_id=:f and is_active=true '
            'and (version=:v or version is null) order by "position"',
            f=form_id, v=version,
        )
    else:
        rows = await qa(
            fdb,
            'select * from form_section where form_id=:f and is_active=true '
            'and version=:v order by "position"',
            f=form_id, v=version,
        )
    if not rows:
        rows = await qa(
            fdb, 'select * from form_section where form_id=:f order by "position"', f=form_id
        )
    return rows


def label_pt(obj) -> str:
    if isinstance(obj, dict):
        return obj.get("pt") or obj.get("en") or ""
    return str(obj or "")


@app.get("/forms")
async def get_all_forms(
    year: Optional[str] = None,
    notice: Optional[str] = None,
    user: dict = Depends(current_user),
):
    async with FormsSessionLocal() as fdb:
        sql = "select id, title, description, tags, phase, created_at, version from form where 1=1"
        params: dict = {}
        if year:
            sql += " and tags->>'Ano' ilike :y"
            params["y"] = "%" + year + "%"
        if notice:
            sql += " and tags->>'Edital' ilike :n"
            params["n"] = "%" + notice + "%"
        sql += " order by id"
        rows = await qa(fdb, sql, **params)
    return [
        {
            "id": r["id"],
            "title": label_pt(r["title"]),
            "description": label_pt(r["description"]),
            "tags": r["tags"],
            "phase": r["phase"],
            "created_at": iso(r["created_at"]),
            "version": r["version"],
        }
        for r in rows
    ]


@app.get("/forms/{form_id}")
async def get_form_full(
    form_id: int,
    version: Optional[int] = None,
    user: dict = Depends(current_user),
):
    async with FormsSessionLocal() as fdb:
        f = await q1(fdb, "select * from form where id=:i", i=form_id)
        if not f:
            raise HTTPException(status_code=404, detail="Form not found")
        sections = await form_sections(fdb, form_id, version)
        out = []
        for s in sections:
            fields = await qa(
                fdb,
                'select * from form_field where section_id=:s and is_active=true order by "position"',
                s=s["id"],
            )
            out.append(
                {
                    "id": s["id"],
                    "title": label_pt(s["title"]),
                    "description": label_pt(s["description"]),
                    "position": s["position"],
                    "is_active": s["is_active"],
                    "version": s["version"],
                    "fields": [
                        {
                            "id": fd["id"],
                            "name": fd["name"],
                            "label": label_pt(fd["label"]),
                            "type": fd["type"],
                            "prefix": fd["prefix"],
                            "description": label_pt(fd["description"]),
                            "required": fd["required"],
                            "position": fd["position"],
                        }
                        for fd in fields
                    ],
                }
            )
    return {
        "id": f["id"],
        "title": label_pt(f["title"]),
        "description": label_pt(f["description"]),
        "tags": f["tags"],
        "phase": f["phase"],
        "version": f["version"],
        "sections": out,
    }


@app.get("/forms/{form_id}/sections")
async def get_form_sections_ids(
    form_id: int,
    version: Optional[int] = None,
    user: dict = Depends(current_user),
):
    async with FormsSessionLocal() as fdb:
        sections = await form_sections(fdb, form_id, version)
    return [s["id"] for s in sections]


@app.get("/forms/{form_id}/sessions/{section_id}/fields")
async def get_form_fields(
    form_id: int,
    section_id: int,
    user: dict = Depends(current_user),
):
    async with FormsSessionLocal() as fdb:
        s = await q1(
            fdb, "select * from form_section where id=:i and form_id=:f", i=section_id, f=form_id
        )
        if not s:
            raise HTTPException(status_code=404, detail="Section not found")
        fields = await qa(
            fdb,
            'select * from form_field where section_id=:s and is_active=true order by "position"',
            s=section_id,
        )
    return [
        {
            "id": fd["id"],
            "name": fd["name"],
            "label": label_pt(fd["label"]),
            "type": fd["type"],
            "prefix": fd["prefix"],
            "description": label_pt(fd["description"]),
            "placeholder": fd["placeholder"],
            "required": fd["required"],
            "disabled": fd["disabled"],
            "position": fd["position"],
        }
        for fd in fields
    ]


# ---------------------------------------------------------------- edicts


def validate_edict_dates(a: datetime, ev: datetime, v: datetime, c: datetime):
    # phase order: inscricoes(a) < homologacao(date_evaluation) <
    # avaliacao(date_verification) < encerrado(c)
    if not (a < ev < v < c):
        raise HTTPException(status_code=422, detail="Dates must be in strict chronological order")


@app.get("/edicts")
async def get_all_edicts(
    type: Optional[str] = None,
    is_open: Optional[bool] = None,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sql = "select * from edict where 1=1"
        params: dict = {}
        if type is not None:
            sql += " and type=:t"
            params["t"] = type
        if is_open is not None:
            sql += " and is_open=:o"
            params["o"] = is_open
        sql += " order by closed_date desc"
        rows = await qa(db, sql, **params)
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


async def get_edict(db, edict_id: int) -> dict:
    e = await q1(db, "select * from edict where id=:i", i=edict_id)
    if not e:
        raise HTTPException(status_code=404, detail="Edict not found")
    return dict(e)


@app.post("/edicts")
async def create_edict(
    payload: InsertEdictSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    validate_edict_dates(
        payload.date_application, payload.date_evaluation, payload.date_verification, payload.date_closed
    )
    async with SessionLocal() as db:
        res = await db.execute(
            text(
                "insert into edict (title, description, candidate_forms, recommenders_forms, "
                "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
                "values (:t, :d, :cf, :rf, :cd, :y, :s, :ty, 'inscricoes', :o, now(), now(), :u) "
                "returning id"
            ),
            t=payload.title,
            d=payload.description,
            cf=str(payload.candidate_forms),
            rf=str(payload.recommenders_forms),
            cd=payload.date_closed.date(),
            y=payload.year,
            s=payload.semester,
            ty=payload.edict_type,
            o=payload.is_open,
            u=user["id"],
        )
        edict_id = res.scalar_one()
        phase_dates = {
            "inscricoes": payload.date_application.date(),
            "homologacao": payload.date_evaluation.date(),
            "avaliacao": payload.date_verification.date(),
            "encerrado": payload.date_closed.date(),
        }
        for ph, dt in phase_dates.items():
            await db.execute(
                text(
                    "insert into edict_phase (edict_id, closed_date, phase) values (:e, :d, :p)"
                ),
                e=edict_id, d=dt, p=ph,
            )
        await db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "is_open": payload.is_open,
        "candidate_forms": payload.candidate_forms,
        "recommenders_forms": payload.recommenders_forms,
        "date_application": iso(payload.date_application),
        "date_verification": iso(payload.date_verification),
        "date_evaluation": iso(payload.date_evaluation),
        "date_closed": iso(payload.date_closed),
        "id": edict_id,
        "closed_date": iso(payload.date_closed),
    }


@app.get("/edicts/{edict_id}")
async def get_edict_route(edict_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        e = await get_edict(db, edict_id)
        phases = await qa(
            db, "select * from edict_phase where edict_id=:e order by id", e=edict_id
        )
        slot = await q1(
            db,
            "select slots from user_edict_slots where edict_id=:e and user_id=:u",
            e=edict_id,
            u=user["id"],
        )
    return {
        "id": e["id"],
        "title": e["title"],
        "candidate_form_id": e["candidate_forms"],
        "recommender_form_id": e["recommenders_forms"],
        "description": e["description"],
        "closed_date": iso(e["closed_date"]),
        "created_at": iso(e["created_at"]),
        "year": e["year"],
        "semester": e["semester"],
        "type": e["type"],
        "is_open": e["is_open"],
        "updated_at": iso(e["updated_at"]),
        "phase": e["phase"],
        "phases": [
            {"id": p["id"], "closed_date": iso(p["closed_date"]), "phase": p["phase"]}
            for p in phases
        ],
        "slots": str(slot["slots"]) if slot and slot["slots"] is not None else "0",
    }


@app.post("/edicts/{edict_id}/edit")
async def edit_edict(
    edict_id: int,
    payload: EditEdictSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    validate_edict_dates(
        payload.date_application, payload.date_evaluation, payload.date_verification, payload.date_closed
    )
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        await db.execute(
            text(
                "update edict set title=:t, description=:d, year=:y, semester=:s, type=:ty, "
                "closed_date=:cd, updated_at=now() where id=:i"
            ),
            t=payload.title,
            d=payload.description,
            y=to_int(payload.year),
            s=to_int(payload.semester),
            ty=payload.edict_type,
            cd=payload.date_closed.date(),
            i=edict_id,
        )
        phase_dates = {
            "inscricoes": payload.date_application.date(),
            "homologacao": payload.date_evaluation.date(),
            "avaliacao": payload.date_verification.date(),
            "encerrado": payload.date_closed.date(),
        }
        for ph, dt in phase_dates.items():
            await db.execute(
                text("update edict_phase set closed_date=:d where edict_id=:e and phase=:p"),
                d=dt, e=edict_id, p=ph,
            )
        await db.commit()
    return {
        "title": payload.title,
        "description": payload.description,
        "year": payload.year,
        "semester": payload.semester,
        "edict_type": payload.edict_type,
        "date_application": iso(payload.date_application),
        "date_verification": iso(payload.date_verification),
        "date_evaluation": iso(payload.date_evaluation),
        "date_closed": iso(payload.date_closed),
    }


@app.post("/edicts/{edict_id}/edit-date")
async def edit_edict_date(
    edict_id: int,
    payload: EditEdictDateSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        await db.execute(
            text("update edict set closed_date=:d, updated_at=now() where id=:i"),
            d=payload.closed_date, i=edict_id,
        )
        await db.execute(
            text("update edict_phase set closed_date=:d where edict_id=:e and phase='encerrado'"),
            d=payload.closed_date, e=edict_id,
        )
        await db.commit()
    return {"closed_date": payload.closed_date.isoformat()}


@app.post("/edicts/{edict_id}/advance-phase")
async def advance_phase(
    edict_id: int,
    payload: AdvancePhaseEdictSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        ph = await q1(
            db,
            "select * from edict_phase where id=:i and edict_id=:e",
            i=payload.id,
            e=edict_id,
        )
        if not ph:
            raise HTTPException(status_code=404, detail="Phase not found")
        await db.execute(
            text("update edict set phase=:p, updated_at=now() where id=:i"),
            p=ph["phase"], i=edict_id,
        )
        await db.commit()
        e = await get_edict(db, edict_id)
    forms_phase = PHASE_TO_FORMS.get(ph["phase"])
    if forms_phase and e["candidate_forms"]:
        async with FormsSessionLocal() as fdb:
            await fdb.execute(
                text(
                    "select * from change_form_phase(:fid, cast(:ph as form_phase))"
                ),
                fid=int(e["candidate_forms"]),
                ph=forms_phase,
            )
            await fdb.commit()
    return {"id": ph["id"], "label": ph["phase"]}


@app.patch("/edicts/{edict_id}/close")
async def close_edict(
    edict_id: int,
    payload: CloseEdictSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    async with SessionLocal() as db:
        e = await get_edict(db, edict_id)
        if not e["is_open"]:
            raise HTTPException(status_code=409, detail="Edict already closed")
        await db.execute(
            text("update edict set is_open=false, updated_at=now() where id=:i"), i=edict_id
        )
        await db.commit()
    return {"message": "Edict closed successfully"}


@app.delete("/edicts/{edict_id}/remove")
async def remove_edict(edict_id: int, user: dict = Depends(current_user)):
    await require_admin(user)
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        await db.execute(text("delete from edict where id=:i"), i=edict_id)
        await db.commit()
    return {"message": "Edict deleted successfully"}


@app.post("/edicts/{edict_id}/slots")
async def set_user_slots(
    edict_id: int,
    payload: SlotsSchema,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        try:
            amount = int(payload.amount.strip())
        except (ValueError, AttributeError):
            raise HTTPException(status_code=422, detail="Invalid amount")
        if amount < 0:
            amount = 0
        await db.execute(
            text(
                "insert into user_edict_slots (user_id, edict_id, slots) values (:u, :e, :s) "
                "on conflict (user_id, edict_id) do update set slots=excluded.slots"
            ),
            u=user["id"], e=edict_id, s=amount,
        )
        await db.commit()
    return {"amount": str(amount)}


# ---------------------------------------------------------------- mappings


def form_type_of(tipo: str) -> str:
    if tipo == "candidates":
        return "candidate"
    if tipo == "recommenders":
        return "recommender"
    raise HTTPException(status_code=404, detail="Unknown mapping type")


def flatten_mapping(node: Any, out: dict, path: tuple = ()):
    if not isinstance(node, dict):
        return
    if "section" in node and "field" in node:
        out[path] = (node["section"], node["field"])
        return
    for k, v in node.items():
        flatten_mapping(v, out, path + (k,))


async def validate_mapping(fdb, form_id: int, version: int, tree: dict) -> None:
    sections = await form_sections(fdb, form_id, version)
    if not sections:
        sections = await form_sections(fdb, form_id, None)
    section_ids = {s["id"] for s in sections}
    flat: dict = {}
    flatten_mapping(tree, flat)
    for path, (sec, fld) in flat.items():
        if sec not in section_ids:
            raise HTTPException(status_code=422, detail="Invalid section reference")
        f = await q1(
            fdb, "select id from form_field where id=:i and section_id=:s", i=fld, s=sec
        )
        if not f:
            raise HTTPException(status_code=422, detail="Invalid field reference")


def mapping_payload(m) -> dict:
    return {
        "id": m["id"],
        "edict_id": m["edict_id"],
        "form_type": m["form_type"],
        "user_id": m["user_id"],
        "form_id": m["form_id"],
        "form_version": m["form_version"],
        "mapping": m["mapping"],
        "is_active": m["is_active"],
        "created_at": iso(m["created_at"]),
    }


@app.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
async def create_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    tree: dict,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    ft = form_type_of(tipo)
    async with SessionLocal() as db:
        e = await get_edict(db, edict_id)
        form_id = int(e["candidate_forms"] if ft == "candidate" else e["recommenders_forms"])
        existing = await q1(
            db,
            "select id from edict_form_mappings where edict_id=:e and form_type=:t and form_version=:v",
            e=edict_id, t=ft, v=version,
        )
        if existing:
            raise HTTPException(status_code=409, detail="Mapping already exists")
    async with FormsSessionLocal() as fdb:
        await validate_mapping(fdb, form_id, version, tree)
    async with SessionLocal() as db:
        res = await db.execute(
            text(
                "insert into edict_form_mappings "
                "(edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
                "values (:e, :t, cast(:m as jsonb), true, :f, :u, :v) returning id"
            ),
            e=edict_id, t=ft, m=json.dumps(tree), f=str(form_id), u=user["id"], v=version,
        )
        mid = res.scalar_one()
        await db.commit()
        m = await q1(db, "select * from edict_form_mappings where id=:i", i=mid)
    return mapping_payload(m)


@app.get("/edicts/{edict_id}/{tipo}/mappings")
async def list_mappings(edict_id: int, tipo: str, user: dict = Depends(current_user)):
    ft = form_type_of(tipo)
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        rows = await qa(
            db,
            "select * from edict_form_mappings where edict_id=:e and form_type=:t order by id",
            e=edict_id, t=ft,
        )
    return [mapping_payload(m) for m in rows]


async def find_mapping(db, edict_id, ft, version, mapping_id):
    m = await q1(
        db,
        "select * from edict_form_mappings where id=:i and edict_id=:e and form_type=:t "
        "and form_version=:v",
        i=mapping_id, e=edict_id, t=ft, v=version,
    )
    if not m:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return m


@app.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def update_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    tree: dict,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    ft = form_type_of(tipo)
    async with SessionLocal() as db:
        e = await get_edict(db, edict_id)
        m = await find_mapping(db, edict_id, ft, version, mapping_id)
        form_id = int(e["candidate_forms"] if ft == "candidate" else e["recommenders_forms"])
    async with FormsSessionLocal() as fdb:
        await validate_mapping(fdb, form_id, version, tree)
    async with SessionLocal() as db:
        await db.execute(
            text("update edict_form_mappings set mapping=cast(:m as jsonb) where id=:i"),
            m=json.dumps(tree), i=mapping_id,
        )
        await db.commit()
        m = await q1(db, "select * from edict_form_mappings where id=:i", i=mapping_id)
    return mapping_payload(m)


@app.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
async def delete_mapping(
    edict_id: int,
    tipo: str,
    version: int,
    mapping_id: int,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    ft = form_type_of(tipo)
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        await find_mapping(db, edict_id, ft, version, mapping_id)
        await db.execute(text("delete from edict_form_mappings where id=:i"), i=mapping_id)
        await db.commit()
    return {"message": "Mapping deleted successfully"}


@app.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
async def unmapped_versions(edict_id: int, tipo: str, user: dict = Depends(current_user)):
    ft = form_type_of(tipo)
    col = "candidate_form_version" if ft == "candidate" else "recommender_form_version"
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        rows = await qa(
            db,
            "select distinct %s as v from submission where edict_id=:e" % col,
            e=edict_id,
        )
        mapped = await qa(
            db,
            "select form_version from edict_form_mappings where edict_id=:e and form_type=:t",
            e=edict_id, t=ft,
        )
    mapped_set = {r["form_version"] for r in mapped}
    return sorted(r["v"] for r in rows if r["v"] not in mapped_set)


# ---------------------------------------------------------------- submissions


async def load_form_values(fdb, response_id: int) -> dict:
    rows = await qa(
        fdb,
        "select f.id as field_id, f.name, f.label, f.type, f.prefix, f.section_id, r.value "
        "from responses r join form_field f on r.field_id=f.id where r.response_id=:rid",
        rid=response_id,
    )
    return {r["field_id"]: dict(r) for r in rows}


def make_getter(mapping: dict, values: dict):
    flat: dict = {}
    flatten_mapping(mapping or {}, flat)

    def get(key: str, default=""):
        for path, (sec, fld) in flat.items():
            if path and path[-1] == key:
                row = values.get(fld)
                return row["value"] if row and row["value"] is not None else default
        return default

    return get


async def get_mapping(db, edict_id: int, ft: str, version: int) -> Optional[dict]:
    m = await q1(
        db,
        "select mapping from edict_form_mappings where edict_id=:e and form_type=:t "
        "and form_version=:v and is_active=true",
        e=edict_id, t=ft, v=version,
    )
    if not m:
        m = await q1(
            db,
            "select mapping from edict_form_mappings where edict_id=:e and form_type=:t "
            "and form_version=1 and is_active=true",
            e=edict_id, t=ft,
        )
    return m["mapping"] if m else {}



async def accept_info(fdb, sub: dict) -> dict:
    if not sub["accept_form_id"]:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    fr = await q1(fdb, "select * from form_response where id=:i", i=sub["accept_form_id"])
    if not fr or not fr["submitted_at"]:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    vals = await load_form_values(fdb, sub["accept_form_id"])
    acc = com = None
    for row in vals.values():
        if row["name"] in ("decision", "accept", "aceite") and acc is None:
            acc = row["value"]
        elif row["name"] in ("comments", "observacoes", "observations") and com is None:
            com = row["value"]
    return {
        "sent": "replied",
        "accept": acc,
        "comments": com,
        "submitted_at": iso(fr["submitted_at"]),
    }


async def build_submission(db, fdb, sub: dict, user: dict) -> dict:
    fr = await q1(fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"])
    values = await load_form_values(fdb, sub["candidate_form_id"])
    mapping = await get_mapping(db, sub["edict_id"], "candidate", sub["candidate_form_version"])
    get = make_getter(mapping, values)
    advisor = None
    if sub["advisor_id"]:
        a = await q1(db, 'select * from "user" where id=:i', i=sub["advisor_id"])
        if a:
            advisor = {"id": a["id"], "name": a["name"], "email": a["email"]}
    fav = await q1(
        db,
        "select 1 from favorites where submission_id=:s and user_id=:u",
        s=sub["id"], u=user["id"],
    )
    labels = await qa(
        db,
        "select id, label, color from labels where submission_id=:s and user_id=:u "
        "and (context_type='candidate' or context_type is null)",
        s=sub["id"], u=user["id"],
    )
    bid_rows = await qa(
        db,
        'select u.id, u.name, u.email, l.label as bidding, sl.slots from labels l '
        'join "user" u on l.user_id=u.id '
        'left join user_edict_slots sl on sl.user_id=u.id and sl.edict_id=:e '
        "where l.submission_id=:s and l.context_type='bidding'",
        e=sub["edict_id"], s=sub["id"],
    )
    bidding_users: dict = {}
    for r in bid_rows:
        bidding_users.setdefault(r["bidding"], []).append(
            {
                "id": r["id"],
                "name": r["name"],
                "email": r["email"],
                "slots": str(r["slots"]) if r["slots"] is not None else "0",
            }
        )
    poscomp = None
    if get("year") or get("score"):
        poscomp = {"year": to_int(get("year")), "score": str(get("score"))}
    return {
        "id": sub["id"],
        "token": str(fr["token"]) if fr else "",
        "name": str(get("name")),n        "email": str(get("email") or (fr["email"] if fr else "")),
        "phone_number": str(get("phone_number")),
        "nationality": str(get("nationality")),
        "personal_website": str(get("personal_website")),
        "gender": str(get("gender")),
        "advisor": advisor,
        "birth_date": str(get("birth_date")) or None,
        "graduation": {
            "country": str(get("country")),
            "course": str(get("course")),
            "institution": str(get("institution")),
            "year": to_int(get("year")),
        },
        "poscomp": poscomp,
        "current_occupation": str(get("current_occupation")) or None,
        "research": {
            "program": str(get("program")),
            "semester": str(get("semester")),
            "field": {"primary": str(get("primary")), "secondary": str(get("secondary"))},
            "will_apply_scholarship": to_bool(get("will_apply_scholarship")),
            "dedication_level": str(get("dedication_level")),
        },
        "lattes_curriculum": str(get("lattes_curriculum")),
        "stats": sub["stats"],
        "is_favorite": bool(fav),
        "bidding_users": {"data": bidding_users},
        "labels": [
            {"id": l["id"], "label": l["label"], "color": l["color"]} for l in labels
        ],
        "disabilities": to_bool(get("disabilities")),
        "ethnicity_race": to_bool(get("ethnicity_race")),
        "accept": await accept_info(fdb, sub),
    }


@app.get("/edicts/{edict_id}/submissions")
async def get_all_submissions_from_edict(
    edict_id: int,
    stats: Optional[str] = None,
    only_favorites: bool = False,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        sql = "select * from submission where edict_id=:e"
        params: dict = {"e": edict_id}
        if stats:
            sql += " and stats=:s"
            params["s"] = stats
        if only_favorites:
            sql += " and id in (select submission_id from favorites where user_id=:u)"
            params["u"] = user["id"]
        subs = await qa(db, sql, **params)
        out = []
        async with FormsSessionLocal() as fdb:
            for sub in subs:
                out.append(await build_submission(db, fdb, dict(sub), user))
    return {"submissions": out}


async def get_submission(db, submission_id: int) -> dict:
    s = await q1(db, "select * from submission where id=:i", i=submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    return dict(s)


@app.get("/submissions/{submission_id}")
async def get_submission_details(
    submission_id: int,
    include_comments: bool = False,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        async with FormsSessionLocal() as fdb:
            summary = await build_submission(db, fdb, sub, user)
            fr = await q1(
                fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"]
            )
            values = await load_form_values(fdb, sub["candidate_form_id"])
            sections = await form_sections(
                fdb, int(edict["candidate_forms"]), sub["candidate_form_version"]
            )
            form_sections_out = []
            for s in sections:
                fields = await qa(
                    fdb,
                    'select * from form_field where section_id=:sid and is_active=true '
                    'order by "position"',
                    sid=s["id"],
                )
                form_sections_out.append(
                    {
                        "id": s["id"],
                        "title": label_pt(s["title"]),
                        "fields": [
                            {
                                "id": fd["id"],
                                "name": fd["name"],
                                "label": label_pt(fd["label"]),
                                "type": fd["type"],
                                "prefix": fd["prefix"],
                                "value": (
                                    values[fd["id"]]["value"]
                                    if fd["id"] in values
                                    else None
                                ),
                            }
                            for fd in fields
                        ],
                    }
                )
            # recommendations
            recommendations = []
            rec_mapping = await get_mapping(
                db, sub["edict_id"], "recommender", sub["recommender_form_version"]
            )
            for rid in sub["recommenders_form_ids"] or []:
                rfr = await q1(fdb, "select * from form_response where id=:i", i=rid)
                if not rfr:
                    continue
                rvals = await load_form_values(fdb, rid)
                rget = make_getter(rec_mapping, rvals)
                recommendations.append(
                    {
                        "id": rid,
                        "name": str(rget("name")),
                        "email": str(rget("email") or rfr["email"] or ""),
                        "submitted_at": iso(rfr["submitted_at"]),
                    }
                )
        note = await q1(
            db,
            "select note from private_note where submission_id=:s and user_id=:u",
            s=submission_id, u=user["id"],
        )
        bidding = await q1(
            db,
            "select label from labels where submission_id=:s and user_id=:u and context_type='bidding'",
            s=submission_id, u=user["id"],
        )
        comments = []
        if include_comments:
            comments = await get_activity(db, fdb, sub)
    summary.update(
        {
            "access_email": fr["email"] if fr else None,
            "recommendations": recommendations,
            "private_note": note["note"] if note else "",
            "bidding": bidding["label"] if bidding else "",
            "entry_semester": sub["entry_semester"],
            "letter_sent": sub["letter_sent"],
            "edict_id": sub["edict_id"],
        }
    )
    resp = {"summary": summary, "submission_form": form_sections_out}
    if include_comments:
        resp["comments"] = comments
    return resp


async def get_activity(db, fdb, sub: dict) -> list:
    rows = await qa(
        db,
        'select c.*, u.name from comment c join "user" u on c.user_id=u.id '
        "where c.submission_id=:s",
        s=sub["id"],
    )
    events = [
        {
            "user": None,
            "comment": "",
            "type": "submission",
            "created_at": iso(sub["created_at"]),
            "_d": sub["created_at"],
        }
    ]
    for r in rows:
        events.append(
            {
                "user": {"id": r["user_id"], "name": r["name"]},
                "comment": r["comment"],
                "type": "comment",
                "created_at": iso(r["created_at"]),
                "_d": r["created_at"],
            }
        )
    async with FormsSessionLocal() as fdb:
        for rid in sub["recommenders_form_ids"] or []:
            rfr = await q1(fdb, "select * from form_response where id=:i", i=rid)
            if rfr and rfr["submitted_at"]:
                events.append(
                    {
                        "user": None,
                        "comment": "",
                        "type": "recommender",
                        "created_at": iso(rfr["submitted_at"]),
                        "_d": rfr["submitted_at"],
                    }
                )
        if sub["accept_form_id"]:
            afr = await q1(
                fdb, "select * from form_response where id=:i", i=sub["accept_form_id"]
            )
            if afr and afr["submitted_at"]:
                events.append(
                    {
                        "user": None,
                        "comment": "",
                        "type": "accept",
                        "created_at": iso(afr["submitted_at"]),
                        "_d": afr["submitted_at"],
                    }
                )
    events.sort(key=lambda e: (e["_d"] is None, e["_d"]))
    for e in events:
        e.pop("_d", None)
    return events


@app.get("/submissions/{submission_id}/comments")
async def get_comments(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        async with FormsSessionLocal() as fdb:
            return await get_activity(db, fdb, sub)


@app.post("/submissions/{submission_id}/comments")
async def add_comment(
    submission_id: int,
    payload: CommentSchema,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if edict["phase"] != "avaliacao":
            raise HTTPException(status_code=400, detail="Comments allowed only in avaliacao phase")
        created_at = payload.created_at or datetime.now().astimezone()
        res = await db.execute(
            text(
                "insert into comment (user_id, submission_id, comment, created_at, updated_at) "
                "values (:u, :s, :c, :ca, :ua) returning id"
            ),
            u=user["id"], s=submission_id, c=payload.comment,
            ca=created_at, ua=payload.updated_at or created_at,
        )
        cid = res.scalar_one()
        await db.commit()
    return {
        "id": cid,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "comment": payload.comment,
        "created_at": iso(created_at),
        "updated_at": iso(payload.updated_at or created_at),
    }


@app.delete("/submissions/comments/{comment_id}", status_code=204)
async def remove_comment(comment_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        c = await q1(db, "select * from comment where id=:i", i=comment_id)
        if not c:
            raise HTTPException(status_code=404, detail="Comment not found")
        if c["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Not the comment author")
        await db.execute(text("delete from comment where id=:i"), i=comment_id)
        await db.commit()
    return None


@app.post("/submissions/{submission_id}/favorites", status_code=201)
async def create_favorite(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if edict["phase"] != "avaliacao":
            raise HTTPException(status_code=400, detail="Favorites allowed only in avaliacao phase")
        ex = await q1(
            db,
            "select 1 from favorites where submission_id=:s and user_id=:u",
            s=submission_id, u=user["id"],
        )
        if ex:
            raise HTTPException(status_code=409, detail="Already favorite")
        await db.execute(
            text(
                "insert into favorites (user_id, submission_id, created_at) values (:u, :s, now())"
            ),
            u=user["id"], s=submission_id,
        )
        await db.commit()
    return "Favorite created successfully"


@app.delete("/submissions/{submission_id}/favorites", status_code=204)
async def remove_favorite(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        ex = await q1(
            db,
            "select 1 from favorites where submission_id=:s and user_id=:u",
            s=submission_id, u=user["id"],
        )
        if not ex:
            raise HTTPException(status_code=404, detail="Favorite not found")
        await db.execute(
            text("delete from favorites where submission_id=:s and user_id=:u"),
            s=submission_id, u=user["id"],
        )
        await db.commit()
    return None


@app.post("/submissions/{submission_id}/labels")
async def add_label(
    submission_id: int,
    payload: LabelInput,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if edict["phase"] != "avaliacao":
            raise HTTPException(status_code=400, detail="Labels allowed only in avaliacao phase")
        res = await db.execute(
            text(
                "insert into labels (user_id, submission_id, label, color, context_type) "
                "values (:u, :s, :l, :c, 'candidate') returning id"
            ),
            u=user["id"], s=submission_id, l=payload.label, c=payload.color,
        )
        lid = res.scalar_one()
        await db.execute(
            text(
                "update labels set color=:c where user_id=:u and label=:l "
                "and (context_type='candidate' or context_type is null)"
            ),
            u=user["id"], l=payload.label, c=payload.color,
        )
        await db.commit()
    return {
        "id": lid,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": payload.label,
    }


@app.get("/submissions/{submission_id}/labels")
async def get_labels(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        rows = await qa(
            db,
            "select distinct label, color from labels where user_id=:u "
            "and (context_type='candidate' or context_type is null) order by label",
            u=user["id"],
        )
    return {
        "labels": [
            {"id": i, "label": r["label"], "color": r["color"]}
            for i, r in enumerate(rows, start=1)
        ]
    }


@app.delete("/submissions/label/{label_id}", status_code=204)
async def remove_label(label_id: int, user: dict = Depends(current_user))):
    async with SessionLocal() as db:
        l = await q1(db, "select * from labels where id=:i", i=label_id)
        if not l:
            raise HTTPException(status_code=404, detail="Label not found")
        if l["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Not the label author")
        await db.execute(text("delete from labels where id=:i"), i=label_id)
        await db.commit()
    return None


@app.post("/submissions/{submission_id}/private_notes")
async def add_or_update_note(
    submission_id: int,
    payload: PrivateNoteSchema,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if edict["phase"] != "avaliacao":
            raise HTTPException(status_code=400, detail="Notes allowed only in avaliacao phase")
        await db.execute(
            text(
                "insert into private_note (user_id, submission_id, note, created_at, updated_at) "
                "values (:u, :s, :n, now(), now()) "
                "on conflict (user_id, submission_id) do update set note=excluded.note, "
                "updated_at=now()"
            ),
            u=user["id"], s=submission_id, n=payload.note,
        )
        await db.commit()
    return {"note": payload.note}


@app.post("/submissions/{submission_id}/view")
async def register_view(submission_id: int, user: dict = Depends(current_user)):
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        ex = await q1(
            db,
            "select id from submission_view where submission_id=:s and user_id=:u "
            "and (created_at at time zone 'America/Sao_Paulo')::date = :d",
            s=submission_id, u=user["id"], d=today,
        )
        if not ex:
            await db.execute(
                text(
                    "insert into submission_view (user_id, submission_id, created_at, updated_at) "
                    "values (:u, :s, now(), now())"
                ),
                u=user["id"], s=submission_id,
            )
            await db.commit()
    return {"message": "View registered"}


@app.get("/submissions/{submission_id}/view")
async def get_views(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        rows = await qa(
            db,
            "select user_id, created_at, updated_at from submission_view "
            "where submission_id=:s order by created_at",
            s=submission_id,
        )
    return [
        {"user_id": r["user_id"], "created_at": iso(r["created_at"]), "updated_at": iso(r["updated_at"])}
        for r in rows
    ]


@app.get("/submissions/{submission_id}/files/{label}/{filename}")
async def get_submission_file(
    submission_id: int,
    label: str,
    filename: str,
    user: dict = Depends(current_user),
):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
    async with FormsSessionLocal() as fdb:
        fields = await qa(
            fdb,
            "select * from form_field where form_id=:f and type='File'",
            f=int(edict["candidate_forms"]),
        )
        values = await load_form_values(fdb, sub["candidate_form_id"])
    target = None
    for fd in fields:
        if fd["name"] == label or label_pt(fd["label"]) == label:
            row = values.get(fd["id"])
            if row and row["value"]:
                target = row["value"]
                break
    if target is None or target != filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = None
    if UPLOADS_DIR.exists():
        for cand in UPLOADS_DIR.rglob(str(filename)):
            if cand.is_file():
                path = cand
                break
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        str(path),
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="attachment",
    )


# ---------------------------------------------------------------- decisions


@app.post("/submissions/{submission_id}/select")
async def select_stats(
    submission_id: int,
    payload: StatsSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    if payload.stats not in {"approved", "refused", "underreview", "waitlist"}:
        raise HTTPException(status_code=422, detail="Invalid stats")
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if not edict["is_open"]:
            raise HTTPException(status_code=409, detail="Edict is closed")
        advisor_id = None
        if payload.stats == "approved":
            ids = payload.user_ids or []
            if len(ids) != 1:
                raise HTTPException(status_code=422, detail="Approved requires exactly one advisor")
            adv = await q1(db, 'select * from "user" where id=:i', i=ids[0])
            if not adv:
                raise HTTPException(status_code=422, detail="Advisor not found")
            advisor_id = ids[0]
        await db.execute(
            text(
                "update submission set stats=:s, advisor_id=:a, updated_at=now() where id=:i"
            ),
            s=payload.stats, a=advisor_id, i=submission_id,
        )
        await db.commit()
    return "Submission updated to %s" % payload.stats


@app.post("/submissions/{submission_id}/bidding")
async def toggle_bidding(
    submission_id: int,
    payload: BiddingSchema,
    user: dict = Depends(current_user),
):
    if payload.bidding not in BIDDING_VALUES:
        raise HTTPException(status_code=422, detail="Invalid bidding")
    target = user["id"]
    if payload.user_id is not None and user["role"] in ADMIN_ROLES:
        target = payload.user_id
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        ex = await q1(
            db,
            "select id from labels where submission_id=:s and user_id=:u and context_type='bidding'",
            s=submission_id, u=target,
        )
        if ex:
            await db.execute(
                text("update labels set label=:l where id=:i"), l=payload.bidding, i=ex["id"]
            )
        else:
            await db.execute(
                text(
                    "insert into labels (user_id, submission_id, label, color, context_type) "
                    "values (:u, :s, :l, '', 'bidding')"
                ),
                u=target, s=submission_id, l=payload.bidding,
            )
        await db.commit()
    return "Bidding updated"


@app.post("/submissions/{submission_id}/entry-semester")
async def toggle_entry_semester(
    submission_id: int,
    payload: EntrySemesterSchema,
    user: dict = Depends(current_user),
):
    norm = {
        "primeiro": "Primeiro semestre.",
        "first": "Primeiro semestre.",
        "segundo": "Segundo semestre.",
        "second": "Segundo semestre.",
    }
    value = norm.get(payload.semester.strip().lower(), payload.semester)
    async with SessionLocal() as db:
        await get_submission(db, submission_id)
        await db.execute(
            text("update submission set entry_semester=:v, updated_at=now() where id=:i"),
            v=value, i=submission_id,
        )
        await db.commit()
    return value


# ---------------------------------------------------------------- mail


async def candidate_identity(db, fdb, sub: dict) -> tuple:
    fr = await q1(fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"])
    values = await load_form_values(fdb, sub["candidate_form_id"])
    mapping = await get_mapping(db, sub["edict_id"], "candidate", sub["candidate_form_version"])
    get = make_getter(mapping, values)
    name = str(get("name")) or (fr["email"] if fr else "")
    email = fr["email"] if fr else None
    return name, email


@app.post("/submissions/{submission_id}/reesend_submission")
async def reesend_submission(
    submission_id: int,
    payload: RequestReesendSchema,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if edict["phase"] != "homologacao":
            raise HTTPException(status_code=400, detail="Allowed only in homologacao phase")
    async with FormsSessionLocal() as fdb:
        fr = await q1(
            fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"]
        )
        if not fr:
            raise HTTPException(status_code=404, detail="Candidate response not found")
        await fdb.execute(
            text("select * from update_form_response_section(:i, 0)"), i=sub["candidate_form_id"]
        )
        await fdb.execute(
            text("update form_response set submitted_at=null where id=:i"),
            i=sub["candidate_form_id"],
        )
        await fdb.commit()
    link = "%s/form/%s" % (settings.BASE_URL, fr["token"])
    html = (
        "<p>Prezado(a) candidato(a),</p>"
        "<p>Sua inscri&ccedil;&atilde;o precisa de corre&ccedil;&atilde;o.</p>"
        "<p>Motivo: %s</p>"
        '<p>Para corrigir e reenviar, acesse: <a href="%s">%s</a></p>' % (payload.text, link, link)
    )
    send_email(
        fr["email"],
        "Solicita&ccedil;&atilde;o de corre&ccedil;&atilde;o de inscri&ccedil;&atilde;o",
        html,
        bcc=[user["email"]],
    )
    return {
        "message": "Resubmission requested",
        "email_sent": fr["email"],
    }


@app.post("/submissions/{submission_id}/send-accept")
async def send_accept_forms(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if not edict["accept_forms"]:
            raise HTTPException(status_code=404, detail="Accept form not configured")
        if sub["stats"] != "approved":
            raise HTTPException(status_code=400, detail="Candidate not approved")
        if sub["accept_form_id"]:
            raise HTTPException(status_code=400, detail="Accept form already sent")
    async with FormsSessionLocal() as fdb:
        fr = await q1(
            fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"]
        )
        token = str(uuid.uuid4())
        res = await fdb.execute(
            text(
                "insert into form_shared (form_id, unique_answers, is_public, token, created_at, "
                "expiration_at) values (:f, true, false, :tok, now(), :exp) returning id"
            ),
            f=int(edict["accept_forms"]), tok=token, exp=datetime.combine(
                edict["closed_date"], datetime.min.time()
            ),
        )
        shared_id = res.scalar_one()
        res = await fdb.execute(
            text(
                "insert into form_response (form_id, shared_id, email, token, current_section, "
                "form_version) values (:f, :sh, :e, :tok, 0, 1) returning id"
            ),
            f=int(edict["accept_forms"]), sh=shared_id, e=fr["email"], tok=str(uuid.uuid4()),
        )
        accept_form_id = res.scalar_one()
        await fdb.commit()
    async with SessionLocal() as db:
        await db.execute(
            text("update submission set accept_form_id=:a, updated_at=now() where id=:i"),
            a=accept_form_id, i=submission_id,
        )
        await db.commit()
        name, _ = await candidate_identity(db, FormsSessionLocal and fdb, sub)
    advisor = None
    if sub["advisor_id"]:
        async with SessionLocal() as db:
            a = await q1(db, 'select * from "user" where id=:i', i=sub["advisor_id"])
            advisor = a["email"] if a else None
    link = "%s/form/%s" % (settings.BASE_URL, token)
    html = (
        "<p>Prezado(a) %s,</p>"
        "<p>Parab&eacute;ns pela aprova&ccedil;&atilde;o! Preencha o formul&aacute;rio de aceite "
        "at&eacute; %s.</p>"
        '<p>Dear %s, please fill the acceptance form until %s.</p>'
        '<p><a href="%s">%s</a></p>'
        % (name, edict["closed_date"], name, edict["closed_date"], link, link)
    )
    send_email(
        fr["email"],
        "Formul&aacute;rio de aceite / Acceptance form",
        html,
        cc=[advisor] if advisor else None,
    )
    return {"message": "Accept form sent", "email_sent": fr["email"]}


@app.post("/submissions/{submission_id}/send-letter")
async def send_accept_letter(submission_id: int, user: dict = Depends(current_user)):
    async with SessionLocal() as db:
        sub = await get_submission(db, submission_id)
        edict = await get_edict(db, sub["edict_id"])
        if sub["stats"] != "approved":
            raise HTTPException(status_code=400, detail="Candidate not approved")
        if sub["letter_sent"]:
            raise HTTPException(status_code=400, detail="Letter already sent")
    async with FormsSessionLocal() as fdb:
        fr = await q1(
            fdb, "select * from form_response where id=:i", i=sub["candidate_form_id"]
        )
    async with SessionLocal() as db:
        name, _ = await candidate_identity(db, fdb, sub)
        advisor_name = None
        advisor_email = None
        if sub["advisor_id"]:
            a = await q1(db, 'select * from "user" where id=:i', i=sub["advisor_id"])
            if a:
                advisor_name = a["name"]
                advisor_email = a["email"]
    signature = BASE_DIR / "data" / "signature.png"
    html = (
        "<h2>Carta de Aceite</h2>"
        "<p>Prezado(a) %s, voc&ecirc; foi aprovado(a) no edital \"%s\".</p>"
        "<p>Orientador(a): %s</p>"
        "<p>Semestre de ingresso: %s</p>"
        "<p>Ano de ingresso: %s</p>"
        '<img src="cid:signature"/>'
        % (
            name,
            edict["title"],
            advisor_name or "-",
            sub["entry_semester"] or "-",
            edict["year"],
        )
    )
    send_email(
        fr["email"],
        "Carta de aceite / Acceptance letter",
        html,
        cc=[advisor_email] if advisor_email else None,
        inline_images={"signature": str(signature)},
    )
    async with SessionLocal() as db:
        await db.execute(
            text("update submission set letter_sent=true, updated_at=now() where id=:i"),
            i=submission_id,
        )
        await db.commit()
    return {"message": "Acceptance letter sent", "email_sent": fr["email"]}


# ---------------------------------------------------------------- reports


@app.post("/edicts/{edict_id}/interactors_list")
async def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    payload: Optional[SectionsDocument] = None,
    user: dict = Depends(current_user),
):
    await require_admin(user)
    options = payload or SectionsDocument()
    async with SessionLocal() as db:
        e = await get_edict(db, edict_id)
        rows = await qa(
            db,
            'select distinct u.id, u.name, u.email from ('
            "select user_id from comment where submission_id in "
            "(select id from submission where edict_id=:e) "
            "union select user_id from favorites where submission_id in "
            "(select id from submission where edict_id=:e) "
            "union select user_id from labels where submission_id in "
            "(select id from submission where edict_id=:e) "
            "union select user_id from private_note where submission_id in "
            "(select id from submission where edict_id=:e)) x "
            'join "user" u on u.id=x.user_id order by u.name',
            e=edict_id,
        )
        interactors = [
            {"id": r["id"], "name": r["name"], "email": r["email"]} for r in rows
        ]
    if mode != "pdf":
        return interactors
    job_id = uuid.uuid4().hex
    await generate_pdf_report(job_id, e, options, interactors)
    return {"job_id": job_id, "status": "processing"}


async def generate_pdf_report(job_id, edict, options, interactors) -> None:
    async with SessionLocal() as db:
        subs = await qa(db, "select * from submission where edict_id=:e", e=edict["id"])
        approved = []
        for s in subs:
            if s["stats"] == "approved":
                a = await q1(db, 'select name from "user" where id=:i', i=s["advisor_id"])
                approved.append((s, a["name"] if a else "-"))
        advisors = await qa(
            db,
            'select u.name, u.email, s.slots from user_edict_slots s '
            'join "user" u on u.id=s.user_id where s.edict_id=:e order by u.name',
            e=edict["id"],
        )
    async with FormsSessionLocal() as fdb:
        finished = await q1(
            fdb,
            "select count(*) as c from form_response where form_id=:f and submitted_at is not null",
            f=int(edict["candidate_forms"]),
        )
        in_progress = await q1(
            fdb,
            "select count(*) as c from form_response where form_id=:f and submitted_at is null",
            f=int(edict["candidate_forms"]),
        )
    pdf = FPDF()
    pdf.add_page()
    assets = BASE_DIR / "assets"
    if (assets / "logo.png").exists():
        pdf.image(str(assets / "logo.png"), x=10, y=8, w=40)
    if (assets / "usp.png").exists():
        pdf.image(str(assets / "usp.png"), x=160, y=8, w=40)
    pdf.ln(25)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio - Edital %s" % edict["title"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, "Ano: %s" % edict["year"], new_x="LMARGIN", new_y="NEXT")
    if options.general_statistics:
        pdf.cell(
            0,
            8,
            "Candidaturas finalizadas: %d | em preenchimento: %d"
            % (finished["c"], in_progress["c"]),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    if options.approved:
        pdf.cell(0, 8, "Aprovados:", new_x="LMARGIN", new_y="NEXT")
        for s, an in approved:
            pdf.cell(0, 6, "- aprovado (submission %d), orientador: %s" % (s["id"], an), new_x="LMARGIN", new_y="NEXT")
    if options.refused:
        pdf.cell(0, 8, "Reprovados: %d" % sum(1 for s in subs if s["stats"] == "refused"), new_x="LMARGIN", new_y="NEXT")
    if options.underreview:
        pdf.cell(0, 8, "Em revisao: %d" % sum(1 for s in subs if s["stats"] == "underreview"), new_x="LMARGIN", new_y="NEXT")
    if options.list_of_advisors:
        pdf.cell(0, 8, "Orientadores:", new_x="LMARGIN", new_y="NEXT")
        for a in advisors:
            pdf.cell(0, 6, "- %s (vagas: %s)" % (a["name"], a["slots"]), new_x="LMARGIN", new_y="NEXT")
    if options.relation:
        pdf.cell(0, 8, "Relacao de aprovados e orientadores:", new_x="LMARGIN", new_y="NEXT")
        for s, an in approved:
            pdf.cell(0, 6, "- submission %d -> %s" % (s["id"], an), new_x="LMARGIN", new_y="NEXT")
    if options.show_emails:
        pdf.cell(0, 8, "E-mails dos interatores:", new_x="LMARGIN", new_y="NEXT")
        for i in interactors:
            pdf.cell(0, 6, "- %s <%s>" % (i["name"], i["email"]), new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(TMP_DIR / ("%s.pdf" % job_id)))


@app.post("/edicts/{edict_id}/pairing-biddings")
async def pairing_biddings(edict_id: int, user: dict = Depends(current_user)):
    await require_admin(user)
    job_id = uuid.uuid4().hex
    async with SessionLocal() as db:
        await get_edict(db, edict_id)
        subs = await qa(db, "select * from submission where edict_id=:e", e=edict_id)
        teachers = await qa(
            db,
            'select distinct u.id, u.email from labels l join "user" u on u.id=l.user_id '
            "where l.context_type='bidding' and l.submission_id in "
            "(select id from submission where edict_id=:e) order by u.email",
            e=edict_id,
        )
        slots = {
            r["user_id"]: r["slots"]
            for r in await qa(
                db,
                "select user_id, slots from user_edict_slots where edict_id=:e",
                e=edict_id,
            )
        }
        bid = {}
        for s in subs:
            rows = await qa(
                db,
                'select l.user_id, l.label from labels l where l.submission_id=:s '
                "and l.context_type='bidding'",
                s=s["id"],
            )
            bid[s["id"]] = {r["user_id"]: r["label"] for r in rows}
    async with FormsSessionLocal() as fdb:
        emails = {}
        for s in subs:
            fr = await q1(fdb, "select email from form_response where id=:i", i=s["candidate_form_id"])
            emails[s["id"]] = fr["email"] if fr else ""
    path = TMP_DIR / ("%s.csv" % job_id)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        teacher_emails = [t["email"] for t in teachers]
        w.writerow(["#"] + teacher_emails)
        w.writerow(["slots"] + [str(slots.get(t["id"]) or "0") for t in teachers])
        for s in subs:
            w.writerow([emails.get(s["id"], "")] + [bid.get(s["id"], {}).get(t["id"], "") for t in teachers])
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, ext: str, media_type: str):
    path = TMP_DIR / ("%s%s" % (job_id, ext))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        str(path),
        media_type=media_type,
        filename=path.name,
        content_disposition_type="inline",
        background=BackgroundTask(lambda p=str(path): os.remove(p)),
    )


@app.get("/edicts/download_pdf/{job_id}")
async def download_pdf(job_id: str):
    return _download(job_id, ".pdf", "application/pdf")


@app.get("/edicts/download_csv/{job_id}")
async def download_csv(job_id: str):
    return _download(job_id, ".csv", "text/csv")
