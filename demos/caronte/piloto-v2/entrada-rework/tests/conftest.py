import email
import json
import os
from email.policy import default
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from ambiente import AQUI, ESTADO, URL, dc, linhas, restaurar, sql

BASE = os.environ.get("CARONTE_V2_BASE", URL)
SMTP = "http://localhost:8182"
OAUTH = "http://localhost:8181"
IDS = {"admin": 1, "docente": 2, "outro": 3, "secretaria": 4, "coordenador": 5, "estudante": 6}
INVENTARIO = json.loads((AQUI / "interfaces.json").read_text())
DIVERGENCIAS = json.loads((AQUI / "gabarito/divergencias.json").read_text())
CHAMADAS, CASOS = [], []
ATUAL = ""
COOKIES = {}


def rastrear(response):
    p = response.request.url.path
    if p.startswith("/backend/"):
        caminho = p[len("/backend"):]
        CHAMADAS.append({"caso": ATUAL, "metodo": response.request.method,
                         "caminho": caminho, "status": response.status_code,
                         "erro": response.text[:1500] if response.status_code >= 400 else None})


def cliente(prefixo="/backend/"):
    return httpx.Client(base_url=BASE + prefixo, verify=False, timeout=30,
                        event_hooks={"response": [lambda r: (r.read(), rastrear(r))]})


def entrar(c, perfil):
    inicio = c.post("auth/login/senhaunica")
    assert inicio.status_code == 200, inicio.text
    token = parse_qs(urlsplit(inicio.json()["redirect_to"]).query)["oauth_token"][0]
    autorizado = httpx.get(OAUTH + "/wsusuario/oauth/authorize",
                          params={"oauth_token": token, "perfil": perfil}).json()
    return c.post("auth/login/senhaunica", params=autorizado)


def pytest_configure(config):
    config.addinivalue_line("markers", "req(*ids): requisitos v2 verificados")
    config.addinivalue_line("markers", "integracao(*ids): fronteiras de integração observadas")


@pytest.fixture(autouse=True)
def estado_inicial(request):
    global ATUAL
    ATUAL = request.node.nodeid
    restaurar()
    r = httpx.delete(SMTP + "/api/Messages/*")
    assert r.status_code in (200, 204), r.text


@pytest.fixture
def clientes():
    abertos = []
    def criar(perfil="docente"):
        c = cliente()
        abertos.append(c)
        if perfil not in COOKIES:
            r = entrar(c, perfil)
            assert r.status_code == 200, r.text
            COOKIES[perfil] = dict(c.cookies)
        else:
            c.cookies.update(COOKIES[perfil])
        return c
    yield criar
    for c in abertos:
        c.close()


@pytest.fixture
def api(clientes):
    return clientes()


@pytest.fixture
def admin(clientes):
    return clientes("admin")


@pytest.fixture
def anonimo():
    with cliente() as c:
        yield c


@pytest.fixture
def local():
    with cliente("/local/") as c:
        yield c


@pytest.fixture
def sem_atalho():
    with cliente("/sem-atalho/") as c:
        yield c


def banco(consulta, nome="prejanus"):
    return linhas(consulta, nome)


def emails():
    lista = httpx.get(SMTP + "/api/Messages", params={"pageSize": 100}).json()["results"]
    return [email.message_from_string(httpx.get(f"{SMTP}/api/Messages/{m['id']}/raw").text, policy=default)
            for m in lista]


def corpo(mensagem):
    return "\n".join(p.get_content() for p in mensagem.walk() if p.get_content_maintype() == "text")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    rep = (yield).get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.failed):
        CASOS.append({"id": item.nodeid, "resultado": rep.outcome,
                      "requisitos": [v for mark in item.iter_markers("req") for v in mark.args],
                      "integracoes": [v for mark in item.iter_markers("integracao") for v in mark.args],
                      "falha": str(rep.longrepr) if rep.failed else None})


def pytest_sessionfinish(session, exitstatus):
    vistos = set()
    for o in INVENTARIO["operacoes"]:
        padrao = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", o["caminho"]) + "$"
        if any(c["metodo"] == o["metodo"] and re.match(padrao, c["caminho"]) for c in CHAMADAS):
            vistos.add((o["metodo"], o["caminho"]))
    relatorio = {"referencia": "46b89c1", "exitstatus": exitstatus, "casos": CASOS,
                 "operacoes_exercitadas": len(vistos), "operacoes_declaradas": 50,
                 "chamadas": CHAMADAS,
                 "nao_exercitadas": [o for o in INVENTARIO["operacoes"]
                                     if (o["metodo"], o["caminho"]) not in vistos]}
    registradas = {t for a in DIVERGENCIAS["achados"].values() for t in a["testes"]}
    falhas = {c["id"].split("gabarito/")[-1] for c in CASOS if c["resultado"] == "failed"}
    relatorio["falhas_nao_registradas"] = sorted(falhas - registradas)
    relatorio["divergencias_que_passaram"] = sorted(registradas - falhas)
    ESTADO.mkdir(exist_ok=True)
    (ESTADO / "GABARITO.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n")
