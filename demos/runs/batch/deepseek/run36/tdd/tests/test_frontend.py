"""Testes da parte estatica: pagina, abas, rotulos e arquivos servidos."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _home():
    r = client.get("/")
    assert r.status_code == 200, "a raiz deve servir a pagina do formulario"
    return r


def test_raiz_serve_html_institucional():
    r = _home()
    assert "text/html" in r.headers.get("content-type", "")
    assert "Universidade de Sao Paulo" in r.text or "Universidade de São Paulo" in r.text
    assert "usp-logo.png" in r.text


def test_abas_com_rotulos_exatos_na_ordem():
    html = _home().text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos_visiveis():
    html = _home().text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_rotulos_exatos_dos_campos():
    html = _home().text
    rotulos = [
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
        "Enviar solicitação",
    ]
    for rotulo in rotulos:
        assert rotulo in html, rotulo


def test_opcoes_de_selecao_presentes():
    html = _home().text
    for opcao in [
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ]:
        assert opcao in html, opcao


def _serve_algum(caminhos):
    return any(client.get(c).status_code == 200 for c in caminhos)


def test_arquivos_estaticos_servidos():
    assert _serve_algum(["/style.css", "/static/style.css"])
    assert _serve_algum(["/app.js", "/static/app.js"])
    assert _serve_algum(["/assets/usp-logo.png"])


def test_sem_recursos_externos():
    for caminho in [
        "/style.css",
        "/static/style.css",
        "/app.js",
        "/static/app.js",
        "/",
    ]:
        r = client.get(caminho)
        if r.status_code != 200:
            continue
        texto = r.text
        assert "http://" not in texto, caminho
        assert "https://" not in texto, caminho
        assert "cdnjs" not in texto, caminho
        assert "googleapis" not in texto, caminho
