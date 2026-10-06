import re


def _alunos_section(html):
    start = html.index("id=\"aba-alunos\"")
    try:
        end = html.index("id=\"aba-docentes\"")
    except ValueError:
        end = len(html)
    return html[start:end]


def _docentes_section(html):
    start = html.index("id=\"aba-docentes\"")
    return html[start:]


def test_aba_alunos_ativa_por_padrao(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    assert "active" in alunos.split("<")[0], alunos.split("<")[0]


def test_aba_docentes_inativa_por_padrao(client):
    html = client.get("/").text
    docentes = _docentes_section(html)
    primeira_tag = docentes.split("<")[0]
    assert "active" not in primeira_tag, primeira_tag


CAMPOS_OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
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

CAMPOS_SO_ALUNOS = [
    "NÍVEL",
    "TIPO DE AUXÍLIO",
]

OPCIONAL_SO_ALUNOS = [
    "LINK DO EVENTO, EXAME OU DEFESA",
]


def test_campos_obrigatorios_presentes_na_aba_alunos(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    for campo in CAMPOS_OBRIGATORIOS:
        assert campo in alunos, campo


def test_campos_exclusivos_alunos_na_aba_alunos(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    for campo in CAMPOS_SO_ALUNOS:
        assert campo in alunos, campo


def test_campos_exclusivos_alunos_ausentes_na_aba_docentes(client):
    html = client.get("/").text
    docentes = _docentes_section(html)
    for campo in CAMPOS_SO_ALUNOS:
        assert campo not in docentes, campo


def test_campos_obrigatorios_presentes_na_aba_docentes(client):
    html = client.get("/").text
    docentes = _docentes_section(html)
    for campo in CAMPOS_OBRIGATORIOS:
        assert campo in docentes, campo


def test_campos_opcionais_presentes_na_aba_alunos(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    for campo in OPCIONAL_SO_ALUNOS:
        assert campo in alunos, campo



def test_rutulos_exatos_na_ordem_correta(client):
    import pathlib
    html = pathlib.Path("app.js").read_text(encoding="utf-8")
    labels = re.findall(r"label\s*:\s*\"([^\"]+)\"", html)

    alunos_expected = [
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

    docentes_expected = [
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

    assert labels[:len(alunos_expected)] == alunos_expected
    assert labels[len(alunos_expected):] == docentes_expected


def test_titulos_dos_blocos(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    docentes = _docentes_section(html)
    assert "SOLICITANTE E EVENTO" in alunos
    assert "ENDEREÇO DO SOLICITANTE" in alunos
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in alunos
    assert "SOLICITANTE E EVENTO" in docentes
    assert "ENDEREÇO DO SOLICITANTE" in docentes
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in docentes


def test_titulo_pagina_e_cabecalho_institucional(client):
    html = client.get("/").text
    assert "Universidade de São Paulo" in html


def test_botao_enviar_solicitacao_em_cada_aba(client):
    html = client.get("/").text
    alunos = _alunos_section(html)
    docentes = _docentes_section(html)
    assert "Enviar solicitação" in alunos
    assert "Enviar solicitação" in docentes


def test_abas_rutulos_exatos_ordem(client):
    import pathlib
    html = pathlib.Path("index.html").read_text(encoding="utf-8")
    tabs = re.findall(r'role=\"tab\"[^>]*>\s*([A-Z]+)\s*<', html)
    assert tabs == ["ALUNOS", "DOCENTES"]


def test_placeholder_visivel_em_todos_os_campos(client):
    html = client.get("/").text
    placeholders = re.findall(r'placeholder\s*=\s*\"([^\"]*)\"', html)
    campos = re.findall(r'<(?:input|select|textarea)[^>]*>', html)
    assert len(placeholders) >= len(campos)
    for p in placeholders:
        assert p.strip(), "placeholder vazio encontrado"


def test_javascript_esta_presente(client):
    js = client.get("/app.js").text
    assert "R$" in js
    assert "1.500,00" not in js  # hardcoded formatting shouldn't be there
    assert "formatar" in js.lower() or "mask" in js.lower() or "centavos" in js.lower()
