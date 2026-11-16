from helpers import source_edict


def _find_file_field(node):
    if isinstance(node, dict):
        t = str(node.get("type", "")).lower()
        v = node.get("value")
        if t == "file" and v:
            name = node.get("name") or node.get("label")
            if name:
                return name, v
        for val in node.values():
            found = _find_file_field(val)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_file_field(item)
            if found:
                return found
    return None


def test_listar_inscricoes(api):
    src = source_edict(api)
    subs = src["submissions"]
    s = subs[0]
    for key in (
        "id",
        "token",
        "name",
        "email",
        "phone_number",
        "nationality",
        "personal_website",
        "gender",
        "advisor",
        "birth_date",
        "graduation",
        "poscomp",
        "current_occupation",
        "research",
        "lattes_curriculum",
        "stats",
        "is_favorite",
        "bidding_users",
        "labels",
        "disabilities",
        "ethnicity_race",
        "accept",
    ):
        assert key in s, s


def test_filtro_stats(api):
    src = source_edict(api)
    s = src["submissions"][0]
    r = api.get(f"/edicts/{src['id']}/submissions", params={"stats": s["stats"]})
    assert r.status_code == 200, r.text
    assert all(x["stats"] == s["stats"] for x in r.json()["submissions"])


def test_filtro_only_favorites(api):
    src = source_edict(api)
    r = api.get(f"/edicts/{src['id']}/submissions", params={"only_favorites": True})
    assert r.status_code == 200, r.text
    assert all(x["is_favorite"] for x in r.json()["submissions"])


def test_leituras_repetidas_nao_duplicam(api):
    src = source_edict(api)
    r1 = api.get(f"/edicts/{src['id']}/submissions").json()["submissions"]
    r2 = api.get(f"/edicts/{src['id']}/submissions").json()["submissions"]
    ids1 = [s["id"] for s in r1]
    ids2 = [s["id"] for s in r2]
    assert sorted(ids1) == sorted(ids2)
    assert len(ids1) == len(set(ids1))


def test_detalhe_inscricao(api):
    src = source_edict(api)
    sid = src["submissions"][0]["id"]
    r = api.get(f"/submissions/{sid}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert "summary" in d and "submission_form" in d, d.keys()
    summ = d["summary"]
    for key in ("name", "email", "favorite", "labels", "private_note", "letter_sent", "accept"):
        assert key in summ, summ
    # formulário completo com seções e campos
    assert d["submission_form"]
    r2 = api.get(f"/submissions/{sid}", params={"include_comments": True})
    assert r2.status_code == 200, r2.text


def test_detalhe_inexistente_404(api):
    assert api.get("/submissions/99999999").status_code == 404


def test_baixar_anexo(api):
    src = source_edict(api)
    for s in src["submissions"]:
        d = api.get(f"/submissions/{s['id']}").json()
        found = _find_file_field(d["submission_form"])
        if not found:
            continue
        label, filename = found
        r = api.get(f"/submissions/{s['id']}/files/{label}/{filename}")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("application/pdf")
        assert "attachment" in r.headers.get("content-disposition", "")
        assert r.content[:4] == b"%PDF"
        # nome que não confere com o valor do campo
        assert (
            api.get(f"/submissions/{s['id']}/files/{label}/nao-existe.pdf").status_code
            == 404
        )
        return
    raise AssertionError("nenhum anexo encontrado nas inscrições do edital-fonte")
