import pytest

from conftest import find_edict, submissions_of

REQUIRED = {
    "id",
    "token",
    "name",
    "email",
    "phone_number",
    "nationality",
    "personal_website",
    "gender",
    "advisor",
    "birth_date",
    "graduation",
    "poscomp",
    "current_occupation",
    "research",
    "lattes_curriculum",
    "stats",
    "is_favorite",
    "bidding_users",
    "labels",
    "disabilities",
    "ethnicity_race",
    "accept",
}


def _edict_with_submissions(client):
    ed = find_edict(client, with_submissions=True)
    if ed is None:
        pytest.skip("nenhum edital com inscricoes")
    return ed


def test_submissions_list(client):
    ed = _edict_with_submissions(client)
    subs = submissions_of(client, ed["id"])
    assert subs
    for s in subs:
        assert REQUIRED <= set(s)
    # leitura repetida nao duplica inscricoes
    again = submissions_of(client, ed["id"])
    assert [s["id"] for s in again] == [s["id"] for s in subs]


def test_submissions_stats_filter(client):
    ed = _edict_with_submissions(client)
    subs = submissions_of(client, ed["id"])
    stats = subs[0]["stats"]
    filtered = submissions_of(client, ed["id"], stats=stats)
    assert all(s["stats"] == stats for s in filtered)


def test_submissions_only_favorites_filter(client):
    ed = _edict_with_submissions(client)
    favs = submissions_of(client, ed["id"], only_favorites=True)
    assert isinstance(favs, list)


def test_submission_detail(client):
    ed = _edict_with_submissions(client)
    sid = submissions_of(client, ed["id"])[0]["id"]
    r = client.get(f"/submissions/{sid}")
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "submission_form" in data
    r = client.get(f"/submissions/{sid}", params={"include_comments": True})
    assert r.status_code == 200


def test_submission_detail_404(client):
    assert client.get("/submissions/99999999").status_code == 404


def _find_file_field(node):
    if isinstance(node, dict):
        if node.get("type") == "File" and node.get("value"):
            return node
        for v in node.values():
            f = _find_file_field(v)
            if f:
                return f
    elif isinstance(node, list):
        for v in node:
            f = _find_file_field(v)
            if f:
                return f
    return None


def test_download_attachment(client):
    ed = _edict_with_submissions(client)
    sid = submissions_of(client, ed["id"])[0]["id"]
    detail = client.get(f"/submissions/{sid}").json()
    field = _find_file_field(detail.get("submission_form"))
    if field is None:
        pytest.skip("nenhum campo de arquivo preenchido")
    filename = field["value"]
    label = field.get("name") or field.get("label")
    r = client.get(f"/submissions/{sid}/files/{label}/{filename}")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content
