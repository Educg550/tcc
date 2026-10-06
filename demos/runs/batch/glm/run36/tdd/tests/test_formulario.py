import re
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def valida(dados):
    resposta = client.post(
        "/solicitacao",
        json={"tipo": "alunos", "campos": dados},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("erros") == []
    return corpo


BASE = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "12345678",
    "PROGRAMA": "Matemática",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Nacional",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10 a 12 de maio de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "",
    "VALOR SOLICITADO (R$)": "150000",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01021980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "",
    "BAIRRO": "Butantã",
    "CEP": "05508090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "56789-0",
}


def test_pagina_inicial_contem_abas_e_blocos():
    resposta = client.get("/")
    assert resposta.status_code == 200
    texto = resposta.text
    for rotulo in (
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "Enviar solicitação",
        "Solicitação de Auxílio Financeiro",
        "Universidade de São Paulo",
    ):
        assert rotulo in texto
    assert "usp-logo.png" in texto
    assert texto.count("Enviar solicitação") >= 2


def test_campos_alunos_contem_nivel_e_tipo_de_auxilio():
    resposta = client.get("/")
    assert "NÍVEL" in resposta.text
    assert "TIPO DE AUXÍLIO" in resposta.text


def test_formato_do_cpf():
    dados = dict(BASE)
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    assert "123.456.789-09" in corpo["oficio"]


def test_erro_cpf_fora_do_formato():
    dados = dict(BASE)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "1234567890"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]
    assert corpo["oficio"] == ""


def test_erro_cpf_com_digitos_verificadores_incorretos():
    dados = dict(BASE)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "11111111111"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "CPF inválido" in corpo["erros"]
    assert "CPF deve estar no formato 000.000.000-00" not in corpo["erros"]


def test_erro_cep_fora_do_formato():
    dados = dict(BASE)
    dados["CEP"] = "05508-90"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_erro_data_fora_do_formato():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "1980-02-01"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


def test_erro_data_inexistente():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "31021980"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Data de nascimento inválida" in corpo["erros"]
    assert (
        "Data de nascimento deve estar no formato dd/mm/aaaa" not in corpo["erros"]
    )


def test_erro_numero_usp_com_letras():
    dados = dict(BASE)
    dados["N. USP"] = "1234567a"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_erro_agencia_com_letras():
    dados = dict(BASE)
    dados["NÚMERO DA AGÊNCIA"] = "123a"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_erro_email_invalido():
    dados = dict(BASE)
    dados["E-MAIL"] = "maria@ime"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "E-mail inválido" in corpo["erros"]


def test_erro_email_sem_arroba():
    dados = dict(BASE)
    dados["E-MAIL"] = "mariaime.usp.br"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "E-mail inválido" in corpo["erros"]


def test_erro_valor_zero():
    dados = dict(BASE)
    dados["VALOR SOLICITADO (R$)"] = "0"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_erro_campo_obrigatorio_vazio():
    dados = dict(BASE)
    dados["NOME COMPLETO - SEM ABREVIAR"] = ""
    dados["E-MAIL"] = ""
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["erros"].count("Preencha todos os campos") == 1
    assert corpo["oficio"] == ""


def test_todos_os_erros_de_uma_vez():
    dados = dict(BASE)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "12"
    dados["CEP"] = "123"
    dados["DATA DE NASCIMENTO"] = "32/13/1980"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    for erro in (
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert erro in corpo["erros"]


def test_oficio_alunos_completo():
    dados = dict(BASE)
    corpo = valida(dados)
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    )
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Evento: Congresso Nacional" in oficio
    assert "Período: 10 a 12 de maio de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem aérea" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_campo_opcional_vazio_nao_aparece():
    dados = dict(BASE)
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    dados["COMPLEMENTO"] = ""
    corpo = valida(dados)
    assert "Link do evento:" not in corpo["oficio"]
    assert "Complemento:" not in corpo["oficio"]


def test_oficio_alunos_campo_opcional_preenchido_aparece():
    dados = dict(BASE)
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = "https://exemplo.com"
    dados["COMPLEMENTO"] = "Sala 2"
    corpo = valida(dados)
    assert "Link do evento: https://exemplo.com" in corpo["oficio"]
    assert "Complemento: Sala 2" in corpo["oficio"]


def test_oficio_docentes():
    dados = dict(BASE)
    del dados["NÍVEL"]
    del dados["TIPO DE AUXÍLIO"]
    resposta = client.post(
        "/solicitacao", json={"tipo": "docentes", "campos": dados}
    )
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["erros"] == []
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "NÍVEL" not in oficio


def test_data_31_de_mes_com_31_dias():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "31012000"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    assert resposta.json()["erros"] == []


def test_erro_data_mes_fora_de_1_a_12():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "01131980"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_erro_data_29_de_fevereiro_em_ano_nao_bissexto():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "29021981"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    corpo = resposta.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_erro_data_29_de_fevereiro_em_ano_bissexto():
    dados = dict(BASE)
    dados["DATA DE NASCIMENTO"] = "29021980"
    resposta = client.post(
        "/solicitacao", json={"tipo": "alunos", "campos": dados}
    )
    assert resposta.json()["erros"] == []


def test_valor_milhoes_formatado():
    dados = dict(BASE)
    dados["VALOR SOLICITADO (R$)"] = "150000000"
    corpo = valida(dados)
    assert "Valor solicitado: R$ 1.500.000,00" in corpo["oficio"]


def test_valor_menor_que_cem_centavos():
    dados = dict(BASE)
    dados["VALOR SOLICITADO (R$)"] = "15"
    corpo = valida(dados)
    assert "Valor solicitado: R$ 0,15" in corpo["oficio"]
