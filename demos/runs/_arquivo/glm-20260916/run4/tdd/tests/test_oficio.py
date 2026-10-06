import pytest

LINHAS_ALUNO = [
    "Interessada(o): Maria da Silva - 1234567",
    "E-mail: maria@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "Evento: SBBD 2025",
    "Período: 1 a 4 de outubro de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://sbbd.org.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Passagem aérea e inscrição no evento.",
    "Rua do Anfiteatro, 181",
    "Complemento: Sala 214",
    "CEP: 05508-090",
    "Cidade Universitária, São Paulo - SP",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-04",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 98765-4",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def test_oficio_do_aluno_vem_completo(enviar, texto, dados_aluno):
    resposta = enviar(dados_aluno)
    assert resposta.status_code in (200, 201)
    t = texto(resposta)
    faltando = [linha for linha in LINHAS_ALUNO if linha not in t]
    assert not faltando, f"linhas ausentes do ofício: {faltando}"
    assert "Preencha todos os campos" not in t
    assert "<<" not in t
    assert ">>" not in t


@pytest.mark.parametrize(
    ("digitos", "moeda"),
    [
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ],
)
def test_valor_solicitado_aparece_formatado(enviar, texto, dados_aluno, digitos, moeda):
    dados_aluno["VALOR SOLICITADO (R$)"] = digitos
    assert f"Valor solicitado: {moeda}" in texto(enviar(dados_aluno))


def test_oficio_do_docente(enviar, texto, dados_docente):
    t = texto(enviar(dados_docente))
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in t
    assert "Programa: Ciência da Computação" in t
    assert "Interessada(o): Maria da Silva - 1234567" in t
    assert "Encaminhe-se ao Serviço Financeiro para providências." in t


def test_oficio_do_docente_nao_tem_nivel_nem_tipo(enviar, texto, dados_docente):
    t = texto(enviar(dados_docente))
    assert "Ciência da Computação - Mestrado" not in t
    assert " - Participação em evento" not in t


def test_link_vazio_sai_do_oficio(enviar, texto, dados_aluno):
    dados_aluno["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    assert "Link do evento:" not in texto(enviar(dados_aluno))


def test_complemento_vazio_sai_do_oficio(enviar, texto, dados_aluno):
    dados_aluno["COMPLEMENTO"] = ""
    assert "Complemento:" not in texto(enviar(dados_aluno))
