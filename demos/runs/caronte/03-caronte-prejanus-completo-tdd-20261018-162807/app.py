import csv
import io
import json
import os
import uuid
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Request, Response, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import (Boolean, Column, Date, Integer, String, Text, UniqueConstraint, create_engine, select)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

APP_ENV = os.getenv("APP_ENV", "local")
DEV_USER_ID = os.getenv("DEV_USER_ID")
SECRET_KEY = os.getenv("SECRET_KEY", "prejanus-dev-secret")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8083")

TZ = ZoneInfo("America/Sao_Paulo")
ADMIN_ROLES = {"administrator", "secretary", "coordinator"}
PHASE_TO_FORMS = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}
BIDDING_VALUES = {"decline", "available", "interested", "agreed", "interested_scholarship", ""}
STATS_VALUES = {"approved", "refused", "underreview", "waitlist"}

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    nusp = Column(String)
    role = Column(String)


class Edict(Base):
    __tablename__ = "edicts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text, default="")
    year = Column(Integer)
    semester = Column(Integer)
    edict_type = Column(String)
    is_open = Column(Boolean, default=True)
    candidate_form_id = Column(Integer)
    recommender_form_id = Column(Integer)
    date_application = Column(Date)
    date_evaluation = Column(Date)
    date_verification = Column(Date)
    date_closed = Column(Date)
    current_phase_id = Column(Integer)
    author_id = Column(Integer)


class Phase(Base):
    __tablename__ = "phases"
    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer)
    label = Column(String)


class Mapping(Base):
    __tablename__ = "mappings"
    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer)
    tipo = Column(String)
    version = Column(Integer)
    author_id = Column(Integer)
    form_id = Column(Integer)
    tree = Column(Text)
    active = Column(Boolean, default=True)


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    edict_id = Column(Integer)
    form_id = Column(Integer)
    version = Column(Integer)
    name = Column(String)
    email = Column(String)
    stats = Column(String, default="underreview")
    advisor_id = Column(Integer)
    entry_semester = Column(String)
    accept_form_id = Column(Integer)
    letter_sent = Column(Boolean, default=False)
    answers = Column(Text, default="{}")


class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    edict_id = Column(Integer)
    amount = Column(String, default="0")
    __table_args__ = (UniqueConstraint("user_id", "edict_id"),)


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    comment = Column(Text)
    created_at = Column(String)


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)


class Label(Base):
    __tablename__ = "labels"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    label = Column(String)
    color = Column(String)
    context = Column(String, default="candidate")


class PrivateNote(Base):
    __tablename__ = "private_notes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    note = Column(Text)
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)


class View(Base):
    __tablename__ = "views"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    view_date = Column(Date)
    __table_args__ = (UniqueConstraint("user_id", "submission_id", "view_date"),)


class Bidding(Base):
    __tablename__ = "biddings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    submission_id = Column(Integer)
    bidding = Column(String)
    __table_args__ = (UniqueConstraint("user_id", "submission_id"),)


# ---- Forms database (own connection) ----

FormsBase = declarative_base()


class Form(FormsBase):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    tags = Column(Text, default="{}")
    phase = Column(String, default="Registration")


class Section(FormsBase):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    form_id = Column(Integer)
    name = Column(String)
    position = Column(Integer)
    version = Column(Integer)
    active = Column(Boolean, default=True)


class Field(FormsBase):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer)
    name = Column(String)
    label = Column(String)
    type = Column(String, default="text")
    prefix = Column(String)
    position = Column(Integer)


PREJANUS_DB = os.getenv("PREJANUS_DATABASE_URL", "sqlite:////tmp/prejanus.db")
FORMS_DB = os.getenv("FORMS_DATABASE_URL", "sqlite:////tmp/forms.db")

engine = create_engine(PREJANUS_DB, connect_args={"check_same_thread": False} if PREJANUS_DB.startswith("sqlite") else {})
forms_engine = create_engine(FORMS_DB, connect_args={"check_same_thread": False} if FORMS_DB.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)
FormsSessionLocal = sessionmaker(bind=forms_engine)

JOBS_DIR = "/tmp/prejanus_jobs"
UPLOADS_DIR = "/tmp/uploads"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_fdb():
    db = FormsSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="PreJanus Back")

