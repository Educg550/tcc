import pytest

from tests.conftest import find_submission


def test_listar_submissions(api):
    edict_id, _ = find_submission(api)
    r = api.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "submissions" in body
    subs = body["submissions"]
    assert subs
    sub = subs[0]
    for key in (
        "id", "token", "name", "email", "phone_number", "nationality",
        "personal_website", "gender", "advisor", "birth_date", "graduation",
        "poscomp", "current_occupation", "research", "lattes_curriculum",
        "stats", "is_favorite", "bidding_users", "labels", "disabilities",
        "ethnicity_race", "accept",
    ):
        assert key in sub, f"chave ausente: {key}"

    # leitura repetida não duplica
    r2 = api.get(f"/edicts/{edict_id}/submissions")
    ids1 = [s["id"] for s in subs]
    ids2 = [s["id"] for s in r2.json()["submissions"]]
    assert ids1 == ids2


def test_filtro_stats_e_favoritos(api):
    edict_id, _ = find_submission(api)
    subs = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    stats = subs[0]["stats"]
    r = api.get(f"/edicts/{edict_id}/submissions", params={"stats": stats})
    assert r.status_code == 200
    assert all(s["stats"] == stats for s in r.json()["submissions"])

    r = api.get(f"/edicts/{edict_id}/submissions", params={"only_favorites": True})
    assert r.status_code == 200
    assert all(s["is_favorite"] for s in r.json()["submissions"])


def test_detalhe_submissao(api):
    _, submission_id = find_submission(api)
    r = api.get(f"/submissions/{submission_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "summary" in body, body
    assert "submission_form" in body, body
    summary = body["summary"]
    for key in (
        "name", "email", "graduation", "poscomp", "research", "stats",
        "is_favorite", "labels", "private_note", "accept", "entry_semester",
        "letter_sent",
    ):
        assert key in summary, f"chave ausente no summary: {key}"

    # include_comments
    r2 = api.get(f"/submissions/{submission_id}", params={"include_comments": True})
    assert r2.status_code == 200


def test_detalhe_submissao_inexistente(api):
    r = api.get("/submissions/99999999")
    assert r.status_code == 404, r.text


def test_baixar_anexo(api):
    _, submission_id = find_submission(api)
    detail = api.get(f"/submissions/{submission_id}").json()
    form = detail["submission_form"]
    # localiza um campo de arquivo com valor
    alvo = None
    sections = form if isinstance(form, list) else form.get("sections", [])
    for section in sections:
        fields = section.get("fields", []) if isinstance(section, dict) else []
        for field in fields:
            if field.get("type") == "File" and field.get("value"):
                alvo = (field.get("label") or field.get("name"), field["value"])
                break
        if alvo:
            break
    if not alvo:
        pytest.skip("nenhum anexo disponível nesta inscrição")
    label, filename = alvo
    r = api.get(f"/submissions/{submission_id}/files/{label}/{filename}")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content

    # arquivo de outra candidatura não é servido
    r2 = api.get(f"/submissions/{submission_id}/files/{label}/outro-arquivo.pdf")
    assert r2.status_code == 404, r2.text
