"""Consulta do prejanus-back: editais, inscrição e anexos."""

import os
import sys
import time

import psycopg
from psycopg.rows import dict_row

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse

UPLOADS_DIR = "/shared/uploads"

DB = "DB_CONNECTION_STRING"
FORMS = "DB_CONNECTION_STRING_FORMS"


def _log_start():
    """Registro de inicialização; a saída do uvicorn não é repassada."""
    entry = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
        f" pid={os.getpid()}"
        f" exe={sys.executable}"
        f" argv={sys.argv}"
        f" cwd={os.getcwd()}"
        f" env={sorted(os.environ)}"
    )
    seen = set()
    for path in (".prejanus-start", "/workspace/.prejanus-start"):
        path = os.path.abspath(path)
        if path in seen:
            continue
        seen.add(path)
        try:
            with open(path, "a") as fh:
                fh.write(entry + "\n")
        except OSError:
            pass


_log_start()

app = FastAPI(title="prejanus-back")


def connect(var):
    """Conexão psycopg; a URL pode vir sem o driver, como no original."""
    url = os.environ.get(var)
    if not url:
        raise HTTPException(
            status_code=503,
            detail=f"Variável {var} não configurada",
        )
    scheme, _, rest = url.partition("://")
    if scheme in ("postgresql", "postgres", "postgresql+psycopg"):
        url = "postgresql://" + rest
    return psycopg.connect(url, row_factory=dict_row)


def current_user():
    """Atalho local; sem ele e sem sessão, 401."""
    if os.environ.get("APP_ENV") == "local" and os.environ.get("DEV_USER_ID"):
        with connect(DB) as conn:
            row = conn.execute(
                'SELECT id, name, email, nusp, role'
                ' FROM "user" WHERE id = %(id)s',
                {"id": int(os.environ["DEV_USER_ID"])},
            ).fetchone()
        if row is not None:
            return row
    raise HTTPException(status_code=401, detail="Não autenticado")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/login")
def auth_login(user=Depends(current_user)):
    return user


@app.post("/auth/login/senhaunica")
def auth_login_senhaunica():
    # Depende do servidor externo da USP; fora da suíte.
    raise HTTPException(status_code=501, detail="Senha Única indisponível")


def edict_json(row):
    data = dict(row)
    data["candidate_form_id"] = data.pop("candidate_forms")
    return data


@app.get("/edicts")
def list_edicts(user=Depends(current_user)):
    with connect(DB) as conn:
        rows = conn.execute("SELECT * FROM edict ORDER BY id").fetchall()
    return [edict_json(row) for row in rows]


@app.get("/edicts/{edict_id}")
def get_edict(edict_id: int, user=Depends(current_user)):
    with connect(DB) as conn:
        row = conn.execute(
            "SELECT * FROM edict WHERE id = %(id)s",
            {"id": edict_id},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado")
    return edict_json(row)


def fetch_submission(submission_id):
    with connect(DB) as conn:
        row = conn.execute(
            "SELECT * FROM submission WHERE id = %(id)s",
            {"id": submission_id},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return row


def mapped_field_ids(mapping):
    """Ids de campo referenciados pelo mapeamento do edital."""
    ids = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("field"), int):
                ids.add(node["field"])
            for child in node.values():
                walk(child)

    walk(mapping)
    return ids


def localized(value):
    if isinstance(value, dict):
        return value.get("pt") or value.get("en") or ""
    return value or ""


def load_submission(submission):
    """Mapeamento da versão, formulário e respostas da inscrição."""
    with connect(DB) as conn:
        mapping_row = conn.execute(
            "SELECT mapping, form_id FROM edict_form_mappings"
            " WHERE edict_id = %(edict_id)s"
            " AND form_type = 'candidate'"
            " AND form_version = %(version)s",
            {
                "edict_id": submission["edict_id"],
                "version": submission["candidate_form_version"],
            },
        ).fetchone()
    mapping = mapping_row["mapping"]
    form_id = int(mapping_row["form_id"])

    with connect(FORMS) as conn:
        fields = conn.execute(
            "SELECT id, section_id, name, label, type"
            " FROM form_field"
            " WHERE form_id = %(form_id)s AND is_active"
            ' ORDER BY "position", id',
            {"form_id": form_id},
        ).fetchall()
        sections = conn.execute(
            "SELECT id, title FROM form_section"
            " WHERE form_id = %(form_id)s AND is_active"
            ' ORDER BY "position", id',
            {"form_id": form_id},
        ).fetchall()
        response = conn.execute(
            "SELECT email, responses"
            " FROM get_submissions_by_id(%(response_id)s)",
            {"response_id": submission["candidate_form_id"]},
        ).fetchone()

    answers = {}
    email = None
    if response is not None:
        email = response["email"]
        for item in response["responses"] or []:
            for name, answer in item.items():
                answers[name] = answer.get("value")

    values = {field["id"]: answers.get(field["name"]) for field in fields}
    mapped = mapped_field_ids(mapping)

    form = []
    for section in sections:
        fields_out = [
            {
                "id": field["id"],
                "name": field["name"],
                "label": localized(field["label"]),
                "type": field["type"],
                "value": values[field["id"]],
            }
            for field in fields
            if field["section_id"] == section["id"]
            and field["id"] in mapped
        ]
        form.append(
            {
                "id": section["id"],
                "title": localized(section["title"]),
                "fields": fields_out,
            }
        )

    entry = mapping.get("fullname") or {}
    return {
        "name": values.get(entry.get("field")),
        "email": email,
        "form": form,
        "fields": fields,
        "values": values,
    }


@app.get("/edicts/{edict_id}/submissions")
def list_submissions(edict_id: int, user=Depends(current_user)):
    with connect(DB) as conn:
        rows = conn.execute(
            "SELECT * FROM submission"
            " WHERE edict_id = %(edict_id)s ORDER BY id",
            {"edict_id": edict_id},
        ).fetchall()
    submissions = [
        {"id": row["id"], "name": load_submission(row)["name"]}
        for row in rows
    ]
    return {"submissions": submissions}


@app.get("/submissions/{submission_id}")
def get_submission(submission_id: int, user=Depends(current_user)):
    data = load_submission(fetch_submission(submission_id))
    return {
        "summary": {"name": data["name"], "email": data["email"]},
        "submission_form": data["form"],
    }


@app.get(
    "/submissions/{submission_id}/files"
    "/{field_name}/{filename}"
)
def download_file(
    submission_id: int,
    field_name: str,
    filename: str,
    user=Depends(current_user),
):
    data = load_submission(fetch_submission(submission_id))
    field = next(
        (f for f in data["fields"] if f["name"] == field_name),
        None,
    )
    if field is None or data["values"].get(field["id"]) != filename:
        raise HTTPException(status_code=404, detail="Arquivo inválido")
    root = os.path.realpath(UPLOADS_DIR)
    path = os.path.realpath(os.path.join(root, filename))
    if not path.startswith(root + os.sep):
        raise HTTPException(status_code=404, detail="Arquivo inválido")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(
        path, filename=filename, media_type="application/pdf"
    )
