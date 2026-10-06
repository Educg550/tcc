import re

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


def _html_visivel():
    resposta = client.get("/")
    assert resposta.status_code == 200
    sem_tags = re.sub(r"<[^>]+>", " ", resposta.text)
    return re.sub(r"\s+", " ", sem_tags)


def _js():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    return resposta.text


def _frontend():
    return _html_visivel() + "\n" + _js()


def test_pagina_inicial_serve_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_abas_alunos_e_docentes_na_ordem():
    texto = _frontend()
    assert "ALUNOS" in texto
    assert "DOCENTES" in texto
    assert texto.index("ALUNOS") < texto.index("DOCENTES")


def test_cabecalho_institucional():
    assert "Universidade de São Paulo" in _frontend()


def test_logotipo_da_usp():
    bruto = client.get("/").text + "\n" + _js()
    assert "usp-logo.png" in bruto


def test_blocos_de_campos():
    texto = _frontend()
    assert "SOLICITANTE E EVENTO" in texto
    assert "ENDEREÇO DO SOLICITANTE" in texto
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in texto


def test_rotulos_dos_campos():
    texto = _frontend()
    faltando = [rotulo for rotulo in ROTULOS if rotulo not in texto]
    assert not faltando, faltando


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in _frontend()


def test_titulo_de_confirmacao():
    assert "Solicitação registrada" in _frontend()


def test_oficio_redigido_no_frontend():
    texto = _frontend()
    for trecho in [
        "Interessada(o):",
        "Dados do evento",
        "Dados para pagamento",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert trecho in texto, trecho


def test_oficio_docentes_usa_verba_do_programa():
    assert "Verba do programa" in _frontend()


def test_placeholders_com_exemplo():
    bruto = client.get("/").text + "\n" + _js()
    valores = re.findall(r"""placeholder\s*=\s*["']([^"']*)["']""", bruto)
    assert len(valores) >= 10
    assert all(valor.strip() for valor in valores)
    assert not set(valores) & set(ROTULOS)


def test_cores_da_universidade():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_da_identidade_sem_serifa():
    css = client.get("/style.css").text.lower()
    assert "open sans" in css or "sans-serif" in css


def test_sem_recursos_baixados_da_rede():
    html = client.get("/").text
    assert not re.search(r"""(?:src|href)\s*=\s*["']https?://""", html)
    css = client.get("/style.css").text
    assert "http://" not in css
    assert "https://" not in css


def test_arquivos_estaticos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    logo = client.get("/assets/usp-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"].startswith("image/")


def test_backend_rejeita_solicitacao_vazia():
    spec = client.get("/openapi.json").json()
    caminhos = [c for c, ops in spec.get("paths", {}).items() if "post" in ops]
    assert caminhos
    for caminho in caminhos:
        for envio in ({"data": {}}, {"json": {}}):
            resposta = client.post(caminho, **envio)
            if "Preencha todos os campos" in resposta.text:
                return
    assert False, "o backend não devolveu 'Preencha todos os campos'"
