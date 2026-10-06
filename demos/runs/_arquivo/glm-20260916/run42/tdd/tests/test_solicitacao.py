import pytest

MENSAGENS_DE_ERRO = [
    "Preencha todos os campos",
    "N. USP deve conter apenas números",
    "Número da agência deve conter apenas números",
    "Valor solicitado deve ser maior que 0",
    "E-mail inválido",
    "CPF deve estar no formato 000.000.000-00",
    "CEP deve estar no formato 00000-000",
    "Data de nascimento deve estar no formato dd/mm/aaaa",
    "CPF inválido",
    "Data de nascimento inválida",
]

CASOS_DE_ERRO = [
    ("N. USP", "12a4567", "N. USP deve conter apenas números", None),
    ("NÚMERO DA AGÊNCIA", "12a4", "Número da agência deve conter apenas números", None),
    ("E-MAIL", "maria.usp.br", "E-mail inválido", None),
    ("E-MAIL", "maria@", "E-mail inválido", None),
    ("CEP", "5508090", "CEP deve estar no formato 00000-000", None),
    (
        "DATA DE NASCIMENTO",
        "010280",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        None,
    ),
    (
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "123.456.7890",
        "CPF deve estar no formato 000.000.000-00",
        "CPF inválido",
    ),
    (
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "123.456.789-00",
        "CPF inválido",
        "CPF deve estar no formato 000.000.000-00",
    ),
    (
        "DATA DE NASCIMENTO",
        "31/02/1980",
        "Data de nascimento inválida",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ),
    ("DATA DE NASCIMENTO", "15/13/1980", "Data de nascimento inválida", None),
]


def test_solicitacao_valida_devolve_oficio_preenchido(payload, enviar, canal):
    texto = enviar(payload(**{"VALOR SOLICITADO (R$)": canal.valor}))
    assert "Interessada(o): Maria Silva - 1234567" in texto
    assert "E-mail: maria@usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "A CCP-Ciência da Computação aprovou" in texto
    assert "Evento: SBBD" in texto
    assert "Período: 1 a 4 de outubro de 2025" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://sbbd.org.br" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e inscrição" in texto
    assert "Rua do Anfiteatro, 123" in texto
    assert "Complemento: Sala 5" in texto
    assert "CEP: 05508-090" in texto
    assert "Cidade Universitária, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
    assert "<<" not in texto
    assert ">>" not in texto
    for mensagem in MENSAGENS_DE_ERRO:
        assert mensagem not in texto


def test_oficio_da_aba_docentes(payload, enviar):
    texto = enviar(payload(**{"NÍVEL": None, "TIPO DE AUXÍLIO": None}))
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação - Mestrado" not in texto
    assert "Interessada(o): Maria Silva - 1234567" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_opcionais_vazios_saem_do_oficio(payload, enviar):
    texto = enviar(payload(**{"LINK DO EVENTO, EXAME OU DEFESA": "", "COMPLEMENTO": ""}))
    assert "Link do evento" not in texto
    assert "Complemento" not in texto
    assert "Preencha todos os campos" not in texto
    assert "Interessada(o): Maria Silva - 1234567" in texto


def test_opcionais_ausentes_saem_do_oficio(payload, enviar):
    texto = enviar(payload(**{"LINK DO EVENTO, EXAME OU DEFESA": None, "COMPLEMENTO": None}))
    assert "Link do evento" not in texto
    assert "Complemento" not in texto


@pytest.mark.parametrize("campo,valor,mensagem,outra", CASOS_DE_ERRO)
def test_mensagens_de_erro(payload, enviar, campo, valor, mensagem, outra):
    texto = enviar(payload(**{campo: valor}))
    assert mensagem in texto
    if outra:
        assert outra not in texto
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


def test_valor_solicitado_zero_e_recusado(payload, enviar, canal):
    valor = "0" if canal.valor == "150000" else "R$ 0,00"
    texto = enviar(payload(**{"VALOR SOLICITADO (R$)": valor}))
    assert "Valor solicitado deve ser maior que 0" in texto
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


def test_campo_obrigatorio_vazio_mensagem_unica(payload, enviar):
    texto = enviar(payload(**{"LOGRADOURO": ""}))
    assert texto.count("Preencha todos os campos") == 1
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


def test_campo_obrigatorio_ausente(payload, enviar):
    texto = enviar(payload(**{"NOME DO BANCO": None}))
    assert "Preencha todos os campos" in texto
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


def test_varias_mensagens_de_erro_juntas(payload, enviar):
    texto = enviar(
        payload(
            **{
                "N. USP": "abc",
                "E-MAIL": "sem arroba",
                "NÚMERO DA AGÊNCIA": "x1",
            }
        )
    )
    assert "N. USP deve conter apenas números" in texto
    assert "E-mail inválido" in texto
    assert "Número da agência deve conter apenas números" in texto


def test_confirmacao_tem_titulo(html, js, payload, enviar):
    corpo = html + js + enviar(payload())
    assert "Solicitação registrada" in corpo