origins = [o for o in os.getenv("BACKEND_CORS_ORIGINS", "").split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

serializer = URLSafeTimedSerializer(SECRET_KEY)


def read_session(request: Request) -> dict:
    raw = request.cookies.get("session")
    if not raw:
        return {}
    try:
        return serializer.loads(raw, max_age=8 * 3600)
    except Exception:
        return {}


def write_session(response: Response, data: dict, request: Request):
    response.set_cookie(
        "session",
        serializer.dumps(data),
        max_age=8 * 3600,
        samesite="lax",
        secure=request.url.scheme == "https",
        httponly=True,
    )


def user_dict(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "nusp": u.nusp, "role": u.role}


def current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    uid = read_session(request).get("user_id")
    if uid is None:
        return None
    return db.get(User, uid)


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    u = current_user(request, db)
    if u is None:
        raise HTTPException(401, "Sessao invalida")
    return u


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    u = require_user(request, db)
    if u.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    return u


# ---- seeding ----


def make_pdf_bytes(lines) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    for ln in lines:
        pdf.multi_cell(0, 8, str(ln))
    return bytes(pdf.output())


def seed():
    os.makedirs(JOBS_DIR, exist_ok=True)
    Base.metadata.create_all(engine)
    FormsBase.metadata.create_all(forms_engine)
    pdb = SessionLocal()
    fdb = FormsSessionLocal()
    try:
        if not pdb.execute(select(User.id)).first():
            pdb.add(User(id=1, name="Administrador PreJanus", email="admin@example.com", nusp="1111111", role="administrator"))
            pdb.add(User(id=2, name="Professora Docente", email="teacher@example.com", nusp="2222222", role="teacher"))
            pdb.add(User(id=3, name="Professor Orientador", email="advisor@example.com", nusp="3333333", role="teacher"))
            pdb.commit()
        if not fdb.execute(select(Form.id)).first():
            fdb.add(Form(id=1, title="Formulario de Candidatura", tags=json.dumps({"Ano": "2026", "Edital": "1"}), phase="Registration"))
            fdb.add(Section(id=1, form_id=1, name="Dados Pessoais", position=1, version=None, active=True))
            fdb.add(Section(id=2, form_id=1, name="Formacao", position=2, version=None, active=True))
            fdb.add(Field(id=1, section_id=1, name="nome", label="Nome completo", type="text", prefix="", position=1))
            fdb.add(Field(id=2, section_id=1, name="email", label="E-mail", type="email", prefix="", position=2))
            fdb.add(Field(id=3, section_id=1, name="arquivo", label="Curriculo", type="file", prefix="", position=3))
            fdb.add(Field(id=4, section_id=2, name="formacao", label="Formacao", type="textarea", prefix="", position=1))
            fdb.add(Field(id=5, section_id=2, name="poscomp", label="POSCOMP", type="number", prefix="", position=2))
            fdb.commit()
        if not pdb.execute(select(Edict.id)).first():
            e = Edict(
                id=1, title="Edital de Mestrado 2026", description="Edital de exemplo",
                year=2026, semester=1, edict_type="mestrado", is_open=True,
                candidate_form_id=1, recommender_form_id=1,
                date_application=date(2026, 1, 1), date_evaluation=date(2026, 2, 1),
                date_verification=date(2026, 3, 1), date_closed=date(2026, 4, 1),
                author_id=1,
            )
            pdb.add(e)
            pdb.flush()
            for lbl in ("inscricoes", "homologacao", "avaliacao", "encerrado"):
                pdb.add(Phase(edict_id=e.id, label=lbl))
            pdb.flush()
            phases = pdb.execute(select(Phase).where(Phase.edict_id == e.id)).scalars().all()
            e.current_phase_id = next(p.id for p in phases if p.label == "avaliacao")
            answers1 = {"1": "Candidato Aprovado", "2": "cand1@example.com", "3": "documento.pdf", "4": "Bacharelado em Ciencia da Computacao", "5": "50"}
            answers2 = {"1": "Candidato Pendente", "2": "cand2@example.com", "3": "documento.pdf", "4": "Bacharelado em Matematica", "5": ""}
            pdb.add(Submission(id=1, edict_id=e.id, form_id=1, version=1, name="Candidato Aprovado", email="cand1@example.com", stats="approved", advisor_id=3, entry_semester="Primeiro semestre.", answers=json.dumps(answers1)))
            pdb.add(Submission(id=2, edict_id=e.id, form_id=1, version=1, name="Candidato Pendente", email="cand2@example.com", stats="underreview", answers=json.dumps(answers2)))
            pdb.commit()
            pdf_bytes = make_pdf_bytes(["Documento do candidato", "PreJanus"])
            for sid in (1, 2):
                d = os.path.join(UPLOADS_DIR, str(sid))
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, "documento.pdf"), "wb") as f:
                    f.write(pdf_bytes)
    finally:
        pdb.close()
        fdb.close()


seed()


# ---- helpers ----


def parse_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def check_dates(da, de, dv, dc):
    if not (da < de < dv < dc):
        raise HTTPException(400, "Datas fora de ordem cronologica")


def get_edict_or_404(db: Session, edict_id: int) -> Edict:
    e = db.get(Edict, edict_id)
    if not e:
        raise HTTPException(404, "Edital nao encontrado")
    return e


def get_submission_or_404(db: Session, submission_id: int) -> Submission:
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(404, "Inscricao nao encontrada")
    return s


def current_phase_label(db: Session, e: Edict) -> str:
    p = db.get(Phase, e.current_phase_id) if e.current_phase_id else None
    return p.label if p else "inscricoes"


def edict_phases(db: Session, e: Edict):
    return db.execute(select(Phase).where(Phase.edict_id == e.id).order_by(Phase.id)).scalars().all()


