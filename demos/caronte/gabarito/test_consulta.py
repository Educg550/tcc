import pytest

from dados import ANEXOS, CARONTE, respostas_da_fixture, secoes_do_formulario

CANDIDATA = "Ana Piloto Caronte"
EMAIL = "candidata.piloto@example.com"


@pytest.mark.req("PIL-AMB-01")
def test_api_responde(api):
    assert api.get("/").status_code == 200


@pytest.mark.req("PIL-AUT-01")
def test_login_local_reconhece_o_docente(api):
    r = api.get("/auth/login")
    assert r.status_code == 200
    assert r.json() == {"id": 2, "name": "Docente", "email": "docente@example.com",
                        "nusp": "0000001", "role": "teacher"}


@pytest.mark.req("PIL-AUT-01")
@pytest.mark.parametrize("rota", ["/auth/login", "/edicts", "/edicts/1/submissions", "/submissions/1"])
def test_sem_atalho_e_sem_sessao_responde_401(api_sem_atalho, rota):
    assert api_sem_atalho.get(rota).status_code == 401


@pytest.mark.req("PIL-DOC-01")
def test_lista_o_edital(api):
    r = api.get("/edicts")
    assert r.status_code == 200
    assert [(e["id"], e["title"]) for e in r.json()] == [(1, "Piloto TCC - Mestrado 2026")]


@pytest.mark.req("PIL-DOC-01")
def test_consulta_o_edital(api):
    r = api.get("/edicts/1")
    assert r.status_code == 200
    e = r.json()
    assert (e["id"], e["title"], e["candidate_form_id"]) == (1, "Piloto TCC - Mestrado 2026", "1")


@pytest.mark.req("PIL-DOC-01", "PIL-BD-01")
def test_encontra_a_inscricao_pelo_nome(api):
    r = api.get("/edicts/1/submissions")
    assert r.status_code == 200
    assert [(s["id"], s["name"]) for s in r.json()["submissions"]] == [(1, CANDIDATA)]


@pytest.mark.req("PIL-DOC-01")
def test_consultas_repetidas_nao_duplicam(api):
    for _ in range(3):
        assert [s["id"] for s in api.get("/edicts/1/submissions").json()["submissions"]] == [1]


@pytest.mark.req("PIL-DOC-02")
def test_detalhe_identifica_a_candidata(api):
    r = api.get("/submissions/1")
    assert r.status_code == 200
    resumo = r.json()["summary"]
    assert (resumo["name"], resumo["email"]) == (CANDIDATA, EMAIL)


@pytest.mark.req("PIL-DOC-02", "PIL-BD-01")
@pytest.mark.parametrize("secao", range(8))
def test_detalhe_traz_as_respostas_da_secao(api, secao):
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f["name"]: f for s in api.get("/submissions/1").json()["submission_form"] for f in s["fields"]}
    assert {n: str(campos[n]["value"] or "") for n in nomes} == {n: esperado[n] for n in nomes}


@pytest.mark.req("PIL-DOC-03", "PIL-AMB-01")
@pytest.mark.parametrize("arquivo", ANEXOS)
def test_baixa_o_anexo(api, arquivo):
    campo = arquivo.split("_", 1)[1].removesuffix(".pdf")
    r = api.get(f"/submissions/1/files/{campo}/{arquivo}")
    assert r.status_code == 200
    assert r.headers["content-disposition"].startswith("attachment")
    assert r.content == (CARONTE / "uploads-consulta" / arquivo).read_bytes()
    assert f"(Piloto Caronte - {campo})".encode() in r.content
