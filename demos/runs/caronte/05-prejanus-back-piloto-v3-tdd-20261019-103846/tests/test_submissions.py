"""V2-INS-01 a V2-INS-03: listagem, detalhe e anexos das inscrições."""


def test_listagem_submissions_formato(api, edict_with_submissions):
    resp = api.get(f"/edicts/{edict_with_submissions['id']}/submissions")
    assert resp.status_code == 200
    data = resp.json()
    assert "submissions" in data
    assert data["submissions"]
    sub = data["submissions"][0]
    for key in (
        "id", "token", "name", "email", "phone_number", "nationality",
        "personal_website", "gender", "advisor", "birth_date", "graduation",
        "poscomp", "current_occupation", "research", "lattes_curriculum",
        "stats", "is_favorite", "bidding_users", "labels", "disabilities",
        "ethnicity_race", "accept",
    ):
        assert key in sub, f"chave ausente: {key}"
    assert isinstance(sub["is_favorite"], bool)
    assert isinstance(sub["labels"], list)


def test_listagem_submissions_leitura_estavel(api, edict_with_submissions):
    edict_id = edict_with_submissions["id"]
    first = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    second = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    assert [s["id"] for s in first] == [s["id"] for s in second]


def test_listagem_filtro_stats(api, edict_with_submissions):
    edict_id = edict_with_submissions["id"]
    subs = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    stats = {s["stats"] for s in subs}
    for stat in stats:
        filtered = api.get(f"/edicts/{edict_id}/submissions",
                           params={"stats": stat}).json()["submissions"]
        assert {s["stats"] for s in filtered} == {stat}


def test_listagem_filtro_favoritos(api, edict_with_submissions):
    edict_id = edict_with_submissions["id"]
    resp = api.get(f"/edicts/{edict_id}/submissions",
                   params={"only_favorites": True})
    assert resp.status_code == 200
    for sub in resp.json()["submissions"]:
        assert sub["is_favorite"] is True


def test_detalhe_submission(api, any_submission):
    resp = api.get(f"/submissions/{any_submission['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "submission_form" in data
    summary = data["summary"]
    for key in ("name", "email", "graduation", "research", "stats",
                "is_favorite", "labels", "accept", "letter_sent"):
        assert key in summary, f"chave ausente no summary: {key}"
    # formulário completo com seções e campos
    form = data["submission_form"]
    assert isinstance(form, (list, dict))
    if isinstance(form, list):
        assert form


def test_detalhe_submission_inexistente_404(api):
    assert api.get("/submissions/99999999").status_code == 404


def test_detalhe_nao_cria_inscricao(api, any_submission):
    before = api.get(f"/submissions/{any_submission['id']}").json()
    after = api.get(f"/submissions/{any_submission['id']}").json()
    assert before == after


def test_download_anexo(api, any_submission):
    """V2-INS-03: anexo com tipo e disposição corretos."""
    detail = api.get(f"/submissions/{any_submission['id']}").json()
    form = detail["submission_form"]
    sections = form if isinstance(form, list) else form.get("sections", [])
    file_entry = None
    for section in sections:
        fields = section.get("fields", []) if isinstance(section, dict) else []
        for field in fields:
            if field.get("type") == "File" and field.get("value"):
                file_entry = field
                break
        if file_entry:
            break
    if not file_entry:
        pytest.skip("nenhum anexo nesta inscrição")
    filename = file_entry["value"]
    label = file_entry["name"]
    resp = api.get(f"/submissions/{any_submission['id']}/files/{label}/{filename}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content[:4] == b"%PDF"


def test_download_anexo_de_outro_candidato_negado(api, any_submission):
    detail = api.get(f"/submissions/{any_submission['id']}").json()
    form = detail["submission_form"]
    sections = form if isinstance(form, list) else form.get("sections", [])
    for section in sections:
        for field in (section.get("fields", []) if isinstance(section, dict) else []):
            if field.get("type") == "File" and field.get("value"):
                resp = api.get(
                    f"/submissions/{any_submission['id']}/files/{field['name']}/outro-arquivo.pdf"
                )
                assert resp.status_code in (404, 400)
                return
    pytest.skip("nenhum anexo nesta inscrição")
