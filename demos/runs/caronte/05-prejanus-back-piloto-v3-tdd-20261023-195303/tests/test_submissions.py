import pytest

REQUIRED_SUBMISSION_KEYS = (
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
)


def test_list_submissions_shape(client, edict_with_submissions):
    detail, subs = edict_with_submissions
    assert subs
    for sub in subs:
        for key in REQUIRED_SUBMISSION_KEYS:
            assert key in sub, key
        assert sub["stats"] in ("approved", "refused", "underreview", "waitlist")
        assert sub["accept"]["sent"] in ("not_sent", "sent", "replied")


def test_list_submissions_stable(client, edict_with_submissions):
    detail, _ = edict_with_submissions
    ids1 = [s["id"] for s in client.get(f"/edicts/{detail['id']}/submissions").json()["submissions"]]
    ids2 = [s["id"] for s in client.get(f"/edicts/{detail['id']}/submissions").json()["submissions"]]
    assert ids1 == ids2
    assert len(ids1) == len(set(ids1))


def test_list_submissions_filter_stats(client, edict_with_submissions):
    detail, subs = edict_with_submissions
    stats = subs[0]["stats"]
    filtered = client.get(
        f"/edicts/{detail['id']}/submissions", params={"stats": stats}
    ).json()["submissions"]
    assert filtered
    assert all(s["stats"] == stats for s in filtered)


def test_submission_detail(client, edict_with_submissions):
    _, subs = edict_with_submissions
    resp = client.get(f"/submissions/{subs[0]['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "submission_form" in data
    summary = data["summary"]
    for key in ("name", "email", "graduation", "research", "stats", "favorite", "labels", "accept"):
        assert key in summary, key
    # formulário completo: seções com campos e valores
    assert data["submission_form"]
    sections = data["submission_form"]
    if isinstance(sections, dict):
        sections = list(sections.values())
    found_field = False
    for section in sections:
        fields = section.get("fields", []) if isinstance(section, dict) else []
        for field in fields:
            found_field = True
            for key in ("id", "name", "label", "type"):
                assert key in field, key
    assert found_field


def test_submission_detail_include_comments(client, evaluation_edict):
    _, subs = evaluation_edict
    resp = client.get(
        f"/submissions/{subs[0]['id']}", params={"include_comments": True}
    )
    assert resp.status_code == 200
    assert "comments" in resp.json()["summary"] or "comments" in resp.json()


def test_submission_not_found(client):
    assert client.get("/submissions/99999999").status_code == 404


def test_download_attachment(client, edict_with_submissions):
    _, subs = edict_with_submissions
    detail = client.get(f"/submissions/{subs[0]['id']}").json()
    sections = detail["submission_form"]
    if isinstance(sections, dict):
        sections = list(sections.values())
    target = None
    for section in sections:
        for field in section.get("fields", []):
            if field.get("type") == "File" and field.get("value"):
                target = field
                break
        if target:
            break
    if target is None:
        pytest.skip("nenhum anexo nesta candidatura")

    filename = target["value"]
    if "/" in filename:
        filename = filename.rsplit("/", 1)[-1]
    label = target["name"]
    resp = client.get(f"/submissions/{subs[0]['id']}/files/{label}/{filename}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content[:4] == b"%PDF"


def test_download_attachment_wrong_filename(client, edict_with_submissions):
    _, subs = edict_with_submissions
    resp = client.get(
        f"/submissions/{subs[0]['id']}/files/qualquer/outro.pdf"
    )
    assert resp.status_code == 404
