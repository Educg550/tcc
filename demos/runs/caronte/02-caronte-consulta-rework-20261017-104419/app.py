import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text

UPLOADS_DIR = "/shared/uploads"

app = FastAPI(title="Caronte")

prejanus_engine = create_engine(os.environ["DB_CONNECTION_STRING"])
forms_engine = create_engine(os.environ["DB_CONNECTION_STRING_FORMS"])


def current_user():
    if os.environ.get("APP_ENV") == "local" and os.environ.get("DEV_USER_ID"):
        with prejanus_engine.connect() as conn:
            row = conn.execute(
                text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :i'),
                {"i": int(os.environ["DEV_USER_ID"])},
            ).mappings().first()
        if row:
            return dict(row)
    raise HTTPException(status_code=401)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/auth/login")
def login(user=Depends(current_user)):
    return user


@app.get("/edicts")
def list_edicts(user=Depends(current_user)):
    with prejanus_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, description, year, semester, type, phase,"
                " is_open, closed_date FROM edict ORDER BY id"
            )
        ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/edicts/{edict_id}")
def get_edict(edict_id: int, user=Depends(current_user)):
    with prejanus_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, title, description, candidate_forms, recommenders_forms,"
                " year, semester, type, phase, is_open, closed_date FROM edict"
                " WHERE id = :i"
            ),
            {"i": edict_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404)
    edict = dict(row)
    return {
        "id": edict["id"],
        "title": edict["title"],
        "description": edict["description"],
        "candidate_form_id": edict["candidate_forms"],
        "recommenders_form_ids": edict["recommenders_forms"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "phase": edict["phase"],
        "is_open": edict["is_open"],
        "closed_date": edict["closed_date"],
    }


def _candidate_form_id(edict_id: int) -> int:
    with prejanus_engine.connect() as conn:
        row = conn.execute(
            text("SELECT candidate_forms FROM edict WHERE id = :i"), {"i": edict_id}
        ).first()
    if not row:
        raise HTTPException(status_code=404)
    return int(row[0])


@app.get("/edicts/{edict_id}/submissions")
def edict_submissions(edict_id: int, user=Depends(current_user)):
    form_id = _candidate_form_id(edict_id)
    with forms_engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, email, submitted_at FROM form_response"
                " WHERE form_id = :f AND submitted_at IS NOT NULL ORDER BY id"
            ),
            {"f": form_id},
        ).mappings().all()
    return {"submissions": [dict(r) for r in rows]}


@app.get("/submissions/{submission_id}")
def submission_detail(submission_id: int, user=Depends(current_user)):
    with forms_engine.connect() as conn:
        resp = conn.execute(
            text(
                "SELECT id, form_id, email, submitted_at FROM form_response"
                " WHERE id = :i AND submitted_at IS NOT NULL"
            ),
            {"i": submission_id},
        ).mappings().first()
        if not resp:
            raise HTTPException(status_code=404)
        sections = conn.execute(
            text(
                "SELECT id, title FROM form_section"
                " WHERE form_id = :f AND is_active ORDER BY position, id"
            ),
            {"f": resp["form_id"]},
        ).mappings().all()
        fields = conn.execute(
            text(
                "SELECT id, section_id, name, label, type, required FROM form_field"
                " WHERE form_id = :f AND is_active ORDER BY position, id"
            ),
            {"f": resp["form_id"]},
        ).mappings().all()
        values = dict(
            conn.execute(
                text("SELECT field_id, value FROM responses WHERE response_id = :i"),
                {"i": submission_id},
            ).all()
        )

    submission_form = []
    for section in sections:
        section_fields = []
        for field in fields:
            if field["section_id"] != section["id"]:
                continue
            section_fields.append(
                {
                    "name": field["name"],
                    "label": field["label"],
                    "type": field["type"],
                    "required": field["required"],
                    "value": values.get(field["id"]),
                }
            )
        submission_form.append(
            {"id": section["id"], "title": section["title"], "fields": section_fields}
        )

    name = next(
        (values.get(f["id"]) for f in fields if f["name"] == "fullname"), None
    )
    return {
        "id": resp["id"],
        "summary": {"name": name, "email": resp["email"]},
        "submitted_at": resp["submitted_at"],
        "submission_form": submission_form,
    }


def _find_upload(filename: str):
    for dirpath, _, files in os.walk(UPLOADS_DIR):
        if filename in files:
            return os.path.join(dirpath, filename)
    return None


@app.get("/submissions/{submission_id}/files/{field}/{filename}")
def download_file(
    submission_id: int, field: str, filename: str, user=Depends(current_user)
):
    with forms_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT r.value FROM responses r"
                " JOIN form_field f ON f.id = r.field_id"
                " WHERE r.response_id = :i AND f.name = :n"
            ),
            {"i": submission_id, "n": field},
        ).first()
    if not row or row[0] != filename:
        raise HTTPException(status_code=404)
    path = _find_upload(filename)
    if not path:
        raise HTTPException(status_code=404)
    return FileResponse(path, filename=filename)