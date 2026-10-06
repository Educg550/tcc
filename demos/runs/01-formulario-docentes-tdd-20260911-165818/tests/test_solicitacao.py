import copy

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

BASE_ALUNOS = {
    "aba": "alunos",
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de IA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/03/2024 a 15/03/2024",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.com",
    "VALOR SOLICITADO (R$)": 1500,
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e hospedagem",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua das Flores",
    "NÚMERO": "100",
    "COMPLEMENTO": "Apto 12",
    "BAIRRO": "Centro",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-01",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "56789-0",
}


def campos_alunos():
    return copy.deepcopy(BASE_ALUNOS)


def campos_docentes():
    dados = copy.deepcopy(BASE_ALUNOS)
    dados["aba"] = "docentes"
    del dados["NÍVEL"]
    del dados["TIPO DE AUXÍLIO"]
    return dados


def enviar(dados):
    return client.post("/api/solicitacao", json=dados)


def test_solicitacao_alunos_valida_gera_oficio():
    resp = enviar(campos_alunos())
    assert resp.status_code == 200
    corpo = resp.json()
    assert "erros" not in corpo
    esperado = (
        "Interessada(o): Maria da Silva - 1234567\n"
        "E-mail: maria@usp.br\n"
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento\n"
        "Programa: Ciência da Computação - Mestrado\n"
        "\n"
        "A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a\n"
        "interessada(o) acima, conforme segue:\n"
        "\n"
        "Dados do evento\n"
        "Evento: Congresso Brasileiro de IA\n"
        "Período: 10/03/2024 a 15/03/2024\n"
        "Local: São Paulo - SP - Brasil\n"
        "Link do evento: https://evento.com\n"
        "Apresentação de trabalho: Pôster\n"
        "Valor solicitado: R$ 1.500,00\n"
        "Detalhamento: Passagem aérea e hospedagem\n"
        "\n"
        "Endereço da(o) interessada(o)\n"
        "Rua das Flores, 100\n"
        "Complemento: Apto 12\n"
        "CEP: 05508-090\n"
        "Centro, São Paulo - SP\n"
        "\n"
        "Dados para pagamento\n"
        "Data de nascimento: 01/02/1980\n"
        "CPF: 123.456.789-01\n"
        "RG / RNM: 12.345.678-9\n"
        "Banco: Banco do Brasil\n"
        "Agência: 1234\n"
        "Conta: 56789-0\n"
        "\n"
        "Encaminhe-se ao Serviço Financeiro para providências."
    )
    assert corpo["oficio"] == esperado


def test_solicitacao_docentes_valida_gera_oficio_sem_nivel_e_tipo_auxilio():
    resp = enviar(campos_docentes())
    assert resp.status_code == 200
    corpo = resp.json()
    assert "erros" not in corpo
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio
    assert "Programa: Ciência da Computação - " not in oficio


def test_link_e_complemento_vazios_removem_linha_do_oficio():
    dados = campos_alunos()
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    dados["COMPLEMENTO"] = ""
    resp = enviar(dados)
    assert resp.status_code == 200
    corpo = resp.json()
    assert "erros" not in corpo
    oficio = corpo["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_valor_solicitado_formatado_em_reais_no_oficio():
    dados = campos_alunos()
    dados["VALOR SOLICITADO (R$)"] = 1500000
    resp = enviar(dados)
    assert resp.status_code == 200
    oficio = resp.json()["oficio"]
    assert "Valor solicitado: R$ 1.500.000,00" in oficio


def test_campo_obrigatorio_vazio_gera_mensagem_unica():
    dados = campos_alunos()
    dados["NOME COMPLETO - SEM ABREVIAR"] = ""
    dados["PROGRAMA"] = ""
    resp = enviar(dados)
    assert resp.status_code == 200
    erros = resp.json()["erros"]
    assert erros.count("Preencha todos os campos") == 1


def test_docentes_nao_exige_nivel_nem_tipo_auxilio():
    resp = enviar(campos_docentes())
    assert resp.status_code == 200
    assert "erros" not in resp.json()


def test_alunos_exige_nivel_e_tipo_auxilio():
    dados = campos_docentes()
    dados["aba"] = "alunos"
    resp = enviar(dados)
    erros = resp.json()["erros"]
    assert "Preencha todos os campos" in erros


def test_n_usp_deve_conter_apenas_numeros():
    dados = campos_alunos()
    dados["N. USP"] = "12A456"
    resp = enviar(dados)
    assert "N. USP deve conter apenas números" in resp.json()["erros"]


def test_numero_da_agencia_deve_conter_apenas_numeros():
    dados = campos_alunos()
    dados["NÚMERO DA AGÊNCIA"] = "12B4"
    resp = enviar(dados)
    assert "Número da agência deve conter apenas números" in resp.json()["erros"]


def test_valor_solicitado_deve_ser_maior_que_zero():
    dados = campos_alunos()
    dados["VALOR SOLICITADO (R$)"] = 0
    resp = enviar(dados)
    assert "Valor solicitado deve ser maior que 0" in resp.json()["erros"]


def test_email_sem_arroba_invalido():
    dados = campos_alunos()
    dados["E-MAIL"] = "mariasilva.com"
    resp = enviar(dados)
    assert "E-mail inválido" in resp.json()["erros"]


def test_email_sem_dominio_invalido():
    dados = campos_alunos()
    dados["E-MAIL"] = "maria@"
    resp = enviar(dados)
    assert "E-mail inválido" in resp.json()["erros"]


def test_cpf_fora_do_formato():
    dados = campos_alunos()
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "12345678901"
    resp = enviar(dados)
    assert "CPF deve estar no formato 000.000.000-00" in resp.json()["erros"]


def test_cep_fora_do_formato():
    dados = campos_alunos()
    dados["CEP"] = "05508090"
    resp = enviar(dados)
    assert "CEP deve estar no formato 00000-000" in resp.json()["erros"]


def test_data_nascimento_fora_do_formato():
    dados = campos_alunos()
    dados["DATA DE NASCIMENTO"] = "01021980"
    resp = enviar(dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.json()["erros"]


def test_multiplos_erros_aparecem_juntos():
    dados = campos_alunos()
    dados["N. USP"] = "12A"
    dados["NÚMERO DA AGÊNCIA"] = "12B"
    resp = enviar(dados)
    erros = resp.json()["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "Número da agência deve conter apenas números" in erros


def test_erro_nao_gera_oficio():
    dados = campos_alunos()
    dados["N. USP"] = "abc"
    resp = enviar(dados)
    assert "oficio" not in resp.json()


def test_link_e_complemento_sao_opcionais():
    dados = campos_alunos()
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    dados["COMPLEMENTO"] = ""
    resp = enviar(dados)
    assert "erros" not in resp.json()
