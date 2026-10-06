"""Testes da tela servida como arquivos estáticos: index.html, style.css e app.js."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

RAIZ = Path(__file__).resolve().parents[1]

client = TestClient(app)

BLOCO_SOLICITANTE_E_EVENTO = "SOLICITANTE E EVENTO"
BLOCO_ENDERECO = "ENDEREÇO DO SOLICITANTE"
BLOCO_PAGAMENTO = "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"

CAMPOS_SOLICITANTE_E_EVENTO = [
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
]

CAMPOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]

CAMPOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

ORDEM_ALUNOS = (
    [BLOCO_SOLICITANTE_E_EVENTO]
    + CAMPOS_SOLICITANTE_E_EVENTO
    + [BLOCO_ENDERECO]
    + CAMPOS_ENDERECO
    + [BLOCO_PAGAMENTO]
    + CAMPOS_PAGAMENTO
)

SO_NA_ABA_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]
ORDEM_DOCENTES = [rotulo for rotulo in ORDEM_ALUNOS if rotulo not in SO_NA_ABA_ALUNOS]


def _obter(caminho):
    resposta = client.get(caminho)
    assert resposta.status_code == 200, f"GET {caminho} devolveu {resposta.status_code}"
    return resposta


def _encontrar_em_ordem(texto, rotulos, inicio=0):
    """Exige que os rótulos apareçam no texto, nessa ordem."""
    posicao = inicio
    achados = []
    for rotulo in rotulos:
        achado = texto.find(rotulo, posicao)
        assert achado != -1, f"rótulo ausente ou fora de ordem na página: {rotulo!r}"
        achados.append((achado, rotulo))
        posicao = achado + len(rotulo)
    return achados


def test_pagina_inicial_e_html():
    resposta = _obter("/")
    assert "html" in resposta.headers["content-type"].lower()
    assert "<html" in resposta.text.lower()


def test_cabecalho_institucional_da_usp():
    pagina = _obter("/").text
    assert "Universidade de São Paulo" in pagina
    assert "assets/usp-logo.png" in pagina


def test_abas_alunos_e_docentes_nesta_ordem():
    pagina = _obter("/").text
    assert "ALUNOS" in pagina
    assert "DOCENTES" in pagina
    assert pagina.find("ALUNOS") < pagina.find("DOCENTES")


def test_os_dois_formularios_com_os_campos_na_ordem():
    pagina = _obter("/").text
    alunos = _encontrar_em_ordem(pagina, ORDEM_ALUNOS)
    fim_alunos = alunos[-1][0] + len(alunos[-1][1])
    docentes = _encontrar_em_ordem(pagina, ORDEM_DOCENTES, inicio=fim_alunos)
    regiao_docentes = pagina[docentes[0][0] : docentes[-1][0] + len(docentes[-1][1])]
    for rotulo in SO_NA_ABA_ALUNOS:
        assert rotulo not in regiao_docentes, f"{rotulo} só deve existir na aba ALUNOS"


def test_um_formulario_e_um_botao_por_aba():
    pagina = _obter("/").text
    assert pagina.count("<form") >= 2
    assert pagina.count("Enviar solicitação") >= 2


def test_todos_os_campos_tem_placeholder_com_exemplo():
    pagina = _obter("/").text
    valores = re.findall(r'placeholder\s*=\s*"([^"]*)"', pagina, re.IGNORECASE)
    valores += re.findall(r"placeholder\s*=\s*'([^']*)'", pagina, re.IGNORECASE)
    assert len(valores) >= 50, f"só {len(valores)} placeholders na página"
    rotulos = set(ORDEM_ALUNOS)
    for valor in valores:
        assert valor.strip(), "placeholder vazio"
        assert valor not in rotulos, f"placeholder repete o rótulo: {valor!r}"


def test_pagina_usa_style_css_e_app_js():
    pagina = _obter("/").text
    assert "style.css" in pagina
    assert "app.js" in pagina


def test_css_e_js_ficam_em_arquivos_proprios():
    pagina = _obter("/").text
    assert "<style" not in pagina.lower(), "CSS embutido na página"
    assert re.search(r"<script(?![^>]*\bsrc\s*=)", pagina) is None, "JS embutido na página"


def test_sem_recurso_externo():
    pagina = _obter("/").text
    css = _obter("/style.css").text
    assert re.search(r'(?:src|href)\s*=\s*["\'](?:https?:)?//', pagina) is None
    assert "@import" not in css
    assert re.search(r'url\(\s*["\']?(?:https?:)?//', css) is None


def test_cores_e_fonte_institucionais():
    css = _obter("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, f"cor institucional ausente: {cor}"
    assert "open sans" in css or "sans-serif" in css


def test_style_css_e_app_js_servidos():
    css = _obter("/style.css")
    assert "css" in css.headers["content-type"].lower()
    js = _obter("/app.js")
    assert "javascript" in js.headers["content-type"].lower()
    assert js.text.strip(), "app.js vazio"


def test_logotipo_da_usp_servido():
    resposta = _obter("/assets/usp-logo.png")
    assert "image" in resposta.headers["content-type"].lower()
    assert resposta.content


def test_apenas_o_logotipo_como_imagem_da_pasta_assets():
    pagina = _obter("/").text
    css = _obter("/style.css").text
    referencias = re.findall(r'<img[^>]*?\bsrc\s*=\s*"([^"]+)"', pagina)
    referencias += re.findall(r"<img[^>]*?\bsrc\s*=\s*'([^']+)'", pagina)
    referencias += re.findall(r"url\(\s*[\"']?\s*([^\"')\s]+)", css)
    pasta = RAIZ / "assets"
    if not pasta.is_dir():
        return
    disponiveis = {caminho.name for caminho in pasta.iterdir() if caminho.is_file()}
    for referencia in referencias:
        nome = referencia.strip().split("/")[-1]
        if nome in disponiveis:
            assert nome == "usp-logo.png", f"imagem fora do requisito na página: {referencia}"


def test_texto_da_confirmacao_no_frontend():
    pagina = _obter("/").text
    js = _obter("/app.js").text
    assert "Solicitação registrada" in pagina or "Solicitação registrada" in js