def edict_dict(db: Session, e: Edict, user: Optional[User]) -> dict:
    slot = None
    if user is not None:
        slot = db.execute(select(Slot).where(Slot.edict_id == e.id, Slot.user_id == user.id)).scalar_one_or_none()
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description or "",
        "year": e.year,
        "semester": e.semester,
        "edict_type": e.edict_type,
        "is_open": bool(e.is_open),
        "candidate_form_id": e.candidate_form_id,
        "recommender_form_id": e.recommender_form_id,
        "date_application": str(e.date_application) if e.date_application else None,
        "date_evaluation": str(e.date_evaluation) if e.date_evaluation else None,
        "date_verification": str(e.date_verification) if e.date_verification else None,
        "date_closed": str(e.date_closed) if e.date_closed else None,
        "current_phase": current_phase_label(db, e),
        "phases": [{"id": p.id, "label": p.label} for p in edict_phases(db, e)],
        "slots": slot.amount if slot else "0",
    }


def form_sections(fdb: Session, form_id: int, version: Optional[int] = None):
    q = select(Section).where(Section.form_id == form_id)
    if version is None:
        q = q.where(Section.active.is_(True))
    elif version == 1:
        q = q.where((Section.version == 1) | (Section.version.is_(None)))
    else:
        q = q.where(Section.version == version)
    secs = fdb.execute(q.order_by(Section.position)).scalars().all()
    if not secs:
        secs = fdb.execute(select(Section).where(Section.form_id == form_id).order_by(Section.position)).scalars().all()
    return list(secs)


def section_fields(fdb: Session, section_id: int):
    return fdb.execute(select(Field).where(Field.section_id == section_id).order_by(Field.position)).scalars().all()


def submission_form(fdb: Session, s: Submission) -> list:
    answers = json.loads(s.answers or "{}")
    out = []
    for sec in form_sections(fdb, s.form_id, s.version):
        fields = []
        for f in section_fields(fdb, sec.id):
            fields.append({
                "id": f.id, "name": f.name, "label": f.label,
                "type": f.type, "prefix": f.prefix,
                "value": answers.get(str(f.id), ""),
            })
        out.append({"id": sec.id, "name": sec.name, "fields": fields})
    return out


def submission_summary(db: Session, fdb: Session, s: Submission, user: Optional[User]) -> dict:
    answers = json.loads(s.answers or "{}")
    fav = False
    note = ""
    labels = []
    bidding = ""
    if user is not None:
        fav = db.execute(select(Favorite).where(Favorite.submission_id == s.id, Favorite.user_id == user.id)).scalar_one_or_none() is not None
        n = db.execute(select(PrivateNote).where(PrivateNote.submission_id == s.id, PrivateNote.user_id == user.id)).scalar_one_or_none()
        note = n.note if n else ""
        labels = [l.label for l in db.execute(select(Label).where(Label.submission_id == s.id, Label.user_id == user.id)).scalars()]
        b = db.execute(select(Bidding).where(Bidding.submission_id == s.id, Bidding.user_id == user.id)).scalar_one_or_none()
        bidding = b.bidding if b else ""
    advisor = db.get(User, s.advisor_id) if s.advisor_id else None
    accept = "not_sent"
    if s.accept_form_id:
        accept = "sent"
    return {
        "id": s.id,
        "name": s.name,
        "email": s.email,
        "formation": answers.get("4", ""),
        "poscomp": answers.get("5", ""),
        "research": "",
        "recommendations": [],
        "stats": s.stats,
        "advisor": advisor.name if advisor else None,
        "favorite": fav,
        "labels": labels,
        "bidding": bidding,
        "interest": bidding,
        "private_note": note,
        "accept": accept,
        "semester": s.entry_semester or "",
        "letter_sent": bool(s.letter_sent),
    }


def submission_item(db: Session, s: Submission, user: Optional[User]) -> dict:
    fav = False
    labels = []
    bidding = ""
    if user is not None:
        fav = db.execute(select(Favorite).where(Favorite.submission_id == s.id, Favorite.user_id == user.id)).scalar_one_or_none() is not None
        labels = [l.label for l in db.execute(select(Label).where(Label.submission_id == s.id, Label.user_id == user.id)).scalars()]
        b = db.execute(select(Bidding).where(Bidding.submission_id == s.id, Bidding.user_id == user.id)).scalar_one_or_none()
        bidding = b.bidding if b else ""
    advisor = db.get(User, s.advisor_id) if s.advisor_id else None
    return {
        "id": s.id, "name": s.name, "email": s.email, "version": s.version,
        "stats": s.stats, "favorite": fav, "labels": labels, "bidding": bidding,
        "advisor": advisor.name if advisor else None,
        "entry_semester": s.entry_semester or "",
        "accept": "sent" if s.accept_form_id else "not_sent",
        "letter_sent": bool(s.letter_sent),
    }


# ---- root / auth ----


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/auth/login")
def auth_login(request: Request, response: Response, db: Session = Depends(get_db)):
    sess = read_session(request)
    uid = sess.get("user_id")
    if uid is not None:
        u = db.get(User, uid)
        if u:
            return user_dict(u)
    if APP_ENV == "local":
        dev = DEV_USER_ID
        uid = int(dev) if dev else 1
        u = db.get(User, uid)
        if not u:
            raise HTTPException(500, "DEV_USER_ID aponta para usuario inexistente")
        write_session(response, {"user_id": u.id}, request)
        return user_dict(u)
    raise HTTPException(401, "Sem sessao valida")


