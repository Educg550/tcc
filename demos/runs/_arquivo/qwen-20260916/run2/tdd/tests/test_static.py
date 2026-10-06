import pytest

@pytest.mark.parametrize("path", ["/static/style.css", "/static/app.js", "/static/assets/usp-logo.png"])
def test_static(client, path):
    r = client.get(path)
    assert r.status_code == 200
    if path.endswith(".css"):
        assert "text/css" in r.headers.get("content-type", "")
    elif path.endswith(".js"):
        assert "javascript" in r.headers.get("content-type", "")
    elif path.endswith(".png"):
        assert "image" in r.headers.get("content-type", "")
