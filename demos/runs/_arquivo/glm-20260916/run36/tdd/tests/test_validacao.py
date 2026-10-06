import pytest

from conftest import ALUNOS_VALIDOS, DOCENTES_VALIDOS, assert_erro, texto_normalizado


CASOS_DE_ERRO = [
    ("N. USP", "1234a567", "N. USP deve conter apenas números"),
    ("NÚMERO DA AGÊNCIA", "12a3", "Número da agência deve conter apenas números"),
    ("VALOR SOLICITADO (R$)", "R$ 0,00", "Valor solicitado deve ser maior que 0"),
    ("E-MAIL", "maria.silva.usp.br", "E-mail inválido"),
    ("E-MAIL", "maria@", "E-mail inválido"),
    (
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "12345678909",
        "CPF deve estar no formato 000.000.000-00",
    ),
    ("CEP", "05508090", "CEP deve estar no formato 00000-000"),
    (
        "DATA DE NASCIMENTO",
        "01021980",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ),
    ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "123.456.789-00", "CPF inválido"),
    ("DATA DE NASCIMENTO", "31/02/1990", "Data de nascimento inválida"),
    ("DATA DE NASCIMENTO", "13/13/1990", "Data de nascimento inválida"),
]


@pytest.mark.parametrize(("campo", "valor", "mensagem"), CASOS_DE_ERRO)
def test_erro_de_campo_invalido(enviar, campo, valor, mensagem):
    resposta = enviar({**ALUNOS_VALIDOS, campo: valor})
    assert_erro(resposta, [mensagem], ["Preencha todos os campos"])


def test_campos_vazios_geram_unica_mensagem_de_preenchimento(enviar):
    payload = {chave: "" for chave in ALUNOS_VALIDOS}
    texto = texto_normalizado(enviar(payload))
    assert texto.count("Preencha todos os campos") == 1
    assert "Interessada(o):" not in texto


def test_todas_as_mensagens_de_erro_aparecem_juntas(enviar):
    payload = {
        **ALUNOS_VALIDOS,
        "N. USP": "12a45",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00",
        "CEP": "05508090",
        "DATA DE NASCIMENTO": "31/02/1990",
    }
    assert_erro(
        enviar(payload),
        [
            "N. USP deve conter apenas números",
            "CPF inválido",
            "CEP deve estar no formato 00000-000",
            "Data de nascimento inválida",
        ],
        ["Preencha todos os campos"],
    )


def test_docentes_tem_a_mesma_validacao(enviar):
    resposta = enviar({**DOCENTES_VALIDOS, "N. USP": "abc123"})
    assert_erro(resposta, ["N. USP deve conter apenas números"], ["Preencha todos os campos"])
