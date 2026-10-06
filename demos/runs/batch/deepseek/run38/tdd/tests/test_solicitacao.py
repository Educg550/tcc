import json

import app as app_module
from fastapi.testclient import TestClient

cliente = TestClient(app_module.app)

VALORES = {
    "nome": "Maria Silva Santos",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria.silva@ime.usp.br",
    "evento": "Congresso Brasileiro de Matemática",
    "periodo": "10 a 15 de julho de 2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://evento.ime.usp.br",
    "valor": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e hospedagem",
    "apresentar": "Apresentação oral",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Bloco B",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}

ALIASES = {
    "nome": ["NOME COMPLETO - SEM ABREVIAR", "nome", "nome_completo"],
    "n_usp": ["N. USP", "n_usp", "nusp", "numero_usp"],
    "programa": ["PROGRAMA", "programa"],
    "nivel": ["NÍVEL", "nivel"],
    "tipo_auxilio": ["TIPO DE AUXÍLIO", "tipo_auxilio", "tipo_de_auxilio"],
    "email": ["E-MAIL", "email", "e_mail"],
    "evento": ["NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "nome_evento", "evento"],
    "periodo": ["PERÍODO DO EVENTO, EXAME OU DEFESA", "periodo", "periodo_evento"],
    "cidade_evento": ["CIDADE DO EVENTO, EXAME OU DEFESA", "cidade_evento"],
    "estado_evento": ["ESTADO DO EVENTO, EXAME OU DEFESA", "estado_evento"],
    "pais_evento": ["PAÍS DO EVENTO, EXAME OU DEFESA", "pais_evento"],
    "link_evento": ["LINK DO EVENTO, EXAME OU DEFESA", "link_evento"],
    "valor": ["VALOR SOLICITADO (R$)", "valor", "valor_solicitado"],
    "detalhamento": ["DETALHAMENTO DO PEDIDO", "detalhamento"],
    "apresentar": [
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "apresentar",
        "apresentacao",
        "tipo_apresentacao",
    ],
    "data_nascimento": ["DATA DE NASCIMENTO", "data_nascimento"],
    "logradouro": ["LOGRADOURO", "logradouro"],
    "numero": ["NÚMERO", "numero"],
    "complemento": ["COMPLEMENTO", "complemento"],
    "bairro": ["BAIRRO", "bairro"],
    "cep": ["CEP", "cep"],
    "cidade": ["CIDADE", "cidade"],
    "estado": ["ESTADO", "estado"],
    "cpf": ["CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf"],
    "rg": ["RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "rg"],
    "banco": ["NOME DO BANCO", "banco", "nome_banco"],
    "agencia": ["NÚMERO DA AGÊNCIA", "agencia", "numero_agencia"],
    "conta": ["NÚMERO DA CONTA", "conta", "numero_conta"],
}

CHAVES_DA_ABA = [
    "aba",
    "aba_ativa",
    "formulario",
    "formulário",
    "tipo_formulario",
    "tipoFormulario",
    "tipo_solicitacao",
]


def rota_post(aba):
    caminhos = [
        rota.path
        for rota in app_module.app.routes
        if "POST" in (getattr(rota, "methods", None) or set())
    ]
    assert caminhos, "a aplicação não tem rota POST"
    por_aba = [caminho for caminho in caminhos if "aluno" in caminho or "docente" in caminho]
    if por_aba:
        for caminho in por_aba:
            if aba in caminho:
                return caminho
    return caminhos[0]


def corpo(resposta):
    try:
        objeto = resposta.json()
    except Exception:
        return resposta.text
    return json.dumps(objeto, ensure_ascii=False)


def payload(aba="alunos", **mudancas):
    campos = dict(VALORES)
    if aba == "docentes":
        campos["nivel"] = ""
        campos["tipo_auxilio"] = ""
    dados = {chave: aba for chave in CHAVES_DA_ABA}
    for campo, valor in campos.items():
        for apelido in ALIASES[campo]:
            dados[apelido] = valor
    for campo, valor in mudancas.items():
        for apelido in ALIASES[campo]:
            dados[apelido] = valor
    return dados


def sem_campos(dados, campos):
    for campo in campos:
        for apelido in ALIASES[campo]:
            dados.pop(apelido, None)
    return dados


def enviar(dados, alternativo=None):
    aba = "docentes" if dados.get("aba") == "docentes" else "alunos"
    caminho = rota_post(aba)
    variantes = [dados] + ([alternativo] if alternativo else [])
    ultima = None
    for variante in variantes:
        resposta = cliente.post(caminho, json=variante)
        if resposta.status_code == 422:
            resposta = cliente.post(caminho, data=variante)
        if resposta.status_code != 422:
            return resposta
        ultima = resposta
    return ultima


def test_solicitacao_valida_gera_o_oficio():
    texto = corpo(enviar(payload()))
    assert "Interessada(o): Maria Silva Santos - 12345678" in texto
    assert "E-mail: maria.silva@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Matemática - Doutorado" in texto
    assert "A CCP-Matemática aprovou na data de hoje" in texto
    assert "Evento: Congresso Brasileiro de Matemática" in texto
    assert "Período: 10 a 15 de julho de 2024" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://evento.ime.usp.br" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e hospedagem" in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Bloco B" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_da_aba_docentes():
    alternativo = sem_campos(payload(aba="docentes"), ["nivel", "tipo_auxilio"])
    texto = corpo(enviar(payload(aba="docentes"), alternativo=alternativo))
    assert "Interessada(o): Maria Silva Santos - 12345678" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática" in texto
    assert "Programa: Matemática - " not in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_link_vazio_sai_do_oficio():
    texto = corpo(enviar(payload(link_evento="")))
    assert "Link do evento" not in texto


def test_complemento_vazio_sai_do_oficio():
    texto = corpo(enviar(payload(complemento="")))
    assert "Complemento" not in texto


def test_campo_obrigatorio_vazio():
    texto = corpo(enviar(payload(nome="")))
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1


def test_n_usp_precisa_ser_numerico():
    texto = corpo(enviar(payload(n_usp="12a34")))
    assert "N. USP deve conter apenas números" in texto


def test_agencia_precisa_ser_numerica():
    texto = corpo(enviar(payload(agencia="12-34")))
    assert "Número da agência deve conter apenas números" in texto


def test_valor_precisa_ser_maior_que_zero():
    texto = corpo(enviar(payload(valor="R$ 0,00")))
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_invalido():
    texto = corpo(enviar(payload(email="maria.ime.usp.br")))
    assert "E-mail inválido" in texto


def test_cpf_fora_do_formato():
    texto = corpo(enviar(payload(cpf="12345678909")))
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cep_fora_do_formato():
    texto = corpo(enviar(payload(cep="05508090")))
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_fora_do_formato():
    texto = corpo(enviar(payload(data_nascimento="1980-02-01")))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_cpf_com_digitos_verificadores_errados():
    texto = corpo(enviar(payload(cpf="123.456.789-00")))
    assert "CPF inválido" in texto


def test_data_inexistente():
    texto = corpo(enviar(payload(data_nascimento="31/02/1980")))
    assert "Data de nascimento inválida" in texto


def test_todos_os_erros_sao_mostrados():
    texto = corpo(
        enviar(
            payload(
                n_usp="abc",
                agencia="abc",
                valor="R$ 0,00",
                email="invalido",
                cpf="123.456.789-00",
                cep="123",
                data_nascimento="32/13/2020",
            )
        )
    )
    for mensagem in [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF inválido",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
    ]:
        assert mensagem in texto


def test_com_erro_o_oficio_nao_e_gerado():
    texto = corpo(enviar(payload(nome="")))
    assert "Encaminhe-se ao Serviço Financeiro" not in texto
