import pytest

from tests.conftest import create_edict, first_submission, advance_phase


@pytest.fixture(scope="module")
def edital(admin):
    forms = admin.get("/forms").json()
    cand = forms[0]["id"]
    rec = forms[1]["id"] if len(forms) > 1 else forms[0]["id"]
    return create_edict(admin, cand, rec, title="Edital seleção")


@pytest.fixture(scope="module")
def cenário(admin, api, edital):
    # usa inscrições de um edital existente para select/bidding
    edicts = api.get("/edicts").json()
    for e in edicts:
        r = api.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200 and r.json()["submissions"]:
            edict_id = e["id"]
            break
    else:
        pytest.skip("nenhum edital com inscrições")
    detail = admin.get(f"/edicts/{edict_id}").json()
    if detail["phase"] != "avaliacao":
        advance_phase(admin, edict_id, "avaliacao")
    return {"edict_id": edict_id, "sub": first_submission(api, edict_id)}


def test_slots(admin, edital):
    r = admin.post(f"/edicts/{edital['id']}/slots", json={"amount": "3"})
    assert r.status_code == 200
    assert r.json()["amount"] == "3"
    # reflete no detalhe
    assert admin.get(f"/edicts/{edital['id']}").json()["slots"] == "3"
    # vazio ou negativo vira "0"
    assert admin.post(f"/edicts/{edital['id']}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert admin.post(f"/edicts/{edital['id']}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    # texto inválido rejeitado
    r2 = admin.post(f"/edicts/{edital['id']}/slots", json={"amount": "abc"})
    assert r2.status_code == 422
    # repetir atualiza
    assert admin.post(f"/edicts/{edital['id']}/slots", json={"amount": "5"}).json()["amount"] == "5"


def test_bidding(api, admin, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200, r.text
    detail = api.get(f"/submissions/{sid}").json()
    # docente não administra outro usuário
    r2 = api.post(
        f"/submissions/{sid}/bidding", json={"bidding": "decline", "user_id": 1}
    )
    assert r2.status_code == 200
    detail2 = api.get(f"/submissions/{sid}").json()
    # admin pode indicar outro usuário
    r3 = admin.post(
        f"/submissions/{sid}/bidding", json={"bidding": "agreed", "user_id": 2}
    )
    assert r3.status_code == 200


def test_select_aprovar(admin, api, cenário):
    sid = cenário["sub"]["id"]
    r = admin.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r.status_code == 200, r.text
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["stats"] == "approved"
    assert detail["summary"]["advisor"]["id"] == 2


def test_select_docente_403(api, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(
        f"/submissions/{sid}/select", json={"stats": "refused", "user_ids": None}
    )
    assert r.status_code == 403


def test_select_inexistente_404(admin):
    r = admin.post(
        "/submissions/99999999/select", json={"stats": "refused", "user_ids": None}
    )
    assert r.status_code == 404


def test_entry_semester(admin, api, cenário):
    sid = cenário["sub"]["id"]
    r = admin.post(
        f"/submissions/{sid}/entry-semester", json={"semester": "first"}
    )
    assert r.status_code == 200, r.text
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["entry_semester"] == "Primeiro semestre."
    r2 = admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "Segundo semestre."})
    assert r2.status_code == 200
    assert api.get(f"/submissions/{sid}").json()["summary"]["entry_semester"] == "Segundo semestre."
