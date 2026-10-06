import 
import re
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

VALOR_DIGITOS = "150000"
VALOR_MOEDA = "R$ 1.500,00"

DADOS_VALIDOS = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBBD",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "1 a 4 de outubro de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbbd.org.br",
    "VALOR SOLICITADO (R$)": VALOR_DIGITOS,
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "123",
    "COMPLEMENTO": "Sala 5",
    "BAIRRO": "Cidade Universitária",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "56789-0",
}


def _atributo(tag, nome):
    m = re.search(rf'{nome}\s*=\s*[\'"]([^\'"]*)[\'"]', tag, re.I)
    return m.group(1) if m else None


def _rotas_post():
    rotas = []
    for rota in app.routes:
        metodos = getattr(rota, "methods", None) or set()
        if "POST" in metodos:
            rotas.append(rota.path)
    return rotas


def _chave_normalizada(rotulo):
    texto = unicodedata.normalize("NFKD", rotulo)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def _montar(dados, variante):
    if variante == "rotulo":
        return dict(dados)
    return {_chave_normalizada(chave): valor for chave, valor in dados.items()}


def _post(client, rota, modo, dados):
    if modo == "":
        return client.post(rota, =dados)
    return client.post(rota, data=dados)


def _texto(resp):
    try:
        dados = resp.()
    except ValueError:
        return resp.text
    if isinstance(dados, str):
        return dados
    return .dumps(dados, ensure_ascii=False)


def _caminho_local(url):
    if re.match(r"https?://", url):
        return None
    return url if url.startswith("/") else "/" + url


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    return resp.text


@pytest.fixture(scope="session")
def css(client, html):
    textos = []
    for tag in re.findall(r"<link\b[^>]*>", html, re.I):
        href = _atributo(tag, "href")
        if not href or not href.split("?")[0].endswith(".css"):
            continue
        caminho = _caminho_local(href)
        if caminho is None:
            continue
        resp = client.get(caminho)
        assert resp.status_code == 200, f"CSS não servido: {href}"
        textos.append(resp.text)
    return "\n".join(textos)


@pytest.fixture(scope="session")
def js(client, html):
    textos = []
    for tag in re.findall(r"<script\b[^>]*>", html, re.I):
        src = _atributo(tag, "src")
        if not src:
            continue
        caminho = _caminho_local(src)
        if caminho is None:
            continue
        resp = client.get(caminho)
        assert resp.status_code == 200, f"JS não servido: {src}"
        textos.append(resp.text)
    return "\n".join(textos)


@pytest.fixture(scope="session")
def payload():
    def _payload(**substituicoes):
        dados = dict(DADOS_VALIDOS)
        for chave, valor in substituicoes.items():
            if valor is None:
                dados.pop(chave, None)
            else:
                dados[chave] = valor
        return dados

    return _payload


@pytest.fixture(scope="session")
def canal(client):
    for rota in _rotas_post():
        for modo in ("", "form"):
            for variante in ("rotulo", "normalizado"):
                for valor in (VALOR_DIGITOS, VALOR_MOEDA):
                    dados = _montar(
                        {**DADOS_VALIDOS, "VALOR SOLICITADO (R$)": valor}, variante
                    )
                    resp = _post(client, rota, modo, dados)
                    if resp.status_code != 422 and "Interessada(o):" in _texto(resp):
                        return SimpleNamespace(
                            rota=rota, modo=modo, variante=variante, valor=valor
                        )
    pytest.fail(
        "Nenhuma rota POST do backend devolveu o ofício de uma solicitação válida. "
        f"Rotas POST encontradas: {_rotas_post() or 'nenhuma'}"
    )


@pytest.fixture(scope="session")
def enviar(client, canal):
    def _enviar(dados):
        resp = _post(client, canal.rota, canal.modo, _montar(dados, canal.variante))
        assert resp.status_code < 500, f"backend respondeu {resp.status_code}"
        return _texto(resp)

    return _enviar
