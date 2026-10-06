import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

RAIZ = Path(__file__).resolve().parents[1]

BLOCOS = (
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REIMBOLSO",
)

ROTULOS_DAS_DUAS_ABAS = (
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
)

ROTULOS_SO_NA_ABA_ALUNOS = ("NÍVEL", "TIPO DE AUXÍLIO")

OPCOES = (
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
)


def test_pagina_inicial_e_o_proprio_index_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert resposta.text == (RAIZ / "index.html").read_text(encoding="utf-8")


def test_cabecalho_institucional_da_usp():
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert any(
        nome in html
        for nome in ("IME-USP", "IME USP", "Instituto de Matemática e Estatística", "Pós-Graduação")
    )
    minusculo = html.lower()
    assert "escudo" not in minusculo
    assert "brasão" not in minusculo
    assert "brasao" not in minusculo


def test_abas_alunos_e_docentes_nesta_ordem():
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cada_aba_tem_formulario_e_botao_proprios():
    html = client.get("/").text
    assert len(re.findall(r"<form\b", html, re.IGNORECASE)) == 2
    assert html.count("Enviar solicitação") == 2


def test_blocos_de_campos_com_seus_titulos():
    html = client.get("/").text
    for titulo in BLOCOS:
        assert html.count(titulo) >= 2


def test_rotulos_exatos_dos_campos():
    html = client.get("/").text
    for rotulo in ROTULOS_DAS_DUAS_ABAS:
        assert rotulo in html
        assert html.count(rotulo) >= 2
    for rotulo in ROTULOS_SO_NA_ABA_ALUNOS:
        assert html.count(rotulo) == 1


def test_opcoes_dos_selects():
    html = client.get("/").text
    for opcao in OPCOES:
        assert opcao in html


def test_todo_campo_tem_placeholder_com_exemplo():
    html = client.get("/").text
    placeholders = re.findall(r'(?<![-\w])placeholder\s*=\s*(["\'])(.*?)\1', html)
    assert placeholders, "nenhum placeholder encontrado na página"
    rotulos = set(ROTULOS_DAS_DUAS_ABAS) | set(ROTULOS_SO_NA_ABA_ALUNOS)
    for _, exemplo in placeholders:
        assert exemplo.strip(), "placeholder não pode ser vazio"
        assert exemplo not in rotulos, f"placeholder não pode repetir o rótulo: {exemplo}"
    campos = len(re.findall(r"<input\b", html, re.IGNORECASE)) + len(
        re.findall(r"<textarea\b", html, re.IGNORECASE)
    )
    sem_placeholder = len(
        re.findall(
            r'<input\b[^>]*\btype\s*=\s*["\'](?:submit|button|reset|hidden)',
            html,
            re.IGNORECASE,
        )
    )
    assert len(placeholders) >= campos - sem_placeholder


def test_a_pagina_usa_style_css_e_app_js():
    html = client.get("/").text
    assert "style.css" in html
    assert "app.js" in html


def test_style_css_app_js_e_logo_sao_servidos():
    css = client.get("/style.css")
    assert css.status_code == 200
    assert "css" in css.headers["content-type"]
    assert css.text.strip()

    js = client.get("/app.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]
    assert js.text.strip()

    logo = client.get("/assets/usp-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"].startswith("image/")


def test_arquivos_do_frontend_existem_na_raiz():
    for nome in ("index.html", "style.css", "app.js"):
        assert (RAIZ / nome).is_file(), f"{nome} deve existir na raiz do projeto"
    assert (RAIZ / "assets" / "usp-logo.png").is_file()


def test_cores_da_identidade_visual_da_usp():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_da_identidade():
    css = client.get("/style.css").text
    assert "Open Sans" in css or "sans-serif" in css


def test_nenhum_recurso_externo():
    html = client.get("/").text
    css = client.get("/style.css").text
    js = client.get("/app.js").text
    assert not re.search(
        r"<(?:script|link|img|iframe)\b[^>]*\b(?:src|href|srcset)\s*=\s*[\"']https?://",
        html,
        re.IGNORECASE,
    )
    assert "@import" not in css
    assert not re.search(r"url\(\s*[\"']?\s*https?://", css, re.IGNORECASE)
    assert not re.search(r"(?:fetch|import)\s*\(?\s*[\"']https?://", js)
