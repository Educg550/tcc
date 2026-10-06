"""Contrato da API que valida a solicitação e devolve o ofício.

POST /api/solicitacao recebe o formulário em JSON:

- ``aba``: "alunos" ou "docentes" - a aba DOCENTES não tem NÍVEL nem
  TIPO DE AUXÍLIO, então essas chaves não vão no pedido dela;
- uma chave por campo, com o mesmo valor exibido no campo: os campos que se
  formatam sozinhos chegam já formatados (``R$ 1.500,00``,
  ``123.456.789-09``, ``05508-090``, ``01/02/1980``).

Resposta:

- pedido válido: {"oficio": ...} com o ofício já redigido, com os dados no
  lugar dos marcadores e preservando as quebras de linha;
- pedido inválido: {"erros": [...]} com todas as mensagens que se aplicam.
"""

import pytest

ENDPOINT = "/api/solicitacao"

DADOS = {
    "nome_completo": "Maria Souza",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "email": "maria@usp.br",
    "nome_do_evento": "Congresso Brasileiro de Computação",
    "periodo_do_evento": "01/07/2025 a 05/07/2025",
    "cidade_do_evento": "São Paulo",
    "estado_do_evento": "SP",
    "pais_do_evento": "Brasil",
    "link_do_evento": "https://congresso.example.br",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento_do_pedido": "Passagens e hospedagem",
    "ira_apresentar_trabalho": "Pôster",
    "data_de_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "101",
    "complemento": "Sala 5",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_do_banco": "Banco do Brasil",
    "numero_da_agencia": "1234",
    "numero_da_conta": "98765-4",
}


def dados_alunos(**trocas):
    dados = {
        "aba": "alunos",
        **DADOS,
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
    }
    dados.update(trocas)
    return dados


def dados_docentes(**trocas):
    dados = {"aba": "docentes", **DADOS}
    dados.update(trocas)
    return dados


def enviar(client, dados):
    return client.post(ENDPOINT, =dados)


