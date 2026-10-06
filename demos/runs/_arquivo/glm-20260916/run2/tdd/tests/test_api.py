import html
import re

import pytest

CANDIDATOS_DE_ENDPOINT = (
    "/api/solicitacao",
    "/solicitacao",
    "/solicitar",
    "/api/solicitar",
    "/submit",
)

SEQUENCIAS_ESCAPADAS = (chr(92) + "r", chr(92) + "n", chr(92) + "t")


def normaliza(texto):
    for sequencia in SEQUENCIAS_ESCAPADAS:
        texto = texto.replace(sequencia, " ")
    texto = html.unescape(texto)
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto)


def _candidatos_do_js(js):
    urls = re.findall(r'''['"`](/[^'"`\s]*)['"`]''', js)
    return [
        url
        for url in urls
        if len(url) > 1
        and not url.endswith("/")
        and not url.startswith("/assets")
        and "." not in url.rsplit("/", 1)[-1]
    ]


@pytest.fixture(scope="session")
def endpoint(client, buscar):
    js = buscar("/app.js")
    if js is not None:
        direto = re.search(r'''fetch\(\s*['"`]([^'"`\s]+)['"`]''', js.text)
        if direto:
            url = direto.group(1)
            return url if url.startswith("/") else "/" + url
        candidatos = _candidatos_do_js(js.text) + list(CANDIDATOS_DE_ENDPOINT)
    else:
        candidatos = list(CANDIDATOS_DE_ENDPOINT)
    for candidato in candidatos:
        if client.post(candidato, ={}).status_code not in (404, 405):
            return candidato
    return CANDIDATOS_DE_ENDPOINT[0]


def enviar(client, endpoint, buscar, dados):
    js = buscar("/app.js")
    if js is not None and "FormData" in js.text:
        return client.post(endpoint, data=dados)
    return client.post(endpoint, =dados)


def carga_base():
    return {
        "aba": "alunos",
        "nome_completo": "Maria Souza da Silva",
        "n_usp": "1234567",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria.souza@usp.br",
        "nome_do_evento": "Congresso Brasileiro de Computação",
        "periodo_do_evento": "1 a 5 de julho de 2025",
        "cidade_do_evento": "São Paulo",
        "estado_do_evento": "SP",
        "pais_do_evento": "Brasil",
        "link_do_evento": "https://congresso.example.org",
        "valor_solicitado": "150000",
        "detalhamento_do_pedido": "Passagem aérea e inscrição no evento",
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


def carga(**substituicoes):
    dados = carga_base()
    dados.update(substituicoes)
    return dados


TRECHOS_DO_OFICIO = [
    "Dados do evento",
    "Interessada(o): Maria Souza da Silva - 1234567",
    "E-mail: maria.souza@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro",
    "Evento: Congresso Brasileiro de Computação",
    "Período: 1 a 5 de julho de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://congresso.example.org",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Passagem aérea e inscrição no evento",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 101",
    "Complemento: Sala 5",
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


def test_envio_valido_de_alunos_gera_oficio(client, endpoint, buscar):
    resposta = enviar(client, endpoint, buscar, carga())
    assert resposta.status_code == 200
    corpo = normaliza(resposta.text)
    for trecho in TRECHOS_DO_OFICIO:
        assert trecho in corpo, trecho
    assert "Verba do programa" not in corpo


def test_valor_solicitado_formatado_como_moeda(client, endpoint, buscar):
    resposta = enviar(client, endpoint, buscar, carga(valor_solicitado="1500"))
    assert "Valor solicitado: R$ 15,00" in normaliza(resposta.text)
    resposta = enviar(client, endpoint, buscar, carga(valor_solicitado="150000000"))
    assert "Valor solicitado: R$ 1.500.000,00" in normaliza(resposta.text)


def test_envio_valido_de_docentes_gera_oficio(client, endpoint, buscar):
    dados = carga(aba="docentes")
    del dados["nivel"]
    del dados["tipo_de_auxilio"]
    resposta = enviar(client, endpoint, buscar, dados)
    assert resposta.status_code == 200
    corpo = normaliza(resposta.text)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in corpo
    assert "Programa: Ciência da Computação" in corpo
    assert "Mestrado" not in corpo
    assert "Interessada(o): Maria Souza da Silva - 1234567" in corpo


@pytest.mark.parametrize("aba", ["alunos", "docentes"])
def test_campos_obrigatorios_vazios(client, endpoint, buscar, aba):
    resposta = enviar(client, endpoint, buscar, {"aba": aba})
    corpo = normaliza(resposta.text)
    assert "Preencha todos os campos" in corpo
    assert corpo.count("Preencha todos os campos") == 1
    assert "Interessada(o):" not in corpo


def test_todas_as_mensagens_de_erro_juntas(client, endpoint, buscar):
    resposta = enviar(
        client,
        endpoint,
        buscar,
        carga(
            n_usp="123a5",
            email="maria.souza_usp.br",
            cpf="12345678909",
            cep="05508090",
            data_de_nascimento="01021980",
            numero_da_agencia="12a4",
            valor_solicitado="0",
        ),
    )
    corpo = normaliza(resposta.text)
    for mensagem in [
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
    ]:
        assert mensagem in corpo, mensagem
    assert "Preencha todos os campos" not in corpo
    assert "CPF inválido" not in corpo
    assert "Data de nascimento inválida" not in corpo
    assert "Interessada(o):" not in corpo


def test_cpf_com_digitos_verificadores_incorretos(client, endpoint, buscar):
    resposta = enviar(client, endpoint, buscar, carga(cpf="123.456.789-00"))
    corpo = normaliza(resposta.text)
    assert "CPF inválido" in corpo
    assert "CPF deve estar no formato 000.000.000-00" not in corpo
    assert "Interessada(o):" not in corpo


@pytest.mark.parametrize("data_invalida", ["31/02/1980", "01/13/1980"])
def test_data_de_nascimento_inexistente(client, endpoint, buscar, data_invalida):
    resposta = enviar(client, endpoint, buscar, carga(data_de_nascimento=data_invalida))
    corpo = normaliza(resposta.text)
    assert "Data de nascimento inválida" in corpo
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in corpo
    assert "Interessada(o):" not in corpo


@pytest.mark.parametrize("email_invalido", ["maria.souza_usp.br", "maria@"])
def test_email_invalido(client, endpoint, buscar, email_invalido):
    resposta = enviar(client, endpoint, buscar, carga(email=email_invalido))
    corpo = normaliza(resposta.text)
    assert "E-mail inválido" in corpo
    assert "Interessada(o):" not in corpo


def test_campos_opcionais_vazios_saem_do_oficio(client, endpoint, buscar):
    resposta = enviar(client, endpoint, buscar, carga(link_do_evento="", complemento=""))
    assert resposta.status_code == 200
    corpo = normaliza(resposta.text)
    assert "Link do evento" not in corpo
    assert "Complemento" not in corpo
