import pytest

from tests.test_validacao import ALUNOS, DOCENTES, _post


def _oficio(client, dados):
    corpo = _post(client, dados).json()
    assert "erros" not in corpo
    return corpo["oficio"]


@pytest.mark.parametrize("dados", [ALUNOS, DOCENTES], ids=["alunos", "docentes"])
def test_sem_marcadores(client, dados):
    oficio = _oficio(client, dados)
    assert "<<" not in oficio


def test_dados_alunos(client):
    oficio = _oficio(client, ALUNOS)
    for esperado in (
        "Interessada(o): Ana Souza - 1234567",
        "E-mail: ana@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Mestrado",
        "A CCP-Ciência da Computação aprovou na data de hoje",
        "Evento: SBIE 2025",
        "Período: 01/09/2025 a 05/09/2025",
        "Local: Fortaleza - CE - Brasil",
        "Link do evento: https://sbie.org",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Custo de inscrição",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "Complemento: Apto 2",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-0",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ):
        assert esperado in oficio


def test_oficio_docentes(client):
    oficio = _oficio(client, DOCENTES)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio
    assert "Mestrado" not in oficio
    assert "Participação em evento" not in oficio

@pytest.mark.parametrize("campo,linha", [
    ("LINK DO EVENTO, EXAME OU DEFESA", "Link do evento:"),
    ("COMPLEMENTO", "Complemento:"),
])
def test_linha_omitida_quando_vazia(client, campo, linha):
    oficio = _oficio(client, {**ALUNOS, campo: ""})
    assert linha not in oficio
