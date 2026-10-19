import os
import re
import csv
import json
import uuid
import secrets
import smtplib
import threading
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
import requests
from oauthlib.oauth1 import Client as OAuth1Client, SIGNATURE_HMAC
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from pydantic import BaseModel

APP_ENV = os.getenv("APP_ENV", "local")
BASE_URL = os.getenv("BASE_URL", "")
SECRET_KEY = os.getenv("SECRET_KEY", "prejanus-dev-secret")
UPLOADS = "/shared/uploads"
TMPDIR = "/tmp"
HERE = os.path.dirname(os.path.abspath(__file__))


def _dsn(env: str) -> str:
    s = os.getenv(env, "")
    if "+psycopg" in s:
        s = s.replace("postgresql+psycopg://", "postgresql://")
    return s


def pj():
    return psycopg.connect(_dsn("DB_CONNECTION_STRING"), row_factory=dict_row)


def fdb():
    return psycopg.connect(_dsn("DB_CONNECTION_STRING_FORMS"), row_factory=dict_row)


# ---------------------------------------------------------------- session

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="prejanus-session")
SESSION_MAX_AGE = 8 * 3600


def read_session(request: Request) -> dict:
    raw = request.cookies.get("session")
    if not raw:
        return {}
    try:
        data = _serializer.loads(raw, max_age=SESSION_MAX_AGE)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def with_session(payload: Any, session: dict) -> JSONResponse:
    resp = JSONResponse(payload)
    resp.set_cookie(
        "session",
        _serializer.dumps(session),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return resp


# ---------------------------------------------------------------- users

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def get_user(uid: int) -> Optional[dict]:
    with pj() as c, c.cursor() as cur:
        cur.execute('SELECT * FROM "user" WHERE id = %s', (uid,))
        return cur.fetchone()


def user_out(u: dict) -> dict:
    return {
        "id": u["id"],
        "name": u["name"],
        "email": u["email"],
        "nusp": u.get("nusp"),
        "role": u["role"],
    }


def current_user(request: Request) -> dict:
    sess = read_session(request)
    uid = sess.get("user_id")
    if uid is None:
        raise HTTPException(401, "Not authenticated")
    u = get_user(uid)
    if not u:
        raise HTTPException(401, "Not authenticated")
    return u


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")
    return user


app = FastAPI(title="FastAPI", version="0.1.0")

_origins = [o.strip() for o in os.getenv("BACKEND_CORS_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    return {"message": "Hello World"}


# ---------------------------------------------------------------- helpers


def _nrm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _jtext(j: Any, lang: str = "pt") -> Any:
    if isinstance(j, dict):
        if lang in j:
            return j[lang]
        for v in j.values():
            if isinstance(v, str):
                return v
        return ""
    return j if isinstance(j, str) else ""


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(str(v))
    except Exception:
        return default


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v or "").strip().lower() in ("true", "yes", "sim", "1", "on", "y")


def _pick(vals: dict, names: List[str]) -> Any:
    for n in names:
        if n in vals and vals[n] not in (None, ""):
            return vals[n]
    return None


# ---------------------------------------------------------------- forms db


def form_sections(fcur, form_id: int, version: Optional[int] = None) -> List[dict]:
    if version is None:
        fcur.execute(
            "SELECT * FROM form_section WHERE form_id = %s AND is_active = true ORDER BY position, id",
            (form_id,),
        )
    elif version == 1:
        fcur.execute(
            "SELECT * FROM form_section WHERE form_id = %s AND (version = 1 OR version IS NULL) ORDER BY position, id",
            (form_id,),
        )
    else:
        fcur.execute(
            "SELECT * FROM form_section WHERE form_id = %s AND version = %s ORDER BY position, id",
            (form_id, version),
        )
    rows = fcur.fetchall()
    if rows:
        return rows
    fcur.execute(
        "SELECT * FROM form_section WHERE form_id = %s ORDER BY position, id", (form_id,)
    )
    return fcur.fetchall()


def section_fields(fcur, section_id: int) -> List[dict]:
    fcur.execute(
        "SELECT * FROM form_field WHERE section_id = %s ORDER BY position, id", (section_id,)
    )
    return fcur.fetchall()


def response_rows(fcur, response_id: int) -> List[dict]:
    fcur.execute(
        "SELECT r.field_id, r.value, ff.name, ff.type FROM responses r "
        "JOIN form_field ff ON ff.id = r.field_id WHERE r.response_id = %s",
        (response_id,),
    )
    return fcur.fetchall()


def accept_info(fcur, s: dict) -> dict:
    if not s.get("accept_form_id"):
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    fcur.execute("SELECT * FROM form_response WHERE id = %s", (s["accept_form_id"],))
    fr = fcur.fetchone()
    if fr and fr.get("submitted_at"):
        vals = {_nrm(r["name"]): r["value"] for r in response_rows(fcur, fr["id"])}
        return {
            "sent": "replied",
            "accept": _pick(vals, ["accept", "aceite", "decision"]),
            "comments": _pick(vals, ["comments", "observacoes", "comment"]),
            "submitted_at": fr["submitted_at"],
        }
    return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}


def submission_payload(pcur, fcur, s: dict, user: dict) -> dict:
    fcur.execute("SELECT * FROM form_response WHERE id = %s", (s["candidate_form_id"],))
    fr = fcur.fetchone() or {}
    vals = {}
    if fr.get("id"):
        vals = {_nrm(r["name"]): r["value"] for r in response_rows(fcur, fr["id"])}

    advisor = None
    if s.get("advisor_id"):
        pcur.execute('SELECT * FROM "user" WHERE id = %s', (s["advisor_id"],))
        a = pcur.fetchone()
        if a:
            advisor = {"id": a["id"], "name": a["name"], "email": a["email"]}

    pcur.execute(
        "SELECT 1 FROM favorites WHERE user_id = %s AND submission_id = %s",
        (user["id"], s["id"]),
    )
    is_fav = pcur.fetchone() is not None

    pcur.execute(
        "SELECT id, label, color FROM labels WHERE submission_id = %s AND user_id = %s "
        "AND (context_type = 'candidate' OR context_type IS NULL)",
        (s["id"], user["id"]),
    )
    labels = [
        {"id": r["id"], "label": r["label"], "color": r["color"]} for r in pcur.fetchall()
    ]

    pcur.execute(
        'SELECT DISTINCT ON (u.id) u.id, u.name, u.email, sl.slots '
        'FROM labels l JOIN "user" u ON u.id = l.user_id '
        'LEFT JOIN user_edict_slots sl ON sl.user_id = l.user_id AND sl.edict_id = %s '
        "WHERE l.submission_id = %s AND l.context_type = 'bidding' ORDER BY u.id",
        (s["edict_id"], s["id"]),
    )
    bidding = [
        {
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "slots": str(r["slots"]) if r["slots"] is not None else None,
        }
        for r in pcur.fetchall()
    ]

    pcur.execute(
        "SELECT label FROM labels WHERE submission_id = %s AND user_id = %s AND context_type = 'bidding'",
        (s["id"], user["id"]),
    )
    row = pcur.fetchone()
    my_bidding = row["label"] if row else ""

    pos_year = _pick(vals, ["poscompyear", "anoposcomp", "poscompyearscore"])
    pos_score = _pick(vals, ["poscompscore", "notaposcomp", "poscompgrade"])
    poscomp = None
    if pos_year is not None or pos_score is not None:
        poscomp = {"year": _int(pos_year), "score": str(pos_score or "")}

    return {
        "id": s["id"],
        "token": str(fr.get("token") or ""),
        "name": _pick(vals, ["name", "fullname", "nome", "nomedocandidato", "applicantname"]) or "",
        "email": fr.get("email") or "",
        "phone_number": _pick(vals, ["phonenumber", "phone", "telefone", "celular", "mobile"]) or "",
        "nationality": _pick(vals, ["nationality", "nacionalidade"]) or "",
        "personal_website": _pick(vals, ["personalwebsite", "website", "site", "personalpage"]) or "",
        "gender": _pick(vals, ["gender", "genero", "sex"]) or "",
        "advisor": advisor,
        "birth_date": _pick(
            vals, ["birthdate", "datadenascimento", "birthday", "datanascimento"]
        )
        or "",
        "graduation": {
            "country": _pick(vals, ["graduationcountry", "country", "pais", "paisdegraduacao"]) or "",
            "course": _pick(vals, ["graduationcourse", "course", "curso", "cursodegraduacao"]) or "",
            "institution": _pick(
                vals, ["graduationinstitution", "institution", "instituicao", "instituicaodegraduacao"]
            )
            or "",
            "year": _int(
                _pick(
                    vals,
                    ["graduationyear", "yearofgraduation", "anograduacao", "anodeconclusao", "conclusionyear"],
                )
                or 0
            ),
        },
        "poscomp": poscomp,
        "current_occupation": _pick(
            vals, ["currentoccupation", "occupation", "ocupacaoatual", "currentjob"]
        ),
        "research": {
            "program": _pick(vals, ["researchprogram", "program", "programa"]) or "",
            "semester": _pick(vals, ["researchsemester", "semester", "semestre"]) or "",
            "field": {
                "primary": _pick(
                    vals,
                    ["researchfieldprimary", "primaryfield", "fieldprimary", "primary", "areaprincipal"],
                )
                or "",
                "secondary": _pick(
                    vals,
                    ["researchfieldsecondary", "secondaryfield", "fieldsecondary", "secondary", "areasecundaria"],
                )
                or "",
            },
            "will_apply_scholarship": _truthy(
                _pick(vals, ["willapplyscholarship", "scholarship", "aplicarscholarship"])
            ),
            "dedication_level": _pick(
                vals, ["dedicationlevel", "dedication", "dedicacao", "niveldededicacao"]
            )
            or "",
        },
        "lattes_curriculum": _pick(vals, ["lattescurriculum", "lattes", "curriculumlattes"]) or "",
        "stats": s["stats"],
        "is_favorite": is_fav,
        "bidding_users": {"data": bidding},
        "labels": labels,
        "disabilities": _truthy(
            _pick(vals, ["disabilities", "deficiencia", "disability", "possuideficiencia"])
        ),
        "ethnicity_race": _truthy(
            _pick(vals, ["ethnicityrace", "ethnicity", "raca", "corraca", "etnia"])
        ),
        "accept": accept_info(fcur, s),
        "bidding": my_bidding,
    }


def comments_list(pcur, submission_id: int) -> List[dict]:
    pcur.execute(
        'SELECT c.*, u.name AS user_name FROM comment c JOIN "user" u ON u.id = c.user_id '
        "WHERE c.submission_id = %s ORDER BY c.created_at, c.id",
        (submission_id,),
    )
    return [
        {
            "id": r["id"],
            "user": {"id": r["user_id"], "name": r["user_name"]},
            "user_id": r["user_id"],
            "submission_id": r["submission_id"],
            "comment": r["comment"],
            "text": r["comment"],
            "type": "comment",
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in pcur.fetchall()
    ]


def _get_submission(pcur, submission_id: int) -> Optional[dict]:
    pcur.execute("SELECT * FROM submission WHERE id = %s", (submission_id,))
    return pcur.fetchone()


def _get_edict(pcur, edict_id: int) -> Optional[dict]:
    pcur.execute("SELECT * FROM edict WHERE id = %s", (edict_id,))
    return pcur.fetchone()


def _candidate_form_response(fcur, s: dict) -> Optional[dict]:
    fcur.execute("SELECT * FROM form_response WHERE id = %s", (s["candidate_form_id"],))
    return fcur.fetchone()


def find_upload(filename: str) -> Optional[str]:
    if not os.path.isdir(UPLOADS):
        return None
    for root, _, files in os.walk(UPLOADS):
        if filename in files:
            return os.path.join(root, filename)
    return None


# ---------------------------------------------------------------- auth


@app.get("/auth/login")
def login(request: Request):
    sess = read_session(request)
    dev_id = os.getenv("DEV_USER_ID")
    if APP_ENV == "local" and dev_id:
        uid = _int(dev_id)
        u = get_user(uid)
        if not u:
            raise HTTPException(500, "DEV_USER_ID configured but user does not exist")
        sess["user_id"] = uid
        return with_session(user_out(u), sess)
    if sess.get("user_id"):
        u = get_user(sess["user_id"])
        if u:
            return user_out(u)
    raise HTTPException(401, "Not authenticated")


SU_HOST = os.getenv("SENHAUNICA_OAUTH_HOST", "")
SU_KEY = os.getenv("SENHAUNICA_CONSUMER_KEY", "")
SU_SECRET = os.getenv("SENHAUNICA_CONSUMER_SECRET", "")
SU_REQ = os.getenv("SENHAUNICA_REQUEST_TOKEN_RESOURCE", "/wsauth/request")
SU_AUTH = os.getenv("SENHAUNICA_AUTHORIZE_URL", "")
SU_ACC = os.getenv("SENHAUNICA_ACCESS_TOKEN_RESOURCE", "/wsauth/access")
SU_CB = os.getenv("SENHAUNICA_CALLBACK_ID", "")


def _signed_post(url: str, token: Optional[str] = None, token_secret: Optional[str] = None,
                 verifier: Optional[str] = None):
    client = OAuth1Client(
        SU_KEY,
        client_secret=SU_SECRET,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
        signature_method=SIGNATURE_HMAC,
    )n    _, headers, _ = client.sign(url, http_method="POST")
    return requests.post(url, headers=headers, timeout=10)


def _load_whitelist() -> Optional[set]:
    path = os.path.join(HERE, "data", "nusp_whitelist.txt")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        raw = f.read()
    out = set()
    for part in re.split(r"[\n,]+", raw):
        part = part.strip()
        if part:
            out.add(part)
    return out


@app.post("/auth/login/senhaunica")
def login_senhaunica(request: Request):
    sess = read_session(request)
    oauth_token = request.query_params.get("oauth_token")
    oauth_verifier = request.query_params.get("oauth_verifier")

    if not oauth_token:
        token = None
        tsecret = None
        try:
            r = _signed_post(SU_HOST.rstrip("/") + SU_REQ)
            data = dict(p.split("=", 1) for p in r.text.split("&") if "=" in p)
            token = data.get("oauth_token")
            tsecret = data.get("oauth_token_secret")
        except Exception:
            token = None
        if not token:
            token = secrets.token_hex(16)
            tsecret = secrets.token_hex(16)
        sess["oauth_token"] = token
        sess["oauth_secret"] = tsecret
        redirect_to = f"{SU_AUTH}?oauth_token={token}&callback_id={SU_CB}"
        return with_session({"redirect_to": redirect_to}, sess)

    if not sess.get("oauth_secret") or sess.get("oauth_token") != oauth_token:
        raise HTTPException(401, "Missing request token secret in session")

    try:
        r = _signed_post(
            SU_HOST.rstrip("/") + SU_ACC,
            token=oauth_token,
            token_secret=sess["oauth_secret"],
            verifier=oauth_verifier,
        )
        data = dict(p.split("=", 1) for p in r.text.split("&") if "=" in p)
        atoken = data["oauth_token"]
        atsecret = data["oauth_token_secret"]
        r2 = _signed_post(
            SU_HOST.rstrip("/") + "/wsusuario/oauth/usuariousp",
            token=atoken,
            token_secret=atsecret,
        )
        info = r2.json()
    except Exception:
        raise HTTPException(500, "Failed to exchange tokens")

    nusp = str(info.get("loginUsuario", ""))
    whitelist = _load_whitelist()
    if whitelist is not None and nusp not in whitelist:
        raise HTTPException(403, "NUSP not in whitelist")

    email = info.get("emailPrincipalUsuario") or ""
    name = info.get("nomeUsuario") or ""
    with pj() as c, c.cursor() as cur:
        cur.execute('SELECT * FROM "user" WHERE email = %s', (email,))
        u = cur.fetchone()
        if u:
            uid = u["id"]
        else:
            cur.execute(
                'INSERT INTO "user" (email, name, role, nusp, created_at) '
                "VALUES (%s, %s, 'teacher', %s, now()) RETURNING id",
                (email, name, nusp),
            )
            uid = cur.fetchone()["id"]
    sess["user_id"] = uid
    u = get_user(uid)
    return with_session(user_out(u), sess)


# ---------------------------------------------------------------- forms


@app.get("/forms")
def list_forms(
    year: Optional[str] = None, notice: Optional[str] = None, user: dict = Depends(current_user)
):
    with fdb() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM form ORDER BY id")
        rows = cur.fetchall()
    out = []
    for r in rows:
        tags = r.get("tags") or {}
        if year is not None and (tags.get("Ano") or "") != year:
            continue
        if notice is not None and (tags.get("Edital") or "") != notice:
            continue
        out.append(
            {
                "id": r["id"],
                "title": _jtext(r["title"]),
                "description": _jtext(r["description"]),
                "tags": tags,
                "phase": r["phase"],
                "created_at": r["created_at"],
                "created_by": r.get("created_by"),
                "version": r.get("version"),
            }
        )
    return out


def _form_full(form_id: int, version: Optional[int]) -> dict:
    with fdb() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM form WHERE id = %s", (form_id,))
        f = cur.fetchone()
        if not f:
            raise HTTPException(404, "Form not found")
        sections = form_sections(cur, form_id, version)
        secs_out = []
        for sec in sections:
            fields = [
                {
                    "id": fd["id"],
                    "name": fd["name"],
                    "label": _jtext(fd["label"]),
                    "type": fd["type"],
                    "prefix": fd.get("prefix"),
                    "position": fd.get("position"),
                    "required": fd.get("required"),
                    "placeholder": fd.get("placeholder"),
                    "description": _jtext(fd["description"]),
                }
                for fd in section_fields(cur, sec["id"])
            ]
            secs_out.append(
                {
                    "id": sec["id"],
                    "title": _jtext(sec["title"]),
                    "description": _jtext(sec["description"]),
                    "position": sec.get("position"),
                    "version": sec.get("version"),
                    "is_active": sec.get("is_active"),
                    "fields": fields,
                }
            )
        return {
            "id": f["id"],
            "title": _jtext(f["title"]),
            "description": _jtext(f["description"]),
            "tags": f.get("tags") or {},
            "phase": f["phase"],
            "created_at": f["created_at"],
            "created_by": f.get("created_by"),
            "version": f.get("version"),
            "sections": secs_out,
        }


@app.get("/forms/{form_id}")
def get_form_full(form_id: int, version: Optional[int] = None, user: dict = Depends(current_user)):
    return _form_full(form_id, version)


@app.get("/forms/{form_id}/sections")
def get_form_sections(form_id: int, version: Optional[int] = None, user: dict = Depends(current_user)):
    with fdb() as c, c.cursor() as cur:
        rows = form_sections(cur, form_id, version)
    return [
        {
            "id": r["id"],
            "title": _jtext(r["title"]),
            "description": _jtext(r["description"]),
            "position": r.get("position"),
            "version": r.get("version"),
            "is_active": r.get("is_active"),
        }
        for r in rows
    ]


@app.get("/forms/{form_id}/sessions/{section_id}/fields")
def get_form_fields(form_id: int, section_id: int, user: dict = Depends(current_user)):
    with fdb() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM form_field WHERE form_id = %s AND section_id = %s ORDER BY position, id", (form_id, section_id))
        rows = cur.fetchall()
        if not rows:
            rows = section_fields(cur, section_id)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "label": _jtext(r["label"]),
            "type": r["type"],
            "prefix": r.get("prefix"),
            "position": r.get("position"),
            "required": r.get("required"),
            "placeholder": r.get("placeholder"),
            "description": _jtext(r["description"]),
        }
        for r in rows
    ]


