import uuid

from tests.conftest import all_edicts


def test_download_unknown_jobs_404(api):
    job = uuid.uuid4().hex
    assert api.get(f"/edicts/download_pdf/{job}").status_code == 404
    assert api.get(f"/edicts/download_csv/{job}").status_code == 404


def test_report_creation_requires_admin(api):
    edicts = all_edicts(api)
    if not edicts:
        return
    edict_id = edicts[0]["id"]
    resp = api.post(f"/edicts/{edict_id}/interactors_list", json={})
    assert resp.status_code == 403
    resp = api.post(
        f"/edicts/{edict_id}/interactors_list", params={"mode": "pdf"}, json={}
    )
    assert resp.status_code == 403
    assert api.post(f"/edicts/{edict_id}/pairing-biddings").status_code == 403
