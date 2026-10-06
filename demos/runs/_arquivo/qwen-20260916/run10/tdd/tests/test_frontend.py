import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def _text(path):
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.text


def test_index_servido():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<form" in resp.text.lower()


def test_estaticos_servidos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/assets/usp-logo.png").status_code == 200


def test_abas_exatas_em_ordem():
    html = _text("/")
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_aba_alunos_ativa():
    html = _text("/")
    assert "aba ativa" in html


def test_botoes_enviar():
    html = _text("/")
    assert html.count("Enviar solicitação") == 2


def test_titulos_dos_blocos():
    html = _text("/")
    for bloco in ("SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"):
        assert bloco in html


def test_campos_almunos():
    html = _text("/")
    for label in [
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
    ]:
        assert label in html
    assert 'Mestrado' in html and 'Doutorado' in html
    assert 'Participação em evento' in html
    assert 'Banca de exame ou defesa' in html
    assert 'Pôster' in html
    assert 'Apresentação oral' in html
    assert 'Não irá apresentar trabalho' in html


def test_docentes_sem_nivel_e_tipo_de_auxilio():
    html = _text("/")
    partes = re.split(r'(?=\bDOCENTES\b)', html, maxsplit=1)
    assert len(partes) == 2
    docentes = partes[1]
    assert 'NÍVEL' not in docentes
    assert 'TIPO DE AUXÍLIO' not in docentes


def test_campos_com_placeholder():
    html = _text("/")
    inputs = re.findall(r'<(?:input|textarea|select)[^>]*>', html)
    assert inputs
    for tag in inputs:
        assert 'placeholder=' in tag
    assert 'placeholder="NOME COMPLETO - SEM ABREVIAR"' not in html


def test_campos_formataveis():
    js = _text("/app.js")
    for padrao in (r'R\$', r'\.', r'-', r'/'):
        assert re.search(padrao, js)


def test_css_usa_cores_institucionais():
    css = _text("/style.css")
    for hexcor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert hexcor in css


def test_css_e_js_sem_rede():
    css = _text("/style.css")
    js = _text("/app.js")
    assert 'http://' not in css and 'https://' not in css
    assert 'http://' not in js and 'https://' not in js


def test_oficio_preserva_quebras():
    css = _text("/style.css")
    assert 'white-space' in css and ('pre' in css or 'pre-line' in css)
