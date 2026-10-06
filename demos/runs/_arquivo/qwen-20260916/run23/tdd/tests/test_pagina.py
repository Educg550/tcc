def test_servida(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<html" in r.text.lower()


def test_estaticos(client):
    for caminho in ("/index.html", "/style.css", "/app.js"):
        assert client.get(caminho).status_code == 200
