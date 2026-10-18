"""Smoke tests: the app exposes the 50 operations of the original contract."""
from app import app

EXPECTED = {
    ("GET", "/"): 1,
    ("GET", "/auth/login"): 1,
    ("POST", "/auth/login/senhaunica"): 1,
    ("GET", "/forms"): 1,
    ("GET", "/forms/{form_id}"): 1,
    ("GET", "/forms/{form_id}/sections"): 1,
    ("GET", "/forms/{form_id}/sessions/{section_id}/fields"): 1,
    ("GET", "/edicts"): 1,
    ("POST", "/edicts"): 1,
    ("GET", "/edicts/{edict_id}"): 1,
    ("POST", "/edicts/{edict_id}/edit"): 1,
    ("POST", "/edicts/{edict_id}/edit-date"): 1,
    ("POST", "/edicts/{edict_id}/advance-phase"): 1,
    ("DELETE", "/edicts/{edict_id}/remove"): 1,
    ("PATCH", "/edicts/{edict_id}/close"): 1,
    ("POST", "/edicts/{edict_id}/slots"): 1,
    ("GET", "/edicts/{edict_id}/submissions"): 1,
    ("POST", "/edicts/{edict_id}/interactors_list"): 1,
    ("POST", "/edicts/{edict_id}/pairing-biddings"): 1,
    ("GET", "/edicts/download_pdf/{job_id}"): 1,
    ("GET", "/edicts/download_csv/{job_id}"): 1,
    ("POST", "/edicts/{edict_id}/candidates/mappings/versions/{version}/"): 1,
    ("POST", "/edicts/{edict_id}/recommenders/mappings/versions/{version}/"): 1,
    ("GET", "/edicts/{edict_id}/candidates/mappings"): 1,
    ("GET", "/edicts/{edict_id}/recommenders/mappings"): 1,
    ("PUT", "/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}"): 1,
    ("DELETE", "/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}"): 1,
    ("PUT", "/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}"): 1,
    ("DELETE", "/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}"): 1,
    ("GET", "/edicts/{edict_id}/candidates/forms/versions/unmapped"): 1,
    ("GET", "/edicts/{edict_id}/recommenders/forms/versions/unmapped"): 1,
    ("GET", "/submissions/{submission_id}"): 1,
    ("POST", "/submissions/{submission_id}/send-accept"): 1,
    ("POST", "/submissions/{submission_id}/send-letter"): 1,
    ("GET", "/submissions/{submission_id}/comments"): 1,
    ("POST", "/submissions/{submission_id}/comments"): 1,
    ("DELETE", "/submissions/comments/{comment_id}"): 1,
    ("POST", "/submissions/{submission_id}/favorites"): 1,
    ("DELETE", "/submissions/{submission_id}/favorites"): 1,
    ("GET", "/submissions/{submission_id}/labels"): 1,
    ("POST", "/submissions/{submission_id}/labels"): 1,
    ("DELETE", "/submissions/label/{label_id}"): 1,
    ("POST", "/submissions/{submission_id}/private_notes"): 1,
    ("POST", "/submissions/{submission_id}/reesend_submission"): 1,
    ("POST", "/submissions/{submission_id}/select"): 1,
    ("POST", "/submissions/{submission_id}/bidding"): 1,
    ("POST", "/submissions/{submission_id}/entry-semester"): 1,
    ("GET", "/submissions/{submission_id}/files/{label}/{filename}"): 1,
    ("POST", "/submissions/{submission_id}/view"): 1,
    ("GET", "/submissions/{submission_id}/view"): 1,
}


def _operations():
    ops = {}
    for route in app.routes:
        path = route.path
        if (
            path in ("/docs", "/redoc", "/openapi.json")
            or path.startswith("/docs/")
        ):
            continue
        for method in getattr(route, "methods", ()) - {"HEAD", "OPTIONS"}:
            ops.setdefault((method, path), 0)
            ops[(method, path)] += 1
    return ops


def test_all_operations_present():
    ops = _operations()
    for key in EXPECTED:
        assert key in ops, f"missing operation {key}"
    assert len(ops) == len(EXPECTED), (
        f"unexpected extra operations: {set(ops) - set(EXPECTED)}"
    )


def test_openapi_contract():
    schema = app.openapi()
    assert schema["paths"]["/edicts/{edict_id}/submissions"]
    assert schema["paths"]["/submissions/{submission_id}/private_notes"]
    assert schema["paths"]["/submissions/{submission_id}/reesend_submission"]
    assert schema["paths"]["/forms/{form_id}/sessions/{section_id}/fields"]
    assert "MappingNode" in schema["components"]["schemas"]
    assert "InsertEdictSchema" in schema["components"]["schemas"]