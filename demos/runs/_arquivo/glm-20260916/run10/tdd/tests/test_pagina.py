import html as html_lib
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app

ROTULOS_EM_ORDEM = [
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


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _primeiro_200(client, caminhos):
    for caminho in caminhos:
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            return resposta
    return None


@pytest.fixture(scope="module")
def pagina(client):
    resposta = _primeiro_200(client, ["/", "/index.html"])
    assert resposta is not None, "index.html não está sendo servido"
    assert "html" in resposta.headers.get("content-type", "")
    return resposta.text


@pytest.fixture(scope="module")
def css(client):
    resposta = _primeiro_200(client, ["/style.css", "/static/style.css", "/css/style.css"])
    assert resposta is not None, "style.css não está sendo servido"
    return resposta.text


@pytest.fixture(scope="module")
def js(client):
    resposta = _primeiro_200(client, ["/app.js", "/static/app.js", "/js/app.js"])
    assert resposta is not None, "app.js não está sendo servido"
    return resposta.text


def _visivel(texto_html):
    sem_blocos = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", texto_html, flags=re.S | re.I)
    sem_tags = re.sub(r"<[^>]+>", " ", sem_blocos)
    texto = html_lib.unescape(sem_tags).replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", texto)


@pytest.fixture(scope="module")
def fonte(pagina, js):
    return _visivel(pagina) + " | " + re.sub(r"\s+", " ", html_lib.unescape(js))


def test_index_e_servido(pagina):
    assert pagina.strip() != ""


def test_css_e_servido_com_conteudo(css):
    assert len(css.strip()) > 100


def test_app_js_e_servido_com_conteudo(js):
    assert len(js.strip()) > 0


def test_logo_da_usp_e_servido(client):
    resposta = _primeiro_200(
        client,
        ["/assets/usp-logo.png", "/static/assets/usp-logo.png", "/static/usp-logo.png"],
    )
    assert resposta is not None, "assets/usp-logo.png não está sendo servido"
    assert (
        resposta.headers.get("content-type", "").startswith("image")
        or len(resposta.content) > 100
    )


def test_cabecalho_institucional_da_usp(pagina):
    assert "usp-logo.png" in pagina
    assert "Universidade de São Paulo" in _visivel(pagina)


def test_abas_alunos_e_docentes_nessa_ordem(fonte):
    i_alunos = fonte.find("ALUNOS")
    i_docentes = fonte.find("DOCENTES")
    assert i_alunos != -1, "aba ALUNOS ausente"
    assert i_docentes != -1, "aba DOCENTES ausente"
    assert i_alunos < i_docentes


def test_aba_alunos_esta_ativa_ao_abrir(pagina, js):
    marcadores = ("activ", "ativa", "ativo", "selected", "checked", "current", "selecionada")
    i_alunos = pagina.find("ALUNOS")
    if i_alunos != -1:
        janela = pagina[max(0, i_alunos - 400):i_alunos].lower()
        if any(m in janela for m in marcadores):
            return
        i_docentes = pagina.find("DOCENTES")
        if i_docentes != -1:
            janela_docentes = pagina[max(0, i_docentes - 400):i_docentes].lower()
            if any(m in janela_docentes for m in marcadores):
                pytest.fail("a aba DOCENTES é a que aparece marcada como ativa ao abrir")
    baixo_js = js.lower()
    if ("alunos" in baixo_js or "alunos" in pagina.lower()) and any(
        m in baixo_js for m in ("activ", "ativa", "selected")
    ):
        return
    pytest.fail("não foi possível confirmar que a aba ALUNOS inicia ativa")


def test_rotulos_e_blocos_na_ordem_exata(fonte):
    pos = 0
    for rotulo in ROTULOS_EM_ORDEM:
        i = fonte.find(rotulo, pos)
        assert i != -1, f"rótulo ausente ou fora de ordem: {rotulo}"
        pos = i + len(rotulo)


def test_cada_aba_tem_botao_enviar(fonte):
    assert fonte.count("Enviar solicitação") >= 2


def test_titulo_da_confirmacao(pagina, js):
    assert "Solicitação registrada" in _visivel(pagina) or "Solicitação registrada" in js


def test_todo_campo_tem_placeholder_de_exemplo(pagina, js):
    placeholders = re.findall(r'placeholder\s*=\s*["\']([^"\']+)["\']', pagina)
    placeholders += re.findall(r'placeholder\s*=\s*["\']([^"\']+)["\']', js)
    placeholders += re.findall(r'placeholder\s*:\s*["\']([^"\']+)["\']', js)
    assert len(placeholders) >= 40, f"poucos placeholders encontrados: {len(placeholders)}"
    rotulos = {re.sub(r"\s+", " ", r).strip().casefold() for r in ROTULOS_EM_ORDEM}
    rotulos.add("enviar solicitação")
    for placeholder in placeholders:
        limpo = re.sub(r"\s+", " ", placeholder).strip()
        assert limpo != ""
        assert limpo.casefold() not in rotulos, f"placeholder repete o rótulo: {placeholder}"


def test_cores_da_identidade_usp(css):
    baixo = css.lower()
    assert "#1094ab" in baixo
    assert "#64c4d2" in baixo or "#fcb421" in baixo


def test_fonte_e_identidade_sem_recursos_externos(css, pagina):
    baixo = css.lower()
    assert "open sans" in baixo or "sans-serif" in baixo
    assert "@import" not in baixo
    assert not re.search(r"<(script|link)\b[^>]*\b(src|href)=['\"]https?://", pagina, re.I)


def test_campos_distribuidos_em_colunas(css):
    baixo = css.lower()
    assert "grid" in baixo or "flex" in baixo


def test_quebras_de_linha_do_oficio_preservadas(css, pagina, js):
    baixo = css.lower()
    assert (
        "pre-wrap" in baixo
        or "pre-line" in baixo
        or "<pre" in pagina.lower()
        or "<pre" in js.lower()
    )
