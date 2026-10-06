"""Testes do backend.

O frontend envia o formulário em JSON para POST /solicitacao: os campos do
formulário como texto e um campo 'tipo' com 'aluno' ou 'docente'. A resposta
traz 'oficio' (o texto pronto) quando a solicitação é válida e 'erros' (a lista
de mensagens, cada uma uma vez) quando não é.
"""

ENDERECO = "/solicitacao"


def solicitacao_aluno(**sobrescrever):
    dados = {
        "tipo": "aluno",
        "nome": "Maria da Silva Santos",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria.santos@ime.usp.br",
        "evento": "XXX Congresso Nacional de Matemática",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link": "https://congresso.exemplo.br",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição no evento e passagens aéreas",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Prédio C",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(sobrescrever)
    return dados


def solicitacao_docente(**sobrescrever):
    dados = solicitacao_aluno(
        nome="João Carlos de Oliveira",
        n_usp="87654321",
        programa="Estatística",
        email="joao.carlos@ime.usp.br",
        cpf="529.982.247-25",
        data_nascimento="15/09/1975",
    )
    dados.update(sobrescrever)
    dados["tipo"] = "docente"
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    return dados


OFICIO_ALUNO = """Interessada(o): Maria da Silva Santos - 12345678
E-mail: maria.santos@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Matemática - Mestrado

A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: XXX Congresso Nacional de Matemática
Período: 10 a 12 de outubro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://congresso.exemplo.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Inscrição no evento e passagens aéreas

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Prédio C
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 56789-0

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_DOCENTE = """Interessada(o): João Carlos de Oliveira - 87654321
E-mail: joao.carlos@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Estatística

A CCP-Estatística aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: XXX Congresso Nacional de Matemática
Período: 10 a 12 de outubro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://congresso.exemplo.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Inscrição no evento e passagens aéreas

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Prédio C
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 15/09/1975
CPF: 529.982.247-25
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 56789-0

Encaminhe-se ao Serviço Financeiro para providências."""


def test_solicitacao_de_aluno_gera_o_oficio(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno())
    assert resp.status_code == 200
    assert resp.json()["oficio"].strip() == OFICIO_ALUNO.strip()


def test_solicitacao_de_docente_gera_oficio_com_verba_do_programa(client):
    resp = client.post(ENDERECO, json=solicitacao_docente())
    assert resp.status_code == 200
    assert resp.json()["oficio"].strip() == OFICIO_DOCENTE.strip()


def test_link_vazio_e_complemento_vazio_saem_do_oficio(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(link="", complemento=""))
    assert resp.status_code == 200
    oficio = resp.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_valor_aparece_no_oficio_como_moeda_brasileira(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(valor="R$ 15,00"))
    assert resp.status_code == 200
    assert "Valor solicitado: R$ 15,00" in resp.json()["oficio"]


def test_campos_obrigatorios_vazios_pedem_preencher_todos(client):
    resp = client.post(
        ENDERECO,
        json=solicitacao_aluno(
            nome="", programa="", cpf="", cep="", data_nascimento=""
        ),
    )
    assert resp.json()["erros"] == ["Preencha todos os campos"]


def test_formulario_de_aluno_todo_vazio(client):
    vazio = {campo: "" for campo in solicitacao_aluno()}
    vazio["tipo"] = "aluno"
    resp = client.post(ENDERECO, json=vazio)
    assert resp.json()["erros"] == ["Preencha todos os campos"]


def test_formulario_de_docente_todo_vazio(client):
    vazio = {campo: "" for campo in solicitacao_docente()}
    vazio["tipo"] = "docente"
    resp = client.post(ENDERECO, json=vazio)
    assert resp.json()["erros"] == ["Preencha todos os campos"]


def test_nivel_e_tipo_de_auxilio_sao_obrigatorios_para_aluno(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(nivel="", tipo_auxilio=""))
    assert resp.json()["erros"] == ["Preencha todos os campos"]


def test_n_usp_deve_conter_apenas_numeros(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(n_usp="1234a567"))
    assert resp.json()["erros"] == ["N. USP deve conter apenas números"]


def test_agencia_deve_conter_apenas_numeros(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(agencia="12-x34"))
    assert resp.json()["erros"] == ["Número da agência deve conter apenas números"]


def test_valor_deve_ser_maior_que_zero(client):
    for valor in ("R$ 0,00", "de graça"):
        resp = client.post(ENDERECO, json=solicitacao_aluno(valor=valor))
        assert resp.json()["erros"] == ["Valor solicitado deve ser maior que 0"], valor


def test_email_sem_arroba_ou_sem_dominio_e_invalido(client):
    for email in ("maria.santos.ime.usp.br", "maria.santos@"):
        resp = client.post(ENDERECO, json=solicitacao_aluno(email=email))
        assert resp.json()["erros"] == ["E-mail inválido"], email


def test_cpf_fora_do_formato(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(cpf="12345678909"))
    assert resp.json()["erros"] == ["CPF deve estar no formato 000.000.000-00"]


def test_cpf_no_formato_mas_com_digitos_verificadores_errados(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(cpf="123.456.789-00"))
    assert resp.json()["erros"] == ["CPF inválido"]


def test_cep_fora_do_formato(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(cep="05508090"))
    assert resp.json()["erros"] == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(data_nascimento="1980-02-01"))
    assert resp.json()["erros"] == [
        "Data de nascimento deve estar no formato dd/mm/aaaa"
    ]


def test_data_de_nascimento_inexistente(client):
    for data in ("31/02/2020", "01/13/1980"):
        resp = client.post(ENDERECO, json=solicitacao_aluno(data_nascimento=data))
        assert resp.json()["erros"] == ["Data de nascimento inválida"], data


def test_todos_os_erros_aplicaveis_aparecem_juntos(client):
    resp = client.post(
        ENDERECO,
        json=solicitacao_aluno(
            n_usp="12a34",
            email="sem.arroba",
            cpf="1",
            cep="1",
            data_nascimento="1",
        ),
    )
    assert sorted(resp.json()["erros"]) == sorted(
        [
            "N. USP deve conter apenas números",
            "E-mail inválido",
            "CPF deve estar no formato 000.000.000-00",
            "CEP deve estar no formato 00000-000",
            "Data de nascimento deve estar no formato dd/mm/aaaa",
        ]
    )


def test_oficio_nao_e_gerado_enquanto_houver_erro(client):
    resp = client.post(ENDERECO, json=solicitacao_aluno(email="errado"))
    assert resp.json()["erros"]
    assert not resp.json().get("oficio")


def test_validacao_vale_igual_para_a_aba_docentes(client):
    resp = client.post(ENDERECO, json=solicitacao_docente(n_usp="abc"))
    assert resp.json()["erros"] == ["N. USP deve conter apenas números"]
