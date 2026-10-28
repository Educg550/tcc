"""V2-INS-01..03 — listagem, detalhe e anexos."""

REQUIRED_KEYS = [
    "id", "token", "name", "email", "phone_number", "nationality",
    "personal_website", "gender", "advisor", "birth_date", "graduation",
    "poscomp", "current_occupation", "research", "lattes_curriculum",
    "stats", "is_favorite", "bidding_users", "labels", "disabilities",
    "ethnicity_race", "accept",
]


def test_listar_submissions(admin, submission_ctx):
    edict, _ = submission_ctx
    r = admin.get(f"/edicts/{edict['id']}/submissions")
    assert r.status_code == 200
    subs = r.json()["submissions"]
    assert subs
    for s in subs:
        for key in REQUIRED_KEYS:
            assert key in s, key


def test_listar_submissions_nao_duplica(admin, submission_ctx):
    edict, _ = submission_ctx
    ids1 = [s["id"] for s in admin.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]]
    ids2 = [s["id"] for s in admin.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]]
    assert sorted(ids1) == sorted(ids2)
    assert len(ids1) == len(set(ids1))


def test_filtro_stats(admin, submission_ctx):
    edict, _ = submission_ctx
    subs = admin.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
    stats = subs[0]["stats"]
    filtered = admin.get(
        f"/edicts/{edict['id']}/submissions", params={"stats": stats}
    ).json()["submissions"]
    assert all(s["stats"] == stats for s in filtered)


def test_filtro_favoritos_por_usuario(admin, submission_ctx):
    edict, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/favorites")
    assert r.status_code == 201
    favs = admin.get(
        f"/edicts/{edict['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert any(s["id"] == sub["id"] for s in favs)
    assert all(s["is_favorite"] for s in favs)
    admin.delete(f"/submissions/{sub['id']}/favorites")


def test_detalhe_submission(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.get(f"/submissions/{sub['id']}")
    assert r.status_code == 200
    detail = r.json()
    assert "summary" in detail
    assert "submission_form" in detail
    summary = detail["summary"]
    for key in ("name", "email", "graduation", "research", "stats", "favorite",
                "labels", "private_note", "accept", "letter_sent"):
        assert key in summary, key
    form = detail["submission_form"]
    assert form


def test_detalhe_submission_inexistente(admin):
    assert admin.get("/submissions/99999999").status_code == 404


def test_detalhe_include_comments(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.get(f"/submissions/{sub['id']}", params={"include_comments": True})
    assert r.status_code == 200
    assert "comments" in r.json()


def _walk_files(node):
    if isinstance(node, dict):
        if node.get("type") == "File" and node.get("value"):
            yield node
        for v in node.values():
            yield from _walk_files(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_files(v)


def test_baixar_anexo(admin, submission_ctx):
    _, sub = submission_ctx
    detail = admin.get(f"/submissions/{sub['id']}").json()
    files = list(_walk_files(detail["submission_form"]))
    assert files, "fixture data must contain file fields with values"
    field = files[0]
    label = field.get("name") or field.get("label")
    filename = field["value"]
    r = admin.get(f"/submissions/{sub['id']}/files/{label}/{filename}")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content


def test_baixar_anexo_nome_errado(admin, submission_ctx):
    _, sub = submission_ctx
    detail = admin.get(f"/submissions/{sub['id']}").json()
    files = list(_walk_files(detail["submission_form"]))
    assert files
    field = files[0]
    label = field.get("name") or field.get("label")
    r = admin.get(f"/submissions/{sub['id']}/files/{label}/arquivo-inexistente.pdf")
    assert r.status_code == 404