# ---------------------------------------------------------------- edicts


@app.get("/edicts")
def list_edicts(
    type: Optional[str] = None, is_open: Optional[bool] = None, user: dict = Depends(current_user)
):
    q = "SELECT id, title, year, semester, type, is_open FROM edict"
    conds, params = [], []
    if type is not None:
        conds.append("type = %s")
        params.append(type)
    if is_open is not None:
        conds.append("is_open = %s")
        params.append(is_open)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY closed_date DESC, id DESC"
    with pj() as c, c.cursor() as cur:
        cur.execute(q, params)
        rows = cur.fetchall()
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


def _edict_detail(edict_id: int, user: dict) -> dict:
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute(
            "SELECT id, closed_date, phase FROM edict_phase WHERE edict_id = %s ORDER BY id",
            (edict_id,),
        )
        phases = [
            {"id": r["id"], "closed_date": r["closed_date"], "phase": r["phase"]}
            for r in cur.fetchall()
        ]
        cur.execute(
            "SELECT slots FROM user_edict_slots WHERE user_id = %s AND edict_id = %s",
            (user["id"], edict_id),
        )
        r = cur.fetchone()
        slots = str(r["slots"]) if r and r["slots"] is not None else "0"
    return {
        "id": e["id"],
        "title": e["title"],
        "candidate_form_id": str(e["candidate_forms"]),
        "recommender_form_id": str(e["recommenders_forms"]),
        "description": e.get("description"),
        "closed_date": e["closed_date"],
        "created_at": e.get("created_at"),
        "year": e["year"],
        "semester": e["semester"],
        "type": e["type"],
        "is_open": e["is_open"],
        "updated_at": e.get("updated_at"),
        "phase": e["phase"],
        "phases": phases,
        "slots": slots,
    }


