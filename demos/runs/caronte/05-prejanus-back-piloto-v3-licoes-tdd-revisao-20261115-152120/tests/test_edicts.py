from helpers import DATES, advance, create_edict, edict_body, source_edict


def test_listar_editais(api):
    r = api.get("/edicts")
    assert r.status_code == 200, r.text
    edicts = r.json()
    assert edicts
    e = edicts[0]
    for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
        assert key in e, e


def test_filtros_type_is_open(admin):
    e = admin.get("/edicts").json()[0]
    r = admin.get(
        "/edicts", params={"type": e["edict_type"], "is_open": e["is_open"]}
    )
    assert r.status_code == 200
    assert any(x["id"] == e["id"] for x in r.json())


def test_consulta_completa(api):
    src = source_edict(api)
    d = src["detail"]
    for key in (
        "id",
        "title",
        "candidate_form_id",
        "recommender_form_id",
        "description",
        "year",
        "semester",
        "type",
        "is_open",
        "phase",
        "phases",
        "slots",
    ):
        assert key in d, d
    assert isinstance(d["slots"], str)
    assert len(d["phases"]) == 4
    assert {p["phase"] for p in d["phases"]} == {
        "inscricoes",
        "homologacao",
        "avaliacao",
        "encerrado",
    }


def test_criar_edital_admin(admin, api):
    eid = create_edict(admin, "Edital teste criação")
    d = admin.get(f"/edicts/{eid}").json()
    assert d["title"] == "Edital teste criação"
    assert d["phase"] == "inscricoes"
    assert d["is_open"] is True
    # vagas do usuário autenticado sem configuração: "0"
    d2 = api.get(f"/edicts/{eid}").json()
    assert d2["slots"] == "0"


def test_criar_edital_secretaria_e_coordenador(secretaria, coordenador):
    assert secretaria.post("/edicts", json=edict_body(secretaria, "Edital secretaria")).status_code == 200
    assert coordenador.post("/edicts", json=edict_body(coordenador, "Edital coordenador")).status_code == 200


def test_criar_edital_docente_403(api):
    assert api.post("/edicts", json=edict_body(api, "Edital docente")).status_code == 403


def test_criar_edital_estudante_403(estudante):
    assert estudante.post("/edicts", json=edict_body(estudante, "Edital estudante")).status_code == 403


def test_datas_fora_de_ordem_422(admin):
    body = edict_body(admin, "Edital datas invertidas")
    # homologacao (date_evaluation) depois de avaliacao (date_verification)
    body["date_evaluation"] = DATES[3]
    body["date_verification"] = DATES[1]
    r = admin.post("/edicts", json=body)
    assert r.status_code == 422, r.text


def test_editar_edital(admin):
    eid = create_edict(admin, "Edital edição")
    body = edict_body(admin, "Edital edição")
    body.update(
        {
            "title": "Edital editado",
            "description": "nova descrição",
            "year": "2032",
            "semester": "2",
        }
    )
    r = admin.post(f"/edicts/{eid}/edit", json=body)
    assert r.status_code == 200, r.text
    d = admin.get(f"/edicts/{eid}").json()
    assert d["title"] == "Edital editado"
    assert d["description"] == "nova descrição"
    assert d["year"] == 2032
    assert d["semester"] == 2


def test_editar_apenas_data(admin):
    eid = create_edict(admin, "Edital data")
    r = admin.post(f"/edicts/{eid}/edit-date", json={"closed_date": "2031-06-01"})
    assert r.status_code == 200, r.text
    assert r.json()["closed_date"] == "2031-06-01"
    assert admin.get(f"/edicts/{eid}").json()["closed_date"] == "2031-06-01"


def test_avancar_fase_propaga_para_forms(admin):
    eid = create_edict(admin, "Edital fases")
    d = admin.get(f"/edicts/{eid}").json()
    fid = int(d["candidate_form_id"])

    def form_phase():
        forms = admin.get("/forms").json()
        return next(f["phase"] for f in forms if f["id"] == fid)

    res = advance(admin, eid, "homologacao")
    assert res["label"] == "homologacao"
    assert form_phase() == "Approval"
    assert admin.get(f"/edicts/{eid}").json()["phase"] == "homologacao"

    advance(admin, eid, "avaliacao")
    assert form_phase() == "Completed"


def test_encerrar_edital(admin, api):
    eid = create_edict(admin, "Edital encerrar")
    body = {"confirmation_deadline": "2031-05-01", "send_approval_letter": False}
    r = admin.patch(f"/edicts/{eid}/close", json=body)
    assert r.status_code == 200, r.text
    assert admin.get(f"/edicts/{eid}").json()["is_open"] is False
    # encerrar de novo
    assert admin.patch(f"/edicts/{eid}/close", json=body).status_code == 409
    # docente não encerra
    eid2 = create_edict(admin, "Edital encerrar docente")
    assert api.patch(f"/edicts/{eid2}/close", json=body).status_code == 403


def test_remover_edital(admin):
    eid = create_edict(admin, "Edital remover")
    assert admin.delete(f"/edicts/{eid}/remove").status_code == 200
    assert admin.get(f"/edicts/{eid}").status_code == 404
    # remoção refletida na listagem
    assert all(e["id"] != eid for e in admin.get("/edicts").json())
