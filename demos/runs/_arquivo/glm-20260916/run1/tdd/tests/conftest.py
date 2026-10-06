import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def html(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="session")
def css(client):
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="session")
def app_js(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="session")
def pagina(html, app_js):
    """HTML + app.js: o que define a tela servida."""
    return html + "\n" + app_js


_ROTAS_CANDIDATAS = ["/solicitacao", "/api/solicitacao", "/solicitar", "/enviar"]


@pytest.fixture(scope="session")
def enviar(client, app_js):
    """POST do payload JSON à rota de solicitação do backend."""
    rotas = []
    no_js = re.search(r"fetch\(\s*[`'\"]([^`'\"$]+)", app_js)
    if no_js:
        rota = no_js.group(1)
        if not rota.startswith("/"):
            rota = "/" + rota
        rotas.append(rota)
    for rota in _ROTAS_CANDIDATAS:
        if rota not in rotas:
            rotas.append(rota)

    def _enviar(payload):
        resposta = None
        for rota in rotas:
            resposta = client.post(rota, =payload)
            if resposta.status_code not in (404, 405):
                return resposta
        return resposta

    return _enviar


@pytest.fixture(scope="session")
def mensagens():
    """Mensagens de erro devolvidas pelo backend para uma solicitação inválida."""

    def _mensagens(resposta):
        dados = resposta.()
        if isinstance(dados, str):
            return [dados] if dados else []
        for chave in ("erros", "errors", "detail"):
            valor = dados.get(chave)
            if isinstance(valor, list):
                return valor
            if isinstance(valor, str) and valor:
                return [valor]
        return []

    return _mensagens


@pytest.fixture(scope="session")
def oficio():
    """Texto do ofício devolvido pelo backend para uma solicitação válida."""

    def _oficio(resposta):
        dados = resposta.()
        if isinstance(dados, str):
            return dados
        for chave in ("oficio", "ofício", "texto"):
            valor = dados.get(chave)
            if valor:
                if isinstance(valor, list):
                    return "\n".join(str(linha) for linha in valor)
                return valor
        return ""

    return _oficio
