import pytest

from tests.conftest import first_submission


def _edict_com_inscricoes(client):
    edicts = client.get("/edicts").json()
    for e in edicts:
        r = client.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200 and r.json()["submissions"]:
            return e["id"]
    pytest.skip("nenhum edital com inscrições no ambiente")


def test_listar_inscricoes(api):
    edict_id = _edict_com_inscricoes(api)
    r = api.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200
    subs = r.json()["submissions"]
    assert subs
    s = subs[0]
    for key in (
        "id", "token", "name", "email", "phone_number", "nationality",
        "personal_website", "gender", "advisor", "birth_date", "graduation",
        "poscomp", "current_occupation", "research", "lattes_curriculum",
        "stats", "is_favorite", "bidding_users", "labels", "disabilities",
        "ethnicity_race", "accept",
    ):
        assert key in s, f"chave ausente: {key}"
    # leituras repetidas não duplicam
    subs2 = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    ids1 = [s["id"] for s in subs]
    ids2 = [s["id"] for s in subs2]
    assert ids1 == ids2
    assert len(ids2) == len(set(ids2))


def test_filtro_stats(api):
    edict_id = _edict_com_inscricoes(api)
    r = api.get(f"/edicts/{edict_id}/submissions", params={"stats": "underreview"})
    assert r.status_code == 200
    assert all(s["stats"] == "underreview" for s in r.json()["submissions"])


def test_filtro_favoritos(api):
    edict_id = _edict_com_inscricoes(api)
    r = api.get(
        f"/edicts/{edict_id}/submissions", params={"only_favorites": True}
    )
    assert r.status_code == 200
    assert all(s["is_favorite"] for s in r.json()["submissions"])


def test_detalhe_inscricao(api):
    edict_id = _edict_com_inscricoes(api)
    s = first_submission(api, edict_id)
    r = api.get(f"/submissions/{s['id']}")
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "submission_form" in data
    summary = data["summary"]
    for key in ("name", "email", "graduation", "research", "stats", "is_favorite",
                "labels", "accept", "letter_sent"):
        assert key in summary, f"chave ausente no summary: {key}"
    # formulário completo com seções e campos
    form = data["submission_form"]
    assert form
    r2 = api.get(f"/submissions/{s['id']}", params={"include_comments": True})
    assert r2.status_code == 200


def test_detalhe_inexistente_404(api):
    r = api.get("/submissions/99999999")
    assert r.status_code == 404


def test_baixar_anexo(api):
    edict_id = _edict_com_inscricoes(api)
    s = first_submission(api, edict_id)
    detail = api.get(f"/submissions/{s['id']}").json()
    # procura um campo de arquivo no formulário
    found = None
    sections = detail["submission_form"]
    sections = sections if isinstance(sections, list) else sections.get("sections", [])
    for sec in sections:
        fields = sec.get("fields", []) if isinstance(sec, dict) else []
        for f in fields:
            if f.get("type") == "File" and f.get("value"):
                found = (f, sec)
                break
        if found:
            break
    if not found:
        pytest.skip("nenhum anexo nesta inscrição")
    field, sec = found
    label = field.get("name") or field.get("label")
    filename = field["value"]
    r = api.get(f"/submissions/{s['id']}/files/{label}/{filename}")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content[:4] == b"%PDF"
    # arquivo de outra candidatura não é servido
    r2 = api.get(f"/submissions/{s['id']}/files/{label}/arquivo-estranho.pdf")
    assert r2.status_code == 404
