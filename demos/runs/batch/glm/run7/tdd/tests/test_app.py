"""Testes do Requisito 01: formulário de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app import app

    return TestClient(app)


def _solicitante():
    return {
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de agosto de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com/congresso",
        "valor": "150000",
        "detalhamento": "Inscrição e hospedagem.",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "endereco_cidade": "São Paulo",
        "endereco_estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "98765-4",
    }


def _docente():
    dados = _solicitante()
    dados.update(
        {
            "tipo_auxilio": "Verba do programa",
            "evento": "Escola de Verão",
            "nivel": "",
            "apresentacao": "Não irá apresentar trabalho",
        }
    )
    return dados


def _enviar(client, aba, dados):
    return client.post(
        "/solicitar",
        data={"aba": aba, **dados},
        follow_redirects=False,
    )


def _marcadores(conteudo):
    return re.findall(r"<<[^>]*>>", conteudo)


# ---------------------------------------------------------------------------
# Página e arquivos estáticos
# ---------------------------------------------------------------------------


def test_pagina_cabecalho_duas_abas(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    pagina = resposta.text
    assert "ALUNOS" in pagina
    assert "DOCENTES" in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")
    assert "usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina


def test_arquivos_estaticos_existem(client):
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/assets/usp-logo.png").status_code == 200


def test_placeholder_nao_repete_rotulo(client):
    pagina = client.get("/").text
    rotulo = "VALOR SOLICITADO (R$)"
    m = re.search(rotulo + r"</label>\s*<input[^>]*placeholder=\"([^\"]*)\"", pagina)
    assert m, "VALOR SOLICITADO (R$) precisa de um placeholder que não seja o rótulo"
    assert m.group(1) != rotulo


# ---------------------------------------------------------------------------
# Formatação de campos no backend
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "digitado,mostrado",
    [
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ],
)
def test_formata_valor(client, digitado, mostrado):
    dados = _docente()
    dados["valor"] = digitado
    resposta = _enviar(client, "docentes", dados)
    assert resposta.context["oficio"].count("Valor solicitado: " + mostrado) == 1


def test_formata_cpf(client):
    dados = _docente()
    resposta = _enviar(client, "docentes", dados)
    assert "CPF: 123.456.789-09" in resposta.context["oficio"]


def test_formata_cep(client):
    dados = _docente()
    resposta = _enviar(client, "docentes", dados)
    assert "CEP: 05508-090" in resposta.context["oficio"]


def test_formata_data_nascimento(client):
    dados = _docente()
    resposta = _enviar(client, "docentes", dados)
    assert "Data de nascimento: 01/02/1980" in resposta.context["oficio"]


# ---------------------------------------------------------------------------
# Ofício - aba ALUNOS
# ---------------------------------------------------------------------------


def test_oficio_alunos(client):
    resposta = _enviar(client, "alunos", _solicitante())
    assert resposta.status_code == 200
    assert "erros" not in resposta.context
    oficio = resposta.context["oficio"]
    assert "<<" not in oficio
    assert ">>" not in oficio

    assert oficio.startswith(
        "Interessada(o): Maria da Silva - 12345678\n"
        "E-mail: maria@ime.usp.br\n"
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento\n"
        "Programa: Matemática - Mestrado\n"
    )
    assert (
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro "
        "para a interessada(o) acima, conforme segue:\n" in oficio
    )
    assert (
        "Evento: Congresso Nacional de Matemática\n"
        "Período: 10 a 12 de agosto de 2025\n"
        "Local: São Paulo - SP - Brasil\n"
        "Link do evento: https://exemplo.com/congresso\n"
        "Apresentação de trabalho: Apresentação oral\n"
        "Valor solicitado: R$ 1.500,00\n"
        "Detalhamento: Inscrição e hospedagem.\n" in oficio
    )
    assert (
        "Rua do Matão, 1010\n"
        "CEP: 05508-090\n"
        "Butantã, São Paulo - SP\n" in oficio
    )
    assert (
        "Banco: Banco do Brasil\n"
        "Agência: 1234\n"
        "Conta: 98765-4\n" in oficio
    )
    assert oficio.endswith("Encaminhe-se ao Serviço Financeiro para providências.")


def test_oficio_alunos_marcadores_todos_substituidos(client):
    resposta = _enviar(client, "alunos", _solicitante())
    assert _marcadores(resposta.context["oficio"]) == []


def test_oficio_docentes_sem_nivel_nem_tipo(client):
    resposta = _enviar(client, "docentes", _docente())
    assert resposta.status_code == 200
    assert "erros" not in resposta.context
    oficio = resposta.context["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa\n" in oficio
    assert "Programa: Matemática\n" in oficio
    assert "- Mestrado" not in oficio
    assert "- Doutorado" not in of oficio


def test_oficio_sem_link_tira_linha(client):
    dados = _solicitante()
    dados["link"] = ""
    resposta = _enviar(client, "alunos", dados)
    oficio = resposta.context["oficio"]
    assert "Link do evento" not in oficio


def test_oficio_sem_complemento_tira_linha(client):
    dados = _docente()
    resposta = _enviar(client, "docentes", dados)
    oficio = resposta.context["oficio"]
    assert "Complemento:" not in oficio


# ---------------------------------------------------------------------------
# Persistência de valores e aba ativa em erro
# ---------------------------------------------------------------------------


def test_erro_mantem_valores_e_aba(client):
    dados = _solicitante()
    dados["email"] = ""
    resposta = _enviar(client, "alunos", dados)
    assert resposta.status_code == 200
    assert resposta.context["aba"] == "alunos"
    assert resposta.context["valores"]["nome"] == "Maria da Silva"
    assert resposta.context["valores"]["evento"] == "Congresso Nacional de Matemática"
    assert resposta.context["valores"]["email"] == ""


def test_erro_docentes_mantem_aba_docentes(client):
    dados = _docente()
    dados["n_usp"] = ""
    resposta = _enviar(client, "docentes", dados)
    assert resposta.context["aba"] == "docentes"


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------


def test_campo_obrigatorio_vazio(client):
    dados = _solicitante()
    dados["nome"] = ""
    resposta = _enviar(client, "alunos", dados)
    assert resposta.context["erros"] == ["Preencha todos os campos"]
    assert "oficio" not in resposta.context


def test_campos_opcionais_nao_sao_obrigatorios(client):
    dados = _docente()
    resposta = _enviar(client, "docentes", dados)
    assert "erros" not in resposta.context


@pytest.mark.parametrize(
    "campo,valor,mensagem",
    [
        ("n_usp", "12a456", "N. USP deve conter apenas números"),
        ("agencia", "12-4", "Número da agência deve conter apenas números"),
        ("valor", "0", "Valor solicitado deve ser maior que 0"),
        ("valor", "-5", "Valor solicitado deve ser maior que 0"),
        ("valor", "12,5", "Valor solicitado deve ser maior que 0"),
        ("email", "mariaime.usp.br", "E-mail inválido"),
        ("email", "maria@", "E-mail inválido"),
        ("email", "@ime.usp.br", "E-mail inválido"),
        ("cpf", "1234567890", "CPF deve estar no formato 000.000.000-00"),
        ("cpf", "123.456.789-0X", "CPF deve estar no formato 000.000.000-00"),
        ("cep", "05508-09", "CEP deve estar no formato 00000-000"),
        ("cep", "0550809", "CEP deve estar no formato 00000-000"),
        ("cep", "05508-0900", "CEP deve estar no formato 00000-000"),
        ("data_nascimento", "32/02/1980", "Data de nascimento deve estar no formato dd/mm/aaaa"),
        ("data_nascimento", "0102198", "Data de nascimento deve estar no formato dd/mm/aaaa"),
        ("data_nascimento", "aa/bb/cccc", "Data de nascimento deve estar no formato dd/mm/aaaa"),
    ],
)
def test_erros_de_formato(client, campo, valor, mensagem):
    dados = _docente()
    dados[campo] = valor
    resposta = _enviar(client, "docentes", dados)
    assert mensagem in resposta.context["erros"]
    assert "oficio" not in resposta.context


@pytest.mark.parametrize(
    "cpf",
    [
        "11111111111",
        "12345678900",
        "12345678901",
        "52998224725",
    ],
)
def test_cpf_formato_certo_mas_invalido(client, cpf):
    dados = _docente()
    dados["cpf"] = cpf
    resposta = _enviar(client, "docentes", dados)
    assert "CPF inválido" in resposta.context["erros"]


@pytest.mark.parametrize(
    "cpf",
    [
        "12345678909",
        "52998224725",
        "11144477735",
    ],
)
def test_cpf_formato_certo_e_valido(client, cpf):
    dados = _docente()
    dados["cpf"] = cpf
    resposta = _enviar(client, "docentes", dados)
    assert "CPF inválido" not in resposta.context.get("erros", [])
    assert "CPF deve estar no formato 000.000.000-00" not in resposta.context.get("erros", [])


@pytest.mark.parametrize(
    "data",
    [
        "31022020",
        "32011980",
        "01131980",
        "00111980",
    ],
)
def test_data_formato_certo_mas_inexistente(client, data):
    dados = _docente()
    dados["data_nascimento"] = data
    resposta = _enviar(client, "docentes", dados)
    assert "Data de nascimento inválida" in resposta.context["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in resposta.context["erros"]


def test_data_valida_aceita(client):
    dados = _docente()
    dados["data_nascimento"] = "29022020"
    resposta = _enviar(client, "docentes", dados)
    assert resposta.context.get("erros", []) == []
    assert "Data de nascimento: 29/02/2020" in resposta.context["oficio"]


def test_todos_os_erros_juntos(client):
    resposta = _enviar(
        client,
        "alunos",
        {
            "nome": "",
            "n_usp": "12a456",
            "programa": "Matemática",
            "nivel": "Mestrado",
            "tipo_auxilio": "Participação em evento",
            "email": "mariaime.usp.br",
            "evento": "Congresso",
            "periodo": "agosto",
            "cidade": "São Paulo",
            "estado": "SP",
            "pais": "Brasil",
            "link": "",
            "valor": "0",
            "detalhamento": "Inscrição.",
            "apresentacao": "Pôster",
            "data_nascimento": "31021980",
            "logradouro": "Rua do Matão",
            "numero": "1010",
            "complemento": "",
            "bairro": "Butantã",
            "cep": "05508-09",
            "endereco_cidade": "São Paulo",
            "endereco_estado": "SP",
            "cpf": "1234567890",
            "rg": "12.345.678-9",
            "banco": "Banco do Brasil",
            "agencia": "12-4",
            "conta": "98765-4",
        },
    )
    erros = resposta.context["erros"]
    assert erros == [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "Número da agência deve conter apenas números",
    ]


def test_validacao_igual_nas_duas_abas(client):
    for aba, dados in (("alunos", _solicitante()), ("docentes", _docente())):
        dados["email"] = "mariaime.usp.br"
        resposta = _enviar(client, aba, dados)
        assert "E-mail inválido" in resposta.context["erros"]
