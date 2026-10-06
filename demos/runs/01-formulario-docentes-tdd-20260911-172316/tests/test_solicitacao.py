from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def valid_alunos():
    return {
        "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva Santos",
        "N. USP": "12345678",
        "PROGRAMA": "Ciência da Computação",
        "NÍVEL": "Mestrado",
        "TIPO DE AUXÍLIO": "Participação em evento",
        "E-MAIL": "maria@usp.br",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Computação",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/03/2025 a 12/03/2025",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "Belo Horizonte",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "MG",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.exemplo.br",
        "VALOR SOLICITADO (R$)": 150000,
        "DETALHAMENTO DO PEDIDO": "Solicito auxílio para participação no evento.",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "DATA DE NASCIMENTO": "01/02/1980",
        "LOGRADOURO": "Rua Teste",
        "NÚMERO": "100",
        "COMPLEMENTO": "Apto 2",
        "BAIRRO": "Butantã",
        "CEP": "05508-090",
        "CIDADE": "São Paulo",
        "ESTADO": "SP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "111.444.777-35",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "NOME DO BANCO": "Banco do Brasil",
        "NÚMERO DA AGÊNCIA": "1234",
        "NÚMERO DA CONTA": "12345-6",
    }


def valid_docentes():
    dados = valid_alunos()
    del dados["NÍVEL"]
    del dados["TIPO DE AUXÍLIO"]
    dados["NOME COMPLETO - SEM ABREVIAR"] = "João Pereira Lima"
    dados["N. USP"] = "87654321"
    dados["PROGRAMA"] = "Engenharia Elétrica"
    dados["E-MAIL"] = "joao@usp.br"
    return dados


OFICIO_ALUNOS = """Interessada(o): Maria da Silva Santos - 12345678
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Congresso Brasileiro de Computação
Período: 10/03/2025 a 12/03/2025
Local: Belo Horizonte - MG - Brasil
Link do evento: https://evento.exemplo.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Solicito auxílio para participação no evento.

Endereço da(o) interessada(o)
Rua Teste, 100
Complemento: Apto 2
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 111.444.777-35
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 12345-6

Encaminhe-se ao Serviço Financeiro para providências."""


OFICIO_DOCENTES = """Interessada(o): João Pereira Lima - 87654321
E-mail: joao@usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Engenharia Elétrica

A CCP-Engenharia Elétrica aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Congresso Brasileiro de Computação
Período: 10/03/2025 a 12/03/2025
Local: Belo Horizonte - MG - Brasil
Link do evento: https://evento.exemplo.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Solicito auxílio para participação no evento.

Endereço da(o) interessada(o)
Rua Teste, 100
Complemento: Apto 2
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 111.444.777-35
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 12345-6

Encaminhe-se ao Serviço Financeiro para providências."""


def test_solicitacao_valida_de_aluno_gera_oficio_exato():
    resposta = client.post("/alunos", json=valid_alunos())
    corpo = resposta.json()
    assert corpo["erros"] == []
    assert corpo["oficio"].strip() == OFICIO_ALUNOS.strip()


def test_solicitacao_valida_de_docente_gera_oficio_exato():
    resposta = client.post("/docentes", json=valid_docentes())
    corpo = resposta.json()
    assert corpo["erros"] == []
    assert corpo["oficio"].strip() == OFICIO_DOCENTES.strip()


def test_link_vazio_remove_linha_do_oficio():
    dados = valid_alunos()
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert corpo["erros"] == []
    assert "Link do evento" not in corpo["oficio"]


def test_complemento_vazio_remove_linha_do_oficio():
    dados = valid_alunos()
    dados["COMPLEMENTO"] = ""
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert corpo["erros"] == []
    assert "Complemento" not in corpo["oficio"]


def test_campo_obrigatorio_vazio_gera_erro_unico():
    dados = valid_alunos()
    dados["NOME COMPLETO - SEM ABREVIAR"] = ""
    dados["CIDADE"] = ""
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert corpo["erros"].count("Preencha todos os campos") == 1
    assert corpo["oficio"] is None


def test_n_usp_com_letras_gera_erro():
    dados = valid_alunos()
    dados["N. USP"] = "123A5678"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_numero_da_agencia_com_letras_gera_erro():
    dados = valid_alunos()
    dados["NÚMERO DA AGÊNCIA"] = "12A4"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_valor_solicitado_zero_gera_erro():
    dados = valid_alunos()
    dados["VALOR SOLICITADO (R$)"] = 0
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_valor_solicitado_negativo_gera_erro():
    dados = valid_alunos()
    dados["VALOR SOLICITADO (R$)"] = -100
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_email_sem_arroba_gera_erro():
    dados = valid_alunos()
    dados["E-MAIL"] = "mariaarroba.com"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "E-mail inválido" in corpo["erros"]


def test_email_sem_dominio_gera_erro():
    dados = valid_alunos()
    dados["E-MAIL"] = "maria@"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "E-mail inválido" in corpo["erros"]


def test_cpf_fora_do_formato_gera_erro():
    dados = valid_alunos()
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "11144477735"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]


def test_cpf_com_digitos_verificadores_errados_gera_erro():
    dados = valid_alunos()
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "111.444.777-00"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "CPF inválido" in corpo["erros"]


def test_cep_fora_do_formato_gera_erro():
    dados = valid_alunos()
    dados["CEP"] = "05508090"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_data_nascimento_fora_do_formato_gera_erro():
    dados = valid_alunos()
    dados["DATA DE NASCIMENTO"] = "1980-02-01"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


def test_data_nascimento_com_dia_invalido_gera_erro():
    dados = valid_alunos()
    dados["DATA DE NASCIMENTO"] = "31/02/1980"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_data_nascimento_com_mes_invalido_gera_erro():
    dados = valid_alunos()
    dados["DATA DE NASCIMENTO"] = "01/13/1980"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_multiplos_erros_aparecem_juntos():
    dados = valid_alunos()
    dados["E-MAIL"] = "invalido"
    dados["CEP"] = "12345"
    resposta = client.post("/alunos", json=dados)
    corpo = resposta.json()
    assert "E-mail inválido" in corpo["erros"]
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]
    assert corpo["oficio"] is None


def test_docentes_nao_exige_nivel_nem_tipo_de_auxilio():
    resposta = client.post("/docentes", json=valid_docentes())
    corpo = resposta.json()
    assert corpo["erros"] == []