@app.get("/edicts/{edict_id}")
def edict_detail(edict_id: int, user: dict = Depends(current_user)):
    return _edict_detail(edict_id, user)


class InsertEdict(BaseModel):
    title: str
    description: Optional[str] = None
    year: int
    semester: int
    edict_type: str
    is_open: bool
    candidate_forms: int
    recommenders_forms: int
    date_application: datetime
    date_evaluation: datetime
    date_verification: datetime
    date_closed: datetime


def _check_order(a: datetime, b: datetime, c: datetime, d: datetime):
    if not (a < b < c < d):
        raise HTTPException(422, "Dates must be in strict chronological order")


@app.post("/edicts")
def create_edict(body: InsertEdict, user: dict = Depends(require_admin)):
    _check_order(
        body.date_application, body.date_evaluation, body.date_verification, body.date_closed
    )
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO edict (title, description, candidate_forms, recommenders_forms, "
            "closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'inscricoes',%s,now(),now(),%s) RETURNING id",
            (
                body.title,
                body.description,
                str(body.candidate_forms),
                str(body.recommenders_forms),
                body.date_closed.date(),
                body.year,
                body.semester,
                body.edict_type,
                body.is_open,
                user["id"],
            ),
        )
        eid = cur.fetchone()["id"]
        for phase, dt in (
            ("inscricoes", body.date_application.date()),
            ("homologacao", body.date_evaluation.date()),
            ("avaliacao", body.date_verification.date()),
            ("encerrado", body.date_closed.date()),
        ):
            cur.execute(
                "INSERT INTO edict_phase (edict_id, closed_date, phase) VALUES (%s,%s,%s)",
                (eid, dt, phase),
            )
    return {
        "id": eid,
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
        "closed_date": body.date_closed,
    }


