import uuid

import pytest

from tests.conftest import (
    any_submission,
    submission_in_phase,
    walk_file_fields,
)


@pytest.fixture(scope="module")
def submission(api):
    edict, sub = any_submission(api)
    if not sub:
        pytest.fail("nenhuma inscrição disponível no ambiente")
    return edict, sub


def test_submissions_listing_shape(api):
    from tests.conftest import all_edicts, submissions_of

    edicts = all_edicts(api)
    assert edicts, "nenhum edital disponível"
    subs = submissions_of(api, edicts[0]["id"])
    for sub in subs:
        for key in ("id", "name", "email", "stats", "is_favorite", "labels", "accept"):
            assert key in sub


def test_submissions_listing_idempotent(api, submission):
    edict, _ = submission
    first = api.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
    second = api.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
    assert {s["id"] for s in first} == {s["id"] for s in second}


def test_submissions_stats_filter(api, submission):
    edict, _ = submission
    resp = api.get(
        f"/edicts/{edict['id']}/submissions", params={"stats": "underreview"}
    )
    assert resp.status_code == 200
    assert all(s["stats"] == "underreview" for s in resp.json()["submissions"])


def test_nonexistent_submission_404(api):
    assert api.get("/submissions/999999").status_code == 404


def test_submission_detail_shape(api, submission):
    _, sub = submission
    resp = api.get(f"/submissions/{sub['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "submission_form" in body
    assert body["submission_form"]


def test_submission_detail_include_comments(api, submission):
    _, sub = submission
    resp = api.get(f"/submissions/{sub['id']}", params={"include_comments": True})
    assert resp.status_code == 200


def test_submission_detail_letter_sent(api, submission):
    _, sub = submission
    body = api.get(f"/submissions/{sub['id']}").json()
    assert "letter_sent" in body["summary"]


def test_comments_activity_read_does_not_create(api, submission):
    _, sub = submission
    first = api.get(f"/submissions/{sub['id']}/comments").json()
    second = api.get(f"/submissions/{sub['id']}/comments").json()
    assert first == second


def test_comment_lifecycle_in_evaluation_phase(api):
    edict, sub = submission_in_phase(api, "avaliacao")
    if not sub:
        pytest.skip("nenhum edital em avaliacao com inscrições")
    resp = api.post(
        f"/submissions/{sub['id']}/comments", json={"comment": "comentário de teste"}
    )
    assert resp.status_code == 200
    comment = resp.json()
    for key in ("id", "user", "submission_id", "comment"):
        assert key in comment
    assert comment["comment"] == "comentário de teste"
    assert comment["submission_id"] == sub["id"]
    assert api.delete(f"/submissions/comments/{comment['id']}").status_code == 204
    assert api.delete(f"/submissions/comments/{comment['id']}").status_code == 404


def test_comment_rejected_outside_evaluation_phase(api):
    for phase in ("inscricoes", "homologacao", "encerrado"):
        edict, sub = submission_in_phase(api, phase)
        if sub:
            resp = api.post(
                f"/submissions/{sub['id']}/comments",
                json={"comment": "fora de fase"},
            )
            assert resp.status_code == 400, phase
            return
    pytest.skip("nenhum edital fora de avaliacao com inscrições")


def test_delete_nonexistent_comment_404(api):
    assert api.delete("/submissions/comments/999999").status_code == 404


def test_favorites_lifecycle(api):
    edict, sub = submission_in_phase(api, "avaliacao")
    if not sub:
        pytest.skip("nenhum edital em avaliacao com inscrições")
    api.delete(f"/submissions/{sub['id']}/favorites")
    assert api.post(f"/submissions/{sub['id']}/favorites").status_code == 201
    assert api.post(f"/submissions/{sub['id']}/favorites").status_code == 409
    listing = api.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
    mine = [s for s in listing if s["id"] == sub["id"]][0]
    assert mine["is_favorite"] is True
    only_fav = api.get(
        f"/edicts/{edict['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert any(s["id"] == sub["id"] for s in only_fav)
    assert api.delete(f"/submissions/{sub['id']}/favorites").status_code == 204
    assert api.delete(f"/submissions/{sub['id']}/favorites").status_code == 404


def test_labels_lifecycle(api):
    edict, sub = submission_in_phase(api, "avaliacao")
    if not sub:
        pytest.skip("nenhum edital em avaliacao com inscrições")
    resp = api.post(
        f"/submissions/{sub['id']}/labels",
        json={"label": "etiqueta-teste", "color": "#ff0000"},
    )
    assert resp.status_code == 200
    label = resp.json()
    for key in ("id", "user", "submission_id", "label"):
        assert key in label
    catalog = api.get(f"/submissions/{sub['id']}/labels").json()["labels"]
    assert any(l["label"] == "etiqueta-teste" for l in catalog)
    assert api.delete(f"/submissions/label/{label['id']}").status_code == 204
    assert api.delete(f"/submissions/label/{label['id']}").status_code == 404


def test_delete_nonexistent_label_404(api):
    assert api.delete("/submissions/label/999999").status_code == 404


def test_private_note_upsert(api):
    edict, sub = submission_in_phase(api, "avaliacao")
    if not sub:
        pytest.skip("nenhum edital em avaliacao com inscrições")
    resp = api.post(
        f"/submissions/{sub['id']}/private_notes", json={"note": "primeira nota"}
    )
    assert resp.status_code == 200
    assert resp.json()["note"] == "primeira nota"
    resp = api.post(
        f"/submissions/{sub['id']}/private_notes", json={"note": "nota atualizada"}
    )
    assert resp.status_code == 200
    assert resp.json()["note"] == "nota atualizada"
    detail = api.get(f"/submissions/{sub['id']}").json()
    assert "nota atualizada" in str(detail["summary"])


def test_view_registration(api, submission):
    _, sub = submission
    assert api.post(f"/submissions/{sub['id']}/view").status_code == 200
    first = api.get(f"/submissions/{sub['id']}/view").json()
    assert api.post(f"/submissions/{sub['id']}/view").status_code == 200
    second = api.get(f"/submissions/{sub['id']}/view").json()
    assert len(second) == len(first)  # mesmo dia não duplica


def test_bidding(api, submission):
    edict, sub = submission
    resp = api.post(f"/submissions/{sub['id']}/bidding", json={"bidding": "interested"})
    assert resp.status_code == 200
    detail = api.get(f"/submissions/{sub['id']}")
    assert "interested" in detail.text


def test_bidding_invalid_value_rejected(api, submission):
    _, sub = submission
    resp = api.post(
        f"/submissions/{sub['id']}/bidding", json={"bidding": "valor-invalido"}
    )
    assert resp.status_code == 422


def test_select_requires_admin(api, submission):
    _, sub = submission
    resp = api.post(
        f"/submissions/{sub['id']}/select",
        json={"stats": "approved", "user_ids": None},
    )
    assert resp.status_code == 403


def test_select_nonexistent_submission_404(api):
    resp = api.post(
        "/submissions/999999/select", json={"stats": "refused", "user_ids": None}
    )
    assert resp.status_code == 404


def test_entry_semester_normalization(api, submission):
    _, sub = submission
    resp = api.post(f"/submissions/{sub['id']}/entry-semester", json={"semester": "first"})
    assert resp.status_code == 200
    detail = api.get(f"/submissions/{sub['id']}")
    assert "Primeiro semestre." in detail.text


def test_files_download(api, submission):
    _, sub = submission
    detail = api.get(f"/submissions/{sub['id']}").json()
    files = list(walk_file_fields(detail["submission_form"]))
    if not files:
        pytest.fail("nenhum campo de arquivo encontrado nas inscrições")
    label, filename = files[0]
    resp = api.get(f"/submissions/{sub['id']}/files/{label}/{filename}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content


def test_files_wrong_filename_404(api, submission):
    _, sub = submission
    bogus = f"{uuid.uuid4().hex}.pdf"
    assert (
        api.get(f"/submissions/{sub['id']}/files/qualquer/{bogus}").status_code == 404
    )


def test_reesend_submission_requires_admin(api, submission):
    _, sub = submission
    resp = api.post(
        f"/submissions/{sub['id']}/reesend_submission", json={"text": "corrija"}
    )
    assert resp.status_code == 403


def test_send_accept_and_letter_authenticated(api, submission):
    _, sub = submission
    # Rotas individuais exigem autenticação, sem restrição administrativa extra.
    for path in ("send-accept", "send-letter"):
        resp = api.post(f"/submissions/{sub['id']}/{path}")
        assert resp.status_code in (200, 400, 404), path