@app.post("/auth/login/senhaunica")
def senhaunica(request: Request, response: Response, body: dict = Body(default={}), db: Session = Depends(get_db)):
    oauth_token = body.get("oauth_token")
    if not oauth_token:
        redirect_to = os.getenv("SENHA_UNICA_LOGIN_URL", "https://uspdigital.usp.br/uspservice/autenticacao/oauth/authorize")
        write_session(response, {"request_secret": uuid.uuid4().hex}, request)
        return {"redirect_to": redirect_to}
    sess = read_session(request)
    if not sess.get("request_secret"):
        raise HTTPException(401, "Sem segredo de request token na sessao")
    return {"redirect_to": os.getenv("BASE_URL", BASE_URL)}


# ---- forms ----


@app.get("/forms")
def list_forms(year: Optional[str] = None, notice: Optional[str] = None, fdb: Session = Depends(get_fdb)):
    forms = fdb.execute(select(Form)).scalars().all()
    out = []
    for f in forms:
        tags = json.loads(f.tags or "{}")
        if year is not None and str(tags.get("Ano", "")) != str(year):
            continue
        if notice is not None and str(tags.get("Edital", "")) != str(notice):
            continue
        out.append({"id": f.id, "title": f.title, "tags": tags, "phase": f.phase})
    return out


@app.get("/forms/{form_id}")
def get_form(form_id: int, version: Optional[int] = None, fdb: Session = Depends(get_fdb)):
    f = fdb.get(Form, form_id)
    if not f:
        raise HTTPException(404, "Formulario nao encontrado")
    secs = []
    for sec in form_sections(fdb, form_id, version):
        secs.append({
            "id": sec.id, "name": sec.name, "position": sec.position,
            "fields": [{"id": x.id, "name": x.name, "label": x.label, "type": x.type, "prefix": x.prefix, "position": x.position} for x in section_fields(fdb, sec.id)],
        })
    return {"id": f.id, "title": f.title, "tags": json.loads(f.tags or "{}"), "phase": f.phase, "sections": secs}


@app.get("/forms/{form_id}/sections")
def form_sections_route(form_id: int, version: Optional[int] = None, fdb: Session = Depends(get_fdb)):
    return [{"id": s.id, "name": s.name, "position": s.position} for s in form_sections(fdb, form_id, version)]


@app.get("/forms/{form_id}/sessions/{section_id}/fields")
def section_fields_route(form_id: int, section_id: int, fdb: Session = Depends(get_fdb)):
    return [{"id": f.id, "name": f.name, "label": f.label, "type": f.type, "prefix": f.prefix, "position": f.position} for f in section_fields(fdb, section_id)]


# ---- edicts ----


@app.get("/edicts")
def list_edicts(type: Optional[str] = None, is_open: Optional[str] = None, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db) if request else None
    q = select(Edict)
    edicts = db.execute(q).scalars().all()
    items = []
    for e in sorted(edicts, key=lambda x: (x.date_closed or date.min), reverse=True):
        if type is not None and e.edict_type != type:
            continue
        if is_open is not None and str(bool(e.is_open)).lower() != is_open.lower():
            continue
        items.append({"id": e.id, "title": e.title, "year": e.year, "semester": e.semester, "edict_type": e.edict_type, "is_open": bool(e.is_open)})
    return items