class EditEdict(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


@app.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: int, body: EditEdict, user: dict = Depends(require_admin)):
    _check_order(
        body.date_application, body.date_evaluation, body.date_verification, body.date_closed
    )
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute(
            "UPDATE edict SET title=%s, description=%s, year=%s, semester=%s, type=%s, "
            "closed_date=%s, updated_at=now() WHERE id=%s",
            (
                body.title,
                body.description,
                _int(body.year),
                _int(body.semester),
                body.edict_type,
                body.date_closed.date(),
                edict_id,
            ),
        )
        cur.execute(
            "SELECT id, phase FROM edict_phase WHERE edict_id = %s ORDER BY id", (edict_id,)
        )
        for r, dt in zip(
            cur.fetchall(),
            (
                body.date_application.date(),
                body.date_evaluation.date(),
                body.date_verification.date(),
                body.date_closed.date(),
            ),
        ):
            cur.execute(
                "UPDATE edict_phase SET closed_date=%s WHERE id=%s", (dt, r["id"])
            )
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


class EditEdictDate(BaseModel):
    closed_date: date


@app.post("/edicts/{edict_id}/edit-date")
def edit_edict_date(edict_id: int, body: EditEdictDate, user: dict = Depends(require_admin)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute(
            "UPDATE edict SET closed_date=%s, updated_at=now() WHERE id=%s",
            (body.closed_date, edict_id),
        )
    return {"closed_date": body.closed_date}


class AdvancePhase(BaseModel):
    id: int


PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


@app.post("/edicts/{edict_id}/advance-phase")
def advance_phase(edict_id: int, body: AdvancePhase, user: dict = Depends(require_admin)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute(
            "SELECT * FROM edict_phase WHERE id = %s AND edict_id = %s",
            (body.id, edict_id),
        )
        ph = cur.fetchone()
        if not ph:
            raise HTTPException(404, "Phase not found")
        cur.execute(
            "UPDATE edict SET phase=%s, updated_at=now() WHERE id=%s",
            (ph["phase"], edict_id),
        )
    form_phase = PHASE_TO_FORMS.get(ph["phase"])
    if form_phase:
        try:
            with fdb() as fc, fc.cursor() as fcur:
                fcur.execute(
                    "SELECT id, phase FROM change_form_phase(%s, %s::form_phase)",
                    (_int(e["candidate_forms"]), form_phase),
                )
                fc.commit()
        except Exception:
            pass
    return {"id": body.id, "label": ph["phase"]}


class CloseEdict(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


@app.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: int, body: CloseEdict, user: dict = Depends(require_admin)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        if not e["is_open"]:
            raise HTTPException(409, "Edict already closed")
        cur.execute("UPDATE edict SET is_open=false, updated_at=now() WHERE id=%s", (edict_id,))
    return {"message": "Edict closed"}


@app.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: int, user: dict = Depends(require_admin)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute("DELETE FROM edict WHERE id=%s", (edict_id,))
    return {"message": "Edict removed"}


# ---------------------------------------------------------------- mappings


def _mapping_out(r: dict) -> dict:
    return {
        "id": r["id"],
        "edict_id": r["edict_id"],
        "form_type": r["form_type"],
        "form_id": r.get("form_id"),
        "user_id": r.get("user_id"),
        "form_version": r["form_version"],
        "mapping": r["mapping"],
        "is_active": r["is_active"],
        "created_at": r.get("created_at"),
    }


def _validate_tree(fcur, form_id: int, version: int, tree: Any):
    if not isinstance(tree, dict):
        raise HTTPException(422, "Invalid mapping tree")
    sections = [s["id"] for s in form_sections(fcur, form_id, version)]
    field_ids = set()
    for sid in sections:
        field_ids.update(f["id"] for f in section_fields(fcur, sid))
    stack = [tree]
    while stack:
        node = stack.pop()
        for v in node.values():
            if v is None:
                continue
            if isinstance(v, dict) and "section" in v and "field" in v:
                if v["section"] not in sections or v["field"] not in field_ids:
                    raise HTTPException(422, "Invalid mapping reference")
            elif isinstance(v, dict):
                stack.append(v)
            else:
                raise HTTPException(422, "Invalid mapping tree")


def _tipo_form_id(e: dict, tipo: str) -> int:
    return _int(e["candidate_forms"] if tipo == "candidates" else e["recommenders_forms"])


def _create_mapping(edict_id: int, version: int, tree: dict, user: dict, tipo: str):
    ftype = "candidate" if tipo == "candidates" else "recommender"
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        form_id = _tipo_form_id(e, tipo)
        cur.execute(
            "SELECT id FROM edict_form_mappings WHERE edict_id=%s AND form_type=%s AND form_version=%s",
            (edict_id, ftype, version),
        )
        if cur.fetchone():
            raise HTTPException(409, "Mapping already exists")
        cur.execute(
            "INSERT INTO edict_form_mappings "
            "(edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
            "VALUES (%s,%s,%s,true,%s,%s,%s) RETURNING *",
            (edict_id, ftype, json.dumps(tree), str(form_id), user["id"], version),
        )
        row = cur.fetchone()
    return _mapping_out(row)


def _list_mappings(edict_id: int, tipo: str):
    ftype = "candidate" if tipo == "candidates" else "recommender"
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        cur.execute(
            "SELECT * FROM edict_form_mappings WHERE edict_id=%s AND form_type=%s ORDER BY id",
            (edict_id, ftype),
        )
        return [_mapping_out(r) for r in cur.fetchall()]


def _update_mapping(edict_id: int, version: int, mapping_id: int, tree: dict, user: dict, tipo: str):
    ftype = "candidate" if tipo == "candidates" else "recommender"
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        form_id = _tipo_form_id(e, tipo)
        cur.execute(
            "SELECT * FROM edict_form_mappings WHERE id=%s AND edict_id=%s AND form_type=%s AND form_version=%s",
            (mapping_id, edict_id, ftype, version),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Mapping not found")
        with fdb() as fc, fc.cursor() as fcur:
            _validate_tree(fcur, form_id, version, tree)
        cur.execute(
            "UPDATE edict_form_mappings SET mapping=%s WHERE id=%s",
            (json.dumps(tree), mapping_id),
        )
        cur.execute("SELECT * FROM edict_form_mappings WHERE id=%s", (mapping_id,))
        return _mapping_out(cur.fetchone())


def _delete_mapping(edict_id: int, version: int, mapping_id: int, tipo: str):
    ftype = "candidate" if tipo == "candidates" else "recommender"
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "SELECT id FROM edict_form_mappings WHERE id=%s AND edict_id=%s AND form_type=%s AND form_version=%s",
            (mapping_id, edict_id, ftype, version),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Mapping not found")
        cur.execute("DELETE FROM edict_form_mappings WHERE id=%s", (mapping_id,))
    return {"message": "Mapping deleted successfully"}


def _unmapped_versions(edict_id: int, tipo: str):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        ftype = "candidate" if tipo == "candidates" else "recommender"
        cur.execute(
            "SELECT form_version FROM edict_form_mappings WHERE edict_id=%s AND form_type=%s",
            (edict_id, ftype),
        )
        mapped = {r["form_version"] for r in cur.fetchall()}
        cur.execute(
            "SELECT candidate_form_id, recommender_form_ids FROM submission WHERE edict_id=%s",
            (edict_id,),
        )
        ids = []
        for r in cur.fetchall():
            ids.append(r["candidate_form_id"])
            rec = r.get("recommender_form_ids")
            if isinstance(rec, list):
                ids.extend(x for x in rec if isinstance(x, int))
    versions = set()
    if ids:
        with fdb() as fc, fc.cursor() as fcur:
            fcur.execute(
                "SELECT DISTINCT form_version FROM form_response WHERE id = ANY(%s) AND submitted_at IS NOT NULL",
                (ids,),
            )
            versions = {r["form_version"] for r in fcur.fetchall()}
    return sorted(v for v in versions if v not in mapped)


@app.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
def create_candidate_mapping(
    edict_id: int, version: int, tree: dict, user: dict = Depends(require_admin)
):
    return _create_mapping(edict_id, version, tree, user, "candidates")


@app.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
def create_recommender_mapping(
    edict_id: int, version: int, tree: dict, user: dict = Depends(require_admin)
):
    return _create_mapping(edict_id, version, tree, user, "recommenders")


@app.get("/edicts/{edict_id}/candidates/mappings")
def get_candidate_mappings(edict_id: int, user: dict = Depends(current_user)):
    return _list_mappings(edict_id, "candidates")


@app.get("/edicts/{edict_id}/recommenders/mappings")
def get_recommender_mappings(edict_id: int, user: dict = Depends(current_user)):
    return _list_mappings(edict_id, "recommenders")


@app.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def update_candidate_mapping(
    edict_id: int, version: int, mapping_id: int, tree: dict, user: dict = Depends(require_admin)
):
    return _update_mapping(edict_id, version, mapping_id, tree, user, "candidates")


@app.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def update_recommender_mapping(
    edict_id: int, version: int, mapping_id: int, tree: dict, user: dict = Depends(require_admin)
):
    return _update_mapping(edict_id, version, mapping_id, tree, user, "recommenders")


@app.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def delete_candidate_mapping(
    edict_id: int, version: int, mapping_id: int, user: dict = Depends(require_admin)
):
    return _delete_mapping(edict_id, version, mapping_id, "candidates")


@app.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def delete_recommender_mapping(
    edict_id: int, version: int, mapping_id: int, user: dict = Depends(require_admin)
):
    return _delete_mapping(edict_id, version, mapping_id, "recommenders")


@app.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
def unmapped_candidates(edict_id: int, user: dict = Depends(current_user)):
    return _unmapped_versions(edict_id, "candidates")


@app.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
def unmapped_recommenders(edict_id: int, user: dict = Depends(current_user)):
    return _unmapped_versions(edict_id, "recommenders")


# ---------------------------------------------------------------- submissions


@app.get("/edicts/{edict_id}/submissions")
def get_submissions(
    edict_id: int,
    stats: Optional[str] = None,
    only_favorites: bool = False,
    user: dict = Depends(current_user),
):
    with pj() as pc, pc.cursor() as pcur, fdb() as fc, fc.cursor() as fcur:
        pcur.execute("SELECT * FROM submission WHERE edict_id = %s ORDER BY id", (edict_id,))
        rows = pcur.fetchall()
        if stats is not None:
            rows = [r for r in rows if r["stats"] == stats]
        if only_favorites:
            pcur.execute(
                "SELECT submission_id FROM favorites WHERE user_id = %s", (user["id"],)
            )
            favs = {r["submission_id"] for r in pcur.fetchall()}
            rows = [r for r in rows if r["id"] in favs]
        subs = [submission_payload(pcur, fcur, r, user) for r in rows]
    return {"submissions": subs}


@app.get("/submissions/{submission_id}")
def submission_detail(
    submission_id: int, include_comments: bool = False, user: dict = Depends(current_user)
):
    with pj() as pc, pc.cursor() as pcur:
        s = _get_submission(pcur, submission_id)
    if not s:
        raise HTTPException(404, "Submission not found")

    with fdb() as fc, fc.cursor() as fcur:
        fr = _candidate_form_response(fcur, s) or {}
        vals_by_field = {}
        if fr.get("id"):
            fcur.execute(
                "SELECT field_id, value FROM responses WHERE response_id = %s", (fr["id"],)
            )
            vals_by_field = {r["field_id"]: r["value"] for r in fcur.fetchall()}
        form_id = fr.get("form_id")
        sections = form_sections(fcur, form_id, fr.get("form_version")) if form_id else []
        form_out = []
        for sec in sections:
            fields = []
            for f in section_fields(fcur, sec["id"]):
                fields.append(
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": _jtext(f["label"]),
                        "type": f["type"],
                        "prefix": f.get("prefix"),
                        "position": f.get("position"),
                        "required": f.get("required"),
                        "value": vals_by_field.get(f["id"]),
                    }
                )
            form_out.append(
                {
                    "id": sec["id"],
                    "title": _jtext(sec["title"]),
                    "description": _jtext(sec["description"]),
                    "position": sec.get("position"),
                    "fields": fields,
                }
            )

    with pj() as pc, pc.cursor() as pcur, fdb() as fc, fc.cursor() as fcur:
        summary = submission_payload(pcur, fcur, s, user)
        pcur.execute(
            "SELECT note FROM private_note WHERE user_id = %s AND submission_id = %s",
            (user["id"], s["id"]),
        )
        row = pcur.fetchone()
        summary["private_note"] = row["note"] if row else ""
        summary["semester"] = s.get("entry_semester") or ""
        summary["letter_sent"] = bool(s.get("letter_sent"))
        if include_comments:
            summary["comments"] = comments_list(pcur, s["id"])
    return {"summary": summary, "submission_form": form_out}


@app.get("/submissions/{submission_id}/files/{label}/{filename}")
def get_file(
    submission_id: int, label: str, filename: str, user: dict = Depends(current_user)
):
    with pj() as pc, pc.cursor() as pcur:
        s = _get_submission(pcur, submission_id)
    if not s:
        raise HTTPException(404, "Submission not found")
    with fdb() as fc, fc.cursor() as fcur:
        fr = _candidate_form_response(fcur, s)
        if not fr:
            raise HTTPException(404, "File not found")
        fcur.execute(
            "SELECT r.value FROM responses r JOIN form_field ff ON ff.id = r.field_id "
            "WHERE r.response_id = %s AND ff.name = %s",
            (fr["id"], label),
        )
        row = fcur.fetchone()
    if not row or row["value"] != filename:
        raise HTTPException(404, "File not found")
    path = find_upload(filename)
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "File not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------- comments


class CommentIn(BaseModel):
    comment: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@app.post("/submissions/{submission_id}/comments")
def add_comment(submission_id: int, body: CommentIn, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "SELECT s.*, e.phase AS edict_phase FROM submission s "
            "JOIN edict e ON e.id = s.edict_id WHERE s.id = %s",
            (submission_id,),
        )
        s = cur.fetchone()
        if not s:
            raise HTTPException(404, "Submission not found")
        if s["edict_phase"] != "avaliacao":
            raise HTTPException(400, "Comments are only allowed in the avaliacao phase")
        now = datetime.now()
        cur.execute(
            "INSERT INTO comment (user_id, submission_id, comment, created_at, updated_at) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (
                user["id"],
                submission_id,
                body.comment,
                body.created_at or now,
                body.updated_at or body.created_at or now,
            ),
        )
        row = cur.fetchone()
    return {
        "id": row["id"],
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": row["submission_id"],
        "comment": row["comment"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@app.get("/submissions/{submission_id}/comments")
def get_comments(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        return comments_list(cur, submission_id)


@app.delete("/submissions/comments/{comment_id}")
def remove_comment(comment_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM comment WHERE id = %s", (comment_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Comment not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(403, "Forbidden")
        cur.execute("DELETE FROM comment WHERE id = %s", (comment_id,))
    return Response(status_code=204)


# ---------------------------------------------------------------- favorites


@app.post("/submissions/{submission_id}/favorites")
def create_favorite(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute(
            "SELECT 1 FROM favorites WHERE user_id = %s AND submission_id = %s",
            (user["id"], submission_id),
        )
        if cur.fetchone():
            raise HTTPException(409, "Already a favorite")
        cur.execute(
            "INSERT INTO favorites (user_id, submission_id, created_at) VALUES (%s,%s,now())",
            (user["id"], submission_id),
        )
    return Response(status_code=201)


@app.delete("/submissions/{submission_id}/favorites")
def remove_favorite(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM favorites WHERE user_id = %s AND submission_id = %s",
            (user["id"], submission_id),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Favorite not found")
        cur.execute(
            "DELETE FROM favorites WHERE user_id = %s AND submission_id = %s",
            (user["id"], submission_id),
        )
    return Response(status_code=204)


# ---------------------------------------------------------------- labels


class LabelIn(BaseModel):
    label: str
    color: str


@app.post("/submissions/{submission_id}/labels")
def add_label(submission_id: int, body: LabelIn, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute(
            "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
            "VALUES (%s,%s,%s,%s,'candidate') RETURNING id",
            (user["id"], submission_id, body.label, body.color),
        )
        lid = cur.fetchone()["id"]
        cur.execute(
            "UPDATE labels SET color = %s WHERE user_id = %s AND label = %s",
            (body.color, user["id"], body.label),
        )
    return {
        "id": lid,
        "user": {"id": user["id"], "name": user["name"]},
        "submission_id": submission_id,
        "label": body.label,
        "color": body.color,
    }


@app.get("/submissions/{submission_id}/labels")
def get_labels(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT ON (label) id, label, color FROM labels WHERE user_id = %s "
            "ORDER BY label, id",
            (user["id"],),
        )
        labels = [
            {"id": r["id"], "label": r["label"], "color": r["color"]} for r in cur.fetchall()
        ]
    return {"labels": labels}


@app.delete("/submissions/label/{label_id}")
def remove_label(label_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM labels WHERE id = %s", (label_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Label not found")
        if row["user_id"] != user["id"]:
            raise HTTPException(403, "Forbidden")
        cur.execute("DELETE FROM labels WHERE id = %s", (label_id,))
    return Response(status_code=204)


# ---------------------------------------------------------------- private notes


class PrivateNoteIn(BaseModel):
    note: str


@app.post("/submissions/{submission_id}/private_notes")
def add_or_update_note(submission_id: int, body: PrivateNoteIn, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute(
            "INSERT INTO private_note (user_id, submission_id, note, created_at) "
            "VALUES (%s,%s,%s,now()) "
            "ON CONFLICT (user_id, submission_id) DO UPDATE SET note = EXCLUDED.note, "
            "updated_at = now()",
            (user["id"], submission_id, body.note),
        )
    return {"note": body.note}


# ---------------------------------------------------------------- views


@app.post("/submissions/{submission_id}/view")
def register_view(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        cur.execute(
            "SELECT id FROM submission_view WHERE user_id = %s AND submission_id = %s "
            "AND (created_at AT TIME ZONE 'America/Sao_Paulo')::date = %s",
            (user["id"], submission_id, today),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO submission_view (user_id, submission_id, created_at, updated_at) "
                "VALUES (%s,%s,now(),now())",
                (user["id"], submission_id),
            )
    return {"message": "view registered"}


@app.get("/submissions/{submission_id}/view")
def get_views(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        cur.execute(
            'SELECT v.*, u.name AS user_name FROM submission_view v '
            'JOIN "user" u ON u.id = v.user_id '
            "WHERE v.submission_id = %s ORDER BY v.id",
            (submission_id,),
        )
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "user": {"id": r["user_id"], "name": r["user_name"]},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in cur.fetchall()
        ]


# ---------------------------------------------------------------- slots / bidding


class SlotsIn(BaseModel):
    amount: str


@app.post("/edicts/{edict_id}/slots")
def set_slots(edict_id: int, body: SlotsIn, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
        raw = (body.amount or "").strip()
        if raw == "":
            n = 0
        else:
            try:
                n = int(raw)
            except ValueError:
                raise HTTPException(422, "Invalid amount")
            if n < 0:
                n = 0
        cur.execute(
            "INSERT INTO user_edict_slots (user_id, edict_id, slots) VALUES (%s,%s,%s) "
            "ON CONFLICT (user_id, edict_id) DO UPDATE SET slots = EXCLUDED.slots",
            (user["id"], edict_id, n),
        )
    return {"amount": str(n)}


BIDDINGS = {"decline", "available", "interested", "agreed", "interested_scholarship", ""}


@app.post("/submissions/{submission_id}/bidding")
def toggle_bidding(submission_id: int, body: dict, user: dict = Depends(current_user)):
    bidding = body.get("bidding")
    if bidding not in BIDDINGS:
        raise HTTPException(422, "Invalid bidding")
    uid = user["id"]
    if body.get("user_id") is not None and user["role"] in ADMIN_ROLES:
        uid = _int(body["user_id"])
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute(
            "DELETE FROM labels WHERE user_id = %s AND submission_id = %s AND context_type = 'bidding'",
            (uid, submission_id),
        )
        if bidding:
            cur.execute(
                "INSERT INTO labels (user_id, submission_id, label, color, context_type) "
                "VALUES (%s,%s,%s,'','bidding')",
                (uid, submission_id, bidding),
            )
    return bidding


# ---------------------------------------------------------------- selection


class StatsIn(BaseModel):
    stats: str
    user_ids: Optional[List[int]] = None


@app.post("/submissions/{submission_id}/select")
def select_stats(submission_id: int, body: StatsIn, user: dict = Depends(require_admin)):
    if body.stats not in ("approved", "refused", "underreview", "waitlist"):
        raise HTTPException(422, "Invalid stats")
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute("SELECT is_open FROM edict WHERE id = %s", (s["edict_id"],))
        e = cur.fetchone()
        if not e:
            raise HTTPException(404, "Edict not found")
        if not e["is_open"]:
            raise HTTPException(409, "Edict is closed")
        advisor_id = None
        if body.stats == "approved":
            ids = body.user_ids or []
            if len(ids) != 1:
                raise HTTPException(400, "Approved requires exactly one advisor")
            cur.execute('SELECT id FROM "user" WHERE id = %s', (ids[0],))
            if not cur.fetchone():
                raise HTTPException(400, "Advisor does not exist")
            advisor_id = ids[0]
        cur.execute(
            "UPDATE submission SET stats = %s, advisor_id = %s, updated_at = now() WHERE id = %s",
            (body.stats, advisor_id, submission_id),
        )
    return body.stats


@app.post("/submissions/{submission_id}/entry-semester")
def entry_semester(submission_id: int, body: dict, user: dict = Depends(current_user)):
    sem = str(body.get("semester", ""))
    low = sem.lower()
    if "first" in low or "primeiro" in low:
        out = "Primeiro semestre."
    elif "second" in low or "segundo" in low:
        out = "Segundo semestre."
    else:
        out = sem
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute(
            "UPDATE submission SET entry_semester = %s, updated_at = now() WHERE id = %s",
            (out, submission_id),
        )
    return out


# ---------------------------------------------------------------- mail


def send_mail(to: str, subject: str, html: str, cc: Optional[List[str]] = None,
              bcc: Optional[List[str]] = None) -> bool:
    host = os.getenv("SMTP_SERVER")
    if not host:
        return False
    port = _int(os.getenv("SMTP_PORT", "25"))
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = os.getenv("FROM_EMAIL", "prejanus@example.com")
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            if os.getenv("SMTP_USE_TLS", "").lower() in ("1", "true", "yes"):
                s.starttls()
            u = os.getenv("SMTP_USER")
            p = os.getenv("SMTP_PASSWORD")
            if u:
                s.login(u, p or "")
            s.send_message(msg)
        return True
    except Exception:
        return False


@app.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(submission_id: int, body: dict, user: dict = Depends(require_admin)):
    text = str(body.get("text", ""))
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute("SELECT phase FROM edict WHERE id = %s", (s["edict_id"],))
        e = cur.fetchone()
        if not e or e["phase"] != "homologacao":
            raise HTTPException(400, "Only allowed in homologacao phase")
    with fdb() as fc, fc.cursor() as fcur:
        fr = _candidate_form_response(fcur, s)
        if not fr:
            raise HTTPException(404, "Candidate response not found")
        fcur.execute(
            "SELECT id, current_section FROM update_form_response_section(%s, 0)",
            (fr["id"],),
        )
        fc.commit()
        token = fr["token"]
        email = fr["email"] or ""
    link = f"{BASE_URL}/form/{token}"
    send_mail(
        email,
        "Solicitacao de correcao da inscricao",
        f"<p>Prezado candidato,</p><p>Motivo: {text}</p><p>Link para correcao: {link}</p>",
        bcc=[user["email"]],
    )
    return {
        "message": "Resubmission requested",
        "email_sent": email,
    }


@app.post("/submissions/{submission_id}/send-accept")
def send_accept(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        cur.execute("SELECT * FROM edict WHERE id = %s", (s["edict_id"],))
        e = cur.fetchone()
        if not e or not e.get("accept_forms"):
            raise HTTPException(404, "Accept form not configured")
        if s["stats"] != "approved":
            raise HTTPException(400, "Submission is not approved")
        if s.get("accept_form_id"):
            raise HTTPException(400, "Accept form already sent")
        advisor = None
        if s.get("advisor_id"):
            cur.execute('SELECT * FROM "user" WHERE id = %s', (s["advisor_id"],))
            advisor = cur.fetchone()
    accept_form = _int(e["accept_forms"])
    with fdb() as fc, fc.cursor() as fcur:
        fr = _candidate_form_response(fcur, s)
        candidate_email = (fr or {}).get("email") or ""
        token = uuid.uuid4()
        fcur.execute(
            "INSERT INTO form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
            "VALUES (%s, true, false, %s, now(), %s) RETURNING id",
            (accept_form, token, datetime.combine(e["closed_date"], datetime.min.time())),
        )
        shared_id = fcur.fetchone()["id"]
        rtoken = uuid.uuid4()
        fcur.execute(
            "INSERT INTO form_response (form_id, shared_id, email, token, current_section, form_version) "
            "VALUES (%s,%s,%s,%s,0,1) RETURNING id",
            (accept_form, shared_id, candidate_email, rtoken),
        )
        resp_id = fcur.fetchone()["id"]
        fc.commit()
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "UPDATE submission SET accept_form_id = %s, updated_at = now() WHERE id = %s",
            (resp_id, submission_id),
        )
    link = f"{BASE_URL}/form/{token}"
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    send_mail(
        candidate_email,
        "Formulario de aceite / Acceptance form",
        f"<p>Prezado candidato, preencha o formulario de aceite ate {e['closed_date']}.</p>"
        f"<p>Dear candidate, please fill the acceptance form by {e['closed_date']}.</p>"
        f"<p>Link: {link}</p>",
        cc=cc,
    )
    return {"message": "Accept form sent", "email_sent": candidate_email}


@app.post("/submissions/{submission_id}/send-letter")
def send_letter(submission_id: int, user: dict = Depends(current_user)):
    with pj() as c, c.cursor() as cur:
        s = _get_submission(cur, submission_id)
        if not s:
            raise HTTPException(404, "Submission not found")
        if s["stats"] != "approved":
            raise HTTPException(400, "Submission is not approved")
        if s.get("letter_sent"):
            raise HTTPException(400, "Letter already sent")
        cur.execute("SELECT * FROM edict WHERE id = %s", (s["edict_id"],))
        e = cur.fetchone()
        advisor = None
        if s.get("advisor_id"):
            cur.execute('SELECT * FROM "user" WHERE id = %s', (s["advisor_id"],))
            advisor = cur.fetchone()
    with fdb() as fc, fc.cursor() as fcur:
        fr = _candidate_form_response(fcur, s)
        candidate_email = (fr or {}).get("email") or ""
    sig = ""
    sig_path = os.path.join(HERE, "data", "signature.png")
    if os.path.exists(sig_path):
        sig = f'<p><img src="{BASE_URL}/static/signature.png" alt="assinatura"></p>'
    cc = [advisor["email"]] if advisor and advisor.get("email") else []
    send_mail(
        candidate_email,
        "Carta de aceite",
        f"<p>Parabens! Sua inscricao foi aprovada no edital {e['title']}.</p>"
        f"<p>Orientador: {advisor['name'] if advisor else ''}</p>"
        f"<p>Semestre de ingresso: {s.get('entry_semester') or ''} - Ano: {e['year']}</p>"
        f"{sig}",
        cc=cc,
    )
    with pj() as c, c.cursor() as cur:
        cur.execute(
            "UPDATE submission SET letter_sent = true, updated_at = now() WHERE id = %s",
            (submission_id,),
        )
    return {"message": "Letter sent", "email_sent": candidate_email}


# ---------------------------------------------------------------- reports


def _build_pdf(job: str, edict_id: int, opts: dict):
    try:
        from fpdf import FPDF

        opts = opts or {}
        with pj() as pc, pc.cursor() as pcur:
            e = _get_edict(pcur, edict_id)
            pcur.execute("SELECT * FROM submission WHERE edict_id = %s", (edict_id,))
            subs = pcur.fetchall()
        finished = 0
        in_progress = 0
        with fdb() as fc, fc.cursor() as fcur:
            for s in subs:
                fcur.execute(
                    "SELECT submitted_at FROM form_response WHERE id = %s",
                    (s["candidate_form_id"],),
                )
                r = fcur.fetchone()
                if r and r["submitted_at"]:
                    finished += 1
                else:
                    in_progress += 1
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(os.path.join(HERE, "assets", "usp.png")):
            try:
                pdf.image(os.path.join(HERE, "assets", "usp.png"), 10, 10, 30)
            except Exception:
                pass
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 10, f"Relatorio do Edital: {e['title']}")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 8, f"Ano: {e['year']}")
        if opts.get("general_statistics"):
            pdf.multi_cell(0, 8, f"Candidaturas finalizadas: {finished}")
            pdf.multi_cell(0, 8, f"Candidaturas em preenchimento: {in_progress}")
        if opts.get("approved") or opts.get("relation"):
            with pj() as pc, pc.cursor() as pcur:
                pcur.execute(
                    "SELECT s.*, u.name AS advisor_name FROM submission s "
                    'LEFT JOIN "user" u ON u.id = s.advisor_id '
                    "WHERE s.edict_id = %s AND s.stats = 'approved'",
                    (edict_id,),
                )
                approved = pcur.fetchall()
            for a in approved:
                pdf.multi_cell(
                    0,
                    8,
                    f"Aprovado: {a['id']} - orientador: {a.get('advisor_name') or ''}",
                )
        if opts.get("list_of_advisors"):
            with pj() as pc, pc.cursor() as pcur:
                pcur.execute(
                    'SELECT DISTINCT u.name FROM "user" u JOIN submission s ON s.advisor_id = u.id '
                    "WHERE s.edict_id = %s",
                    (edict_id,),
                )
                for r in pcur.fetchall():
                    pdf.multi_cell(0, 8, f"Orientador: {r['name']}")
        if opts.get("show_emails"):
            with fdb() as fc, fc.cursor() as fcur:
                for s in subs:
                    fcur.execute(
                        "SELECT email FROM form_response WHERE id = %s",
                        (s["candidate_form_id"],),
                    )
                    r = fcur.fetchone()
                    if r and r["email"]:
                        pdf.multi_cell(0, 8, f"Email: {r['email']}")
        pdf.output(os.path.join(TMPDIR, f"{job}.pdf"))
    except Exception:
        pass


def _build_csv(job: str, edict_id: int):
    try:
        with pj() as pc, pc.cursor() as pcur:
            pcur.execute("SELECT * FROM submission WHERE edict_id = %s", (edict_id,))
            subs = pcur.fetchall()
            pcur.execute(
                'SELECT DISTINCT ON (u.id) u.id, u.email, sl.slots '
                'FROM labels l JOIN "user" u ON u.id = l.user_id '
                'LEFT JOIN user_edict_slots sl ON sl.user_id = l.user_id AND sl.edict_id = %s '
                "WHERE l.context_type = 'bidding' AND l.submission_id IN "
                "(SELECT id FROM submission WHERE edict_id = %s) ORDER BY u.id",
                (edict_id, edict_id),
            )
            teachers = pcur.fetchall()
        emails = [t["email"] or "" for t in teachers]
        slots = {t["id"]: (str(t["slots"]) if t["slots"] is not None else "") for t in teachers}
        with pj() as pc, pc.cursor() as pcur:
            interests = {}
            for s in subs:
                pcur.execute(
                    "SELECT user_id, label FROM labels WHERE submission_id = %s AND context_type = 'bidding'",
                    (s["id"],),
                )
                interests[s["id"]] = {r["user_id"]: r["label"] for r in pcur.fetchall()}
        sub_emails = {}
        with fdb() as fc, fc.cursor() as fcur:
            for s in subs:
                fcur.execute(
                    "SELECT email FROM form_response WHERE id = %s", (s["candidate_form_id"],)
                )
                r = fcur.fetchone()
                sub_emails[s["id"]] = (r or {}).get("email") or ""
        path = os.path.join(TMPDIR, f"{job}.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["#"] + emails)
            w.writerow(["slots"] + [slots.get(t["id"], "") for t in teachers])
            for s in subs:
                row = [sub_emails.get(s["id"], "")]
                for t in teachers:
                    row.append(interests.get(s["id"], {}).get(t["id"], ""))
                w.writerow(row)
    except Exception:
        pass


@app.post("/edicts/{edict_id}/interactors_list")
def interactors_list(
    edict_id: int,
    mode: str = "plain_text",
    body: Optional[dict] = None,
    user: dict = Depends(require_admin),
):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
    if mode == "pdf":
        job = uuid.uuid4().hex
        threading.Thread(
            target=_build_pdf, args=(job, edict_id, body or {}), daemon=True
        ).start()
        return {"job_id": job, "status": "processing"}
    with pj() as c, c.cursor() as cur:
        cur.execute(
            'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
            "SELECT user_id FROM comment WHERE submission_id IN "
            "(SELECT id FROM submission WHERE edict_id = %s) UNION "
            "SELECT user_id FROM favorites WHERE submission_id IN "
            "(SELECT id FROM submission WHERE edict_id = %s) UNION "
            "SELECT user_id FROM labels WHERE submission_id IN "
            "(SELECT id FROM submission WHERE edict_id = %s) UNION "
            "SELECT user_id FROM private_note WHERE submission_id IN "
            "(SELECT id FROM submission WHERE edict_id = %s))",
            (edict_id, edict_id, edict_id, edict_id),
        )
        return [
            {"id": r["id"], "name": r["name"], "email": r["email"]} for r in cur.fetchall()
        ]


@app.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(edict_id: int, user: dict = Depends(require_admin)):
    with pj() as c, c.cursor() as cur:
        e = _get_edict(cur, edict_id)
        if not e:
            raise HTTPException(404, "Edict not found")
    job = uuid.uuid4().hex
    threading.Thread(target=_build_csv, args=(job, edict_id), daemon=True).start()
    return {"job_id": job, "status": "processing"}


@app.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    path = os.path.join(TMPDIR, f"{job_id}.pdf")
    if not os.path.isfile(path):
        raise HTTPException(404, "Report not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"content-disposition": f'inline; filename="{job_id}.pdf"'},
        background=BackgroundTask(os.unlink, path),
    )


@app.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    path = os.path.join(TMPDIR, f"{job_id}.csv")
    if not os.path.isfile(path):
        raise HTTPException(404, "Report not found")
    return FileResponse(
        path,
        media_type="text/csv",
        headers={"content-disposition": f'inline; filename="{job_id}.csv"'},
        background=BackgroundTask(os.unlink, path),
    )
