import pytest
from fastapi.testclient import TestClient

from app import app

CLIENTE = TestClient(app)

VALORES = {
    "nome_completo": "Maria da Silva Santos",
    "nome_do_evento": "Congresso Brasileiro de Computação",
    "nome_do_banco": "Banco do Brasil",
    "cidade_do_evento": "São Paulo",
    "estado_do_evento": "SP",
    "pais_do_evento": "Brasil",
    "pais": "Brasil",
    "periodo_do_evento": "01/03/2025 a 05/03/2025",
    "periodo": "01/03/2025 a 05/03/2025",
    "valor_solicitado": "R$ 1.500,00",
    "valor": "R$ 1.500,00",
    "detalhamento": "Passagem aérea",
    "link_do_evento": "https://evento.exemplo.com",
    "link": "https://evento.exemplo.com",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "e_mail": "maria@ime.usp.br",
    "apresentar": "Pôster",
    "apresentacao": "Pôster",
    "data_de_nascimento": "01/02/1980",
    "data_nascimento": "01/02/1980",
    "nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero_da_agencia": "1234",
    "numero_da_conta": "12345-6",
    "numero": "1010",
    "complemento": "Bloco A",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
    "cidade": "São Paulo",
    "estado": "SP",
    "evento": "Congresso Brasileiro de Computação",
}

ALIASES = {
    "nome": ("nome_completo", "nome"),
    "usp": ("usp",),
    "agencia": ("agencia",),
    "valor": ("valor",),
    "email": ("email", "mail"),
    "cpf": ("cpf",),
    "cep": ("cep",),
    "nascimento": ("nascimento",),
    "link": ("link",),
    "complemento": ("complemento",),
}


def _rota():
    spec = CLIENTE.get("/openapi.json").json()
    for caminho, operacoes in spec["paths"].items():
        corpo = operacoes.get("post", {}).get("requestBody", {}).get("content")
        if not corpo:
            continue
        tipo = next(iter(corpo))
        esquema = corpo[tipo]["schema"]
        if "$ref" in esquema:
            esquema = spec["components"]["schemas"][esquema["$ref"].rsplit("/", 1)[-1]]
        return caminho, tipo, list(esquema.get("properties", {}).items())
    pytest.fail("a aplicação não expõe rota POST para a solicitação")


def _valor(campo, esquema):
    for parte in [esquema] + esquema.get("anyOf", []) + esquema.get("allOf", []):
        if "enum" in parte:
            return parte["enum"][0]
    candidatos = [chave for chave in VALORES if chave in campo.lower()]
    if not candidatos:
        return "x"
    return VALORES[max(candidatos, key=len)]


def _campo(campos, termos):
    for termo in termos:
        for campo in campos:
            if termo in campo.lower():
                return campo
    return None


def solicitar(**alteracoes):
    caminho, tipo, propriedades = _rota()
    corpo = {campo: _valor(campo, esquema) for campo, esquema in propriedades}
    for chave, valor in alteracoes.items():
        campo = _campo([nome for nome, _ in propriedades], ALIASES[chave])
        assert campo, f"campo '{chave}' não encontrado em {[n for n, _ in propriedades]}"
        corpo[campo] = valor
    if "json" in tipo:
        resposta = CLIENTE.post(caminho, json=corpo)
    else:
        resposta = CLIENTE.post(caminho, data=corpo)
    assert resposta.status_code == 200, resposta.text
    return resposta.text


def test_campo_obrigatorio_vazio():
    assert "Preencha todos os campos" in solicitar(nome="")


def test_n_usp_apenas_numeros():
    assert "N. USP deve conter apenas números" in solicitar(usp="12a456")


def test_agencia_apenas_numeros():
    assert "Número da agência deve conter apenas números" in solicitar(agencia="12a4")


def test_valor_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in solicitar(valor="0")


def test_email_invalido():
    assert "E-mail inválido" in solicitar(email="maria.ime.usp.br")


def test_cpf_fora_do_formato():
    assert "CPF deve estar no formato 000.000.000-00" in solicitar(cpf="12345678909")


def test_cpf_com_digitos_verificadores_invalidos():
    assert "CPF inválido" in solicitar(cpf="111.111.111-11")


def test_cep_fora_do_formato():
    assert "CEP deve estar no formato 00000-000" in solicitar(cep="05508090")


def test_data_fora_do_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in solicitar(nascimento="01021980")


def test_data_inexistente():
    assert "Data de nascimento inválida" in solicitar(nascimento="31/02/1980")


def test_envio_valido_gera_o_oficio():
    texto = solicitar()
    assert "Interessada(o): Maria da Silva Santos - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Dados do evento" in texto
    assert "Dados para pagamento" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_link_e_complemento_vazios_saem_do_oficio():
    texto = solicitar(link="", complemento="")
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto
