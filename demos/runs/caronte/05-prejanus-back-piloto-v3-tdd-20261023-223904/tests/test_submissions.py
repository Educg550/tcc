from tests.utils import any_submission, edicts_with_submissions, pdf_items

REQUIRED = [
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
]


def test_list_submissions_shape(api):
    eid, subs = edicts_with_submissions(api)[0]
    for key in REQUIRED:
        assert key in subs[0], key


def test_list_submissions_repeated_reads_are_stable(api):
    eid, subs = edicts_with_submissions(api)[0]
    r2 = api.get(f"/edicts/{eid}/submissions")
    assert r2.status_code == 200
    ids1 = [s["id"] for s in subs]
    ids2 = [s["id"] for s in r2.json()["submissions"]]
    assert ids1 == ids2
    assert len(ids2) == len(set(ids2))


def test_submissions_stats_filter(api):
    eid, subs = edicts_with_submissions(api)[0]
    stats = subs[0]["stats"]
    r = api.get(f"/edicts/{eid}/submissions", params={"stats": stats})
    assert r.status_code == 200
    assert all(s["stats"] == stats for s in r.json()["submissions"])


def test_submissions_only_favorites(api, outro):
    eid, sub = None, None
    for e, subs in edicts_with_submissions(outro):
        eid, sub = e, subs[0]
        break
    r = outro.post(f"/submissions/{sub['id']}/favorites")
    assert r.status_code == 201
    try:
        r = outro.get(f"/edicts/{eid}/submissions", params={"only_favorites": True})
        ids = [s["id"] for s in r.json()["submissions"]]
        assert sub["id"] in ids

        r = api.get(f"/edicts/{eid}/submissions", params={"only_favorites": True})
        ids = [s["id"] for s in r.json()["submissions"]]
        assert sub["id"] not in ids
    finally:
        outro.delete(f"/submissions/{sub['id']}/favorites")


def test_submission_detail(api):
    _eid, sub = any_submission(api)
    r = api.get(f"/submissions/{sub['id']}")
    assert r.status_code == 200, r.text
    detail = r.json()
    assert "summary" in detail
    assert "submission_form" in detail
    summary = detail["summary"]
    assert summary["name"] == sub["name"]
    assert summary["email"] == sub["email"]

    r = api.get(f"/submissions/{sub['id']}", params={"include_comments": True})
    assert r.status_code == 200


def test_submission_detail_not_found(api):
    assert api.get("/submissions/99999999").status_code == 404


def test_submission_detail_does_not_create_submission(api):
    before = {
        eid: [s["id"] for s in subs] for eid, subs in edicts_with_submissions(api)
    }
    _eid, sub = any_submission(api)
    api.get(f"/submissions/{sub['id']}")
    after = {
        eid: [s["id"] for s in subs] for eid, subs in edicts_with_submissions(api)
    }
    assert before == after


def test_submission_files_download(api):
    _eid, sub = any_submission(api)
    detail = api.get(f"/submissions/{sub['id']}").json()
    items = pdf_items(detail.get("submission_form"))
    if not items:
        import pytest

        pytest.skip("candidatura sem anexo em arquivo")
    labels, filename = items[0]
    for label in labels[:5]:
        r = api.get(f"/submissions/{sub['id']}/files/{label}/{filename}")
        if r.status_code == 200:
            assert r.headers["content-type"].startswith("application/pdf")
            assert "attachment" in r.headers.get("content-disposition", "")
            assert r.content[:4] == b"%PDF"
            return
    raise AssertionError(f"nao foi possivel baixar o anexo {filename}")
