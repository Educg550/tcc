ENDPOINT = "/api/solicitacao"

BASE = {
    "aba": "alunos",
    "nome_completo": "Maria Souza",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "SBBD",
    "periodo_evento": "30/09/2024 a 03/10/2024",
    "cidade_evento": "Florianópolis",
    "estado_evento": "SC",
    "pais_evento": "Brasil",
    "link_evento": "https://sbbd.org.br",
    "valor_solicitado": "150000",
    "detalhamento": "Inscrição e passagem aérea",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "181",
    "complemento": "Sala 10",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "numero_agencia": "1234",
    "numero_conta": "98765-4",
}


def carga(aba="alunos", **mudancas):
    dados = {**BASE, "aba": aba}
    if aba == "docentes":
        del dados["nivel"]
        del dados["tipo_auxilio"]
    dados.update(mudancas)
    return dados


def test_oficio_de_aluno_com_link_e_complemento(cliente):
    resposta = cliente.post(ENDPOINT, =carga())
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    linhas = [
        "Interessada(o): Maria Souza - 1234567",
        "E-mail: maria@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Doutorado",
        "A CCP-Ciência da Computação aprovou na data de hoje",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: SBBD",
        "Período: 30/09/2024 a 03/10/2024",
        "Local: Florianópolis - SC - Brasil",
        "Link do evento: https://sbbd.org.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e passagem aérea",
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
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    posicao = 0
    for linha in linhas:
        posicao = oficio.find(linha, posicao)
        assert posicao != -1, f"linha ausente ou fora de ordem no ofício: {linha!r}"
        posicao += len(linha)


def test_linhas_opcionais_vazias_saem_do_oficio(cliente):
    resposta = cliente.post(ENDPOINT, =carga(link_evento="", complemento=""))
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    assert "Local: Florianópolis - SC - Brasil" in oficio
    assert "Rua do Anfiteatro, 181" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_de_docente_usa_verba_do_programa_e_sem_nivel(cliente):
    resposta = cliente.post(ENDPOINT, =carga(aba="docentes"))
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio.splitlines()
    assert "- Doutorado" not in oficio
    assert "Interessada(o): Maria Souza - 1234567" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_nivel_e_tipo_escolhidos_aparecem_no_oficio(cliente):
    resposta = cliente.post(
        ENDPOINT, =carga(nivel="Mestrado", tipo_auxilio="Outro")
    )
    oficio = resposta.()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Outro" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio


def test_valor_solicitado_aparece_formatado_em_reais(cliente):
    resposta = cliente.post(ENDPOINT, =carga(valor_solicitado="R$ 1.500,00"))
    assert resposta.status_code == 200
    assert "Valor solicitado: R$ 1.500,00" in resposta.()["oficio"]


def test_campos_obrigatorios_vazios_geram_unica_mensagem(cliente):
    resposta = cliente.post(ENDPOINT, ={"aba": "alunos"})
    dados = resposta.()
    assert dados["erros"] == ["Preencha todos os campos"]
    assert not dados.get("oficio")


def test_aba_alunos_exige_nivel_e_tipo_de_auxilio(cliente):
    dados = carga()
    del dados["nivel"]
    del dados["tipo_auxilio"]
    resposta = cliente.post(ENDPOINT, =dados)
    assert resposta.()["erros"] == ["Preencha todos os campos"]


def test_n_usp_deve_conter_apenas_numeros(cliente):
    resposta = cliente.post(ENDPOINT, =carga(n_usp="1234a67"))
    dados = resposta.()
    assert "N. USP deve conter apenas números" in dados["erros"]
    assert not dados.get("oficio")


def test_agencia_deve_conter_apenas_numeros(cliente):
    resposta = cliente.post(ENDPOINT, =carga(numero_agencia="12a4"))
    assert "Número da agência deve conter apenas números" in resposta.()["erros"]


def test_valor_solicitado_deve_ser_maior_que_zero(cliente):
    resposta = cliente.post(ENDPOINT, =carga(valor_solicitado="0"))
    assert "Valor solicitado deve ser maior que 0" in resposta.()["erros"]


def test_email_sem_arroba_ou_sem_dominio_e_invalido(cliente):
    for email in ("maria.souza.usp.br", "maria@"):
        resposta = cliente.post(ENDPOINT, =carga(email=email))
        assert "E-mail inválido" in resposta.()["erros"]


def test_cpf_fora_do_formato(cliente):
    resposta = cliente.post(ENDPOINT, =carga(cpf="12345678909"))
    erros = resposta.()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CPF inválido" not in erros


def test_cpf_com_digito_verificador_errado(cliente):
    resposta = cliente.post(ENDPOINT, =carga(cpf="123.456.789-00"))
    erros = resposta.()["erros"]
    assert "CPF inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" not in erros


def test_cep_fora_do_formato(cliente):
    resposta = cliente.post(ENDPOINT, =carga(cep="05508090"))
    assert "CEP deve estar no formato 00000-000" in resposta.()["erros"]


def test_data_de_nascimento_fora_do_formato(cliente):
    resposta = cliente.post(ENDPOINT, =carga(data_nascimento="01-02-1980"))
    erros = resposta.()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros
    assert "Data de nascimento inválida" not in erros


def test_data_de_nascimento_inexistente(cliente):
    for data in ("31/02/1980", "15/13/1980"):
        resposta = cliente.post(ENDPOINT, =carga(data_nascimento=data))
        erros = resposta.()["erros"]
        assert "Data de nascimento inválida" in erros
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in erros


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(cliente):
    resposta = cliente.post(
        ENDPOINT,
        =carga(n_usp="12a", email="maria.souza.usp.br", cep="05508090"),
    )
    erros = resposta.()["erros"]
    assert set(erros) == {
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CEP deve estar no formato 00000-000",
    }


def test_campo_vazio_e_campo_invalido_aparecem_juntos(cliente):
    resposta = cliente.post(
        ENDPOINT, =carga(nome_completo="", email="maria.souza.usp.br")
    )
    erros = resposta.()["erros"]
    assert erros.count("Preencha todos os campos") == 1
    assert "E-mail inválido" in erros


def test_validacao_vale_igual_na_aba_docentes(cliente):
    resposta = cliente.post(
        ENDPOINT, =carga(aba="docentes", cpf="123.456.789-00")
    )
    erros = resposta.()["erros"]
    assert "CPF inválido" in erros
    assert not resposta.().get("oficio")
