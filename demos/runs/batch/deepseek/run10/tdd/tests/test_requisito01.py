from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Página servida
# ---------------------------------------------------------------------------

def _html_inicial():
    resposta = client.get("/")
    assert resposta.status_code == 200
    return resposta.text


def test_pagina_inicial_serve_documento_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers.get("content-type", "")
    assert "Universidade de São Paulo" in resposta.text


def test_cabecalho_referencia_o_logo():
    html = _html_inicial()
    assert "assets/usp-logo.png" in html


def test_abas_alunos_e_docentes_na_ordem():
    html = _html_inicial()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_botao_enviar_solicitacao_em_cada_aba():
    html = _html_inicial()
    assert html.count("Enviar solicitação") >= 2


def test_blocos_de_campos():
    html = _html_inicial()
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in html, titulo


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


def test_rotulos_dos_campos():
    html = _html_inicial()
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_opcoes_de_selecao():
    html = _html_inicial()
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in html, opcao


def test_campos_tem_placeholder():
    html = _html_inicial()
    assert html.count("placeholder") >= 10


def test_css_e_js_servidos():
    for caminho in ("/style.css", "/app.js"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200, caminho


def test_logo_usp_servido():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200


def test_cores_da_universidade_no_css():
    css = client.get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, cor


# ---------------------------------------------------------------------------
# Envio da solicitação
# ---------------------------------------------------------------------------

def _rota_post():
    for rota in app.routes:
        metodos = getattr(rota, "methods", None) or set()
        caminho = getattr(rota, "path", "")
        if "POST" in metodos and not caminho.startswith("/assets"):
            return caminho
    raise AssertionError("nenhuma rota POST de envio encontrada")


def _envia(payload):
    caminho = _rota_post()
    try:
        conteudo = (
            app.openapi()["paths"][caminho]["post"]
            .get("requestBody", {})
            .get("content", {})
        )
    except Exception:
        conteudo = {}
    if not conteudo or "application/json" in conteudo:
        return client.post(caminho, json=payload)
    return client.post(caminho, data=payload)


def _corpo(resposta):
    try:
        return resposta.json()
    except Exception:
        return None


def _erros(resposta):
    dados = _corpo(resposta)
    if isinstance(dados, dict):
        for chave in ("erros", "errors", "mensagens"):
            if chave in dados:
                return dados[chave]
    return []


def _oficio(resposta):
    dados = _corpo(resposta)
    if isinstance(dados, dict):
        for chave in ("oficio", "ofício", "documento"):
            valor = dados.get(chave)
            if valor:
                return valor
        return ""
    if isinstance(dados, str):
        return dados
    return resposta.text


def solicitacao_alunos(**alteracoes):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro de Computação",
        "periodo": "10 a 15 de janeiro de 2020",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.ime.usp.br",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Passagens aéreas e hospedagem.",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco A",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(alteracoes)
    return dados


def solicitacao_docentes(**alteracoes):
    dados = solicitacao_alunos()
    dados["aba"] = "docentes"
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    dados.update(alteracoes)
    return dados


def test_envio_valido_gera_oficio_com_os_dados():
    resposta = _envia(solicitacao_alunos())
    assert _erros(resposta) == []
    oficio = _oficio(resposta)
    assert "<<" not in oficio
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "Evento: Congresso Brasileiro de Computação" in oficio
    assert "Período: 10 a 15 de janeiro de 2020" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.ime.usp.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagens aéreas e hospedagem." in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco A" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_de_docentes_nao_tem_tipo_nem_nivel():
    resposta = _envia(solicitacao_docentes())
    assert _erros(resposta) == []
    oficio = _oficio(resposta)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "\nPrograma: Ciência da Computação\n" in "\n" + oficio + "\n"
    assert "Mestrado" not in oficio
    assert "Doutorado" not in oficio


def test_linhas_opcionais_saem_quando_vazias():
    resposta = _envia(solicitacao_alunos(link_evento="", complemento=""))
    oficio = _oficio(resposta)
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio
    assert "Evento: Congresso Brasileiro de Computação" in oficio


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def test_campo_obrigatorio_vazio_mostra_mensagem_unica():
    resposta = _envia(
        solicitacao_alunos(nome_completo="", programa="", nome_evento="")
    )
    assert _erros(resposta).count("Preencha todos os campos") == 1
    assert _oficio(resposta) == ""


def test_n_usp_com_letras():
    erros = _erros(_envia(solicitacao_alunos(n_usp="12a45")))
    assert "N. USP deve conter apenas números" in erros


def test_agencia_com_letras():
    erros = _erros(_envia(solicitacao_alunos(agencia="12a4")))
    assert "Número da agência deve conter apenas números" in erros


def test_valor_solicitado_zero():
    erros = _erros(_envia(solicitacao_alunos(valor_solicitado="R$ 0,00")))
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_invalido():
    erros = _erros(_envia(solicitacao_alunos(email="maria.usp.br")))
    assert "E-mail inválido" in erros


def test_cpf_fora_do_formato():
    erros = _erros(_envia(solicitacao_alunos(cpf="12345678909")))
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cep_fora_do_formato():
    erros = _erros(_envia(solicitacao_alunos(cep="05508090")))
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_de_nascimento_fora_do_formato():
    erros = _erros(_envia(solicitacao_alunos(data_nascimento="01021980")))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_cpf_com_digitos_verificadores_invalidos():
    erros = _erros(_envia(solicitacao_alunos(cpf="123.456.789-00")))
    assert "CPF inválido" in erros


def test_data_de_nascimento_inexistente():
    erros = _erros(_envia(solicitacao_alunos(data_nascimento="31/02/1980")))
    assert "Data de nascimento inválida" in erros


def test_varios_erros_aparecem_juntos():
    erros = _erros(_envia(solicitacao_alunos(n_usp="abc", email="maria.usp.br")))
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros
