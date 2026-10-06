import re

ROTULOS_CAMPOS = [
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


def test_pagina_inicial_servida(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.text.strip()


def test_app_js_servido(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip()


def test_style_css_servido(client):
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert resposta.text.strip()


def test_logo_da_usp_servida(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content


def test_abas_alunos_e_docentes_nessa_ordem(codigo, normalizar):
    texto = normalizar(" ".join(codigo))
    assert "alunos" in texto
    assert "docentes" in texto
    assert texto.index("alunos") < texto.index("docentes")


def test_titulos_dos_blocos(codigo, normalizar):
    texto = normalizar(" ".join(codigo))
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert normalizar(titulo) in texto


def test_rotulos_dos_campos(codigo, normalizar):
    texto = normalizar(" ".join(codigo))
    faltando = [rotulo for rotulo in ROTULOS_CAMPOS if normalizar(rotulo) not in texto]
    assert faltando == []


def test_opcoes_de_selecao(codigo, normalizar):
    texto = normalizar(" ".join(codigo))
    for opcao in OPCOES:
        assert normalizar(opcao) in texto


def test_botao_enviar_solicitacao(codigo, normalizar):
    assert normalizar("Enviar solicitação") in normalizar(" ".join(codigo))


def test_titulo_da_confirmacao(codigo, normalizar):
    assert normalizar("Solicitação registrada") in normalizar(" ".join(codigo))


def test_nome_da_universidade_no_cabecalho(codigo, normalizar):
    assert normalizar("Universidade de São Paulo") in normalizar(" ".join(codigo))


def test_logotipo_referenciado(codigo, normalizar):
    assert "usp-logo" in normalizar(" ".join(codigo))


def test_placeholders_nao_repetem_os_rotulos(codigo, normalizar):
    texto = " ".join(codigo)
    placeholders = re.findall(r'placeholder\s*[:=]\s*["\']([^"\']+)["\']', texto)
    assert len(placeholders) >= 20
    rotulos = {normalizar(rotulo) for rotulo in ROTULOS_CAMPOS}
    repetidos = [p for p in placeholders if normalizar(p) in rotulos]
    assert repetidos == []


def test_cores_da_identidade_no_css(client):
    css = client.get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css
