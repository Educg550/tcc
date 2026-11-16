"""Utilidades sobre as árvores de mapeamento (edict_form_mappings.mapping)."""

import unicodedata


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    return "".join(c if c.isalnum() else "" for c in value.lower())


def is_leaf(node) -> bool:
    return (
        isinstance(node, dict)
        and "section" in node
        and "field" in node
        and set(node.keys()) <= {"section", "field"}
    )


def flatten(tree, prefix=()) -> dict[tuple, dict]:
    """Transforma a árvore em um dicionário caminho -> folha."""
    leaves: dict[tuple, dict] = {}
    if not isinstance(tree, dict):
        return leaves
    for key, value in tree.items():
        if is_leaf(value):
            leaves[prefix + (key,)] = value
        elif isinstance(value, dict):
            leaves.update(flatten(value, prefix + (key,)))
        # valor nulo ou outro tipo: propriedade não mapeada
    return leaves


SYNONYMS = {
    "name": ["name", "nome", "nomecompleto", "fullname", "full_name"],
    "email": ["email", "emaildeacesso", "acessemail", "emaildeacessoaoplataforma"],
    "phone_number": ["phone", "phonenumber", "telefone", "celular"],
    "nationality": ["nationality", "nacionalidade"],
    "personal_website": ["website", "personalwebsite", "site", "pagina"],
    "gender": ["gender", "genero", "sexo"],
    "birth_date": ["birthdate", "datadenascimento", "nascimento"],
    "country": ["country", "pais"],
    "course": ["course", "curso"],
    "institution": ["institution", "instituicao"],
    "graduation_year": ["year", "ano", "graduationyear", "anodeconclusao", "conclusao"],
    "poscomp_year": ["poscompyear", "anoposcomp", "anodoposcomp", "poscomp_ano"],
    "poscomp_score": ["score", "pontuacao", "nota", "poscompscore", "notaposcomp"],
    "current_occupation": ["currentoccupation", "ocupacao", "ocupacaoatual"],
    "program": ["program", "programa"],
    "semester": ["semester", "semestre"],
    "primary": ["primary", "principal", "areaprincipal"],
    "secondary": ["secondary", "secundaria", "areasecundaria"],
    "will_apply_scholarship": ["willapplyscholarship", "bolsa", "scholarship"],
    "dedication_level": ["dedicationlevel", "dedicacao", "niveldededicacao"],
    "lattes_curriculum": ["lattes", "lattescurriculum", "curriculolattes", "curriculo"],
    "disabilities": ["disabilities", "deficiencia", "pcd"],
    "ethnicity_race": ["ethnicity", "ethnicityrace", "etnia", "raca", "cor"],
    "candidate_email": [
        "candidateemail", "emaildocandidato", "candidatoemail", "emailcandidato",
    ],
    "candidate_name": [
        "candidatename", "nomedocandidato", "candidatonome", "nomecandidato",
    ],
    "recommender_name": [
        "recommendername", "nomedorecomendante", "recomendantenome", "nomerecomendante",
    ],
    "recommender_email": [
        "recommenderemail", "emaildorecomendante", "recomendanteemail",
    ],
}


def find_leaf(leaves: dict[tuple, dict], prop: str):
    targets = {normalize_key(s) for s in SYNONYMS.get(prop, [prop])}
    for path, leaf in leaves.items():
        if normalize_key(path[-1]) in targets:
            return leaf
    for path, leaf in leaves.items():
        if any(normalize_key(part) in targets for part in path):
            return leaf
    return None


def get_value(leaves, values: dict[int, str], prop: str):
    leaf = find_leaf(leaves, prop)
    if leaf is None:
        return None
    return values.get(leaf["field"])


def validate_tree(tree, valid_fields: set[int], valid_pairs: set[tuple[int, int]]):
    """Valida as folhas da árvore contra os campos do formulário."""
    for leaf in flatten(tree).values():
        try:
            section = int(leaf["section"])
            field = int(leaf["field"])
        except (TypeError, ValueError):
            return False
        if field not in valid_fields or (section, field) not in valid_pairs:
            return False
    return True


def merge_trees(trees: list[dict]) -> dict:
    merged: dict = {}

    def _merge(base, other):
        for key, value in other.items():
            if is_leaf(value) or not isinstance(value, dict) or key not in base:
                base[key] = value
            else:
                _merge(base[key], value)

    for tree in trees:
        if isinstance(tree, dict):
            _merge(merged, tree)
    return merged
