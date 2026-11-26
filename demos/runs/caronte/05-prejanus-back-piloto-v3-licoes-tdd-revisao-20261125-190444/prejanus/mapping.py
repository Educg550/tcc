"""Utilitários para interpretar árvores de mapeamento de formulários."""


def flatten_tree(tree: dict | None) -> dict:
    """Achata a árvore em caminhos 'a_b_c' -> folha {'section','field'} ou None."""
    out: dict = {}

    def walk(node, prefix):
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            path = prefix + [str(key).lower()]
            if isinstance(value, dict) and "section" in value and "field" in value:
                out["_".join(path)] = value
            elif value is None:
                out["_".join(path)] = None
            elif isinstance(value, dict):
                walk(value, path)

    walk(tree or {}, [])
    return out


def _leaf_for(flat: dict, name: str):
    n = name.lower()
    if n in flat:
        return flat[n]
    for path, leaf in flat.items():
        if path.endswith("_" + n) or path.endswith("/" + n):
            return leaf
    for path, leaf in flat.items():
        if path.endswith(n):
            return leaf
    return None


def value_at(flat: dict, values: dict, name: str, default=""):
    leaf = _leaf_for(flat, name)
    if leaf is None:
        return default
    return values.get(leaf.get("field"), default)


def leaves(tree: dict) -> list:
    result = []

    def walk(node):
        if not isinstance(node, dict):
            return
        for value in node.values():
            if isinstance(value, dict) and "section" in value and "field" in value:
                result.append(value)
            elif isinstance(value, dict):
                walk(value)

    walk(tree or {})
    return result


def to_int(value) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "yes", "sim", "1", "verdadeiro")


def find_candidate_email(flat: dict, values: dict) -> str | None:
    """Extrai o e-mail do candidato a partir do mapeamento do recomendador."""
    for path, leaf in flat.items():
        if leaf is None:
            continue
        if "candidate" in path and "email" in path:
            val = values.get(leaf.get("field"))
            if val:
                return str(val).strip().lower()
    leaf = flat.get("email")
    if leaf is not None:
        val = values.get(leaf.get("field"))
        if val:
            return str(val).strip().lower()
    return None


def find_candidate_name(flat: dict, values: dict) -> str | None:
    for path, leaf in flat.items():
        if leaf is None:
            continue
        if "candidate" in path and "name" in path:
            val = values.get(leaf.get("field"))
            if val:
                return str(val).strip()
    leaf = flat.get("name")
    if leaf is not None:
        val = values.get(leaf.get("field"))
        if val:
            return str(val).strip()
    return None


def normalize_name(name: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.lower().split())
