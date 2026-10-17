import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text

UPLOADS_DIR = "/shared/uploads"

prejanus = create_engine(os.environ["DB_CONNECTION_STRING"])
forms = create_engine(os.environ["DB_CONNECTION_STRING_FORMS"])

app = FastAPI()


def pick(label):
    label = label or {}
    return label.get("pt") or label.get("en")


# -- autenticação -----------------------------------------------------------


def get_user(user_id):
    with prejanus.connect() as conn:
        return conn.execute(
            text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :u'),
            {"u": user_id},
        ).mappings().first()


def require_user():
    if os.environ.get("APP_ENV") == "local" and os.environ.get("DEV_USER_ID"):
        user = get_user(int(os.environ["DEV_USER_ID"]))
        if user:
            return user
    raise HTTPException(status_code=401, detail="Não autenticado")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/auth/login")
def login(user=Depends(require_user)):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "nusp": user["nusp"],
        "role": user["role"],
    }


@app.post("/auth/login/senhaunica")
def senhaunica():
    # Fluxo OAuth da Senha Única: preservado na interface, fora da suíte.
    raise HTTPException(status_code=501, detail="Senha Única fora da suíte")


# -- consultas ao prejanus --------------------------------------------------


def get_edict(edict_id):
    with prejanus.connect() as conn:
        return conn.execute(
            text("SELECT * FROM edict WHERE id = :e"), {"e": edict_id}
        ).mappings().first()


def get_mapping(edict_id, version=None):
    with prejanus.connect() as conn:
        if version is None:
            return conn.execute(
                text(
                    "SELECT * FROM edict_form_mappings"
                    " WHERE edict_id = :e AND form_type = 'candidate' AND is_active"
                    " ORDER BY form_version DESC LIMIT 1"
                ),
                {"e": edict_id},
            ).mappings().first()
        return conn.execute(
            text(
                "SELECT * FROM edict_form_mappings"
                " WHERE edict_id = :e AND form_type = 'candidate'"
                " AND form_version = :v"
            ),
            {"e": edict_id, "v": version},
        ).mappings().first()


def edict_json(edict, mapping):
    form_id = mapping["form_id"] if mapping else None
    if form_id is None:
        form_id = edict["candidate_forms"]
    return {
        "id": edict["id"],
        "title": edict["title"],
        "description": edict["description"],
        "year": edict["year"],
        "semester": edict["semester"],
        "type": edict["type"],
        "phase": edict["phase"],
        "is_open": edict["is_open"],
        "closed_date": edict["closed_date"].isoformat() if edict["closed_date"] else None,
        "candidate_form_id": str(form_id) if form_id is not None else None,
    }


@app.get("/edicts")
def list_edicts(user=Depends(require_user)):
    with prejanus.connect() as conn:
        edicts = conn.execute(text("SELECT * FROM edict ORDER BY id")).mappings().all()
    return [edict_json(e, get_mapping(e["id"])) for e in edicts]


@app.get("/edicts/{edict_id}")
def get_edict_route(edict_id: int, user=Depends(require_user)):
    edict = get_edict(edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict_json(edict, get_mapping(edict_id))


# -- consultas ao forms ------------------------------------------------------


def get_response(response_id):
    with forms.connect() as conn:
        return conn.execute(
            text(
                "SELECT id, form_id, email, submitted_at FROM form_response"
                " WHERE id = :r AND submitted_at IS NOT NULL"
            ),
            {"r": response_id},
        ).mappings().first()


def response_values(response_id):
    with forms.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ff.id, ff.name, r.value FROM responses r"
                " JOIN form_field ff ON ff.id = r.field_id"
                " WHERE r.response_id = :r"
            ),
            {"r": response_id},
        ).mappings().all()
    by_name = {row["name"]: row["value"] for row in rows}
    by_id = {row["id"]: row["value"] for row in rows}
    return by_name, by_id


