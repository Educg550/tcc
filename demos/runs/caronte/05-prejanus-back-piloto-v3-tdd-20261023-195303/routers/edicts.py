import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

from auth import ADMIN_ROLES, get_current_user, require_admin
from database import FormsSession, PrejanusSession
from services import reports
from services.common import get_edict, parse_form_ids
from services.submission_data import flatten_mapping, sync_recommenders, sync_submissions

router = APIRouter(tags=["edicts"])

PHASES = ["inscricoes", "homologacao", "avaliacao", "encerrado"]
FORMS_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
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
    closed_date: str


class AdvancePhaseEdictSchema(BaseModel):
    id: int


class CloseEdictSchema(BaseModel):
    confirmation_deadline: str
    send_approval_letter: bool


class SlotsSchema(BaseModel):
    amount: str


class SectionsDocument(BaseModel):
    list_of_advisors: bool | None = False
    relation: bool | None = False
    approved: bool | None = False
    refused: bool | None = False
    underreview: bool | None = False
    general_statistics: bool | None = False
    show_emails: bool | None = False


def _validate_dates(payload):
    dates = [payload.date_application, payload.date_verification, payload.date_evaluation, payload.date_closed]
    if not all(dates[i] < dates[i + 1] for i in range(3)):
        raise HTTPException(status_code=422, detail="As datas devem estar em ordem cronológica estrita")


def _phase_dates(payload):
    return {
        "inscricoes": payload.date_application.date(),
        "homologacao": payload.date_evaluation.date(),
        "avaliacao": payload.date_verification.date(),
        "encerrado": payload.date_closed.date(),
    }


def _edict_brief(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "year": row["year"],
        "semester": row["semester"],
        "edict_type": row["type"],
        "is_open": row["is_open"],
    }


