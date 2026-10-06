"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Cobrem a página servida, a API de validação e a geração do ofício.
"""
import re
import unicodedata

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def normaliza(texto):
    """Minúsculas e sem acento, para tolerar pequenas variações de casing."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


# --------------------------------------------------------------------------
# Página
# --------------------------------------------------------------------------


def test_pagina_carrega_com_cabecalho_e_abas():
    resposta = client.get("/")
    assert resposta.status_code == 200
    corpo = resposta.text
    assert "usp-logo.png" in corpo
    assert "Universidade de São Paulo" in corpo
    for rotulo in ("ALUNOS", "DOCENTES"):
        assert rotulo in corpo


def test_assets_disponiveis():
    assert client.get("/assets/usp-logo.png").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_campos_das_abas_no_html():
    corpo = client.get("/").text

    rotulos_alunos = [
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
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "Enviar solicitação",
    ]
    for rotulo in rotulos_alunos:
        assert rotulo in corpo, f"rótulo ausente na página: {rotulo}"

    # Opções dos seletores da aba ALUNOS
    for opcao in ("Mestrado", "Doutorado"):
        assert opcao in corpo
    for opcao in (
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ):
        assert opcao in corpo
    for opcao in ("Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert opcao in corpo

    # Formulários independentes: dois botões de envio
    assert corpo.count("Enviar solicitação") == 2


def test_placeholders_sao_exemplos():
    corpo = client.get("/").text
    for exemplo in ("R$ 1.500,00", "000.000.000-00", "00000-000", "dd/mm/aaaa"):
        assert exemplo in corpo
    # O placeholder não pode repetir o rótulo
    for rotulo in ("LOGRADOURO", "BAIRRO", "NÚMERO DA CONTA"):
        padrao = re.compile(
            rotulo + r"[^<]*</label>\s*<input[^>]*placeholder=\"([^\"]*)\"",
            re.IGNORECASE,
        )
        encontrado = padrao.search(corpo)
        assert encontrado, f"placeholder não encontrado para {rotulo}"
        assert normaliza(encontrado.group(1)) != normaliza(rotulo)


# --------------------------------------------------------------------------
# API: envio e validação
# --------------------------------------------------------------------------


def solicitacao_alunos(**sobrescritas):
    dados = {
        "tipo": "alunos",
        "nome": "Maria da Silva",
        "numero_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor": "150000",
        "detalhamento": "Inscrição e passagens",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matao",
        "numero": "1010",
        "complemento": "",
        "bairro": "Cidade Universitária",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(sobrescritas)
    return dados


def solicitacao_docentes(**sobrescritas):
    dados = solicitacao_alunos()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["tipo"] = "docentes"
    dados.update(sobrescritas)
    return dados


def envia_alunos(**sobrescritas):
    return client.post("/api/solicitacao", json=solicitacao_alunos(**sobrescritas))


def envia_docentes(**sobrescritas):
    return client.post("/api/solicitacao", json=solicitacao_docentes(**sobrescritas))


def erros(resposta):
    assert resposta.status_code == 200
    corpo = resposta.json()
    return corpo.get("erros", [])


def test_envio_valido_alunos():
    resposta = envia_alunos()
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("erros") == []
    assert "Interessada(o): Maria da Silva - 12345678" in corpo["oficio"]


def test_envio_valido_docentes():
    resposta = envia_docentes()
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("erros") == []
    assert "Solicitação de Auxílio Financeiro - Verba do programa" in corpo["oficio"]


def test_todos_os_campos_sao_obrigatorios_exceto_opcionais():
    campos = [
        "nome", "numero_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta",
    ]
    campos_alunos = campos + ["nivel", "tipo_auxilio"]
    base = solicitacao_alunos()
    base.update({c: "" for c in campos_alunos})
    resposta = client.post("/api/solicitacao", json=base)
    assert "Preencha todos os campos" in erros(resposta)


def test_campo_opcional_link_pode_ficar_vazio():
    resposta = envia_alunos(link_evento="")
    assert erros(resposta) == []


def test_campo_opcional_complemento_pode_ficar_vazio():
    resposta = envia_alunos(complemento="")
    assert erros(resposta) == []


def test_numero_usp_apenas_digitos():
    assert "N. USP deve conter apenas números" in erros(envia_alunos(numero_usp="12a45"))
    assert "N. USP deve conter apenas números" in erros(envia_alunos(numero_usp="1234-5678"))
    assert "N. USP deve conter apenas números" not in erros(envia_alunos(numero_usp="12345678"))


def test_agencia_apenas_digitos():
    assert "Número da agência deve conter apenas números" in erros(envia_alunos(agencia="12a4"))
    assert "Número da agência deve conter apenas números" in erros(envia_alunos(agencia="1234-5"))
    assert erros(envia_alunos(agencia="1234")) == []


def test_valor_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in erros(envia_alunos(valor="0"))
    assert "Valor solicitado deve ser maior que 0" in erros(envia_alunos(valor="-50"))
    assert "Valor solicitado deve ser maior que 0" in erros(envia_alunos(valor="abc"))
    assert erros(envia_alunos(valor="150000")) == []


def test_email_invalido():
    assert "E-mail inválido" in erros(envia_alunos(email="maria@"))
    assert "E-mail inválido" in erros(envia_alunos(email="@ime.usp.br"))
    assert "E-mail inválido" in erros(envia_alunos(email="maria"))
    assert erros(envia_alunos(email="maria@ime.usp.br")) == []


def test_cpf_formato_invalido():
    mensagem = "CPF deve estar no formato 000.000.000-00"
    assert mensagem in erros(envia_alunos(cpf="1234567890"))
    assert mensagem in erros(envia_alunos(cpf="123.456.789.09"))
    assert mensagem not in erros(envia_alunos(cpf="12345678909"))


def test_cpf_digitos_verificadores():
    assert "CPF inválido" in erros(envia_alunos(cpf="11111111111"))
    assert "CPF inválido" in erros(envia_alunos(cpf="123.456.789-00"))
    assert "CPF inválido" not in erros(envia_alunos(cpf="123.456.789-09"))
    assert erros(envia_alunos(cpf="12345678909")) == []


def test_cep_formato():
    mensagem = "CEP deve estar no formato 00000-000"
    assert mensagem in erros(envia_alunos(cep="05508-0900"))
    assert mensagem in erros(envia_alunos(cep="0550-8090"))
    assert erros(envia_alunos(cep="05508090")) == []
    assert erros(envia_alunos(cep="05508-090")) == []


def test_data_nascimento_formato():
    mensagem = "Data de nascimento deve estar no formato dd/mm/aaaa"
    assert mensagem in erros(envia_alunos(data_nascimento="01/02/198"))
    assert mensagem in erros(envia_alunos(data_nascimento="1021980"))
    assert mensagem not in erros(envia_alunos(data_nascimento="01/02/1980"))


def test_data_nascimento_data_inexistente():
    mensagem = "Data de nascimento inválida"
    assert mensagem in erros(envia_alunos(data_nascimento="31/02/1980"))
    assert mensagem in erros(envia_alunos(data_nascimento="01021980"))  # sem barras -> formato? ver abaixo
    assert mensagem in erros(envia_alunos(data_nascimento="32/01/1980"))
    assert mensagem in erros(envia_alunos(data_nascimento="01/13/1980"))
    assert mensagem in erros(envia_alunos(data_nascimento="30/02/2023"))
    assert mensagem not in erros(envia_alunos(data_nascimento="29/02/2024"))
    assert mensagem not in erros(envia_alunos(data_nascimento="01/02/1980"))


def test_todos_os_erros_aparecem_de_uma_vez():
    base = solicitacao_alunos()
    base.update(
        numero_usp="12a4",
        agencia="12a4",
        valor="0",
        email="sem-arroba",
        cpf="11111111111",
        cep="0550809",
        data_nascimento="31/02/1980",
    )
    resposta = client.post("/api/solicitacao", json=base)
    lista = erros(resposta)
    for esperado in (
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF inválido",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
    ):
        assert esperado in lista


def test_preencha_todos_os_campos_aparece_uma_vez():
    base = solicitacao_alunos()
    base.update(nome="", numero_usp="12a", valor="0")
    resposta = client.post("/api/solicitacao", json=base)
    lista = erros(resposta)
    assert lista.count("Preencha todos os campos") == 1


def test_campos_vazios_nao_impedem_outras_validacoes():
    base = solicitacao_alunos()
    base.update(numero_usp="", email="", cep="")
    resposta = client.post("/api/solicitacao", json=base)
    lista = erros(resposta)
    assert "Preencha todos os campos" in lista
    # Não pode haver duplicatas nem de vazio nem de formato
    assert lista.count("N. USP deve conter apenas números") <= 1
    assert lista.count("E-mail inválido") <= 1
    assert lista.count("CEP deve estar no formato 00000-000") <= 1


def test_sem_oficio_quando_ha_erro():
    resposta = envia_alunos(cpf="11111111111")
    corpo = resposta.json()
    assert not corpo.get("oficio")


# --------------------------------------------------------------------------
# API: formatação
# --------------------------------------------------------------------------


def formatos(resposta):
    return resposta.json().get("formatados", {})


def test_formata_valor_como_moeda():
    casos = {
        "1500": "R$ 15,00",
        "150000": "R$ 1.500,00",
        "150000000": "R$ 1.500.000,00",
    }
    for digitado, esperado in casos.items():
        resposta = envia_alunos(valor=digitado)
        assert formatos(resposta).get("valor") == esperado


def test_formata_cpf():
    resposta = envia_alunos(cpf="12345678909")
    assert formatos(resposta).get("cpf") == "123.456.789-09"


def test_formata_cep():
    resposta = envia_alunos(cep="05508090")
    assert formatos(resposta).get("cep") == "05508-090"


def test_formata_data_nascimento():
    resposta = envia_alunos(data_nascimento="01021980")
    assert formatos(resposta).get("data_nascimento") == "01/02/1980"


# --------------------------------------------------------------------------
# Ofício
# --------------------------------------------------------------------------


def linhas(oficio):
    return [l.strip() for l in oficio.split("\n") if l.strip()]


def test_oficio_alunos_completo():
    resposta = envia_alunos(
        complemento="Bloco A",
        link_evento="https://evento.exemplo",
    )
    oficio = resposta.json()["oficio"]
    L = linhas(oficio)
    esperadas = [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: Congresso Nacional",
        "Período: 10 a 12 de outubro de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://evento.exemplo",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e passagens",
        "Endereço da(o) interessada(o)",
        "Rua do Matao, 1010",
        "Complemento: Bloco A",
        "CEP: 05508-090",
        "Cidade Universitária, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    for linha in esperadas:
        assert linha in L, f"linha ausente no ofício: {linha}"
    assert L == esperadas  # e nessa ordem


def test_oficio_docentes():
    resposta = envia_docentes()
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in linhas(oficio)
    assert "Programa: Matemática - Mestrado" not in linhas(oficio)
    assert "Programa: Matemática - " not in oficio


def test_oficio_omit_linha_do_link_vazio():
    resposta = envia_alunos(link_evento="")
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Link do evento: " not in oficio


def test_oficio_omit_linha_do_complemento_vazio():
    resposta = envia_alunos(complemento="")
    oficio = resposta.json()["oficio"]
    assert "Complemento:" not in oficio


def test_oficio_docentes_tambem_omit_linhas_opcionais():
    resposta = envia_docentes(link_evento="", complemento="")
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_alunos_nivel_doutorado():
    resposta = envia_alunos(nivel="Doutorado")
    assert "Programa: Matemática - Doutorado" in linhas(resposta.json()["oficio"])


def test_oficio_alunos_tipo_outro():
    resposta = envia_alunos(tipo_auxilio="Outro")
    assert "Assunto: Solicitação de Auxílio Financeiro - Outro" in resposta.json()["oficio"]
