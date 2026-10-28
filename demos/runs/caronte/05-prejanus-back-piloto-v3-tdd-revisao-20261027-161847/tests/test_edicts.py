"""V2-EDI-01..04 — listagem, criacao, edicao, fases, encerramento e remocao."""
from datetime import date, timedelta


def _fmt(d):
    return f"{d.isoformat()}T12:00:00"


def test_criar_edict(make_edict):
    edict = make_edict()
    assert edict["id"]
    assert edict["title"].startswith("Edital teste")
    assert edict["year"] == 2027
    assert edict["semester"] == 1
    assert edict["edict_type"] == "mestrado"
    assert edict["is_open"] is True


def test_criar_edict_datas_fora_de_ordem(admin):
    base = date.today()
    forms = admin.get("/forms").json()
    payload = {
        "title": "Fora de ordem", "description": "x", "year": 2027, "semester": 1,
        "edict_type": "mestrado", "is_open": True,
        "candidate_forms": forms[0]["id"],
        "recommenders_forms": forms[1]["id"] if len(forms) > 1 else forms[0]["id"],
        "date_application": _fmt(base + timedelta(days=3)),
        "date_verification": _fmt(base + timedelta(days=1)),
        "date_evaluation": _fmt(base + timedelta(days=2)),
        "date_closed": _fmt(base + timedelta(days=4)),
    }
    r = admin.post("/edicts", json=payload)
    assert r.status_code == 422


def test_get_edict_completo(admin, make_edict):
    created = make_edict()
    r = admin.get(f"/edicts/{created['id']}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == created["id"]
    assert detail["title"] == created["title"]
    assert detail["phase"] == "inscricoes"
    assert len(detail["phases"]) == 4
    assert {p["phase"] for p in detail["phases"]} == {
        "inscricoes", "homologacao", "avaliacao", "encerrado"
    }
    assert detail["slots"] == "0"
    assert str(detail["candidate_form_id"]) != ""


def test_listar_edicts(admin, make_edict):
    created = make_edict(edict_type="doutorado")
    items = admin.get("/edicts").json()
    assert any(e["id"] == created["id"] for e in items)
    for e in items:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in e
    filtrado = admin.get("/edicts", params={"type": "doutorado"}).json()
    assert all(e["edict_type"] == "doutorado" for e in filtrado)
    abertos = admin.get("/edicts", params={"is_open": True}).json()
    assert all(e["is_open"] for e in abertos)
    ambos = admin.get("/edicts", params={"type": "doutorado", "is_open": True}).json()
    assert all(e["edict_type"] == "doutorado" and e["is_open"] for e in ambos)


def test_editar_edict(admin, make_edict):
    created = make_edict()
    base = date.today()
    payload = {
        "title": "Titulo editado",
        "description": "Nova descricao",
        "year": "2028",
        "semester": "2",
        "edict_type": "doutorado",
        "date_application": _fmt(base + timedelta(days=10)),
        "date_verification": _fmt(base + timedelta(days=11)),
        "date_evaluation": _fmt(base + timedelta(days=12)),
        "date_closed": _fmt(base + timedelta(days=13)),
    }
    r = admin.post(f"/edicts/{created['id']}/edit", json=payload)
    assert r.status_code == 200, r.text
    detail = admin.get(f"/edicts/{created['id']}").json()
    assert detail["title"] == "Titulo editado"
    assert detail["year"] == 2028
    assert detail["semester"] == 2
    assert detail["type"] == "doutorado"


def test_editar_apenas_data(admin, make_edict):
    created = make_edict()
    r = admin.post(f"/edicts/{created['id']}/edit-date", json={"closed_date": "2027-06-30"})
    assert r.status_code == 200
    assert r.json()["closed_date"] == "2027-06-30"


def test_avancar_fase_propaga_forms(admin, make_edict):
    created = make_edict()
    detail = admin.get(f"/edicts/{created['id']}").json()
    homologacao = next(p for p in detail["phases"] if p["phase"] == "homologacao")
    r = admin.post(f"/edicts/{created['id']}/advance-phase", json={"id": homologacao["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == homologacao["id"]
    assert body["label"] == "homologacao"
    assert admin.get(f"/edicts/{created['id']}").json()["phase"] == "homologacao"
    # propagacao para o Forms
    forms = admin.get("/forms").json()
    form = next(f for f in forms if f["id"] == created["candidate_forms"])
    assert form["phase"] == "Approval"


def test_encerrar_edict(admin, make_edict):
    created = make_edict()
    r = admin.patch(f"/edicts/{created['id']}/close", json={
        "confirmation_deadline": "2027-03-01", "send_approval_letter": False,
    })
    assert r.status_code == 200
    assert admin.get(f"/edicts/{created['id']}").json()["is_open"] is False
    again = admin.patch(f"/edicts/{created['id']}/close", json={
        "confirmation_deadline": "2027-03-01", "send_approval_letter": False,
    })
    assert again.status_code == 409


def test_remover_edict(admin, make_edict):
    created = make_edict()
    r = admin.delete(f"/edicts/{created['id']}/remove")
    assert r.status_code == 200
    assert admin.get(f"/edicts/{created['id']}").status_code == 404
    assert all(e["id"] != created["id"] for e in admin.get("/edicts").json())