def _edict_detail(ps, row, user_id):
    phases = ps.execute(
        text("select * from edict_phase where edict_id=:e order by id"), {"e": row["id"]}
    ).mappings().all()
    slots = ps.execute(
        text("select slots from user_edict_slots where user_id=:u and edict_id=:e"),
        {"u": user_id, "e": row["id"]},
    ).scalar()
    return {
        "id": row["id"],
        "title": row["title"],
        "candidate_form_id": row["candidate_forms"] or "",
        "recommender_form_id": row["recommenders_forms"] or "",
        "description": row["description"] or "",
        "closed_date": row["closed_date"].isoformat() if row["closed_date"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "year": row["year"],
        "semester": row["semester"],
        "type": row["type"],
        "is_open": row["is_open"],
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "phase": row["phase"],
        "phases": [
            {
                "id": p["id"],
                "closed_date": p["closed_date"].isoformat() if p["closed_date"] else None,
                "phase": p["phase"],
            }
            for p in phases
        ],
        "slots": str(slots) if slots is not None else "0",
    }


@router.get("/edicts")
def get_all_edicts(type: str | None = None, is_open: bool | None = None, user=Depends(get_current_user)):
    query = "select * from edict"
    conditions = []
    params = {}
    if type is not None:
        conditions.append("type = :type")
        params["type"] = type
    if is_open is not None:
        conditions.append("is_open = :is_open")
        params["is_open"] = is_open
    if conditions:
        query += " where " + " and ".join(conditions)
    query += ' order by closed_date desc, id desc'
    with PrejanusSession() as ps:
        rows = ps.execute(text(query), params).mappings().all()
        return [_edict_brief(r) for r in rows]


@router.post("/edicts")
def create_edict(payload: InsertEdictSchema, user=Depends(require_admin)):
    _validate_dates(payload)
    phase_dates = _phase_dates(payload)
    with PrejanusSession() as ps:
        result = ps.execute(
            text(
                "insert into edict (title, description, candidate_forms, recommenders_forms, closed_date, "
                "year, semester, type, phase, is_open, created_at, updated_at, user_id) "
                "values (:t, :d, :cf, :rf, :cd, :y, :s, :ty, 'inscricoes', :io, now(), now(), :u) returning id"
            ),
            {
                "t": payload.title,
                "d": payload.description,
                "cf": str(payload.candidate_forms),
                "rf": str(payload.recommenders_forms),
                "cd": payload.date_closed.date(),
                "y": payload.year,
                "s": payload.semester,
                "ty": payload.edict_type,
                "io": payload.is_open,
                "u": user["id"],
            },
        ).scalar()
        for phase in PHASES:
            ps.execute(
                text("insert into edict_phase (edict_id, closed_date, phase) values (:e, :d, :p)"),
                {"e": result, "d": phase_dates[phase], "p": phase},
            )
        ps.commit()
        return {
            "id": result,
            "title": payload.title,
            "description": payload.description,
            "year": payload.year,
            "semester": payload.semester,
            "edict_type": payload.edict_type,
            "is_open": payload.is_open,
            "candidate_forms": payload.candidate_forms,
            "recommenders_forms": payload.recommenders_forms,
            "date_application": payload.date_application.isoformat(),
            "date_verification": payload.date_verification.isoformat(),
            "date_evaluation": payload.date_evaluation.isoformat(),
            "date_closed": payload.date_closed.isoformat(),
            "closed_date": payload.date_closed.isoformat(),
        }


@router.get("/edicts/{edict_id}")
def get_edict_by_id(edict_id: int, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        row = get_edict(ps, edict_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        return _edict_detail(ps, row, user["id"])


@router.get("/edicts/{edict_id}/submissions")
def get_all_submissions_from_edict(
    edict_id: int,
    stats: str | None = None,
    only_favorites: bool = False,
    user=Depends(get_current_user),
):
    from services.submission_data import build_submission

    with PrejanusSession() as ps, FormsSession() as fs:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        sync_submissions(ps, fs, edict)
        sync_recommenders(ps, fs, edict)
        rows = ps.execute(
            text("select * from submission where edict_id=:e order by id"), {"e": edict_id}
        ).mappings().all()
        fav_ids = {
            r[0]
            for r in ps.execute(
                text("select submission_id from favorites where user_id=:u"), {"u": user["id"]}
            ).all()
        }
        out = []
        for row in rows:
            if stats is not None and row["stats"] != stats:
                continue
            if only_favorites and row["id"] not in fav_ids:
                continue
            out.append(build_submission(ps, fs, row, edict, user["id"]))
        return {"submissions": out}


@router.post("/edicts/{edict_id}/edit")
def edit_edict(edict_id: int, payload: EditEdictSchema, user=Depends(require_admin)):
    _validate_dates(payload)
    phase_dates = _phase_dates(payload)
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        ps.execute(
            text(
                "update edict set title=:t, description=:d, year=:y, semester=:s, type=:ty, "
                "closed_date=:cd, updated_at=now() where id=:i"
            ),
            {
                "t": payload.title,
                "d": payload.description,
                "y": int(payload.year),
                "s": int(payload.semester),
                "ty": payload.edict_type,
                "cd": payload.date_closed.date(),
                "i": edict_id,
            },
        )
        for phase in PHASES:
            ps.execute(
                text("update edict_phase set closed_date=:d where edict_id=:e and phase=:p"),
                {"d": phase_dates[phase], "e": edict_id, "p": phase},
            )
        ps.commit()
        return {
            "title": payload.title,
            "description": payload.description,
            "year": payload.year,
            "semester": payload.semester,
            "edict_type": payload.edict_type,
            "date_application": payload.date_application.isoformat(),
            "date_verification": payload.date_verification.isoformat(),
            "date_evaluation": payload.date_evaluation.isoformat(),
            "date_closed": payload.date_closed.isoformat(),
        }


@router.post("/edicts/{edict_id}/edit-date")
def edit_edict_date_only(edict_id: int, payload: EditEdictDateSchema, user=Depends(require_admin)):
    from datetime import date

    closed = date.fromisoformat(payload.closed_date)
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        ps.execute(
            text("update edict set closed_date=:d, updated_at=now() where id=:i"),
            {"d": closed, "i": edict_id},
        )
        ps.execute(
            text("update edict_phase set closed_date=:d where edict_id=:e and phase='encerrado'"),
            {"d": closed, "e": edict_id},
        )
        ps.commit()
        return {"closed_date": payload.closed_date}


@router.post("/edicts/{edict_id}/advance-phase")
def advance_edict(edict_id: int, payload: AdvancePhaseEdictSchema, user=Depends(require_admin)):
    with PrejanusSession() as ps, FormsSession() as fs:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        phase_row = ps.execute(
            text("select * from edict_phase where id=:i and edict_id=:e"),
            {"i": payload.id, "e": edict_id},
        ).mappings().first()
        if phase_row is None:
            raise HTTPException(status_code=404, detail="Fase não encontrada")
        ps.execute(
            text("update edict set phase=:p, updated_at=now() where id=:i"),
            {"p": phase_row["phase"], "i": edict_id},
        )
        ps.commit()
        edict = get_edict(ps, edict_id)
        form_ids = parse_form_ids(edict["candidate_forms"])
        if form_ids:
            fs.execute(
                text("select change_form_phase(:id, :ph)"),
                {"id": form_ids[0], "ph": FORMS_PHASE[phase_row["phase"]]},
            )
            fs.commit()
        return {"id": phase_row["id"], "label": phase_row["phase"]}


@router.patch("/edicts/{edict_id}/close")
def close_edict(edict_id: int, payload: CloseEdictSchema, user=Depends(require_admin)):
    with PrejanusSession() as ps:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        if not edict["is_open"]:
            raise HTTPException(status_code=409, detail="Edital já está encerrado")
        ps.execute(
            text("update edict set is_open=false, updated_at=now() where id=:i"), {"i": edict_id}
        )
        ps.commit()
        return {"message": "Edital encerrado"}


@router.delete("/edicts/{edict_id}/remove")
def remove_edict(edict_id: int, user=Depends(require_admin)):
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        ps.execute(text("delete from edict where id=:i"), {"i": edict_id})
        ps.commit()
        return {"message": "Edital removido"}


@router.post("/edicts/{edict_id}/slots")
def set_user_slots(edict_id: int, payload: SlotsSchema, user=Depends(get_current_user)):
    amount = (payload.amount or "").strip()
    if amount == "":
        value = 0
    else:
        try:
            value = int(amount)
        except ValueError:
            raise HTTPException(status_code=422, detail="Valor de vagas inválido")
        if value < 0:
            value = 0
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        existing = ps.execute(
            text("select id from user_edict_slots where user_id=:u and edict_id=:e"),
            {"u": user["id"], "e": edict_id},
        ).first()
        if existing:
            ps.execute(
                text("update user_edict_slots set slots=:s where id=:i"),
                {"s": value, "i": existing[0]},
            )
        else:
            ps.execute(
                text("insert into user_edict_slots (user_id, edict_id, slots) values (:u, :e, :s)"),
                {"u": user["id"], "e": edict_id, "s": value},
            )
        ps.commit()
        return {"amount": str(value)}


def _mapping_form_column(tipo):
    return "candidate_forms" if tipo == "candidates" else "recommenders_forms"


def _mapping_form_type(tipo):
    return "candidate" if tipo == "candidates" else "recommender"


def _validate_mapping_tree(fs, form_id, version, tree):
    flat = flatten_mapping(tree)
    if not flat:
        return
    has_version_fields = fs.execute(
        text(
            "select count(*) from form_field ff join form_section s on s.id = ff.section_id "
            "where s.form_id=:f and ff.version=:v"
        ),
        {"f": form_id, "v": version},
    ).scalar()
    for leaf in flat.values():
        row = fs.execute(
            text(
                "select ff.id, ff.version from form_field ff join form_section s on s.id = ff.section_id "
                "where ff.id=:fid and ff.section_id=:sid and s.form_id=:f"
            ),
            {"fid": leaf["field"], "sid": leaf["section"], "f": form_id},
        ).first()
        if row is None:
            raise HTTPException(status_code=422, detail="Referência de seção/campo inválida")
        if has_version_fields and not (row[1] == version or (version == 1 and row[1] is None)):
            raise HTTPException(status_code=422, detail="Campo não pertence à versão solicitada")


def _create_mapping(edict_id, tipo, version, tree, user):
    with PrejanusSession() as ps, FormsSession() as fs:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        form_ids = parse_form_ids(edict[_mapping_form_column(tipo)])
        if not form_ids:
            raise HTTPException(status_code=404, detail="Formulário não configurado no edital")
        _validate_mapping_tree(fs, form_ids[0], version, tree)
        existing = ps.execute(
            text(
                "select id from edict_form_mappings where edict_id=:e and form_type=:t and form_version=:v"
            ),
            {"e": edict_id, "t": _mapping_form_type(tipo), "v": version},
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Já existe mapeamento para esta versão")
        mapping_id = ps.execute(
            text(
                "insert into edict_form_mappings (edict_id, form_type, mapping, is_active, form_id, user_id, form_version) "
                "values (:e, :t, :m, true, :f, :u, :v) returning id"
            ),
            {
                "e": edict_id,
                "t": _mapping_form_type(tipo),
                "m": json.dumps(tree),
                "f": str(form_ids[0]),
                "u": user["id"],
                "v": version,
            },
        ).scalar()
        ps.commit()
        return {
            "id": mapping_id,
            "edict_id": edict_id,
            "form_type": _mapping_form_type(tipo),
            "user_id": user["id"],
            "form_version": version,
            "mapping": tree,
            "is_active": True,
        }


def _list_mappings(edict_id, tipo):
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        rows = ps.execute(
            text(
                "select * from edict_form_mappings where edict_id=:e and form_type=:t order by form_version"
            ),
            {"e": edict_id, "t": _mapping_form_type(tipo)},
        ).mappings().all()
        return [
            {
                "id": r["id"],
                "edict_id": r["edict_id"],
                "form_type": r["form_type"],
                "user_id": r["user_id"],
                "form_version": r["form_version"],
                "mapping": r["mapping"],
                "is_active": r["is_active"],
            }
            for r in rows
        ]


def _update_mapping(edict_id, tipo, version, mapping_id, tree):
    with PrejanusSession() as ps, FormsSession() as fs:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        row = ps.execute(
            text(
                "select * from edict_form_mappings where id=:i and edict_id=:e and form_type=:t and form_version=:v"
            ),
            {"i": mapping_id, "e": edict_id, "t": _mapping_form_type(tipo), "v": version},
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
        form_ids = parse_form_ids(edict[_mapping_form_column(tipo)])
        if form_ids:
            _validate_mapping_tree(fs, form_ids[0], version, tree)
        ps.execute(
            text("update edict_form_mappings set mapping=:m where id=:i"),
            {"m": json.dumps(tree), "i": mapping_id},
        )
        ps.commit()
        return {
            "id": row["id"],
            "edict_id": edict_id,
            "form_type": row["form_type"],
            "user_id": row["user_id"],
            "form_version": version,
            "mapping": tree,
            "is_active": row["is_active"],
        }


def _delete_mapping(edict_id, tipo, version, mapping_id):
    with PrejanusSession() as ps:
        row = ps.execute(
            text(
                "select id from edict_form_mappings where id=:i and edict_id=:e and form_type=:t and form_version=:v"
            ),
            {"i": mapping_id, "e": edict_id, "t": _mapping_form_type(tipo), "v": version},
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Mapeamento não encontrado")
        ps.execute(text("delete from edict_form_mappings where id=:i"), {"i": mapping_id})
        ps.commit()
        return {"message": "Mapping deleted successfully"}


def _unmapped_versions(edict_id, tipo):
    with PrejanusSession() as ps:
        if get_edict(ps, edict_id) is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        column = "candidate_form_version" if tipo == "candidates" else "recommender_form_version"
        versions = ps.execute(
            text(f"select distinct {column} from submission where edict_id=:e"), {"e": edict_id}
        ).scalars().all()
        mapped = set(
            ps.execute(
                text("select form_version from edict_form_mappings where edict_id=:e and form_type=:t"),
                {"e": edict_id, "t": _mapping_form_type(tipo)},
            ).scalars().all()
        )
        return sorted(v for v in versions if v not in mapped)


@router.post("/edicts/{edict_id}/recommenders/mappings/versions/{version}/")
def create_recommender_form_mapping(edict_id: int, version: int, payload: dict, user=Depends(require_admin)):
    return _create_mapping(edict_id, "recommenders", version, payload, user)


@router.post("/edicts/{edict_id}/candidates/mappings/versions/{version}/")
def create_candidate_form_mapping(edict_id: int, version: int, payload: dict, user=Depends(require_admin)):
    return _create_mapping(edict_id, "candidates", version, payload, user)


@router.get("/edicts/{edict_id}/candidates/mappings")
def get_candidate_mappings(edict_id: int, user=Depends(get_current_user)):
    return _list_mappings(edict_id, "candidates")


@router.get("/edicts/{edict_id}/recommenders/mappings")
def get_recommender_mappings(edict_id: int, user=Depends(get_current_user)):
    return _list_mappings(edict_id, "recommenders")


@router.put("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def update_recommender_mapping(edict_id: int, version: int, mapping_id: int, payload: dict, user=Depends(require_admin)):
    return _update_mapping(edict_id, "recommenders", version, mapping_id, payload)


@router.delete("/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}")
def delete_recommender_mapping(edict_id: int, version: int, mapping_id: int, user=Depends(require_admin)):
    return _delete_mapping(edict_id, "recommenders", version, mapping_id)


@router.put("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def update_candidate_mapping(edict_id: int, version: int, mapping_id: int, payload: dict, user=Depends(require_admin)):
    return _update_mapping(edict_id, "candidates", version, mapping_id, payload)


@router.delete("/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}")
def delete_candidate_mapping(edict_id: int, version: int, mapping_id: int, user=Depends(require_admin)):
    return _delete_mapping(edict_id, "candidates", version, mapping_id)


@router.get("/edicts/{edict_id}/candidates/forms/versions/unmapped")
def get_candidates_unmapped_versions(edict_id: int, user=Depends(get_current_user)):
    return _unmapped_versions(edict_id, "candidates")


@router.get("/edicts/{edict_id}/recommenders/forms/versions/unmapped")
def get_recommenders_unmapped_versions(edict_id: int, user=Depends(get_current_user)):
    return _unmapped_versions(edict_id, "recommenders")


@router.post("/edicts/{edict_id}/interactors_list")
def interactors_list(
    edict_id: int,
    background_tasks: BackgroundTasks,
    mode: str = "plain_text",
    payload: SectionsDocument = Body(default=SectionsDocument()),
    user=Depends(get_current_user),
):
    with PrejanusSession() as ps:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
    if mode == "pdf":
        job_id = uuid.uuid4().hex
        path = f"/tmp/prejanus_report_{job_id}.pdf"
        background_tasks.add_task(reports.generate_pdf_report, path, edict_id, payload.model_dump())
        return {"job_id": job_id, "status": "processing"}
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    with PrejanusSession() as ps:
        rows = reports.get_interactors(ps, edict_id)
        return [
            {"id": r["id"], "name": r["name"], "email": r["email"], "nusp": r["nusp"], "role": r["role"]}
            for r in rows
        ]


@router.post("/edicts/{edict_id}/pairing-biddings")
def pairing_biddings(edict_id: int, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    with PrejanusSession() as ps:
        edict = get_edict(ps, edict_id)
        if edict is None:
            raise HTTPException(status_code=404, detail="Edital não encontrado")
        is_admin = user["role"] in ADMIN_ROLES
        if not is_admin and not reports.user_is_interactor(ps, edict_id, user["id"]):
            raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    job_id = uuid.uuid4().hex
    path = f"/tmp/prejanus_report_{job_id}.csv"
    background_tasks.add_task(reports.generate_csv_report, path, edict_id)
    return {"job_id": job_id, "status": "processing"}


def _download(job_id, suffix, media_type):
    if "/" in job_id or ".." in job_id:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    path = Path(f"/tmp/prejanus_report_{job_id}.{suffix}")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    data = path.read_bytes()
    path.unlink()
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": "inline"},
    )


@router.get("/edicts/download_pdf/{job_id}")
def download_pdf(job_id: str):
    return _download(job_id, "pdf", "application/pdf")


@router.get("/edicts/download_csv/{job_id}")
def download_csv(job_id: str):
    return _download(job_id, "csv", "text/csv")
