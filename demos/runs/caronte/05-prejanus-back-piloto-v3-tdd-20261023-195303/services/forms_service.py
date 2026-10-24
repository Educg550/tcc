from sqlalchemy import text


def _localized(value):
    if isinstance(value, dict):
        return value.get("pt") or value.get("en") or ""
    return value or ""


def get_form(fs, form_id):
    return fs.execute(text("select * from form where id=:i"), {"i": form_id}).mappings().first()


def form_dict(row):
    return {
        "id": row["id"],
        "title": _localized(row["title"]),
        "description": _localized(row["description"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "phase": row["phase"],
        "tags": row["tags"] or {},
        "version": row["version"],
    }


def get_sections(fs, form_id, version=None):
    if version is None:
        rows = fs.execute(
            text('select * from form_section where form_id=:f and is_active=true order by "position", id'),
            {"f": form_id},
        ).mappings().all()
    else:
        rows = fs.execute(
            text(
                'select * from form_section where form_id=:f '
                "and (version=:v or (:v = 1 and version is null)) "
                'order by "position", id'
            ),
            {"f": form_id, "v": version},
        ).mappings().all()
    if not rows:
        rows = fs.execute(
            text('select * from form_section where form_id=:f order by "position", id'),
            {"f": form_id},
        ).mappings().all()
    return rows


def section_dict(row):
    return {
        "id": row["id"],
        "form_id": row["form_id"],
        "title": _localized(row["title"]),
        "description": _localized(row["description"]),
        "position": row["position"],
        "is_active": row["is_active"],
        "version": row["version"],
    }


def get_fields(fs, section_id):
    return fs.execute(
        text('select * from form_field where section_id=:s and is_active=true order by "position", id'),
        {"s": section_id},
    ).mappings().all()


def get_all_fields(fs, form_id):
    return fs.execute(
        text(
            'select ff.* from form_field ff join form_section s on s.id = ff.section_id '
            'where s.form_id=:f order by s."position", ff."position", ff.id'
        ),
        {"f": form_id},
    ).mappings().all()


def field_dict(row, value=None):
    return {
        "id": row["id"],
        "form_id": row["form_id"],
        "section_id": row["section_id"],
        "name": row["name"],
        "label": _localized(row["label"]),
        "description": _localized(row["description"]),
        "type": row["type"],
        "placeholder": row["placeholder"],
        "required": row["required"],
        "disabled": row["disabled"],
        "prefix": row["prefix"],
        "position": row["position"],
        "value": value,
    }


def get_form_response(fs, response_id):
    return fs.execute(
        text("select * from form_response where id=:i"), {"i": response_id}
    ).mappings().first()


def get_values(fs, response_id):
    rows = fs.execute(
        text("select field_id, value from responses where response_id=:r"), {"r": response_id}
    ).all()
    return {r[0]: r[1] for r in rows}
