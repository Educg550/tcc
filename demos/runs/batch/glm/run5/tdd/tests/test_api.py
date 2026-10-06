from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

RAIZ = Path(__file__).resolve().parents[1]

ENDPOINT = "/solicitacao"

PREENCHA_TODOS = "Preencha todos os campos"
N_USP_NUMEROS = "N. USP deve conter apenas números"
AGENCIA_NUMEROS = "Número da agência deve conter apenas números"
VALOR_MAIOR_QUE_ZERO = "Valor solicitado deve ser maior que 0"
EMAIL_INVALIDO = "E-mail inválido"
CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
CPF_INVALIDO = "CPF inválido"
CEP_FORMATO = "CEP deve estar no formato 00000-000"
DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
DATA_INVALIDA = "Data de nascimento inválida"


def dados_alunos(**alteracoes):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@usp.br",
        "nome_evento": "Congresso Brasileiro de Matemática",
        "periodo_evento": "10 a 14 de julho de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://congresso.exemplo.com.br",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Inscrição, passagem e diárias.",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Prédio da Administração",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg_rnm": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(alteracoes)
    return dados


def dados_docentes(**alteracoes):
    dados = {
        campo: valor
        for campo, valor in dados_alunos().items()
        if campo not in ("aba", "nivel", "tipo_auxilio")
    }
    dados["aba"] = "docentes"
    dados.update(alteracoes)
    return dados


def erros_de(dados):
    resposta = client.post(ENDPOINT, json=dados)
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert not corpo.get("oficio"), "com erro, o ofício não é gerado"
    return corpo["erros"]


def oficio_de(dados):
    resposta = client.post(ENDPOINT, json=dados)
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert not corpo.get("erros"), corpo
    return corpo["oficio"]


def linhas(texto):
    return [linha.rstrip() for linha in texto.splitlines()]


def oficio_esperado(dados, docente=False):
    if docente:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    linhas_do_oficio = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de "
        + "auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo_evento']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados.get("link_evento"):
        linhas_do_oficio.append(f"Link do evento: {dados['link_evento']}")
    linhas_do_oficio += [
        f"Apresentação de trabalho: {dados['apresentacao_trabalho']}",
        f"Valor solicitado: {dados['valor_solicitado']}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados.get("complemento"):
        linhas_do_oficio.append(f"Complemento: {dados['complemento']}")
    linhas_do_oficio += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg_rnm']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas_do_oficio)


def test_oficio_da_aba_alunos():
    dados = dados_alunos()
    assert linhas(oficio_de(dados)) == linhas(oficio_esperado(dados))


def test_oficio_omite_linhas_de_campos_opcionais_vazios():
    dados = dados_alunos(link_evento="", complemento="")
    oficio = oficio_de(dados)
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    assert linhas(oficio) == linhas(oficio_esperado(dados))


def test_oficio_da_aba_docentes():
    dados = dados_docentes()
    oficio = oficio_de(dados)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert linhas(oficio) == linhas(oficio_esperado(dados, docente=True))


def test_valor_solicitado_aparece_formatado_no_oficio():
    dados = dados_alunos(valor_solicitado="R$ 1.500.000,00")
    assert "Valor solicitado: R$ 1.500.000,00" in oficio_de(dados)


def test_campo_obrigatorio_vazio_pediu_preencher_todos_uma_unica_vez():
    assert erros_de(dados_alunos(nome_completo="", bairro="")) == [PREENCHA_TODOS]


def test_selects_da_aba_alunos_sao_obrigatorios():
    assert erros_de(dados_alunos(nivel="")) == [PREENCHA_TODOS]
    assert erros_de(dados_alunos(tipo_auxilio="")) == [PREENCHA_TODOS]


def test_n_usp_deve_conter_apenas_numeros():
    assert erros_de(dados_alunos(n_usp="1234a678")) == [N_USP_NUMEROS]


def test_agencia_deve_conter_apenas_numeros():
    assert erros_de(dados_alunos(agencia="12a4")) == [AGENCIA_NUMEROS]


def test_valor_solicitado_deve_ser_maior_que_zero():
    assert erros_de(dados_alunos(valor_solicitado="R$ 0,00")) == [VALOR_MAIOR_QUE_ZERO]


@pytest.mark.parametrize("email", ["maria.usp.br", "maria@"])
def test_email_sem_arroba_ou_sem_dominio(email):
    assert erros_de(dados_alunos(email=email)) == [EMAIL_INVALIDO]


def test_cpf_fora_do_formato():
    assert erros_de(dados_alunos(cpf="12345678909")) == [CPF_FORMATO]


def test_cpf_com_digitos_verificadores_errados():
    assert erros_de(dados_alunos(cpf="123.456.789-00")) == [CPF_INVALIDO]


def test_cep_fora_do_formato():
    assert erros_de(dados_alunos(cep="05508090")) == [CEP_FORMATO]


def test_data_de_nascimento_fora_do_formato():
    assert erros_de(dados_alunos(data_nascimento="01021980")) == [DATA_FORMATO]


@pytest.mark.parametrize("data", ["31/02/1980", "01/13/1980"])
def test_data_de_nascimento_no_formato_mas_inexistente(data):
    assert erros_de(dados_alunos(data_nascimento=data)) == [DATA_INVALIDA]


def test_todos_os_erros_aplicaveis_aparecem_juntos():
    erros = erros_de(dados_alunos(email="maria@", cep="05508090", cpf="123.456.789-00"))
    assert sorted(erros) == sorted([EMAIL_INVALIDO, CEP_FORMATO, CPF_INVALIDO])


def test_validacao_e_a_mesma_na_aba_docentes():
    assert erros_de(dados_docentes(email="maria@")) == [EMAIL_INVALIDO]
    assert erros_de(dados_docentes(nome_completo="")) == [PREENCHA_TODOS]


def test_solicitacao_nao_grava_nenhum_arquivo():
    antes = sorted(caminho.name for caminho in RAIZ.iterdir() if caminho.is_file())
    client.post(ENDPOINT, json=dados_alunos())
    client.post(ENDPOINT, json=dados_alunos(email="maria@"))
    depois = sorted(caminho.name for caminho in RAIZ.iterdir() if caminho.is_file())
    assert antes == depois


def test_titulo_da_confirmacao_e_solicitacao_registrada():
    html = client.get("/").text
    js = client.get("/app.js").text
    resposta = client.post(ENDPOINT, json=dados_alunos())
    assert "Solicitação registrada" in html + js + resposta.text
