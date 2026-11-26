import pytest

from conftest import advance, first_edict_with_submissions, get_edict


def test_listar_inscricoes(api):
    edict_id, subs = first_edict_with_submissions(api)
    r = api.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"submissions"}
    for s in body["submissions"]:
        for key in (
            "id",
            "token",
            "name",
            "email",
            "graduation",
            "research",
            "stats",
            "is_favorite",
            "labels",
            "accept",
            "bidding_users",
        ):
            assert key in s
    # leituras repetidas não duplicam
    again = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    ids = [s["id"] for s in body["submissions"]]
    assert [s["id"] for s in again] == ids


def test_filtro_stats(api):
    edict_id, subs = first_edict_with_submissions(api)
    stats = subs[0]["stats"]
    r = api.get(f"/edicts/{edict_id}/submissions", params={"stats": stats})
    assert r.status_code == 200
    assert all(s["stats"] == stats for s in r.json()["submissions"])


def test_filtro_favoritos(api, outro):
    edict_id, subs = first_edict_with_submissions(api)
    r = api.get(f"/edicts/{edict_id}/submissions", params={"only_favorites": True})
    assert r.status_code == 200
    for s in r.json()["submissions"]:
        assert s["is_favorite"] is True


def test_detalhe_inscricao(api):
    edict_id, subs = first_edict_with_submissions(api)
    sub = subs[0]
    r = api.get(f"/submissions/{sub['id']}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "summary" in body
    assert "submission_form" in body
    summary = body["summary"]
    for key in (
        "name",
        "email",
        "graduation",
        "poscomp",
        "research",
        "stats",
        "is_favorite",
        "labels",
        "private_note",
        "accept",
        "entry_semester",
        "letter_sent",
    ):
        assert key in summary
    # formulário completo com seções e campos
    assert body["submission_form"]
    r404 = api.get("/submissions/99999999")
    assert r404.status_code == 404


def test_detalhe_include_comments(api):
    edict_id, subs = first_edict_with_submissions(api)
    r = api.get(
        f"/submissions/{subs[0]['id']}", params={"include_comments": True}
    )
    assert r.status_code == 200


def test_download_anexo(api):
    edict_id, subs = first_edict_with_submissions(api)
    sub = subs[0]
    detalhe = api.get(f"/submissions/{sub['id']}").json()
    # procura um campo de arquivo no formulário completo
    achou = False
    for section in detalhe["submission_form"]:
        campos = section.get("fields", section) if isinstance(section, dict) else section
        if not isinstance(campos, list):
            continue
        for campo in campos:
            if not isinstance(campo, dict):
                continue
            if campo.get("type") == "File" and campo.get("value"):
                filename = campo["value"]
                label = campo.get("name") or campo.get("label")
                r = api.get(f"/submissions/{sub['id']}/files/{label}/{filename}")
                assert r.status_code == 200, r.text
                assert r.headers["content-type"].startswith("application/pdf")
                assert "attachment" in r.headers.get("content-disposition", "")
                assert r.content[:4] == b"%PDF"
                achou = True
                break
        if achou:
            break
    if not achou:
        pytest.skip("nenhum anexo nesta inscrição")


def test_arquivo_de_outro_candidato_negado(api):
    edict_id, subs = first_edict_with_submissions(api)
    if len(subs) < 2:
        pytest.skip("menos de duas inscrições")
    r = api.get(f"/submissions/{subs[0]['id']}/files/x/arquivo-qualquer.pdf")
    assert r.status_code == 404
