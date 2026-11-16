"""Extração de dados das respostas do Forms usando as árvores de mapeamento.

As árvores de mapeamento são dicionários aninhados cujas folhas são
``{"section": id, "field": id}`` (ou ``None`` para propriedade não mapeada).
Como as chaves intermediárias variam entre instalações, a extração aceita
sinônimos (pt/en) tanto no caminho da árvore quanto no nome/rótulo do campo
do Forms, usado como fallback.
"""

import unicodedata


def norm(value) -> str:
    if not value:
        return ""
    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c.lower() for c in s if c.isalnum())


def flatten_mapping(node, path=None, out=None):
    """Retorna [(segmentos_do_caminho, folha)] para as folhas da árvore."""
    if out is None:
        out = []
    if isinstance(node, dict):
        if (
            "section" in node
            and "field" in node
            and isinstance(node.get("section"), int)
            and isinstance(node.get("field"), int)
        ):
            out.append((path or [], node))
        else:
            for key, value in node.items():
                flatten_mapping(value, (path or []) + [key], out)
    return out


def _find_leaf(flat, synonyms):
    syn = {norm(s) for s in synonyms}
    for segs, leaf in flat:
        if norm(".".join(str(s) for s in segs)) in syn:
            return leaf
    for segs, leaf in flat:
        if segs and norm(segs[-1]) in syn:
            return leaf
    for segs, leaf in flat:
        if any(norm(s) in syn for s in segs):
            return leaf
    return None


def _find_by_field(fields, values, synonyms):
    syn = {norm(s) for s in synonyms}
    keys = {}
    for fid, f in fields.items():
        keys[fid] = norm(f.get("name")) or norm(f.get("label"))
    for fid, key in keys.items():
        if key in syn and fid in values:
            return values[fid]
    for fid, key in keys.items():
        if key and any(s in key for s in syn if len(s) >= 4) and fid in values:
            return values[fid]
    return None


CANDIDATE_SYNONYMS = {
    "name": ["name", "nome", "fullname", "nomecompleto", "nomedocandidato",
             "candidate_name", "candidatename"],
    "email": ["email", "emailprincipal", "emaildocandidato", "candidate_email",
              "candidateemail", "accessemail"],
    "phone_number": ["phone", "phonenumber", "telefone", "celular"],
    "nationality": ["nationality", "nacionalidade"],
    "personal_website": ["website", "personalwebsite", "site", "homepage",
                         "personal_site"],
    "gender": ["gender", "genero", "sexo"],
    "birth_date": ["birthdate", "birth", "nascimento", "datadenascimento",
                   "birthday"],
    "graduation.country": ["country", "pais", "graduationcountry"],
    "graduation.course": ["course", "curso", "graduationcourse"],
    "graduation.institution": ["institution", "instituicao", "universidade",
                               "graduationinstitution"],
    "graduation.year": ["year", "ano", "anodeconclusao", "conclusao",
                        "graduationyear", "anograduacao"],
    "poscomp.year": ["poscompyear", "anoposcomp", "poscompano"],
    "poscomp.score": ["score", "nota", "pontuacao", "poscompscore",
                      "notaposcomp"],
    "current_occupation": ["currentoccupation", "occupation", "ocupacao",
                           "ocupacaoatual", "atividadeatual"],
    "research.program": ["program", "programa", "researchprogram"],
    "research.semester": ["semester", "semestre", "researchsemester"],
    "research.field.primary": ["primary", "primaria", "areaprimaria",
                               "fieldprimary", "principal", "areaprincipal"],
    "research.field.secondary": ["secondary", "secundaria", "areasecundaria",
                                 "fieldsecondary"],
    "research.will_apply_scholarship": ["willapplyscholarship", "scholarship",
                                        "bolsa", "aplicarbolsa", "desejobolsa"],
    "research.dedication_level": ["dedicationlevel", "dedicacao",
                                  "niveldededicacao", "dedication"],
    "lattes_curriculum": ["lattescurriculum", "lattes", "curriculumlattes",
                          "curriculo", "curriculum"],
    "disabilities": ["disabilities", "deficiencia", "pcd"],
    "ethnicity_race": ["ethnicityrace", "ethnicity", "etnia", "raca"],
}

RECOMMENDER_SIDES = ("recomend", "recommend", "advisor", "professor", "orient")
CANDIDATE_SIDES = ("candidat", "aluno")
EMAIL_KEYS = {"email", "emailprincipal", "e-mail", "mail"}
NAME_KEYS = {"name", "nome", "fullname", "nomecompleto"}


