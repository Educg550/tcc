from typing import Any


def is_leaf(node: Any) -> bool:
    return (
        isinstance(node, dict)
        and isinstance(node.get("section"), int)
        and isinstance(node.get("field"), int)
    )


def iter_leaves(tree: Any, prefix: tuple = ()):
    """Yields (path, section_id, field_id) for every leaf in the mapping tree."""
    if tree is None:
        return
    if is_leaf(tree):
        yield prefix, tree["section"], tree["field"]
        return
    if isinstance(tree, dict):
        for key, value in tree.items():
            yield from iter_leaves(value, prefix + (key,))


def validate_tree(tree: Any, valid_pairs: set[tuple[int, int]]) -> bool:
    for _, section, field in iter_leaves(tree):
        if (section, field) not in valid_pairs:
            return False
    return True


def extract_values(tree: Any, answers: dict[int, str]) -> dict[tuple, str]:
    """Maps every leaf path to the answer value of its field (None when absent)."""
    values: dict[tuple, str | None] = {}
    for path, _section, field in iter_leaves(tree):
        values[path] = answers.get(field)
    return values


def pick(values: dict[tuple, Any], *path: str, default=None):
    if path in values:
        return values[path]
    key = path[-1]
    for p, v in values.items():
        if p and p[-1] == key:
            return v
    return default


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "yes", "sim", "1", "on")


def _int_or(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _str_or(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_candidate_values(values: dict[tuple, Any]) -> dict:
    """Builds the candidate summary fields from the extracted mapping values."""
    poscomp_year = pick(values, "poscomp", "year")
    poscomp_score = pick(values, "poscomp", "score")
    poscomp = None
    if poscomp_year not in (None, "") or poscomp_score not in (None, ""):
        poscomp = {"year": _int_or(poscomp_year), "score": _str_or(poscomp_score)}
    return {
        "name": _str_or(pick(values, "name")),
        "email": _str_or(pick(values, "email")),
        "phone_number": _str_or(pick(values, "phone_number")),
        "nationality": _str_or(pick(values, "nationality")),
        "personal_website": _str_or(pick(values, "personal_website")),
        "gender": _str_or(pick(values, "gender")),
        "birth_date": _str_or(pick(values, "birth_date")),
        "current_occupation": pick(values, "current_occupation"),
        "lattes_curriculum": _str_or(pick(values, "lattes_curriculum")),
        "disabilities": _truthy(pick(values, "disabilities")),
        "ethnicity_race": _truthy(pick(values, "ethnicity_race")),
        "graduation": {
            "country": _str_or(pick(values, "graduation", "country")),
            "course": _str_or(pick(values, "graduation", "course")),
            "institution": _str_or(pick(values, "graduation", "institution")),
            "year": _int_or(pick(values, "graduation", "year")),
        },
        "poscomp": poscomp,
        "research": {
            "program": _str_or(pick(values, "research", "program")),
            "semester": _str_or(pick(values, "research", "semester")),
            "field": {
                "primary": _str_or(pick(values, "research", "field", "primary")),
                "secondary": _str_or(pick(values, "research", "field", "secondary")),
            },
            "will_apply_scholarship": _truthy(
                pick(values, "research", "will_apply_scholarship")
            ),
            "dedication_level": _str_or(pick(values, "research", "dedication_level")),
        },
    }
