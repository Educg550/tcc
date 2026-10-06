import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

ROTAS = (
    "/solicitacao",
    "/solicitacoes",
    "/api/solicitacao",
    "/api/solicitacoes",
    "/solicitar",
)

DADOS = {
    "aba": "alunos",
    "nome_completo": "Maria Souza de Oliveira",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_de_auxilio": "Participação em evento",
    "email": "maria.oliveira@usp.br",
    "nome_do_evento": "Simpósio Brasileiro de Engenharia de Software",
    "periodo_do_evento": "10/09/2025 a 15/09/2025",
    "cidade_do_evento": "Fortaleza",
    "estado_do_evento": "Ceará",
    "pais_do_evento": "Brasil",
    "link_do_evento": "https://sbes.org.br/2025",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e inscrição no evento",
    "apresentacao": "Pôster",
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


def _post(payload):
    resposta = None
    for rota in ROTAS:
        resposta = client.post(rota, =payload)
        if resposta.status_code != 404:
            return resposta
    return resposta


def _texto(resposta):
    try:
        corpo = resposta.()
    except ValueError:
        return resposta.text

    def pedacos(valor):
        if isinstance(valor, str):
            return [valor]
        if isinstance(valor, dict):
            return [p for v in valor.values() for p in pedacos(v)]
        if isinstance(valor, (list, tuple)):
            return [p for item in valor for p in pedacos(item)]
        return [str(valor)]

    return "\n".join(pedacos(corpo))


def _alunos(**mudancas):
    payload = dict(DADOS)
    payload.update(mudancas)
    return _post(payload)


def _docentes(**mudancas):
    payload = {
        chave: valor
        for chave, valor in DADOS.items()
        if chave not in ("aba", "nivel", "tipo_de_auxilio")
    }
    payload["aba"] = "docentes"
    payload.update(mudancas)
    return _post(payload)


def test_solicitacao_valida_de_aluno_devolve_oficio_preenchido():
    texto = _texto(_alunos())
    for linha in [
        "Interessada(o): Maria Souza de Oliveira - 1234567",
        "E-mail: maria.oliveira@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Mestrado",
        "Evento: Simpósio Brasileiro de Engenharia de Software",
        "Período: 10/09/2025 a 15/09/2025",
        "Local: Fortaleza - Ceará - Brasil",
        "Link do evento: https://sbes.org.br/2025",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea e inscrição no evento",
        "Rua do Anfiteatro, 101",
        "Complemento: Sala 5",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 98765-4",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert linha in texto


def test_oficio_de_docente_nao_tem_nivel_nem_tipo_de_auxilio():
    texto = _texto(_docentes())
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Ciência da Computação - Mestrado" not in texto
    assert "Participação em evento" not in texto
    for linha in [
        "Interessada(o): Maria Souza de Oliveira - 1234567",
        "Valor solicitado: R$ 1.500,00",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert linha in texto


def test_campos_vazios_devolvem_aviso_unico():
    payload = {chave: "" for chave in DADOS}
    payload["aba"] = "alunos"
    texto = _texto(_post(payload))
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1
    assert "N. USP deve conter apenas números" not in texto


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("n_usp", "12a4567", "N. USP deve conter apenas números"),
        ("numero_da_agencia", "12a4", "Número da agência deve conter apenas números"),
        ("valor_solicitado", "R$ 0,00", "Valor solicitado deve ser maior que 0"),
        ("email", "maria.oliveira.usp.br", "E-mail inválido"),
        ("email", "maria.oliveira@", "E-mail inválido"),
        ("cpf", "12345678909", "CPF deve estar no formato 000.000.000-00"),
        ("cep", "05508090", "CEP deve estar no formato 00000-000"),
        (
            "data_de_nascimento",
            "01021980",
            "Data de nascimento deve estar no formato dd/mm/aaaa",
        ),
        ("cpf", "123.456.789-00", "CPF inválido"),
        ("data_de_nascimento", "31/02/1980", "Data de nascimento inválida"),
        ("data_de_nascimento", "05/13/1980", "Data de nascimento inválida"),
    ],
)
def test_mensagens_de_erro_exatas(campo, valor, mensagem):
    texto = _texto(_alunos(**{campo: valor}))
    assert mensagem in texto
    assert "Preencha todos os campos" not in texto


def test_todas_as_mensagens_aplicaveis_aparecem_juntas():
    texto = _texto(
        _alunos(
            n_usp="12a4567",
            email="maria.oliveira.usp.br",
            numero_da_agencia="12a4",
            cep="05508090",
            cpf="123.456.789-00",
        )
    )
    for mensagem in [
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "Número da agência deve conter apenas números",
        "CEP deve estar no formato 00000-000",
        "CPF inválido",
    ]:
        assert mensagem in texto


def test_campos_opcionais_vazios_saiem_do_oficio():
    texto = _texto(_alunos(link_do_evento="", complemento=""))
    assert "Link do evento" not in texto
    assert "Complemento" not in texto
    assert "Evento: Simpósio Brasileiro de Engenharia de Software" in texto