def _as_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _as_int(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _as_bool(value) -> bool:
    return _as_str(value).strip().lower() in ("true", "sim", "yes", "1", "on",
                                              "verdadeiro")


def extract_candidate(mapping_tree, values, fields) -> dict:
    flat = flatten_mapping(mapping_tree) if mapping_tree else []

    def get(prop):
        synonyms = CANDIDATE_SYNONYMS[prop]
        leaf = _find_leaf(flat, synonyms)
        if leaf is not None:
            v = values.get(leaf["field"])
            if v not in (None, ""):
                return v
        return _find_by_field(fields, values, synonyms)

    poscomp_year = get("poscomp.year")
    poscomp_score = get("poscomp.score")
    poscomp = None
    if poscomp_year not in (None, "") or poscomp_score not in (None, ""):
        poscomp = {
            "year": _as_int(poscomp_year),
            "score": _as_str(poscomp_score),
        }

    return {
        "name": _as_str(get("name")),
        "email": _as_str(get("email")),
        "phone_number": _as_str(get("phone_number")),
        "nationality": _as_str(get("nationality")),
        "personal_website": _as_str(get("personal_website")),
        "gender": _as_str(get("gender")),
        "birth_date": _as_str(get("birth_date")),
        "graduation": {
            "country": _as_str(get("graduation.country")),
            "course": _as_str(get("graduation.course")),
            "institution": _as_str(get("graduation.institution")),
            "year": _as_int(get("graduation.year")),
        },
        "poscomp": poscomp,
        "current_occupation": _as_str(get("current_occupation")),
        "research": {
            "program": _as_str(get("research.program")),
            "semester": _as_str(get("research.semester")),
            "field": {
                "primary": _as_str(get("research.field.primary")),
                "secondary": _as_str(get("research.field.secondary")),
            },
            "will_apply_scholarship": _as_bool(get("research.will_apply_scholarship")),
            "dedication_level": _as_str(get("research.dedication_level")),
        },
        "lattes_curriculum": _as_str(get("lattes_curriculum")),
        "disabilities": _as_bool(get("disabilities")),
        "ethnicity_race": _as_bool(get("ethnicity_race")),
    }


def extract_recommender(mapping_tree, values, fields, response_email=None):
    """Extrai identificação do candidato e do recomendador da resposta."""
    flat = flatten_mapping(mapping_tree) if mapping_tree else []
    cand_name = cand_email = rec_name = rec_email = None

    for segs, leaf in flat:
        joined = norm(".".join(str(s) for s in segs))
        segs_norm = [norm(s) for s in segs]
        is_email = any(s in EMAIL_KEYS for s in segs_norm)
        if any(side in joined for side in CANDIDATE_SIDES):
            if is_email:
                cand_email = cand_email or values.get(leaf["field"])
            else:
                cand_name = cand_name or values.get(leaf["field"])
        elif any(side in joined for side in RECOMMENDER_SIDES):
            if is_email:
                rec_email = rec_email or values.get(leaf["field"])
            else:
                rec_name = rec_name or values.get(leaf["field"])

    def by_field(side_markers, want_email):
        for fid, f in fields.items():
            key = norm(f.get("name")) or norm(f.get("label"))
            if not key or fid not in values:
                continue
            if any(m in key for m in side_markers):
                if want_email and "email" in key:
                    return values[fid]
                if not want_email and ("nome" in key or "name" in key):
                    return values[fid]
        return None

    cand_name = cand_name or by_field(CANDIDATE_SIDES, False)
    cand_email = cand_email or by_field(CANDIDATE_SIDES, True)
    rec_name = rec_name or by_field(RECOMMENDER_SIDES, False)
    rec_email = rec_email or by_field(RECOMMENDER_SIDES, True) or response_email

    return {
        "candidate_name": _as_str(cand_name),
        "candidate_email": _as_str(cand_email),
        "recommender_name": _as_str(rec_name),
        "recommender_email": _as_str(rec_email),
    }


ACCEPT_DECISION_KEYS = ("decision", "decisao", "accept", "aceite", "aceita",
                        "aceitacao", "acceptance", "resposta")
ACCEPT_COMMENT_KEYS = ("comments", "comment", "observacoes", "observacao",
                       "comentario", "comentarios", "obs", "notes", "note")


def extract_accept(values, fields) -> tuple[str | None, str | None]:
    decision = None
    comments = None
    for fid, f in fields.items():
        key = norm(f.get("name")) or norm(f.get("label"))
        v = values.get(fid)
        if v in (None, ""):
            continue
        if decision is None and any(k in key for k in ACCEPT_DECISION_KEYS):
            decision = _as_str(v)
        elif comments is None and any(k in key for k in ACCEPT_COMMENT_KEYS):
            comments = _as_str(v)
    return decision, comments
