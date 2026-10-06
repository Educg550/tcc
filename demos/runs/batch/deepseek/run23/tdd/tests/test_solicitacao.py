from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
URL = "/solicitar"


def solicitacao_alunos(**alteracoes):
    dados = {
        "aba": "ALUNOS",
        "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
        "N. USP": "12345678",
        "PROGRAMA": "Ciência da Computação",
        "NÍVEL": "Mestrado",
        "TIPO DE AUXÍLIO": "Participação em evento",
        "E-MAIL": "maria@ime.usp.br",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso SBC 2024",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "21 a 25 de julho de 2024",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "Brasília",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "DF",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://sbc.example.org/2024",
        "VALOR SOLICITADO (R$)": "R$ 1.500,00",
        "DETALHAMENTO DO PEDIDO": "Passagem aérea e hospedagem",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "DATA DE NASCIMENTO": "01/02/1980",
        "LOGRADOURO": "Rua do Matão",
        "NÚMERO": "1010",
        "COMPLEMENTO": "Bloco A",
        "BAIRRO": "Butantã",
        "CEP": "05508-090",
        "CIDADE": "São Paulo",
        "ESTADO": "SP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "NOME DO BANCO": "Banco do Brasil",
        "NÚMERO DA AGÊNCIA": "1234",
        "NÚMERO DA CONTA": "56789-0",
    }
    dados.update(alteracoes)
    return dados


def solicitacao_docentes(**alteracoes):
    dados = solicitacao_alunos()
    dados.pop("NÍVEL")
    dados.pop("TIPO DE AUXÍLIO")
    dados["aba"] = "DOCENTES"
    dados.update(alteracoes)
    return dados


def enviar(dados):
    return client.post(URL, json=dados)


def erros(dados):
    return enviar(dados).json()["erros"]


def test_envio_valido_de_aluno_gera_oficio_com_os_dados():
    resposta = enviar(solicitacao_alunos())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação aprovou na data de hoje" in oficio
    assert "Evento: Congresso SBC 2024" in oficio
    assert "Período: 21 a 25 de julho de 2024" in oficio
    assert "Local: Brasília - DF - Brasil" in oficio
    assert "Link do evento: https://sbc.example.org/2024" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem aérea e hospedagem" in oficio
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


def test_link_e_complemento_vazios_saem_do_oficio():
    oficio = enviar(
        solicitacao_alunos(
            **{
                "LINK DO EVENTO, EXAME OU DEFESA": "",
                "COMPLEMENTO": "",
            }
        )
    ).json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_de_docente_usa_verba_do_programa_e_nao_tem_nivel():
    resposta = enviar(solicitacao_docentes())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio
    assert "Mestrado" not in oficio


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    mensagens = erros(
        solicitacao_alunos(
            **{
                "NOME COMPLETO - SEM ABREVIAR": "",
                "E-MAIL": "",
                "LOGRADOURO": "",
            }
        )
    )
    assert mensagens.count("Preencha todos os campos") == 1


def test_n_usp_com_caractere_nao_numerico():
    assert "N. USP deve conter apenas números" in erros(
        solicitacao_alunos(**{"N. USP": "12a34"})
    )


def test_agencia_com_caractere_nao_numerico():
    assert "Número da agência deve conter apenas números" in erros(
        solicitacao_alunos(**{"NÚMERO DA AGÊNCIA": "12-34"})
    )


def test_valor_solicitado_igual_a_zero():
    assert "Valor solicitado deve ser maior que 0" in erros(
        solicitacao_alunos(**{"VALOR SOLICITADO (R$)": "R$ 0,00"})
    )


def test_email_sem_arroba():
    assert "E-mail inválido" in erros(
        solicitacao_alunos(**{"E-MAIL": "maria.ime.usp.br"})
    )


def test_cpf_fora_do_formato():
    assert "CPF deve estar no formato 000.000.000-00" in erros(
        solicitacao_alunos(**{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "1234567890"})
    )


def test_cep_fora_do_formato():
    assert "CEP deve estar no formato 00000-000" in erros(
        solicitacao_alunos(**{"CEP": "0550809"})
    )


def test_data_de_nascimento_fora_do_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros(
        solicitacao_alunos(**{"DATA DE NASCIMENTO": "0102198"})
    )


def test_cpf_com_digitos_verificadores_invalidos():
    assert "CPF inválido" in erros(
        solicitacao_alunos(**{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})
    )


def test_data_de_nascimento_inexistente():
    assert "Data de nascimento inválida" in erros(
        solicitacao_alunos(**{"DATA DE NASCIMENTO": "31/02/1980"})
    )


def test_quando_ha_erro_o_oficio_nao_e_gerado():
    corpo = enviar(solicitacao_alunos(**{"N. USP": "abc"})).json()
    assert corpo["erros"]
    assert not corpo.get("oficio")


def test_a_mesma_validacao_vale_na_aba_docentes():
    assert "N. USP deve conter apenas números" in erros(
        solicitacao_docentes(**{"N. USP": "12a"})
    )
