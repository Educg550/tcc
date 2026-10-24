import pytest

from tests.utils import edicts_with_submissions


@pytest.fixture(scope="module")
def avaliacao(admin):
    """Edital com inscricoes colocado na fase avaliacao."""
    found = edicts_with_submissions(admin)
    assert found, "nenhum edital com inscricoes"
    eid, subs = found[0]
    detail = admin.get(f"/edicts/{eid}").json()
    if detail["phase"] != "avaliacao":
        phase = next(p for p in detail["phases"] if p["phase"] == "avaliacao")
        r = admin.post(f"/edicts/{eid}/advance-phase", json={"id": phase["id"]})
        assert r.status_code == 200, r.text
    return eid, subs


def _non_avaliacao_edict(admin):
    for eid, _subs in edicts_with_submissions(admin):
        if admin.get(f"/edicts/{eid}").json()["phase"] != "avaliacao":
            return eid
    return None


def test_comment_requires_avaliacao_phase(admin):
    eid = _non_avaliacao_edict(admin)
    if eid is None:
        pytest.skip("nenhum edital fora da fase avaliacao")
    subs = admin.get(f"/edicts/{eid}/submissions").json()["submissions"]
    r = admin.post(
        f"/submissions/{subs[0]['id']}/comments", json={"comment": "fora de fase"}
    )
    assert r.status_code == 400


def test_comment_crud(api, outro, avaliacao):
    _eid, subs = avaliacao
    sid = subs[0]["id"]

    r = api.post(f"/submissions/{sid}/comments", json={"comment": "comentario teste"})
    assert r.status_code == 200, r.text
    comment = r.json()
    assert comment["comment"] == "comentario teste"
    assert comment["submission_id"] == sid
    assert comment["user"]["id"] == 2
    assert comment["created_at"]

    activity = api.get(f"/submissions/{sid}/comments").json()
    texts = [a.get("comment") or a.get("text") for a in activity]
    assert "comentario teste" in texts

    # leitura nao registra evento novo
    again = api.get(f"/submissions/{sid}/comments").json()
    assert len(again) == len(activity)

    assert api.delete(f"/submissions/comments/{comment['id']}").status_code == 204

    other = api.post(f"/submissions/{sid}/comments", json={"comment": "do docente"})
    assert other.status_code == 200
    cid = other.json()["id"]
    assert outro.delete(f"/submissions/comments/{cid}").status_code == 403
    assert api.delete(f"/submissions/comments/{cid}").status_code == 204
    assert api.delete(f"/submissions/comments/{cid}").status_code == 404
    assert api.delete("/submissions/comments/99999999").status_code == 404


def test_favorites(api, outro, avaliacao):
    _eid, subs = avaliacao
    sid = subs[0]["id"]

    assert api.post(f"/submissions/{sid}/favorites").status_code == 201
    assert api.post(f"/submissions/{sid}/favorites").status_code == 409

    detail = api.get(f"/submissions/{sid}").json()["summary"]
    assert detail.get("is_favorite") is True or api.get(
        f"/edicts/{_eid}/submissions"
    ).json()["submissions"][0]["is_favorite"]

    assert outro.post(f"/submissions/{sid}/favorites").status_code == 201
    outro_detail = outro.get(f"/submissions/{sid}").json()["summary"]
    assert outro_detail.get("is_favorite") is True

    assert api.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 404
    assert outro.delete(f"/submissions/{sid}/favorites").status_code == 204


def test_labels(api, outro, avaliacao):
    eid, subs = avaliacao
    sid = subs[0]["id"]
    label = "etiqueta-teste"

    r = api.post(
        f"/submissions/{sid}/labels", json={"label": label, "color": "#112233"}
    )
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["label"] == label
    assert created["submission_id"] == sid
    assert created["user"]["id"] == 2

    catalog = api.get(f"/submissions/{sid}/labels").json()["labels"]
    mine = [l for l in catalog if l["label"] == label]
    assert mine and mine[0]["color"] == "#112233"

    # etiqueta de outro usuario nao aparece no catalogo do docente
    if len(subs) > 1:
        r2 = outro.post(
            f"/submissions/{subs[1]['id']}/labels",
            json={"label": label, "color": "#445566"},
        )
        assert r2.status_code == 200
        outro_id = r2.json()["id"]
        catalog = api.get(f"/submissions/{sid}/labels").json()["labels"]
        assert all(l["id"] != outro_id for l in catalog)
        assert outro.delete(f"/submissions/label/{outro_id}").status_code == 204

    # mesma etiqueta em outra inscricao atualiza a cor das anteriores
    if len(subs) > 1:
        r3 = api.post(
            f"/submissions/{subs[1]['id']}/labels",
            json={"label": label, "color": "#778899"},
        )
        assert r3.status_code == 200
        new_id = r3.json()["id"]
        catalog = api.get(f"/submissions/{sid}/labels").json()["labels"]
        assert next(l for l in catalog if l["label"] == label)["color"] == "#778899"
        assert api.delete(f"/submissions/label/{new_id}").status_code == 204

    assert outro.delete(f"/submissions/label/{created['id']}").status_code == 403
    assert api.delete(f"/submissions/label/{created['id']}").status_code == 204
    assert api.delete(f"/submissions/label/{created['id']}").status_code == 404
    assert api.delete("/submissions/label/99999999").status_code == 404


def test_private_notes(api, outro, avaliacao):
    _eid, subs = avaliacao
    sid = subs[0]["id"]

    r = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota um"})
    assert r.status_code == 200, r.text
    assert r.json()["note"] == "nota um"

    r = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota dois"})
    assert r.status_code == 200
    assert r.json()["note"] == "nota dois"

    mine = api.get(f"/submissions/{sid}").json()["summary"]
    assert "nota dois" in str(mine)
    assert "nota um" not in str(mine)

    other = outro.get(f"/submissions/{sid}").json()["summary"]
    assert "nota dois" not in str(other)


def test_views(api, outro, avaliacao):
    _eid, subs = avaliacao
    sid = subs[0]["id"]

    assert api.post(f"/submissions/{sid}/view").status_code == 200
    assert api.post(f"/submissions/{sid}/view").status_code == 200

    views = api.get(f"/submissions/{sid}/view").json()
    entries = views if isinstance(views, list) else views.get("views", [])
    mine = [v for v in entries if str(v.get("user", {}).get("id", v.get("user_id"))) == "2"]
    assert len(mine) == 1

    assert outro.post(f"/submissions/{sid}/view").status_code == 200
    views = api.get(f"/submissions/{sid}/view").json()
    entries = views if isinstance(views, list) else views.get("views", [])
    assert len(entries) == len(mine) + 1