def form_sections_fields(form_id):
    with forms.connect() as conn:
        sections = conn.execute(
            text(
                'SELECT id, title, description FROM form_section'
                ' WHERE form_id = :f AND is_active ORDER BY "position", id'
            ),
            {"f": form_id},
        ).mappings().all()
        fields = conn.execute(
            text(
                'SELECT id, section_id, name, label, type FROM form_field'
                ' WHERE form_id = :f AND is_active ORDER BY "position", id'
            ),
            {"f": form_id},
        ).mappings().all()
    return sections, fields


# -- inscrições --------------------------------------------------------------


def load_submission(submission_id):
    with prejanus.connect() as conn:
        return conn.execute(
            text("SELECT * FROM submission WHERE id = :s"), {"s": submission_id}
        ).mappings().first()


def submission_context(submission):
    mapping_row = get_mapping(
        submission["edict_id"], version=submission["candidate_form_version"]
    ) or get_mapping(submission["edict_id"])
    mapping = mapping_row["mapping"] if mapping_row else {}
    response = get_response(submission["candidate_form_id"])
    if not response:
        raise HTTPException(status_code=404, detail="Inscrição sem resposta no forms")
    by_name, by_id = response_values(submission["candidate_form_id"])
    name_field = (mapping.get("name") or {}).get("field")
    return mapping, response, by_name, by_id, by_id.get(name_field)


@app.get("/edicts/{edict_id}/submissions")
def edict_submissions(edict_id: int, user=Depends(require_user)):
    edict = get_edict(edict_id)
    if not edict:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    with prejanus.connect() as conn:
        submissions = conn.execute(
            text("SELECT * FROM submission WHERE edict_id = :e ORDER BY id"),
            {"e": edict_id},
        ).mappings().all()
    out = []
    for sub in submissions:
        _, response, _, _, name = submission_context(sub)
        out.append(
            {
                "id": sub["id"],
                "name": name,
                "email": response["email"],
                "stats": sub["stats"],
                "created_at": sub["created_at"].isoformat() if sub["created_at"] else None,
            }
        )
    return {"submissions": out}


@app.get("/submissions/{submission_id}")
def submission_detail(submission_id: int, user=Depends(require_user)):
    sub = load_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    mapping, response, by_name, by_id, name = submission_context(sub)
    sections, fields = form_sections_fields(response["form_id"])
    submission_form = []
    for section in sections:
        section_fields = []
        for field in fields:
            if field["section_id"] != section["id"]:
                continue
            if not mapping.get(field["name"]):
                continue
            section_fields.append(
                {
                    "id": field["id"],
                    "name": field["name"],
                    "label": pick(field["label"]),
                    "type": field["type"],
                    "value": by_name.get(field["name"]),
                }
            )
        submission_form.append(
            {
                "id": section["id"],
                "title": pick(section["title"]),
                "description": pick(section["description"]),
                "fields": section_fields,
            }
        )
    return {
        "summary": {
            "id": sub["id"],
            "name": name,
            "email": response["email"],
            "edict_id": sub["edict_id"],
            "stats": sub["stats"],
            "created_at": sub["created_at"].isoformat() if sub["created_at"] else None,
        },
        "submission_form": submission_form,
    }


@app.get("/submissions/{submission_id}/files/{field_name}/{filename}")
def download_file(
    submission_id: int,
    field_name: str,
    filename: str,
    user=Depends(require_user),
):
    sub = load_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    mapping, _, by_name, _, _ = submission_context(sub)
    if not mapping.get(field_name):
        raise HTTPException(status_code=404, detail="Campo fora do mapeamento do edital")
    stored = by_name.get(field_name)
    if stored != filename:
        raise HTTPException(status_code=404, detail="Arquivo não pertence a este campo")
    if not filename or filename in (".", "..") or os.path.basename(filename) != filename:
        raise HTTPException(status_code=404, detail="Caminho inválido")
    full = os.path.realpath(os.path.join(UPLOADS_DIR, filename))
    if not full.startswith(os.path.realpath(UPLOADS_DIR) + os.sep):
        raise HTTPException(status_code=404, detail="Caminho fora do volume")
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(full, filename=filename)