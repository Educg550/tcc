def _payload(cand, rec):
    return {
        "title": "Edital papéis",
        "description": "d",
        "year": 2026,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": cand,
        "recommenders_forms": rec,
        "date_application": "2026-01-01T00:00:00",
        "date_verification": "2026-02-01T00:00:00",
        "date_evaluation": "2026-03-01T00:00:00",
        "date_closed": "2026-04-01T00:00:00",
    }


def _forms(client):
    forms = client.get("/forms").json()
    cand = forms[0]["id"]
    rec = forms[1]["id"] if len(forms) > 1 else forms[0]["id"]
    return cand, rec


def test_secretaria_pode_criar(secretaria):
    cand, rec = _forms(secretaria)
    r = secretaria.post("/edicts", json=_payload(cand, rec))
    assert r.status_code == 200, r.text


def test_coordenador_pode_criar(coordenador):
    cand, rec = _forms(coordenador)
    r = coordenador.post("/edicts", json=_payload(cand, rec))
    assert r.status_code == 200, r.text


def test_estudante_403(estudante):
    cand, rec = _forms(estudante)
    r = estudante.post("/edicts", json=_payload(cand, rec))
    assert r.status_code == 403
    r2 = estudante.post("/edicts/1/interactors_list", json={})
    assert r2.status_code == 403


def test_consultas_autenticadas_sem_restricao(estudante, api):
    # consultas exigem autenticação, sem restrição administrativa
    assert estudante.get("/edicts").status_code == 200
    assert api.get("/edicts").status_code == 200
    assert api.get("/forms").status_code == 200
