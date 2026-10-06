import re

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app as app_module


def _client() -> TestClient:
    instance = getattr(app_module, "app", None)
    if isinstance(instance, FastAPI):
        return TestClient(instance)
    return TestClient(app_module.create_app())


@staticmethod
def _clean() -> dict:
    return {
        "aba": "ALUNOS",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria.silva@usp.br",
        "nome_evento": "SBIA 2026",
        "periodo_evento": "de 10 a 14 de março",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://sbia.org",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Contribuição para custear inscrição.",
        "apresentar_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Casa 2",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "390.533.447-05",
        "rg_rnm": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "56789-0",
    }


@staticmethod
def _docente() -> dict:
    return {
        "aba": "DOCENTES",
        "nome_completo": "João Souza",
        "n_usp": "87654321",
        "programa": "Matemática",
        "email": "joao.souza@usp.br",
        "nome_evento": "Workshop",
        "periodo_evento": "amanhã",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://workshop.org",
        "valor_solicitado": "R$ 800,00",
        "detalhamento": "Custeio de deslocamento.",
        "apresentar_trabalho": "Não irá apresentar trabalho",
        "data_nascimento": "15/06/1975",
        "logradouro": "Avenida Paulista",
        "numero": "1000",
        "complemento": "",
        "bairro": "Bela Vista",
        "cep": "01310-100",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "529.982.247-25",
        "rg_rnm": "98.765.432-1",
        "nome_banco": "Caixa",
        "numero_agencia": "567",
        "numero_conta": "89012-3",
    }


@staticmethod
def _post(client: TestClient, payload: dict):
    return client.post("/solicitar", json=payload)


def test_abas_existentes():
    client = _client()
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "ALUNOS" in html and "DOCENTES" in html


def test_ordem_abas():
    client = _client()
    html = client.get("/").text
    assert html.find("ALUNOS") < html.find("DOCENTES")


def test_aba_alunos_ativa_por_padrao():
    client = _client()
    html = client.get("/").text
    assert re.search(r'\b(aba|tab)\b[^"]*"(active|ativa)"', html, re.I) or 'class="(active|ativa)"' in html


def test_botao_enviar_solicitacao():
    client = _client()
    html = client.get("/").text
    assert "Enviar solicitação" in html


BLOCO_SOLICITANTE_EVENTO = [
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
]

BLOCO_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]

BLOCO_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]



def test_rotulos_solicitante_evento():
    client = _client()
    html = client.get("/").text
    for rotulo in BLOCO_SOLICITANTE_EVENTO:
        assert rotulo in html, rotulo


def test_rotulos_endereco():
    client = _client()
    html = client.get("/").text
    for rotulo in BLOCO_ENDERECO:
        assert rotulo in html, rotulo


def test_rotulos_pagamento():
    client = _client()
    html = client.get("/").text
    for rotulo in BLOCO_PAGAMENTO:
        assert rotulo in html, rotulo


def test_rotulos_titulos_blocos():
    client = _client()
    html = client.get("/").text
    for bloco in ["SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"]:
        assert bloco in html, bloco


def test_campo_exclusivo_alunos_nivel():
    client = _client()
    html = client.get("/").text
    assert "NÍVEL" in html


def test_campo_exclusivo_alunos_tipo_auxilio():
    client = _client()
    html = client.get("/").text
    assert "TIPO DE AUXÍLIO" in html


def test_opcoes_nivel():
    client = _client()
    html = client.get("/").text
    assert "Mestrado" in html and "Doutorado" in html


def test_opcoes_tipo_auxilio():
    client = _client()
    html = client.get("/").text
    for opcao in ["Participação em evento", "Banca de exame ou defesa", "Outro"]:
        assert opcao in html, opcao


def test_opcoes_apresentar_trabalho():
    client = _client()
    html = client.get("/").text
    for opcao in ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in html, opcao


def test_placeholder_nao_repete_rotulo():
    client = _client()
    html = client.get("/").text
    assert 'placeholder="' in html
    match = re.search(r'placeholder="([^"]+)"', html)
    assert match
    assert "SEM ABREVIAR" not in match.group(1)


def test_cpf_valido_ok():
    client = _client()
    payload = _clean()
    r = _post(client, payload)
    assert r.status_code == 200, r.text


def test_cpf_formato_invalido():
    client = _client()
    payload = _clean()
    payload["cpf"] = "1234567890"
    assert "CPF deve estar no formato 000.000.000-00" in _post(client, payload).text


def test_cpf_digitos_invalidos():
    client = _client()
    payload = _clean()
    payload["cpf"] = "000.000.000-00"
    assert "CPF inválido" in _post(client, payload).text


