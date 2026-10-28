"""V2-FOR-01 / V2-FOR-02 — consulta de formularios do Forms."""


def test_lista_formularios(admin):
    r = admin.get("/forms")
    assert r.status_code == 200
    forms = r.json()
    assert forms
    for f in forms:
        for key in ("id", "title", "tags", "phase"):
            assert key in f


def test_filtros_year_notice(admin):
    forms = admin.get("/forms").json()
    sample = forms[0]
    tags = sample.get("tags") or {}
    year = tags.get("Ano")
    notice = tags.get("Edital")
    if year:
        filtered = admin.get("/forms", params={"year": year}).json()
        assert filtered
        assert all((f.get("tags") or {}).get("Ano") == year for f in filtered)
    if notice:
        filtered = admin.get("/forms", params={"notice": notice}).json()
        assert filtered
        assert all((f.get("tags") or {}).get("Edital") == notice for f in filtered)
    if year and notice:
        both = admin.get("/forms", params={"year": year, "notice": notice}).json()
        assert all(
            (f.get("tags") or {}).get("Ano") == year
            and (f.get("tags") or {}).get("Edital") == notice
            for f in both
        )


def test_form_completo(admin):
    form = admin.get("/forms").json()[0]
    r = admin.get(f"/forms/{form['id']}")
    assert r.status_code == 200
    full = r.json()
    assert "sections" in full
    assert full["sections"]


def test_secoes(admin):
    form = admin.get("/forms").json()[0]
    r = admin.get(f"/forms/{form['id']}/sections")
    assert r.status_code == 200
    sections = r.json()
    assert sections
    assert all(isinstance(s["id"], int) for s in sections)


def test_secoes_versao_1_aceita_nulas(admin):
    form = admin.get("/forms").json()[0]
    r = admin.get(f"/forms/{form['id']}/sections", params={"version": 1})
    assert r.status_code == 200
    assert r.json()


def test_secoes_versao_inexistente_fallback(admin):
    form = admin.get("/forms").json()[0]
    todas = admin.get(f"/forms/{form['id']}/sections").json()
    r = admin.get(f"/forms/{form['id']}/sections", params={"version": 99999})
    assert r.status_code == 200
    assert r.json() == todas


def test_campos_de_secao(admin):
    form = admin.get("/forms").json()[0]
    sections = admin.get(f"/forms/{form['id']}/sections").json()
    section_id = sections[0]["id"]
    r = admin.get(f"/forms/{form['id']}/sessions/{section_id}/fields")
    assert r.status_code == 200
    fields = r.json()
    assert fields
    for f in fields:
        assert "id" in f
        assert "position" in f