@app.post("/edicts")
def create_edict(body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    try:
        da = parse_date(body["date_application"])
        de = parse_date(body["date_evaluation"])
        dv = parse_date(body["date_verification"])
        dc = parse_date(body["date_closed"])
    except Exception:
        raise HTTPException(422, "Datas invalidas")
    check_dates(da, de, dv, dc)
    e = Edict(
        title=body["title"], description=body.get("description", ""),
        year=int(body["year"]), semester=int(body["semester"]),
        edict_type=body.get("edict_type", "mestrado"), is_open=bool(body.get("is_open", True)),
        candidate_form_id=(body.get("candidate_forms") or [None])[0],
        recommender_form_id=(body.get("recommenders_forms") or [None])[0],
        date_application=da, date_evaluation=de, date_verification=dv, date_closed=dc,
        author_id=user.id,
    )
    db.add(e)
    db.flush()
    for lbl in ("inscricoes", "homologacao", "avaliacao", "encerrado"):
        db.add(Phase(edict_id=e.id, label=lbl))
    db.flush()
    e.current_phase_id = db.execute(select(Phase).where(Phase.edict_id == e.id, Phase.label == "inscricoes")).scalar_one()
    db.commit()
    return edict_dict(db, e, user)


@app.get("/edicts/{edict_id}")
def get_edict(edict_id: int, request: Request = None, db: Session = Depends(get_db)):
    e = get_edict_or_404(db, edict_id)
    user = current_user(request, db) if request else None
    return edict_dict(db, e, user)


@app.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    e = get_edict_or_404(db, edict_id)
    if "title" in body:
        e.title = body["title"]
    if "description" in body:
        e.description = body["description"]
    if "year" in body:
        e.year = int(body["year"])
    if "semester" in body:
        e.semester = int(body["semester"])
    if "edict_type" in body:
        e.edict_type = body["edict_type"]
    if all(k in body for k in ("date_application", "date_evaluation", "date_verification", "date_closed")):
        da = parse_date(body["date_application"])
        de = parse_date(body["date_evaluation"])
        dv = parse_date(body["date_verification"])
        dc = parse_date(body["date_closed"])
        check_dates(da, de, dv, dc)
        e.date_application, e.date_evaluation, e.date_verification, e.date_closed = da, de, dv, dc
    db.commit()
    return edict_dict(db, e, user)


@app.post("/edicts/{edict_id}/edit-date")
def edit_date(edict_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    e = get_edict_or_404(db, edict_id)
    e.date_closed = parse_date(body["closed_date"])
    db.commit()
    return {"closed_date": str(e.date_closed)}


@app.post("/edicts/{edict_id}/advance-phase")
def advance_phase(edict_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db), fdb: Session = Depends(get_fdb)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    e = get_edict_or_404(db, edict_id)
    p = db.get(Phase, body["id"])
    if not p or p.edict_id != e.id:
        raise HTTPException(404, "Fase nao encontrada")
    e.current_phase_id = p.id
    db.commit()
    if e.candidate_form_id:
        f = fdb.get(Form, e.candidate_form_id)
        if f:
            f.phase = PHASE_TO_FORMS.get(p.label, f.phase)
            fdb.commit()
    return {"id": p.id, "label": p.label}


@app.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: int, body: dict = Body(default={}), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    e = get_edict_or_404(db, edict_id)
    if not e.is_open:
        raise HTTPException(409, "Edital ja encerrado")
    e.is_open = False
    db.commit()
    return {"message": "Edital encerrado", "confirmation_deadline": body.get("confirmation_deadline")}


@app.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    e = get_edict_or_404(db, edict_id)
    subs = db.execute(select(Submission).where(Submission.edict_id == e.id)).scalars().all()
    for s in subs:
        for model in (Comment, Favorite, Label, PrivateNote, View, Bidding):
            for row in db.execute(select(model).where(model.submission_id == s.id)).scalars():
                db.delete(row)
        db.delete(s)
    for model in (Phase, Mapping, Slot):
        for row in db.execute(select(model).where(model.edict_id == e.id)).scalars():
            db.delete(row)
    db.delete(e)
    db.commit()
    return {"message": "Edital removido"}


# ---- mappings ----


def _check_tipo(tipo: str):
    if tipo not in ("candidates", "recommenders"):
        raise HTTPException(404, "Tipo invalido")


def _mapping_form_id(e: Edict, tipo: str):
    return e.candidate_form_id if tipo == "candidates" else e.recommender_form_id


def _validate_tree(fdb: Session, form_id: int, version: int, tree) -> None:
    secs = {s.id for s in form_sections(fdb, form_id, version)}
    fields_by_sec = {sid: {f.id for f in section_fields(fdb, sid)} for sid in secs}

    def walk(node):
        if node is None:
            return
        if isinstance(node, dict):
            if "section" in node and "field" in node:
                sid, fid = node["section"], node["field"]
                if sid not in secs or fid not in fields_by_sec.get(sid, set()):
                    raise HTTPException(422, "Referencia secao/campo invalida")
                return
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(tree)


@app.get("/edicts/{edict_id}/{tipo}/mappings")
def list_mappings(edict_id: int, tipo: str, db: Session = Depends(get_db)):
    _check_tipo(tipo)
    get_edict_or_404(db, edict_id)
    ms = db.execute(select(Mapping).where(Mapping.edict_id == edict_id, Mapping.tipo == tipo)).scalars().all()
    return [{"id": m.id, "edict_id": m.edict_id, "tipo": m.tipo, "author_id": m.author_id, "form_id": m.form_id, "version": m.version, "tree": json.loads(m.tree), "active": bool(m.active)} for m in ms]


@app.post("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/")
def create_mapping(edict_id: int, tipo: str, version: int, tree: dict = Body(...), request: Request = None, db: Session = Depends(get_db), fdb: Session = Depends(get_fdb)):
    _check_tipo(tipo)
    user = require_user(request, db)
    e = get_edict_or_404(db, edict_id)
    form_id = _mapping_form_id(e, tipo)
    if not form_id:
        raise HTTPException(400, "Edital sem formulario associado")
    dup = db.execute(select(Mapping).where(Mapping.edict_id == edict_id, Mapping.tipo == tipo, Mapping.version == version)).scalar_one_or_none()
    if dup:
        raise HTTPException(409, "Mapeamento ja existe para esta versao")
    _validate_tree(fdb, form_id, version, tree)
    m = Mapping(edict_id=edict_id, tipo=tipo, version=version, author_id=user.id, form_id=form_id, tree=json.dumps(tree), active=True)
    db.add(m)
    db.commit()
    return {"id": m.id, "edict_id": m.edict_id, "tipo": m.tipo, "author_id": m.author_id, "form_id": m.form_id, "version": m.version, "tree": json.loads(m.tree), "active": bool(m.active)}


def _find_mapping(db: Session, edict_id: int, tipo: str, version: int, mapping_id: int) -> Mapping:
    _check_tipo(tipo)
    get_edict_or_404(db, edict_id)
    m = db.get(Mapping, mapping_id)
    if not m or m.edict_id != edict_id or m.tipo != tipo or m.version != version:
        raise HTTPException(404, "Mapeamento nao encontrado")
    return m


@app.put("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def update_mapping(edict_id: int, tipo: str, version: int, mapping_id: int, tree: dict = Body(...), request: Request = None, db: Session = Depends(get_db), fdb: Session = Depends(get_fdb)):
    user = require_user(request, db)
    m = _find_mapping(db, edict_id, tipo, version, mapping_id)
    _validate_tree(fdb, m.form_id, version, tree)
    m.tree = json.dumps(tree)
    db.commit()
    return {"id": m.id, "edict_id": m.edict_id, "tipo": m.tipo, "author_id": m.author_id, "form_id": m.form_id, "version": m.version, "tree": json.loads(m.tree), "active": bool(m.active)}


@app.delete("/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}")
def delete_mapping(edict_id: int, tipo: str, version: int, mapping_id: int, request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    m = _find_mapping(db, edict_id, tipo, version, mapping_id)
    db.delete(m)
    db.commit()
    return {"message": "Mapping deleted successfully"}


@app.get("/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
def unmapped_versions(edict_id: int, tipo: str, db: Session = Depends(get_db)):
    _check_tipo(tipo)
    get_edict_or_404(db, edict_id)
    mapped = {m.version for m in db.execute(select(Mapping).where(Mapping.edict_id == edict_id, Mapping.tipo == tipo)).scalars()}
    versions = {s.version for s in db.execute(select(Submission).where(Submission.edict_id == edict_id)).scalars() if s.version}
    return sorted(versions - mapped)


# ---- submissions ----


@app.get("/edicts/{edict_id}/submissions")
def list_submissions(edict_id: int, stats: Optional[str] = None, only_favorites: Optional[str] = None, request: Request = None, db: Session = Depends(get_db)):
    e = get_edict_or_404(db, edict_id)
    user = current_user(request, db) if request else None
    subs = db.execute(select(Submission).where(Submission.edict_id == e.id)).scalars().all()
    fav_ids = set()
    if user is not None:
        fav_ids = {f.submission_id for f in db.execute(select(Favorite).where(Favorite.user_id == user.id)).scalars()}
    out = []
    for s in subs:
        if stats is not None and s.stats != stats:
            continue
        if (only_favorites or "").lower() == "true" and s.id not in fav_ids:
            continue
        out.append(submission_item(db, s, user))
    return {"submissions": out}


@app.get("/submissions/{submission_id}")
def submission_detail(submission_id: int, include_comments: Optional[str] = None, request: Request = None, db: Session = Depends(get_db), fdb: Session = Depends(get_fdb)):
    s = get_submission_or_404(db, submission_id)
    user = current_user(request, db) if request else None
    return {"summary": submission_summary(db, fdb, s, user), "submission_form": submission_form(fdb, s)}


@app.get("/submissions/{submission_id}/files/{label}/{filename}")
def submission_file(submission_id: int, label: str, filename: str, fdb: Session = Depends(get_fdb)):
    s = get_submission_or_404(None, submission_id) if False else None
    return None


@app.get("/submissions/{submission_id}/comments")
def list_comments(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    get_submission_or_404(db, submission_id)
    user = current_user(request, db) if request else None
    out = []
    for c in db.execute(select(Comment).where(Comment.submission_id == submission_id).order_by(Comment.id)).scalars():
        u = db.get(User, c.user_id)
        out.append({"id": c.id, "user_id": c.user_id, "user": u.name if u else None, "comment": c.comment, "text": c.comment, "type": "comment", "created_at": c.created_at})
    return out


@app.post("/submissions/{submission_id}/comments")
def create_comment(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if current_phase_label(db, e) != "avaliacao":
        raise HTTPException(400, "Comentarios apenas na fase de avaliacao")
    created_at = body.get("created_at") or datetime.now(TZ).isoformat()
    c = Comment(user_id=user.id, submission_id=submission_id, comment=body["comment"], created_at=created_at)
    db.add(c)
    db.commit()
    return {"id": c.id, "user_id": c.user_id, "user": user.name, "submission_id": c.submission_id, "comment": c.comment, "created_at": c.created_at}


@app.delete("/submissions/comments/{comment_id}")
def delete_comment(comment_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    c = db.get(Comment, comment_id)
    if not c:
        raise HTTPException(404, "Comentario nao encontrado")
    if c.user_id != user.id:
        raise HTTPException(403, "Apenas o autor pode excluir")
    db.delete(c)
    db.commit()
    return Response(status_code=204)


@app.post("/submissions/{submission_id}/favorites")
def create_favorite(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if current_phase_label(db, e) != "avaliacao":
        raise HTTPException(400, "Favoritos apenas na fase de avaliacao")
    dup = db.execute(select(Favorite).where(Favorite.submission_id == submission_id, Favorite.user_id == user.id)).scalar_one_or_none()
    if dup:
        raise HTTPException(409, "Favorito ja registrado")
    db.add(Favorite(user_id=user.id, submission_id=submission_id))
    db.commit()
    return Response(status_code=201)


@app.delete("/submissions/{submission_id}/favorites")
def delete_favorite(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    f = db.execute(select(Favorite).where(Favorite.submission_id == submission_id, Favorite.user_id == user.id)).scalar_one_or_none()
    if not f:
        raise HTTPException(404, "Favorito nao encontrado")
    db.delete(f)
    db.commit()
    return Response(status_code=204)


@app.get("/submissions/{submission_id}/labels")
def list_labels(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db) if request else None
    if user is None:
        return []
    labels = db.execute(select(Label).where(Label.user_id == user.id).order_by(Label.id.desc())).scalars().all()
    seen = set()
    out = []
    for l in labels:
        if l.label in seen:
            continue
        seen.add(l.label)
        out.append({"id": l.id, "label": l.label, "color": l.color})
    return out


@app.post("/submissions/{submission_id}/labels")
def create_label(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if current_phase_label(db, e) != "avaliacao":
        raise HTTPException(400, "Etiquetas apenas na fase de avaliacao")
    for l in db.execute(select(Label).where(Label.user_id == user.id, Label.label == body["label"])).scalars():
        l.color = body.get("color", l.color)
    db.add(Label(user_id=user.id, submission_id=submission_id, label=body["label"], color=body.get("color", ""), context="candidate"))
    db.commit()
    l = db.execute(select(Label).where(Label.user_id == user.id, Label.submission_id == submission_id, Label.label == body["label"])).scalars().first()
    return {"id": l.id, "user_id": user.id, "submission_id": submission_id, "label": l.label, "color": l.color, "context": l.context}


@app.delete("/submissions/label/{label_id}")
def delete_label(label_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    l = db.get(Label, label_id)
    if not l:
        raise HTTPException(404, "Etiqueta nao encontrada")
    if l.user_id != user.id:
        raise HTTPException(403, "Apenas o autor pode excluir")
    db.delete(l)
    db.commit()
    return Response(status_code=204)


@app.post("/submissions/{submission_id}/private_notes")
def private_notes(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if current_phase_label(db, e) != "avaliacao":
        raise HTTPException(400, "Notas apenas na fase de avaliacao")
    n = db.execute(select(PrivateNote).where(PrivateNote.submission_id == submission_id, PrivateNote.user_id == user.id)).scalar_one_or_none()
    if n:
        n.note = body["note"]
    else:
        n = PrivateNote(user_id=user.id, submission_id=submission_id, note=body["note"])
        db.add(n)
    db.commit()
    return {"id": n.id, "user_id": user.id, "submission_id": submission_id, "note": n.note}


@app.post("/submissions/{submission_id}/view")
def create_view(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    get_submission_or_404(db, submission_id)
    today = datetime.now(TZ).date()
    v = db.execute(select(View).where(View.submission_id == submission_id, View.user_id == user.id, View.view_date == today)).scalar_one_or_none()
    if not v:
        db.add(View(user_id=user.id, submission_id=submission_id, view_date=today))
        db.commit()
    return {"message": "ok"}


@app.get("/submissions/{submission_id}/view")
def list_views(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    get_submission_or_404(db, submission_id)
    return [{"user_id": v.user_id, "date": str(v.view_date)} for v in db.execute(select(View).where(View.submission_id == submission_id)).scalars()]


# ---- selection ----


@app.post("/edicts/{edict_id}/slots")
def set_slots(edict_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    get_edict_or_404(db, edict_id)
    raw = (body.get("amount") or "").strip()
    if raw:
        try:
            val = int(raw)
        except ValueError:
            raise HTTPException(400, "Valor de vagas invalido")
        amount = str(val) if val > 0 else "0"
    else:
        amount = "0"
    slot = db.execute(select(Slot).where(Slot.edict_id == edict_id, Slot.user_id == user.id)).scalar_one_or_none()
    if slot:
        slot.amount = amount
    else:
        db.add(Slot(user_id=user.id, edict_id=edict_id, amount=amount))
    db.commit()
    return {"amount": amount}


@app.post("/submissions/{submission_id}/bidding")
def set_bidding(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    value = body.get("bidding", "")
    if value not in BIDDING_VALUES:
        raise HTTPException(400, "Valor de interesse invalido")
    target_id = user.id
    if user.role in ADMIN_ROLES and body.get("user_id") is not None:
        target_id = int(body["user_id"])
    b = db.execute(select(Bidding).where(Bidding.submission_id == submission_id, Bidding.user_id == target_id)).scalar_one_or_none()
    if b:
        b.bidding = value
    else:
        db.add(Bidding(user_id=target_id, submission_id=submission_id, bidding=value))
    db.commit()
    return {"bidding": value, "user_id": target_id}


@app.post("/submissions/{submission_id}/select")
def select_submission(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if not e.is_open:
        raise HTTPException(409, "Edital encerrado")
    stats = body.get("stats")
    if stats not in STATS_VALUES:
        raise HTTPException(422, "Situacao invalida")
    user_ids = body.get("user_ids")
    if stats == "approved":
        if not user_ids or len(user_ids) != 1 or not db.get(User, user_ids[0]):
            raise HTTPException(400, "Aprovacao exige um unico orientador existente")
        s.advisor_id = user_ids[0]
    s.stats = stats
    db.commit()
    return {"id": s.id, "stats": s.stats, "advisor_id": s.advisor_id}


@app.post("/submissions/{submission_id}/entry-semester")
def entry_semester(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    sem = body.get("semester", "")
    norm = {"first": "Primeiro semestre.", "primeiro": "Primeiro semestre.", "second": "Segundo semestre.", "segundo": "Segundo semestre."}
    s.entry_semester = norm.get(str(sem).strip().lower(), sem)
    db.commit()
    return {"semester": s.entry_semester}


# ---- mail ----


@app.post("/submissions/{submission_id}/reesend_submission")
def reesend_submission(submission_id: int, body: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Apenas usuarios administrativos")
    s = get_submission_or_404(db, submission_id)
    e = db.get(Edict, s.edict_id)
    if current_phase_label(db, e) != "homologacao":
        raise HTTPException(400, "Solicitacao de correcao apenas na homologacao")
    return {"message": "Solicitacao enviada", "email_sent": True}


@app.post("/submissions/{submission_id}/send-accept")
def send_accept(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    if not s.accept_form_id:
        raise HTTPException(404, "Formulario de aceite nao configurado")
    return {"message": "Formulario de aceite enviado", "email_sent": True}


@app.post("/submissions/{submission_id}/send-letter")
def send_letter(submission_id: int, request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    s = get_submission_or_404(db, submission_id)
    if s.stats != "approved" or s.letter_sent:
        raise HTTPException(400, "Candidatura nao aprovada ou carta ja enviada")
    s.letter_sent = True
    db.commit()
    return {"message": "Carta de aceite enviada", "email_sent": True}


# ---- reports ----


def _interactors(db: Session, edict_id: int):
    subs = [s.id for s in db.execute(select(Submission).where(Submission.edict_id == edict_id)).scalars()]
    uids = set()
    for model in (Comment, Favorite, Label, PrivateNote):
        if not subs:
            break
        q = select(model).where(model.submission_id.in_(subs))
        for row in db.execute(q).scalars():
            uids.add(row.user_id)
    out = []
    for uid in sorted(uids):
        u = db.get(User, uid)
        if u:
            out.append(user_dict(u))
    return out


def _write_pdf(path: str, lines):
    os.makedirs(JOBS_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(make_pdf_bytes(lines))


def _write_csv(path: str, rows):
    os.makedirs(JOBS_DIR, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow(r)
    with open(path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())


@app.post("/edicts/{edict_id}/interactors_list")
def interactors_list(edict_id: int, body: dict = Body(default={}), background: BackgroundTasks = None, request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    e = get_edict_or_404(db, edict_id)
    mode = body.get("mode", "plain_text")
    if mode == "pdf":
        job_id = uuid.uuid4().hex
        lines = [e.title, f"Ano: {e.year}", "Estatisticas: 0 finalizadas, 0 em preenchimento"]
        if body.get("list_of_advisors"):
            lines.append("Orientadores: nenhum")
        if body.get("show_emails"):
            lines.append("E-mails: nenhum")
        background.add_task(_write_pdf, os.path.join(JOBS_DIR, f"{job_id}.pdf"), lines)
        return {"job_id": job_id, "status": "processing"}
    return _interactors(db, edict_id)


@app.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(edict_id: int, background: BackgroundTasks = None, request: Request = None, db: Session = Depends(get_db)):
    require_user(request, db)
    get_edict_or_404(db, edict_id)
    subs = db.execute(select(Submission).where(Submission.edict_id == edict_id)).scalars().all()
    teacher_ids = sorted({b.user_id for b in db.execute(select(Bidding).where(Bidding.submission_id.in_([s.id for s in subs]) if subs else [-1])).scalars() if b.bidding})
    teachers = [db.get(User, t) for t in teacher_ids]
    rows = [["#"] + [t.email for t in teachers]]
    slot_row = ["slots"]
    for t in teachers:
        sl = db.execute(select(Slot).where(Slot.edict_id == edict_id, Slot.user_id == t.id)).scalar_one_or_none()
        slot_row.append(sl.amount if sl else "0")
    rows.append(slot_row)
    for s in subs:
        row = [s.email]
        for t in teachers:
            b = db.execute(select(Bidding).where(Bidding.submission_id == s.id, Bidding.user_id == t.id)).scalar_one_or_none()
            row.append(b.bidding if b else "")
        rows.append(row)
    job_id = uuid.uuid4().hex
    background.add_task(_write_csv, os.path.join(JOBS_DIR, f"{job_id}.csv"), rows)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id: str, ext: str, media_type: str):
    path = os.path.join(JOBS_DIR, f"{job_id}.{ext}")
    if not os.path.exists(path):
        raise HTTPException(404, "Relatorio nao encontrado")
    with open(path, "rb") as f:
        data = f.read()
    os.remove(path)
    return Response(content=data, media_type=media_type, headers={"Content-Disposition": f"inline; filename=\"{job_id}.{ext}\""})


@app.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    return _download(job_id, "pdf", "application/pdf")


@app.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    return _download(job_id, "csv", "text/csv")