def test_cep_formato_invalido():
    client = _client()
    payload = _clean()
    payload["cep"] = "1234"
    assert "CEP deve estar no formato 00000-000" in _post(client, payload).text


def test_data_nascimento_formato_invalido():
    client = _client()
    payload = _clean()
    payload["data_nascimento"] = "1980-01-02"
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _post(client, payload).text


def test_data_nascimento_invalida():
    client = _client()
    payload = _clean()
    payload["data_nascimento"] = "29/02/2023"
    assert "Data de nascimento inválida" in _post(client, payload).text


def test_email_invalido():
    client = _client()
    payload = _clean()
    payload["email"] = "sem-at"
    assert "E-mail inválido" in _post(client, payload).text


def test_email_sem_dominio():
    client = _client()
    payload = _clean()
    payload["email"] = "a@"
    assert "E-mail inválido" in _post(client, payload).text


def test_nusp_invalido():
    client = _client()
    payload = _clean()
    payload["n_usp"] = "abc"
    assert "N. USP deve conter apenas números" in _post(client, payload).text


def test_agencia_invalida():
    client = _client()
    payload = _clean()
    payload["numero_agencia"] = "12a"
    assert "Número da agência deve conter apenas números" in _post(client, payload).text


def test_valor_invalido():
    client = _client()
    payload = _clean()
    payload["valor_solicitado"] = "R$ 0,00"
    assert "Valor solicitado deve ser maior que 0" in _post(client, payload).text


def test_campo_obrigatorio_vazio():
    client = _client()
    payload = _clean()
    payload["programa"] = ""
    assert "Preencha todos os campos" in _post(client, payload).text


def test_opcionais_podem_ficar_vazios():
    client = _client()
    payload = _clean()
    payload["link_evento"] = ""
    payload["complemento"] = ""
    assert _post(client, payload).status_code == 200


def test_confirmacao_titulo():
    client = _client()
    assert "Solicitação registrada" in _post(client, _clean()).text



OFICIO_ALUNOS = """Interessada(o): Maria da Silva - 12345678
E-mail: maria.silva@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Doutorado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBIA 2026
Período: de 10 a 14 de março
Local: São Paulo - SP - Brasil
Link do evento: https://sbia.org
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Contribuição para custear inscrição.

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Casa 2
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 390.533.447-05
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 56789-0

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_DOCENTES = """Interessada(o): João Souza - 87654321
E-mail: joao.souza@usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Matemática

A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Workshop
Período: amanhã
Local: São Paulo - SP - Brasil
Apresentação de trabalho: Não irá apresentar trabalho
Valor solicitado: R$ 800,00
Detalhamento: Custeio de deslocamento.

Endereço da(o) interessada(o)
Avenida Paulista, 1000
CEP: 01310-100
Bela Vista, São Paulo - SP

Dados para pagamento
Data de nascimento: 15/06/1975
CPF: 529.982.247-25
RG / RNM: 98.765.432-1
Banco: Caixa
Agência: 567
Conta: 89012-3

Encaminhe-se ao Serviço Financeiro para providências."""



def test_oficio_alunos_completo():
    client = _client()
    resposta = _post(client, _clean())
    assert resposta.status_code == 200, resposta.text
    texto = "\n".join(re.sub(r"<[^>]+>", "", linha) for linha in resposta.text.splitlines())
    assert OFICIO_ALUNOS in texto


def test_oficio_docentes_completo():
    client = _client()
    resposta = _post(client, _docente())
    assert resposta.status_code == 200, resposta.text
    texto = "\n".join(re.sub(r"<[^>]+>", "", linha) for linha in resposta.text.splitlines())
    assert OFICIO_DOCENTES in texto


def test_link_vazio_sai_do_oficio():
    client = _client()
    payload = _clean()
    payload["link_evento"] = ""
    resposta = _post(client, payload)
    texto = "\n".join(re.sub(r"<[^>]+>", "", linha) for linha in resposta.text.splitlines())
    assert "Link do evento:" not in texto


def test_complemento_vazio_sai_do_oficio():
    client = _client()
    payload = _clean()
    payload["complemento"] = ""
    resposta = _post(client, payload)
    texto = "\n".join(re.sub(r"<[^>]+>", "", linha) for linha in resposta.text.splitlines())
    assert "Complemento:" not in texto


def test_servir_index():
    client = _client()
    r = client.get("/index.html")
    assert r.status_code == 200
    assert "<form" in r.text or "<input" in r.text


def test_servir_style():
    client = _client()
    r = client.get("/style.css")
    assert r.status_code == 200
    assert "#1094ab" in r.text
    assert "#64c4d2" in r.text
    assert "#fcb421" in r.text


def test_servir_appjs():
    client = _client()
    r = client.get("/app.js")
    assert r.status_code == 200


