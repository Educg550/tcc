import pytest

from conftest import banco

BIDDINGS = ["decline", "available", "interested", "agreed", "interested_scholarship", ""]


def submissao(id):
    return banco(f"SELECT stats, advisor_id, entry_semester FROM submission WHERE id={id}")[0]


@pytest.mark.req("V2-SEL-01", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
@pytest.mark.parametrize("valor,esperado", [("3", "3"), ("0", "0"), ("", "0"), ("-4", "0")])
def test_vagas_do_usuario(api, valor, esperado):
    r = api.post("edicts/1/slots", json={"amount": valor})
    assert (r.status_code, r.json()) == (200, {"amount": esperado})
    assert api.get("edicts/1").json()["slots"] == esperado
    assert banco("SELECT user_id, slots FROM user_edict_slots") == [{"user_id": 2, "slots": int(esperado)}]


@pytest.mark.req("V2-SEL-01")
def test_vagas_repetidas_atualizam_o_registro(api):
    api.post("edicts/1/slots", json={"amount": "2"})
    api.post("edicts/1/slots", json={"amount": "5"})
    assert banco("SELECT slots FROM user_edict_slots") == [{"slots": 5}]


@pytest.mark.req("V2-SEL-01")
def test_vagas_nao_inteiras_sao_recusadas(api):
    api.post("edicts/1/slots", json={"amount": "2"})
    assert api.post("edicts/1/slots", json={"amount": "duas"}).status_code >= 400
    assert api.get("edicts/1").json()["slots"] == "2"


@pytest.mark.req("V2-SEL-01", "V2-BD-01")
@pytest.mark.parametrize("valor", BIDDINGS)
def test_interesse_aceita_os_valores_do_contrato(api, valor):
    assert api.post("submissions/1/bidding", json={"bidding": valor}).status_code == 200
    assert banco("SELECT user_id, label FROM labels WHERE context_type='bidding'") == [{"user_id": 2, "label": valor}]
    assert api.get("submissions/1").json()["summary"]["user_bidding"] == valor


@pytest.mark.req("V2-SEL-01")
def test_interesse_invalido_e_recusado(api):
    assert api.post("submissions/1/bidding", json={"bidding": "talvez"}).status_code == 422


@pytest.mark.req("V2-SEL-01")
def test_um_interesse_corrente_por_usuario_refletido_na_listagem(api):
    api.post("submissions/1/bidding", json={"bidding": "interested"})
    api.post("submissions/1/bidding", json={"bidding": "agreed"})
    assert len(banco("SELECT id FROM labels WHERE context_type='bidding'")) == 1
    ana = {s["id"]: s for s in api.get("edicts/1/submissions").json()["submissions"]}[1]
    assert [u["id"] for u in ana["bidding_users"]["data"]["agreed"]] == [2]
    assert ana["bidding_users"]["data"]["interested"] == []
    assert ana["labels"] == []


@pytest.mark.req("V2-SEL-01")
@pytest.mark.parametrize("perfil,registrado", [("admin", 3), ("coordenador", 3), ("docente", 2)])
def test_somente_administrativo_indica_outro_usuario(clientes, perfil, registrado):
    clientes(perfil).post("submissions/1/bidding", json={"bidding": "interested", "user_id": 3})
    assert banco("SELECT user_id FROM labels WHERE context_type='bidding'") == [{"user_id": registrado}]


@pytest.mark.req("V2-SEL-02", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_aprova_com_um_orientador(admin):
    assert admin.post("submissions/1/select", json={"stats": "approved", "user_ids": [3]}).status_code == 200
    assert submissao(1)["stats"] == "approved" and submissao(1)["advisor_id"] == 3
    assert admin.get("submissions/1").json()["summary"]["stats"] == "approved"


@pytest.mark.req("V2-SEL-02")
@pytest.mark.parametrize("stats", ["refused", "underreview", "waitlist"])
def test_outras_situacoes_atualizam_o_estado(clientes, stats):
    assert clientes("secretaria").post("submissions/2/select", json={"stats": stats, "user_ids": None}).status_code == 200
    assert submissao(2)["stats"] == stats


@pytest.mark.req("V2-SEL-02")
@pytest.mark.parametrize("user_ids", [None, [], [999], [2, 3]])
def test_aprovacao_exige_um_unico_orientador_existente(admin, user_ids):
    r = admin.post("submissions/1/select", json={"stats": "approved", "user_ids": user_ids})
    assert r.status_code >= 400
    assert (submissao(1)["stats"], submissao(1)["advisor_id"]) == ("underreview", None)


@pytest.mark.req("V2-SEL-02")
def test_selecao_de_inscricao_inexistente_responde_404(admin):
    assert admin.post("submissions/999/select", json={"stats": "refused", "user_ids": None}).status_code == 404


@pytest.mark.req("V2-SEL-02", "V2-EDI-04")
def test_edital_fechado_impede_decisoes(admin):
    admin.patch("edicts/1/close", json={"confirmation_deadline": "2030-05-01", "send_approval_letter": False})
    assert admin.post("submissions/1/select", json={"stats": "approved", "user_ids": [3]}).status_code == 409
    assert submissao(1)["stats"] == "underreview"


@pytest.mark.req("V2-SEL-02")
@pytest.mark.parametrize("enviado,gravado", [
    ("primeiro", "Primeiro semestre."), ("Second semester", "Segundo semestre."),
    ("SEGUNDO SEMESTRE.", "Segundo semestre."), ("first", "Primeiro semestre."), ("2027/1", "2027/1"),
])
def test_semestre_de_ingresso_normalizado(api, enviado, gravado):
    assert api.post("submissions/1/entry-semester", json={"semester": enviado}).status_code == 200
    assert submissao(1)["entry_semester"] == gravado
    assert api.get("submissions/1").json()["summary"]["entry_semester"] == gravado


@pytest.mark.req("V2-SEL-02")
def test_semestre_de_inscricao_inexistente_responde_404(api):
    assert api.post("submissions/999/entry-semester", json={"semester": "primeiro"}).status_code == 404
