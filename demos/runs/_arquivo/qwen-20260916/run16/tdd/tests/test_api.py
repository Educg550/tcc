import pytest


def cliente():
    pytest.importorskip("app")
    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)


def corpo_alunos(**mudancas):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "numero_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro de Matemática",
        "periodo": "10/07/2025 a 15/07/2025",
        "cidade_evento": "Salvador",
        "estado_evento": "BA",
        "pais_evento": "Brasil",
        "link_evento": "https://cbm.org",
        "valor": "150000",
        "detalhamento": "Participação com trabalho aprovado.",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Apto 12",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(mudancas)
    return dados


def post(dados):
    return cliente().post("/solicitacao", json=dados)


def erros(resposta):
    assert "erros" in resposta.json(), resposta.text
    assert isinstance(resposta.json()["erros"], list), resposta.text
    return resposta.json()["erros"]


def teste_post_solicitacao():
    assert post(corpo_alunos()).status_code == 200


def teste_resposta_de_sucesso_tem_oficio():
    dados = post(corpo_alunos()).json()
    assert "oficio" in dados, dados


def teste_campos_opcionais():
    resposta = post(corpo_alunos(link_evento="", complemento=""))
    assert resposta.status_code == 200, resposta.text
    assert "oficio" in resposta.json(), resposta.text


def teste_campo_obrigatorio_vazio():
    assert "Preencha todos os campos" in erros(post(corpo_alunos(detalhamento="")))


def teste_erro_aparece_uma_unica_vez():
    assert erros(post(corpo_alunos(detalhamento="", programa="", bairro=""))).count(
        "Preencha todos os campos"
    ) == 1


def teste_numusp_so_digitos():
    assert "N. USP deve conter apenas números" in erros(post(corpo_alunos(numero_usp="12a3")))


def teste_agencia_so_digitos():
    assert (
        "Número da agência deve conter apenas números"
        in erros(post(corpo_alunos(agencia="12a4")))
    )


def teste_valor_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in erros(post(corpo_alunos(valor="0")))


def teste_email_invalido():
    assert "E-mail inválido" in erros(post(corpo_alunos(email="maria@")))


def teste_formato_cpf():
    assert (
        "CPF deve estar no formato 000.000.000-00"
        in erros(post(corpo_alunos(cpf="12345678909")))
    )


def teste_digito_verificador_cpf():
    assert "CPF inválido" in erros(post(corpo_alunos(cpf="123.456.789-00")))


def teste_formato_cep():
    assert "CEP deve estar no formato 00000-000" in erros(post(corpo_alunos(cep="05508090")))


def teste_formato_data():
    assert (
        "Data de nascimento deve estar no formato dd/mm/aaaa"
        in erros(post(corpo_alunos(data_nascimento="1-2-1980")))
    )


def teste_data_invalida():
    assert "Data de nascimento inválida" in erros(post(corpo_alunos(data_nascimento="31/02/1980")))


def teste_data_nao_existente_mes_fora():
    assert "Data de nascimento inválida" in erros(post(corpo_alunos(data_nascimento="15/13/1980")))


def teste_todas_as_mensagens_de_error_de_uma_vez():
    lista = erros(
        post(
            corpo_alunos(
                numero_usp="12a",
                agencia="ab",
                valor="0",
                email="sem-arroba",
                cpf="11111111111",
                cep="11111",
                data_nascimento="99/99/9999",
            )
        )
    )
    for mensagem in [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]:
        assert mensagem in lista, lista
    assert "Preencha todos os campos" not in lista


def teste_oficio_alunos():
    texto = post(corpo_alunos()).json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Matemática - Doutorado" in texto
    assert "A CCP-Matemática aprovou na data de hoje" in texto
    assert "Dados do evento" in texto
    assert "Evento: Congresso Brasileiro de Matemática" in texto
    assert "Período: 10/07/2025 a 15/07/2025" in texto
    assert "Local: Salvador - BA - Brasil" in texto
    assert "Link do evento: https://cbm.org" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Participação com trabalho aprovado." in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Apto 12" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def teste_oficio_docentes():
    dados = corpo_alunos(aba="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    texto = post(dados).json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática\n" in texto or texto.endswith("Programa: Matemática")
    assert "Doutorado" not in texto
    assert "Participação em evento" not in texto


def teste_linhas_vazias_sao_omitidas():
    texto = post(corpo_alunos(link_evento="", complemento="")).json()["oficio"]
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto
