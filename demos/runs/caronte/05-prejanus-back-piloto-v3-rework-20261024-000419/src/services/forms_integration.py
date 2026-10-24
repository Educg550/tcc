"""Acesso ao banco do Forms: formulários, seções, campos, respostas e mapeamentos."""
from sqlalchemy import text

EDICT_PHASE_TO_FORM = {"inscricoes": "Registration", "homologacao": "Approval"}

CANDIDATE_LEAVES = {
    "name", "email", "phone_number", "birth_date", "nationality",
    "personal_website", "gender", "current_occupation", "lattes_curriculum",
    "disabilities", "ethnicity_race", "entry_semester",
}
CANDIDATE_GROUPS = {
    "graduation": ({"country", "course", "institution", "year"}, {}),
    "poscomp": ({"year", "score"}, {}),
    "research": (
        {"program", "semester", "will_apply_scholarship", "dedication_level"},
        {"field": ({"primary", "secondary"}, {})},
    ),
}
RECOMMENDER_LEAVES = {
    "fullname", "rating", "affiliation", "sent",
    "candidate", "candidate_email", "candidate_name",
}
RECOMMENDER_GROUPS: dict = {}


def form_phase_for(edict_phase: str) -> str:
    return EDICT_PHASE_TO_FORM.get(edict_phase, "Completed")


def get_form(fdb, form_id):
    return fdb.execute(
        text("SELECT * FROM form WHERE id = :i"), {"i": form_id}
    ).mappings().first()


def get_response(fdb, response_id):
    return fdb.execute(
        text("SELECT * FROM form_response WHERE id = :i"), {"i": response_id}
    ).mappings().first()


def response_values(fdb, response_id) -> dict:
    rows = fdb.execute(
        text("SELECT field_id, value FROM responses WHERE response_id = :r"),
        {"r": response_id},
    ).mappings().all()
    return {r["field_id"]: r["value"] for r in rows}


def extract_data(values: dict, mapping) -> dict:
    def walk(node):
        if node is None:
            return None
        if isinstance(node, dict) and "section" in node and "field" in node:
            return values.get(node["field"])
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        return node

    if not isinstance(mapping, dict):
        return {}
    return walk(mapping) or {}


def form_sections(fdb, form_id, version=None):
    if version is None:
        return fdb.execute(
            text("SELECT * FROM form_section WHERE form_id = :f AND is_active = true ORDER BY position, id"),
            {"f": form_id},
        ).mappings().all()
    rows = fdb.execute(
        text("SELECT * FROM form_section WHERE form_id = :f AND version = :v ORDER BY position, id"),
        {"f": form_id, "v": version},
    ).mappings().all()
    if rows:
        return rows
    return fdb.execute(
        text("SELECT * FROM form_section WHERE form_id = :f ORDER BY position, id"),
        {"f": form_id},
    ).mappings().all()


def section_fields(fdb, section_id, version=None, only_active=False):
    base = "SELECT * FROM form_field WHERE section_id = :s"
    if only_active:
        base += " AND is_active = true"
    if version is not None:
        rows = fdb.execute(
            text(base + " AND version = :v ORDER BY position, id"),
            {"s": section_id, "v": version},
        ).mappings().all()
        if rows:
            return rows
    return fdb.execute(
        text(base + " ORDER BY position, id"), {"s": section_id}
    ).mappings().all()


def form_versions(fdb, form_id) -> list[int]:
    rows = fdb.execute(
        text("SELECT version FROM form_section WHERE form_id = :f "
             "UNION SELECT version FROM form_field WHERE form_id = :f"),
        {"f": form_id},
    )
    return sorted({r[0] for r in rows})


def set_form_phase(fdb, form_id, phase: str) -> None:
    fdb.execute(
        text("UPDATE form SET phase = CAST(:p AS form_phase) WHERE id = :i"),
        {"p": phase, "i": form_id},
    )
    fdb.commit()


def validate_mapping_tree(fdb, form_id, version, tree, kind: str) -> None:
    if not isinstance(tree, dict) or not tree:
        raise ValueError("mapeamento deve ser um objeto não vazio")
    field_rows = fdb.execute(
        text("SELECT id, name, version FROM form_field WHERE form_id = :f"),
        {"f": form_id},
    ).mappings().all()
    if not field_rows:
        raise ValueError("formulário sem campos")
    field_ids = {r["id"] for r in field_rows}
    field_names = {r["name"] for r in field_rows}
    versioned = {r["id"] for r in field_rows if r["version"] == version}
    sections = {
        r["id"] for r in fdb.execute(
            text("SELECT id FROM form_section WHERE form_id = :f"), {"f": form_id}
        ).mappings().all()
    }

    leaves, groups = (
        (CANDIDATE_LEAVES, CANDIDATE_GROUPS)
        if kind == "candidate"
        else (RECOMMENDER_LEAVES, RECOMMENDER_GROUPS)
    )

    def walk(node, allowed_leaves, allowed_groups):
        if not isinstance(node, dict):
            raise ValueError("nó de mapeamento inválido")
        for key, value in node.items():
            if value is None:
                continue
            if key in allowed_groups:
                group_leaves, group_groups = allowed_groups[key]
                walk(value, group_leaves, group_groups)
            elif key in allowed_leaves or key in field_names:
                if (
                    not isinstance(value, dict)
                    or "section" not in value
                    or "field" not in value
                ):
                    raise ValueError(f"folha inválida em '{key}'")
                if value["section"] not in sections or value["field"] not in field_ids:
                    raise ValueError(f"referência inválida em '{key}'")
                if versioned and value["field"] not in versioned:
                    raise ValueError(f"campo fora da versão em '{key}'")
            else:
                raise ValueError(f"chave desconhecida: '{key}'")

    walk(tree, leaves, groups)
