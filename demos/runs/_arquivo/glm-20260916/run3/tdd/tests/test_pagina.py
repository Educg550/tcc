import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

ROTULOS = [
    "SOLICITANTE E EVENTO",
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
    "ENDEREÇO DO SOLICITANTE",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
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


def _pagina():
    html = client.get("/").text
    js = client.get("/app.js").text
    return f"{html}\n{js}"


def test_pagina_inicial_e_servida_como_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_arquivos_do_frontend_sao_servidos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_abas_alunos_e_docentes_nessa_ordem():
    pagina = _pagina().lower()
    assert "alunos" in pagina
    assert "docentes" in pagina
    assert pagina.index("alunos") < pagina.index("docentes")


def test_todos_os_rotulos_estao_na_pagina():
    pagina = _pagina().lower()
    for rotulo in ROTULOS:
        assert rotulo.lower() in pagina


def test_opcoes_das_selecoes_estao_na_pagina():
    pagina = _pagina().lower()
    for opcao in OPCOES:
        assert opcao.lower() in pagina


def test_botao_enviar_e_titulo_da_confirmacao():
    pagina = _pagina().lower()
    assert "enviar solicitação" in pagina
    assert "solicitação registrada" in pagina


def test_cabecalho_institucional_da_usp():
    pagina = _pagina().lower()
    assert "usp-logo.png" in pagina
    assert "universidade de são paulo" in pagina
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert "image" in resposta.headers["content-type"].lower()


def test_paleta_e_fonte_da_identidade_no_css():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "open sans" in css
    assert "sans-serif" in css


def test_placeholders_sao_exemplos_e_nao_repetem_rotulos():
    pagina = _pagina()
    placeholders = re.findall(r'placeholder\s*=\s*["\']([^"\']+)["\']', pagina)
    placeholders += re.findall(r'\.placeholder\s*=\s*["\']([^"\']+)["\']', pagina)
    placeholders += re.findall(
        r'setAttribute\(\s*["\']placeholder["\']\s*,\s*["\']([^"\']+)["\']', pagina
    )
    assert len(placeholders) >= 28
    rotulos = {rotulo.strip().lower() for rotulo in ROTULOS}
    for placeholder in placeholders:
        assert placeholder.strip().lower() not in rotulos
