import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
STYLE = ROOT / "style.css"
APPJS = ROOT / "app.js"
ASSETS = ROOT / "assets"


def test_arquivos_estaticos_existem():
    assert INDEX.is_file()
    assert STYLE.is_file()
    assert APPJS.is_file()


def test_assets_servidos():
    assert ASSETS.is_dir()
    for name in ASSETS.iterdir():
        r = client.get(f"/assets/{name.name}")
        assert r.status_code == 200


def test_css_e_js_escritos_a_mao():
    css = STYLE.read_text(encoding="utf-8")
    js = APPJS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    for blob, label in ((css, "style.css"), (js, "app.js"), (html, "index.html")):
        assert "http://" not in blob.lower().replace("https://", "")
        assert "https://" not in blob.lower()
        assert "cdn" not in blob.lower()
        assert "fonts.googleapis" not in blob.lower()
        assert "@import" not in blob
        assert not re.search(r"url\(\s*['\"]?https?:", blob)


def test_fonte_open_sans():
    css = STYLE.read_text(encoding="utf-8")
    assert "Open Sans" in css
    assert "serif" not in css.replace("sans-serif", "").lower()


def test_brasao_ausente():
    html = INDEX.read_text(encoding="utf-8")
    css = STYLE.read_text(encoding="utf-8")
    js = APPJS.read_text(encoding="utf-8")
    for blob, name in (
        (html, "index.html"),
        (css, "style.css"),
        (js, "app.js"),
    ):
        low = blob.lower()
        assert "escudo" not in low, name
        assert "brasao" not in low, name
        assert "brasão" not in low, name
    # nenhuma imagem de brasao na pasta de assets
    assert not any("brasao" in p.name.lower() or "brasão" in p.name.lower() for p in ASSETS.iterdir())


def test_pagina_inicial_carrega():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_index_contem_abas_e_blocos():
    html = INDEX.read_text(encoding="utf-8")
    for rotulo in (
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "Enviar solicitação",
        "Universidade de São Paulo",
    ):
        assert rotulo in html, rotulo
    # index nao deve conter o formulario completo como html estatico:
    # e gerado pelo app.js, que monta os campos
    rotulos_campos = [
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
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "CPF inválido",
        "Data de nascimento inválida",
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
        "Solicitação registrada",
    ]
    js = APPJS.read_text(encoding="utf-8")
    for rotulo in rotulos_campos:
        assert rotulo in js, rotulo


def test_app_js_define_renderizacao():
    js = APPJS.read_text(encoding="utf-8")
    # o js monta a tela; deve existir codigo executavel, nao apenas dados
    assert "function" in js
    assert "document.getElementById" in js or "querySelector" in js
    assert "fetch(" in js
    # oficio: quebras de linha preservadas
    assert "white-space" in STYLE.read_text(encoding="utf-8") or "pre-line" in js


def test_cabecalho_institucional():
    html = INDEX.read_text(encoding="utf-8")
    assert "assets/usp-logo.png" in html
    assert (ASSETS / "usp-logo.png").is_file()
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
