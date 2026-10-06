from pathlib import Path


def _files():
    base = Path(__file__).resolve().parents[1]
    out = {}
    for name in ("index.html", "style.css", "app.js"):
        p = base / name
        out[name] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def test_arquivos_existem():
    base = Path(__file__).resolve().parents[1]
    for name in ("index.html", "style.css", "app.js"):
        assert (base / name).exists(), name


def test_rotulos_abas_blocos_botao():
    html = _files()["index.html"]
    for s in ("ALUNOS", "DOCENTES", "Enviar solicitação",
              "SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE",
              "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"):
        assert s in html


def test_rotulos_campos():
    html = _files()["index.html"]
    for s in (
        "NOME COMPLETO - SEM ABREVIAR", "N. USP", "PROGRAMA", "NÍVEL", "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)", "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO", "LOGRADOURO", "NÚMERO", "COMPLEMENTO",
        "BAIRRO", "CEP", "CIDADE", "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA", "NÚMERO DA CONTA",
        "TIPO DE AUXÍLIO", "Participação em evento", "Banca de exame ou defesa",
        "Mestrado", "Doutorado", "Pôster", "Apresentação oral",
        "Não irá apresentar trabalho",
    ):
        assert s in html


def test_servidos_como_estaticos():
    from fastapi.testclient import TestClient
    from app import app

    c = TestClient(app)
    for p in ("/index.html", "/style.css", "/app.js", "/assets/usp-logo.png"):
        assert c.get(p).status_code == 200, p


def test_app_js_formatadores():
    js = _files()["app.js"]
    assert "R$" in js and "123.456.789-09" not in js


def test_sem_recurso_externo():
    files = _files()
    for src in files.values():
        low = src.lower()
        for token in ("http://", "https://", "googleapis", "cdnjs", "@import"):
            assert token not in low


def test_estilo_usp():
    css = _files()["style.css"]
    for s in ("#1094ab", "#64c4d2", "#fcb421", "Open Sans"):
        assert s in css


def test_html_cabecalho_usp():
    html = _files()["index.html"]
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_css_abas():
    css = _files()["style.css"]
    low = css.replace(" ", "").lower()
    assert "active" in low and ("display:none" in low or "display:none" in css.lower())
