import pytest

from helpers import create_edict, submissions_of


@pytest.fixture(scope="module")
def sel(admin):
    eid = create_edict(admin, "Edital seleção")
    subs = submissions_of(admin, eid)
    return {"id": eid, "subs": subs}


def test_vagas(api, sel):
    eid = sel["id"]
    r = api.post(f"/edicts/{eid}/slots", json={"amount": "3"})
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == "3"
    assert api.get(f"/edicts/{eid}").json()["slots"] == "3"
    # vazio e negativo viram "0"
    assert api.post(f"/edicts/{eid}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert api.post(f"/edicts/{eid}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    # texto que não representa inteiro é rejeitado
    assert api.post(f"/edicts/{eid}/slots", json={"amount": "abc"}).status_code == 422
    # repetir atualiza o registro
    api.post(f"/edicts/{eid}/slots", json={"amount": "5"})
    assert api.get(f"/edicts/{eid}").json()["slots"] == "5"


def _bidding_users(subs, sid):
    me = next(x for x in subs if x["id"] == sid)
    return me["bidding_users"]["data"]


def test_manifestacao_de_interesse(api, admin, sel):
    eid = sel["id"]
    sid = sel["subs"][0]["id"]
    r = api.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200, r.text
    data = _bidding_users(api.get(f"/edicts/{eid}/submissions").json()["submissions"], sid)
    assert any(u["id"] == 2 for u in data.get("interested", []))

    # administrativo indica outro usuário
    r2 = admin.post(
        f"/submissions/{sid}/bidding", json={"bidding": "decline", "user_id": 3}
    )
    assert r2.status_code == 200, r2.text
    data = _bidding_users(admin.get(f"/edicts/{eid}/submissions").json()["submissions"], sid)
    assert any(u["id"] == 3 for u in data.get("decline", []))

    # docente sempre usa o próprio id
    api.post(f"/submissions/{sid}/bidding", json={"bidding": "available", "user_id": 3})
    data = _bidding_users(api.get(f"/edicts/{eid}/submissions").json()["submissions"], sid)
    assert any(u["id"] == 2 for u in data.get("available", []))
    assert not any(u["id"] == 3 for u in data.get("available", []))

    # valor inválido rejeitado; string vazia aceita
    assert (
        api.post(f"/submissions/{sid}/bidding", json={"bidding": "invalido"}).status_code
        == 422
    )
    assert (
        api.post(f"/submissions/{sid}/bidding", json={"bidding": ""}).status_code == 200
    )


def test_selecao_e_orientador(api, admin, sel):
    eid = sel["id"]
    sid = sel["subs"][1]["id"]
    # docente não altera decisão
    r403 = api.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r403.status_code == 403, r403.text
    r = admin.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r.status_code == 200, r.text
    subs = admin.get(f"/edicts/{eid}/submissions").json()["submissions"]
    me = next(x for x in subs if x["id"] == sid)
    assert me["stats"] == "approved"
    assert me["advisor"]["id"] == 2

    # aprovar exige um único orientador existente
    assert (
        admin.post(
            f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2, 3]}
        ).status_code
        in (400, 422)
    )
    assert (
        admin.post(
            f"/submissions/{sid}/select",
            json={"stats": "approved", "user_ids": [999999]},
        ).status_code
        in (400, 404, 422)
    )
    # outras situações atualizam o estado
    assert (
        admin.post(
            f"/submissions/{sid}/select", json={"stats": "refused", "user_ids": None}
        ).status_code
        == 200
    )
    # inscrição inexistente
    assert (
        admin.post(
            "/submissions/99999999/select", json={"stats": "refused", "user_ids": None}
        ).status_code
        == 404
    )


def test_selecao_edital_fechado_409(admin):
    eid = create_edict(admin, "Edital seleção fechado")
    subs = submissions_of(admin, eid)
    sid = subs[0]["id"]
    r = admin.patch(
        f"/edicts/{eid}/close",
        json={"confirmation_deadline": "2031-05-01", "send_approval_letter": False},
    )
    assert r.status_code == 200, r.text
    r2 = admin.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r2.status_code == 409, r2.text


def test_semestre_de_entrada(admin, sel):
    sid = sel["subs"][0]["id"]

    def summary():
        return admin.get(f"/submissions/{sid}").json()["summary"]

    r = admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "first"})
    assert r.status_code == 200, r.text
    assert "Primeiro semestre." in str(summary())
    admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "Segundo"})
    assert "Segundo semestre." in str(summary())
    admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "Outro texto"})
    assert "Outro texto" in str(summary())
