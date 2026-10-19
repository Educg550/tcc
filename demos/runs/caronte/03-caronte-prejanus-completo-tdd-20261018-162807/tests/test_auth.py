from conftest import build_payload


def test_login_fields(client):
    r = client.get("/auth/login")
    assert r.status_code == 200
    data = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in data


def test_protected_route_requires_session(anon):
    r = anon.post("/edicts", json=build_payload(anon))
    assert r.status_code == 401


def test_senhaunica_request_token(client):
    r = client.post("/auth/login/senhaunica", json={})
    assert r.status_code == 200, r.text
    assert "redirect_to" in r.json()
