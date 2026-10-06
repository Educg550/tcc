from conftest import com, enviar

INTERESSADA = "Interessada(o): Maria de Souza - 1234567"
ENCAMINHE = "Encaminhe-se ao Serviço Financeiro para providências."


def test_envio_valido_de_alunos_gera_oficio(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, base_alunos).text
    trechos = [
        INTERESSADA,
        "E-mail: maria@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Mestrado",
        "A CCP-Ciência da Computação aprovou na data de hoje",
        "Dados do evento",
        "Evento: Congresso Brasileiro de Computação",
        "Período: 10/03/2025 a 14/03/2025",
        "Local: Gramado - RS - Brasil",
        "Link do evento: https://congresso.org.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea e inscrição no evento",
        "Endereço da(o) interessada(o)",
        "Rua do Anfiteatro, 181",
        "Complemento: Sala 10",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 98765-4",
        ENCAMINHE,
    ]
    for trecho in trechos:
        assert trecho in corpo, "esperava no ofício: " + trecho


def test_envio_valido_de_docentes_gera_oficio(client, endpoint, base_docentes):
    corpo = enviar(client, endpoint, base_docentes).text
    assert INTERESSADA in corpo
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in corpo
    assert "Programa: Ciência da Computação" in corpo
    assert "Programa: Ciência da Computação - Mestrado" not in corpo
    assert ENCAMINHE in corpo


def test_campos_opcionais_vazios_saiem_do_oficio(client, endpoint, base_alunos):
    dados = com(base_alunos, {
        "LINK DO EVENTO, EXAME OU DEFESA": "",
        "COMPLEMENTO": "",
    })
    corpo = enviar(client, endpoint, dados).text
    assert INTERESSADA in corpo
    assert "Link do evento:" not in corpo
    assert "Complemento:" not in corpo


def test_envio_vazio_aponta_campos_obrigatorios(client, endpoint):
    corpo = enviar(client, endpoint, {}).text
    assert "Preencha todos os campos" in corpo
    assert "Interessada(o):" not in corpo


def test_n_usp_deve_conter_apenas_numeros(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"N. USP": "12a45b7"})).text
    assert "N. USP deve conter apenas números" in corpo
    assert "Interessada(o):" not in corpo


def test_agencia_deve_conter_apenas_numeros(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"NÚMERO DA AGÊNCIA": "12a4"})).text
    assert "Número da agência deve conter apenas números" in corpo
    assert "Interessada(o):" not in corpo


def test_valor_solicitado_deve_ser_maior_que_zero(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"VALOR SOLICITADO (R$)": "0"})).text
    assert "Valor solicitado deve ser maior que 0" in corpo
    assert "Interessada(o):" not in corpo


def test_email_sem_arroba_e_invalido(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"E-MAIL": "maria.usp.br"})).text
    assert "E-mail inválido" in corpo
    assert "Interessada(o):" not in corpo


def test_email_sem_dominio_e_invalido(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"E-MAIL": "maria@"})).text
    assert "E-mail inválido" in corpo
    assert "Interessada(o):" not in corpo


def test_cpf_fora_do_formato(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123456789"})).text
    assert "CPF deve estar no formato 000.000.000-00" in corpo
    assert "Interessada(o):" not in corpo


def test_cpf_com_digito_verificador_errado(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})).text
    assert "CPF inválido" in corpo
    assert "CPF deve estar no formato 000.000.000-00" not in corpo
    assert "Interessada(o):" not in corpo


def test_cep_fora_do_formato(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"CEP": "0550809"})).text
    assert "CEP deve estar no formato 00000-000" in corpo
    assert "Interessada(o):" not in corpo


def test_data_de_nascimento_fora_do_formato(client, endpoint, base_alunos):
    corpo = enviar(client, endpoint, com(base_alunos, {"DATA DE NASCIMENTO": "010280"})).text
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo
    assert "Interessada(o):" not in corpo


def test_data_de_nascimento_inexistente(client, endpoint, base_alunos):
    for data in ["31/02/2020", "10/13/2020"]:
        corpo = enviar(client, endpoint, com(base_alunos, {"DATA DE NASCIMENTO": data})).text
        assert "Data de nascimento inválida" in corpo
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in corpo
        assert "Interessada(o):" not in corpo


def test_validacao_igual_na_aba_docentes(client, endpoint, base_docentes):
    corpo = enviar(client, endpoint, com(base_docentes, {"E-MAIL": "maria.usp.br"})).text
    assert "E-mail inválido" in corpo
    assert "Interessada(o):" not in corpo


def test_todas_as_mensagens_de_erro_aparecem_juntas(client, endpoint, base_alunos):
    dados = com(base_alunos, {
        "N. USP": "abc",
        "E-MAIL": "maria.usp.br",
        "NÚMERO DA AGÊNCIA": "a1",
        "VALOR SOLICITADO (R$)": "0",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123456789",
        "CEP": "0550809",
        "DATA DE NASCIMENTO": "010280",
    })
    corpo = enviar(client, endpoint, dados).text
    for mensagem in [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]:
        assert mensagem in corpo
    assert "Preencha todos os campos" not in corpo
    assert "Interessada(o):" not in corpo