def oficio_esperado(assunto, linha_programa, com_link=True, com_complemento=True):
    linhas = [
        f"Interessada(o): {DADOS['nome_completo']} - {DADOS['n_usp']}",
        f"E-mail: {DADOS['email']}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{DADOS['programa']} aprovou na data de hoje, "
        "a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {DADOS['nome_do_evento']}",
        f"Período: {DADOS['periodo_do_evento']}",
        "Local: "
        f"{DADOS['cidade_do_evento']} - {DADOS['estado_do_evento']} - {DADOS['pais_do_evento']}",
    ]
    if com_link:
        linhas.append(f"Link do evento: {DADOS['link_do_evento']}")
    linhas += [
        f"Apresentação de trabalho: {DADOS['ira_apresentar_trabalho']}",
        f"Valor solicitado: {DADOS['valor_solicitado']}",
        f"Detalhamento: {DADOS['detalhamento_do_pedido']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{DADOS['logradouro']}, {DADOS['numero']}",
    ]
    if com_complemento:
        linhas.append(f"Complemento: {DADOS['complemento']}")
    linhas += [
        f"CEP: {DADOS['cep']}",
        f"{DADOS['bairro']}, {DADOS['cidade']} - {DADOS['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {DADOS['data_de_nascimento']}",
        f"CPF: {DADOS['cpf']}",
        f"RG / RNM: {DADOS['rg_rnm']}",
        f"Banco: {DADOS['nome_do_banco']}",
        f"Agência: {DADOS['numero_da_agencia']}",
        f"Conta: {DADOS['numero_da_conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def test_solicitacao_valida_de_alunos_devolve_o_oficio_preenchido(client):
    resposta = enviar(client, dados_alunos())
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert oficio.strip() == oficio_esperado(
        assunto="Participação em evento",
        linha_programa="Programa: Ciência da Computação - Mestrado",
    )


def test_solicitacao_de_docentes_nao_usa_nivel_nem_tipo_de_auxilio(client):
    resposta = enviar(client, dados_docentes())
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert oficio.strip() == oficio_esperado(
        assunto="Verba do programa",
        linha_programa="Programa: Ciência da Computação",
    )


def test_alunos_com_tudo_vazio_pede_para_preencher_todos_os_campos(client):
    vazio = {chave: "" for chave in dados_alunos()}
    vazio["aba"] = "alunos"
    resposta = enviar(client, vazio)
    assert resposta.()["erros"] == ["Preencha todos os campos"]


def test_docentes_com_tudo_vazio_pede_para_preencher_todos_os_campos(client):
    vazio = {chave: "" for chave in dados_docentes()}
    vazio["aba"] = "docentes"
    resposta = enviar(client, vazio)
    assert resposta.()["erros"] == ["Preencha todos os campos"]


@pytest.mark.parametrize("n_usp", ["12a3456", "abc"])
def test_n_usp_deve_conter_apenas_numeros(client, n_usp):
    resposta = enviar(client, dados_alunos(n_usp=n_usp))
    assert resposta.()["erros"] == ["N. USP deve conter apenas números"]


def test_numero_da_agencia_deve_conter_apenas_numeros(client):
    resposta = enviar(client, dados_alunos(numero_da_agencia="12a4"))
    assert resposta.()["erros"] == [
        "Número da agência deve conter apenas números"
    ]


@pytest.mark.parametrize("valor", ["R$ 0,00", "abc"])
def test_valor_solicitado_deve_ser_maior_que_zero(client, valor):
    resposta = enviar(client, dados_alunos(valor_solicitado=valor))
    assert resposta.()["erros"] == ["Valor solicitado deve ser maior que 0"]


@pytest.mark.parametrize("email", ["maria", "maria@"])
def test_email_invalido(client, email):
    resposta = enviar(client, dados_alunos(email=email))
    assert resposta.()["erros"] == ["E-mail inválido"]


def test_cpf_fora_do_formato(client):
    resposta = enviar(client, dados_alunos(cpf="12345678909"))
    assert resposta.()["erros"] == [
        "CPF deve estar no formato 000.000.000-00"
    ]


def test_cpf_com_digitos_verificadores_errados(client):
    resposta = enviar(client, dados_alunos(cpf="123.456.789-00"))
    assert resposta.()["erros"] == ["CPF inválido"]


def test_cep_fora_do_formato(client):
    resposta = enviar(client, dados_alunos(cep="05508090"))
    assert resposta.()["erros"] == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato(client):
    resposta = enviar(client, dados_alunos(data_de_nascimento="01021980"))
    assert resposta.()["erros"] == [
        "Data de nascimento deve estar no formato dd/mm/aaaa"
    ]


@pytest.mark.parametrize("data", ["31/02/2000", "01/13/2000"])
def test_data_de_nascimento_inexistente(client, data):
    resposta = enviar(client, dados_alunos(data_de_nascimento=data))
    assert resposta.()["erros"] == ["Data de nascimento inválida"]


def test_as_mesmas_regras_valem_para_docentes(client):
    resposta = enviar(client, dados_docentes(cpf="123.456.789-00"))
    assert resposta.()["erros"] == ["CPF inválido"]


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(client):
    resposta = enviar(
        client,
        dados_alunos(
            n_usp="12a3456",
            email="maria",
            valor_solicitado="R$ 0,00",
            data_de_nascimento="31/02/2000",
            cep="05508090",
            cpf="123.456.789-00",
            numero_da_agencia="12a4",
        ),
    )
    erros = resposta.()["erros"]
    assert len(erros) == 7
    assert set(erros) == {
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "Valor solicitado deve ser maior que 0",
        "Data de nascimento inválida",
        "CEP deve estar no formato 00000-000",
        "CPF inválido",
        "Número da agência deve conter apenas números",
    }


def test_campo_vazio_nao_esconde_as_outras_mensagens(client):
    resposta = enviar(client, dados_alunos(nome_completo="", cpf="123.456.789-00"))
    assert set(resposta.()["erros"]) == {
        "Preencha todos os campos",
        "CPF inválido",
    }


def test_com_erro_o_oficio_nao_e_gerado(client):
    resposta = enviar(client, dados_alunos(n_usp="12a3456"))
    corpo = resposta.()
    assert corpo["erros"]
    assert not corpo.get("oficio")


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(client):
    resposta = enviar(client, dados_alunos(link_do_evento="", complemento=""))
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio
    assert oficio.strip() == oficio_esperado(
        assunto="Participação em evento",
        linha_programa="Programa: Ciência da Computação - Mestrado",
        com_link=False,
        com_complemento=False,
    )
