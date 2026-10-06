def _html(client):
    return client.get("/").text


def _css(client):
    return client.get("/style.css").text


def test_logo_e_nome_usp(client):
    t = _html(client)
    assert "assets/usp-logo.png" in t
    assert "Universidade de São Paulo" in t


def test_cores_usp(client):
    css = _css(client).lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_sem_brasao(client):
    assert "brasao" not in _css(client).lower()


def test_sem_recurso_externo(client):
    t = _html(client).lower()
    js = client.get("/app.js").text.lower()
    css = _css(client).lower()
    for arquivo in (t, js, css):
        assert "http://" not in arquivo
        assert "https://" not in arquivo
