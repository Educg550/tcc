import re
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

ROTULOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]


class _ColetorDeTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        if tag in ("input", "textarea", "img"):
            self.tags.append((tag, dict(attrs)))


@pytest.fixture(scope="module")
def pagina():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers.get("content-type", "")
    return resposta.text


@pytest.fixture(scope="module")
def frontend(pagina):
    return pagina + "\n" + client.get("/app.js").text


def test_abas_alunos_e_docentes_nessa_ordem(frontend):
    assert "ALUNOS" in frontend
    assert "DOCENTES" in frontend
    assert frontend.index("ALUNOS") < frontend.index("DOCENTES")


@pytest.mark.parametrize("bloco", BLOCOS)
def test_bloco_com_titulo_visivel(frontend, bloco):
    assert bloco in frontend, bloco


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_rotulo_de_campo_visivel(frontend, rotulo):
    assert rotulo in frontend, rotulo


@pytest.mark.parametrize("opcao", OPCOES)
def test_opcao_de_selecao_visivel(frontend, opcao):
    assert opcao in frontend, opcao


def test_botao_enviar_solicitacao(frontend):
    assert "Enviar solicitação" in frontend


def test_cabecalho_com_logo_e_nome_da_usp(frontend):
    css = client.get("/style.css").text
    assert "usp-logo.png" in frontend + css
    assert "Universidade de São Paulo" in frontend


def test_todo_campo_de_entrada_tem_placeholder(frontend):
    coletor = _ColetorDeTags()
    coletor.feed(frontend)
    campos = [
        (tag, attrs)
        for tag, attrs in coletor.tags
        if tag == "textarea"
        or attrs.get("type", "text") in ("text", "email", "tel", "number")
    ]
    assert campos
    for tag, attrs in campos:
        assert (attrs.get("placeholder") or "").strip(), f"<{tag}> {attrs} sem placeholder"


def test_placeholder_nao_repete_o_rotulo(frontend):
    coletor = _ColetorDeTags()
    coletor.feed(frontend)
    rotulos = {rotulo.upper() for rotulo in ROTULOS}
    for _, attrs in coletor.tags:
        placeholder = (attrs.get("placeholder") or "").strip().upper()
        if placeholder:
            assert placeholder not in rotulos, attrs


def test_style_css_servido():
    assert client.get("/style.css").status_code == 200


def test_app_js_servido():
    assert client.get("/app.js").status_code == 200


def test_logo_usp_servida():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers.get("content-type", "").startswith("image/")


def test_pagina_referencia_style_e_js(pagina):
    assert re.search(r"href\s*=\s*[\"'][^\"']*style\.css", pagina)
    assert re.search(r"src\s*=\s*[\"'][^\"']*app\.js", pagina)


def test_css_com_as_cores_da_usp():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_com_fonte_sem_serifa():
    assert "sans-serif" in client.get("/style.css").text.lower()


def test_pagina_sem_recursos_remotos(pagina):
    assert not re.search(r"(?:src|href)\s*=\s*[\"']https?://", pagina)


def test_css_e_js_sem_recursos_remotos():
    for caminho in ("/style.css", "/app.js"):
        assert "://" not in client.get(caminho).text


def _rotas_post():
    return [
        rota.path
        for rota in app.routes
        if "POST" in (getattr(rota, "methods", None) or set())
    ]


def test_backend_responde_preencha_todos_os_campos_para_envio_vazio():
    caminhos = _rotas_post()
    assert caminhos, "backend deve expor rota POST para receber a solicitação"
    cliente = TestClient(app, raise_server_exceptions=False)
    corpos = []
    for caminho in caminhos:
        for tentativa in ({"": {}}, {"": {"aba": "alunos"}}, {"data": {}}):
            try:
                resposta = cliente.post(caminho, **tentativa)
            except Exception:
                continue
            corpos.append(resposta.text)
    assert any("Preencha todos os campos" in corpo for corpo in corpos)
