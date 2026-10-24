import unicodedata


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip().replace(" ", "_")


def flatten_mapping(tree, prefix=""):
    """Flatten a mapping tree into {dotted.path: leaf-or-None}."""
    flat = {}
    if not isinstance(tree, dict):
        return flat
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten_mapping(value, path))
        else:
            flat[path] = value
    return flat


def leaf_value(leaf, values_by_field):
    if not isinstance(leaf, dict):
        return None
    return values_by_field.get(leaf.get("field"))


def flat_values(tree, values_by_field):
    return {k: leaf_value(v, values_by_field) for k, v in flatten_mapping(tree).items()}


def _match_score(key_norm: str, alias_norm: str) -> int:
    if key_norm == alias_norm:
        return 3
    if key_norm.endswith("." + alias_norm) or alias_norm.endswith("." + key_norm):
        return 2
    last = key_norm.rsplit(".", 1)[-1]
    if last == alias_norm:
        return 1
    return 0


def resolve(flat: dict, aliases: list[str]):
    """Find the value for the best-matching alias among flattened mapping keys."""
    best_score = 0
    best_value = None
    for key, value in flat.items():
        key_norm = _norm(key)
        for alias in aliases:
            score = _match_score(key_norm, _norm(alias))
            if score > best_score and value is not None:
                best_score = score
                best_value = value
    return best_value


CANDIDATE_ALIASES = {
    "name": ["name", "nome", "full_name", "complete_name", "personal.name", "personal_data.name"],
    "email": ["email", "email_address", "access_email", "personal.email", "contact.email"],
    "phone_number": ["phone", "phone_number", "telefone", "cellphone", "contact.phone"],
    "nationality": ["nationality", "nacionalidade"],
    "personal_website": ["website", "personal_website", "site", "homepage", "lattes_website"],
    "gender": ["gender", "sexo", "sex"],
    "birth_date": ["birth_date", "birthdate", "data_nascimento", "birthday", "date_birth"],
    "graduation.country": ["graduation.country", "country", "pais", "graduation_country"],
    "graduation.course": ["graduation.course", "course", "curso", "graduation_course"],
    "graduation.institution": ["graduation.institution", "institution", "instituicao", "university"],
    "graduation.year": ["graduation.year", "graduation_year", "year_graduation", "conclusion_year"],
    "poscomp.year": ["poscomp.year", "poscomp_year", "poscomp"],
    "poscomp.score": ["poscomp.score", "poscomp_score", "score", "nota"],
    "current_occupation": ["current_occupation", "occupation", "ocupacao", "current_job"],
    "research.program": ["research.program", "program", "programa", "course_program"],
    "research.semester": ["research.semester", "semester", "semestre", "entry_semester"],
    "research.field.primary": ["research.field.primary", "primary", "primary_field", "field.primary",
                                "main_field", "area"],
    "research.field.secondary": ["research.field.secondary", "secondary", "secondary_field", "field.secondary"],
    "research.will_apply_scholarship": ["will_apply_scholarship", "scholarship", "bolsa",
                                        "research.will_apply_scholarship"],
    "research.dedication_level": ["dedication_level", "dedication", "dedicacao", "level"],
    "lattes_curriculum": ["lattes_curriculum", "lattes", "curriculum_lattes", "curriculum"],
    "disabilities": ["disabilities", "deficiency", "deficiencia", "pcd"],
    "ethnicity_race": ["ethnicity_race", "ethnicity", "raca", "etnia", "race"],
}

RECOMMENDER_ALIASES = {
    "name": ["name", "nome", "recommender.name", "full_name"],
    "email": ["email", "recommender.email", "email_address"],
    "text": ["text", "recommendation", "recommendation_text", "letter", "texto", "comments",
             "recommender.text", "opinion"],
    "candidate_name": ["candidate.name", "candidate_name", "student.name", "student_name",
                       "nome_candidato", "candidato"],
    "candidate_email": ["candidate.email", "candidate_email", "student.email", "student_email",
                        "email_candidato"],
}


def extract_candidate(flat: dict):
    data = {}
    for target, aliases in CANDIDATE_ALIASES.items():
        data[target] = resolve(flat, aliases)
    return data


def extract_recommender(flat: dict):
    data = {}
    for target, aliases in RECOMMENDER_ALIASES.items():
        data[target] = resolve(flat, aliases)
    return data


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_bool(value):
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "1", "yes", "sim", "on")


def build_candidate_payload(data: dict):
    """Adapt extracted raw values to the SubmissionSchema shape."""
    poscomp = None
    if data.get("poscomp.year") or data.get("poscomp.score"):
        poscomp = {"year": _to_int(data.get("poscomp.year")) or 0,
                   "score": str(data.get("poscomp.score") or "")}
    return {
        "name": str(data.get("name") or ""),
        "email": str(data.get("email") or ""),
        "phone_number": str(data.get("phone_number") or ""),
        "nationality": str(data.get("nationality") or ""),
        "personal_website": str(data.get("personal_website") or ""),
        "gender": str(data.get("gender") or ""),
        "birth_date": str(data.get("birth_date") or ""),
        "graduation": {
            "country": str(data.get("graduation.country") or ""),
            "course": str(data.get("graduation.course") or ""),
            "institution": str(data.get("graduation.institution") or ""),
            "year": _to_int(data.get("graduation.year")) or 0,
        },
        "poscomp": poscomp,
        "current_occupation": data.get("current_occupation"),
        "research": {
            "program": str(data.get("research.program") or ""),
            "semester": str(data.get("research.semester") or ""),
            "field": {
                "primary": str(data.get("research.field.primary") or ""),
                "secondary": str(data.get("research.field.secondary") or ""),
            },
            "will_apply_scholarship": _to_bool(data.get("research.will_apply_scholarship")),
            "dedication_level": str(data.get("research.dedication_level") or ""),
        },
        "lattes_curriculum": str(data.get("lattes_curriculum") or ""),
        "disabilities": _to_bool(data.get("disabilities")),
        "ethnicity_race": _to_bool(data.get("ethnicity_race")),
    }


def validate_tree(tree, valid_pairs: set) -> bool:
    """Check every leaf references a valid (section, field) pair of the version."""
    if not isinstance(tree, dict):
        return False
    for value in tree.values():
        if value is None:
            continue
        if isinstance(value, dict):
            if "section" in value and "field" in value:
                if (value["section"], value["field"]) not in valid_pairs:
                    return False
            elif not validate_tree(value, valid_pairs):
                return False
        else:
            return False
    return True
