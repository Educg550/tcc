import re

import pytest

ROTULOS_DAS_ABAS = ["ALUNOS", "DOCENTES"]

TITULOS_DOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS_COMUNS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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

ROTULOS_SOMENTE_DA_ABA_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]

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


def _caminho_do_recurso(html, nome):
    for referencia in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', html):
        if referencia.endswith(nome):
            return referencia
    return "/" + nome


@pytest.fixture(scope="session")
def pagina(client):
    html = client.get("/").text
    return {
        "html": html,
        "css": client.get(_caminho_do_recurso(html, "style.css")).text,
        "js": client.get(_caminho_do_recurso(html, "app.js")).text,
        "logo": _caminho_do_recurso(html, "usp-logo.png"),
    }


def test_pagina_inicial_responde(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_abas_com_rotulos_exatos_nessa_ordem(pagina):
    html = pagina["html"]
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos(pagina):
    tela = pagina["html"] + pagina["js"]
    for titulo in TITULOS_DOS_BLOCOS:
        assert titulo in tela


def test_rotulos_dos_campos_presentes(pagina):
    tela = pagina["html"] + pagina["js"]
    for rotulo in ROTULOS_COMUNS + ROTULOS_SOMENTE_DA_ABA_ALUNOS:
        assert rotulo in tela


def test_cada_aba_tem_os_campos_comuns(pagina):
    html = pagina["html"]
    for rotulo in ROTULOS_COMUNS:
        assert html.count(rotulo) >= 2


def test_opcoes_das_selecoes(pagina):
    tela = pagina["html"] + pagina["js"]
    for opcao in OPCOES:
        assert opcao in tela


def test_botao_enviar_em_cada_aba(pagina):
    assert pagina["html"].count("Enviar solicitação") >= 2


def test_cabecalho_institucional(pagina):
    tela = pagina["html"] + pagina["js"]
    assert "Universidade de São Paulo" in tela
    assert "usp-logo.png" in tela


def test_css_e_js_servidos(client, pagina):
    assert client.get(_caminho_do_recurso(pagina["html"], "style.css")).status_code == 200
    assert client.get(_caminho_do_recurso(pagina["html"], "app.js")).status_code == 200


def test_logo_servida(client, pagina):
    resposta = client.get(pagina["logo"])
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def test_placeholders_sao_exemplos(pagina):
    html = pagina["html"]
    placeholders = re.findall(r'placeholder="([^"]+)"', html)
    placeholders += re.findall(r"placeholder='([^']+)'", html)
    assert len(placeholders) >= 40
    rotulos = [rotulo.lower() for rotulo in ROTULOS_COMUNS + ROTULOS_SOMENTE_DA_ABA_ALUNOS]
    for placeholder in placeholders:
        assert placeholder.strip().lower() not in rotulos


def test_identidade_visual_usp_no_css(pagina):
    css = pagina["css"].lower()
    assert "#1094ab" in css
    assert "open sans" in css or "sans-serif" in css


def test_oficio_preserva_quebras_de_linha(pagina):
    tudo = pagina["html"] + pagina["css"] + pagina["js"]
    assert re.search(r"white-space\s*:\s*pre", tudo) or re.search(r"<pre[\s>]", tudo)


def test_titulo_da_confirmacao(pagina):
    tela = pagina["html"] + pagina["js"]
    assert "Solicitação registrada" in tela
