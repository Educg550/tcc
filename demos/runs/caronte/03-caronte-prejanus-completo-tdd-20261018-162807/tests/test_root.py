def test_hello(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi_contract(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


def test_docs(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
