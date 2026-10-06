"""Testes do backend: validação da solicitação e geração do ofício.

Contrato exercitado aqui:
- Envio: POST /solicitacao com corpo JSON. A chave "aba" vale "alunos" ou
  "docentes"; "nivel" e "tipo_auxilio" só existem no envio da aba ALUNOS.
- Resposta: HTTP 200 sempre. Solicitação válida -> {"oficio": "<ofício>"};
  solicitação inválida -> {"erros": ["<mensagem>", ...]}, com todas as
  mensagens que se aplicam e nenhum ofício.
"""

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

PREENCHA = "Preencha todos os campos"
N_USP_NUMEROS = "N. USP deve conter apenas números"
AGENCIA_NUMEROS = "Número da agência deve conter apenas números"
VALOR_MAIOR_QUE_ZERO = "Valor solicitado deve ser maior que 0"
EMAIL_INVALIDO = "E-mail inválido"
CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
CPF_INVALIDO = "CPF inválido"
CEP_FORMATO = "CEP deve estar no formato 00000-000"
DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
DATA_INVALIDA = "Data de nascimento inválida"


def _payload_alunos(**alteracoes):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática Aplicada",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria.silva@usp.br",
        "nome_evento": "Congresso Brasileiro de Matemática",
        "periodo_evento": "10 a 14 de agosto de 2026",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://www.exemplo.com.br/congresso",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Inscrição no evento, diárias e passagens.",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Prédio da Administração",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "9876-5",
    }
    dados.update(alteracoes)
    return dados


def _payload_docentes(**alteracoes):
    dados = _payload_alunos()
    dados["aba"] = "docentes"
    del dados["nivel"]
    del dados["tipo_auxilio"]
    dados.update(alteracoes)
    return dados


def _enviar(dados):
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _erros(dados):
    corpo = _enviar(dados)
    assert not corpo.get("oficio"), "com erro, o ofício não é gerado"
    return corpo["erros"]


def _normalizar(oficio):
    linhas = oficio.replace("\r\n", "\n").split("\n")
    return "\n".join(linha.rstrip() for linha in linhas).strip("\n")


def _oficio_esperado(dados):
    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
    ]
    if dados["aba"] == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    else:
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        )
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    linhas += [
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo_evento']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link_evento"]:
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {dados['valor_solicitado']}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def test_oficio_da_aba_alunos():
    dados = _payload_alunos()
    corpo = _enviar(dados)
    assert _normalizar(corpo["oficio"]) == _oficio_esperado(dados)


def test_oficio_da_aba_docentes():
    dados = _payload_docentes(
        nome_completo="João Carlos Nogueira",
        n_usp="98765432",
        programa="Ciência da Computação",
        email="joao.nogueira@usp.br",
    )
    corpo = _enviar(dados)
    assert _normalizar(corpo["oficio"]) == _oficio_esperado(dados)


def test_campos_opcionais_vazios_tiram_as_linhas_do_oficio():
    dados = _payload_alunos(link_evento="", complemento="")
    corpo = _enviar(dados)
    oficio = _normalizar(corpo["oficio"])
    assert oficio == _oficio_esperado(dados)
    assert "Link do evento" not in oficio
    assert "Complemento:" not in oficio


def test_campo_obrigatorio_vazio():
    assert _erros(_payload_alunos(nome_completo="")) == [PREENCHA]


def test_varios_campos_vazios_uma_unica_mensagem():
    erros = _erros(_payload_alunos(nome_completo="", programa="", banco=""))
    assert Counter(erros) == Counter([PREENCHA])


def test_nivel_obrigatorio_na_aba_alunos():
    assert _erros(_payload_alunos(nivel="")) == [PREENCHA]


def test_campo_obrigatorio_vazio_na_aba_docentes():
    assert _erros(_payload_docentes(cidade="")) == [PREENCHA]


def test_valor_vazio_e_campo_obrigatorio_vazio():
    assert _erros(_payload_alunos(valor_solicitado="")) == [PREENCHA]


def test_n_usp_apenas_numeros():
    assert _erros(_payload_alunos(n_usp="12345A6")) == [N_USP_NUMEROS]


def test_agencia_apenas_numeros():
    assert _erros(_payload_alunos(agencia="1234-X")) == [AGENCIA_NUMEROS]


@pytest.mark.parametrize("valor", ["R$ 0,00", "0", "-10"])
def test_valor_deve_ser_maior_que_zero(valor):
    assert _erros(_payload_alunos(valor_solicitado=valor)) == [VALOR_MAIOR_QUE_ZERO]


@pytest.mark.parametrize("email", ["maria.silva.usp.br", "maria@"])
def test_email_invalido(email):
    assert _erros(_payload_alunos(email=email)) == [EMAIL_INVALIDO]


def test_cpf_fora_do_formato():
    assert _erros(_payload_alunos(cpf="12345678909")) == [CPF_FORMATO]


def test_cpf_com_digitos_verificadores_errados():
    assert _erros(_payload_alunos(cpf="123.456.789-00")) == [CPF_INVALIDO]


def test_cep_fora_do_formato():
    assert _erros(_payload_alunos(cep="05508090")) == [CEP_FORMATO]


def test_data_de_nascimento_fora_do_formato():
    assert _erros(_payload_alunos(data_nascimento="01021980")) == [DATA_FORMATO]


@pytest.mark.parametrize("data", ["31/02/1980", "01/13/1980", "29/02/2023"])
def test_data_de_nascimento_inexistente(data):
    assert _erros(_payload_alunos(data_nascimento=data)) == [DATA_INVALIDA]


def test_todos_os_erros_aplicaveis_de_uma_vez():
    erros = _erros(
        _payload_docentes(
            nome_completo="",
            n_usp="12345A6",
            email="joao@",
            cpf="12345678909",
            cep="5508-090",
        )
    )
    assert Counter(erros) == Counter(
        [PREENCHA, N_USP_NUMEROS, EMAIL_INVALIDO, CPF_FORMATO, CEP_FORMATO]
    )
