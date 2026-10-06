"""Backend: validação da solicitação e redação do ofício."""

PAYLOAD_ALUNOS = {
    "tipo": "alunos",
    "nome_completo": "Fulano de Tal",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "fulano@usp.br",
    "nome_evento": "SBBD",
    "periodo_evento": "13 a 16 de outubro de 2025",
    "cidade_evento": "Campinas",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://sbbd.org.br",
    "valor_solicitado": "150000",
    "detalhamento": "Passagens e diárias",
    "apresentacao_trabalho": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "181",
    "complemento": "Sala 204",
    "bairro": "Cidade Universitária",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "98765-4",
}

PAYLOAD_DOCENTES = {
    "tipo": "docentes",
    "nome_completo": "Beltrana de Oliveira",
    "n_usp": "7654321",
    "programa": "Estatística",
    "email": "beltrana@usp.br",
    "nome_evento": "Banca de defesa de mestrado",
    "periodo_evento": "20 de novembro de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor_solicitado": "50000",
    "detalhamento": "Auxílio para participação em banca",
    "apresentacao_trabalho": "Não irá apresentar trabalho",
    "data_nascimento": "15/07/1975",
    "logradouro": "Av. Prof. Luciano Gualberto",
    "numero": "403",
    "complemento": "",
    "bairro": "Cidade Universitária",
    "cep": "05508-010",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "529.982.247-25",
    "rg_rnm": "9.876.543-2",
    "nome_banco": "Itaú",
    "agencia": "2048",
    "conta": "0415-7",
}

OFICIO_ALUNOS = """\
Interessada(o): Fulano de Tal - 1234567
E-mail: fulano@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD
Período: 13 a 16 de outubro de 2025
Local: Campinas - SP - Brasil
Link do evento: https://sbbd.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagens e diárias

Endereço da(o) interessada(o)
Rua do Anfiteatro, 181
Complemento: Sala 204
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências.
"""

OFICIO_DOCENTES = """\
Interessada(o): Beltrana de Oliveira - 7654321
E-mail: beltrana@usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Estatística

A CCP-Estatística aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Banca de defesa de mestrado
Período: 20 de novembro de 2025
Local: São Paulo - SP - Brasil
Apresentação de trabalho: Não irá apresentar trabalho
Valor solicitado: R$ 500,00
Detalhamento: Auxílio para participação em banca

Endereço da(o) interessada(o)
Av. Prof. Luciano Gualberto, 403
CEP: 05508-010
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 15/07/1975
CPF: 529.982.247-25
RG / RNM: 9.876.543-2
Banco: Itaú
Agência: 2048
Conta: 0415-7

Encaminhe-se ao Serviço Financeiro para providências.
"""


def test_solicitacao_valida_de_aluno_gera_oficio(enviar, mensagens, oficio):
    resposta = enviar(PAYLOAD_ALUNOS)
    assert resposta.status_code in (200, 201)
    assert mensagens(resposta) == []
    assert oficio(resposta).strip() == OFICIO_ALUNOS.strip()


def test_solicitacao_valida_de_docente_gera_oficio(enviar, mensagens, oficio):
    resposta = enviar(PAYLOAD_DOCENTES)
    assert resposta.status_code in (200, 201)
    assert mensagens(resposta) == []
    assert oficio(resposta).strip() == OFICIO_DOCENTES.strip()


def test_valor_solicitado_aparece_como_moeda_brasileira(enviar, mensagens, oficio):
    for digitos, moeda in (
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ):
        resposta = enviar(dict(PAYLOAD_ALUNOS, valor_solicitado=digitos))
        assert mensagens(resposta) == []
        assert "Valor solicitado: " + moeda in oficio(resposta)


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(enviar, oficio):
    resposta = enviar(dict(PAYLOAD_ALUNOS, link_evento="", complemento=""))
    texto = oficio(resposta)
    assert "Link do evento" not in texto
    assert "Complemento" not in texto
    assert "Local: Campinas - SP - Brasil" in texto


def test_campos_obrigatorios_vazios_geram_uma_unica_mensagem(enviar, mensagens, oficio):
    vazio = {chave: ("" if chave != "tipo" else "alunos") for chave in PAYLOAD_ALUNOS}
    resposta = enviar(vazio)
    assert mensagens(resposta) == ["Preencha todos os campos"]
    assert not oficio(resposta)


def test_n_usp_deve_conter_apenas_numeros(enviar, mensagens, oficio):
    resposta = enviar(dict(PAYLOAD_ALUNOS, n_usp="123a567"))
    assert mensagens(resposta) == ["N. USP deve conter apenas números"]
    assert not oficio(resposta)


def test_numero_da_agencia_deve_conter_apenas_numeros(enviar, mensagens, oficio):
    resposta = enviar(dict(PAYLOAD_ALUNOS, agencia="12a4"))
    assert mensagens(resposta) == ["Número da agência deve conter apenas números"]
    assert not oficio(resposta)


def test_valor_solicitado_deve_ser_maior_que_zero(enviar, mensagens, oficio):
    resposta = enviar(dict(PAYLOAD_ALUNOS, valor_solicitado="0"))
    assert mensagens(resposta) == ["Valor solicitado deve ser maior que 0"]
    assert not oficio(resposta)


def test_email_sem_arroba_ou_sem_dominio_e_invalido(enviar, mensagens):
    for email in ("fulano", "fulano@"):
        resposta = enviar(dict(PAYLOAD_ALUNOS, email=email))
        assert mensagens(resposta) == ["E-mail inválido"]


def test_cpf_fora_do_formato_e_rejeitado(enviar, mensagens, oficio):
    resposta = enviar(dict(PAYLOAD_ALUNOS, cpf="12345678909"))
    assert mensagens(resposta) == ["CPF deve estar no formato 000.000.000-00"]
    assert not oficio(resposta)


def test_cep_fora_do_formato_e_rejeitado(enviar, mensagens):
    resposta = enviar(dict(PAYLOAD_ALUNOS, cep="05508090"))
    assert mensagens(resposta) == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato_e_rejeitada(enviar, mensagens):
    resposta = enviar(dict(PAYLOAD_ALUNOS, data_nascimento="01021980"))
    assert mensagens(resposta) == ["Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_cpf_com_digito_verificador_incorreto_e_invalido(enviar, mensagens):
    resposta = enviar(dict(PAYLOAD_ALUNOS, cpf="123.456.789-00"))
    assert mensagens(resposta) == ["CPF inválido"]


def test_data_de_nascimento_inexistente_e_invalida(enviar, mensagens):
    for data in ("31/02/1980", "01/13/1980"):
        resposta = enviar(dict(PAYLOAD_ALUNOS, data_nascimento=data))
        assert mensagens(resposta) == ["Data de nascimento inválida"]


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(enviar, mensagens, oficio):
    payload = dict(
        PAYLOAD_ALUNOS,
        n_usp="12a3",
        agencia="9x8",
        valor_solicitado="0",
        email="sem-arroba",
        cpf="12345678909",
        cep="05508090",
        data_nascimento="01021980",
    )
    resposta = enviar(payload)
    assert set(mensagens(resposta)) == {
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    }
    assert not oficio(resposta)


def test_validacao_vale_igual_na_aba_docentes(enviar, mensagens):
    resposta = enviar(dict(PAYLOAD_DOCENTES, n_usp="abcd"))
    assert mensagens(resposta) == ["N. USP deve conter apenas números"]
