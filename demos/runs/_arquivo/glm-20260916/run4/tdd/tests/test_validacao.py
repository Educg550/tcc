import pytest

OBRIGATORIO = "Preencha todos os campos"


def test_campo_obrigatorio_vazio_mensagem_unica(enviar, texto, dados_aluno):
    dados_aluno["PROGRAMA"] = ""
    t = texto(enviar(dados_aluno))
    assert OBRIGATORIO in t
    assert t.count(OBRIGATORIO) == 1


def test_campo_obrigatorio_ausente(enviar, texto, dados_aluno):
    del dados_aluno["E-MAIL"]
    assert OBRIGATORIO in texto(enviar(dados_aluno))


def test_n_usp_aceita_apenas_digitos(enviar, texto, dados_aluno):
    dados_aluno["N. USP"] = "123A567"
    assert "N. USP deve conter apenas números" in texto(enviar(dados_aluno))


def test_agencia_aceita_apenas_digitos(enviar, texto, dados_aluno):
    dados_aluno["NÚMERO DA AGÊNCIA"] = "12A4"
    assert "Número da agência deve conter apenas números" in texto(enviar(dados_aluno))


@pytest.mark.parametrize("valor", ["0", "abc", "-100"])
def test_valor_solicitado_deve_ser_maior_que_zero(enviar, texto, dados_aluno, valor):
    dados_aluno["VALOR SOLICITADO (R$)"] = valor
    assert "Valor solicitado deve ser maior que 0" in texto(enviar(dados_aluno))


@pytest.mark.parametrize("email", ["maria.usp.br", "maria@"])
def test_email_invalido(enviar, texto, dados_aluno, email):
    dados_aluno["E-MAIL"] = email
    assert "E-mail inválido" in texto(enviar(dados_aluno))


def test_cpf_fora_do_formato(enviar, texto, dados_aluno):
    dados_aluno["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "12345678904"
    t = texto(enviar(dados_aluno))
    assert "CPF deve estar no formato 000.000.000-00" in t


def test_cep_fora_do_formato(enviar, texto, dados_aluno):
    dados_aluno["CEP"] = "05508090"
    assert "CEP deve estar no formato 00000-000" in texto(enviar(dados_aluno))


def test_data_fora_do_formato(enviar, texto, dados_aluno):
    dados_aluno["DATA DE NASCIMENTO"] = "01021980"
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto(
        enviar(dados_aluno)
    )


def test_cpf_com_digito_verificador_errado(enviar, texto, dados_aluno):
    dados_aluno["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123.456.789-00"
    assert "CPF inválido" in texto(enviar(dados_aluno))


@pytest.mark.parametrize("data", ["31/02/1980", "15/13/1980", "00/10/1980"])
def test_data_inexistente(enviar, texto, dados_aluno, data):
    dados_aluno["DATA DE NASCIMENTO"] = data
    assert "Data de nascimento inválida" in texto(enviar(dados_aluno))


def test_todas_as_mensagens_aplicaveis_aparecem(enviar, texto, dados_aluno):
    dados_aluno["N. USP"] = "12A4567"
    dados_aluno["E-MAIL"] = "maria@"
    dados_aluno["CEP"] = "1"
    dados_aluno["DATA DE NASCIMENTO"] = "31/02/1980"
    dados_aluno["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123.456.789-00"
    t = texto(enviar(dados_aluno))
    for mensagem in (
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
        "CPF inválido",
    ):
        assert mensagem in t


def test_com_erro_o_oficio_nao_e_gerado(enviar, texto, dados_aluno):
    dados_aluno["PROGRAMA"] = ""
    t = texto(enviar(dados_aluno))
    assert "Interessada(o): Maria da Silva" not in t


def test_validacao_vale_na_aba_docentes(enviar, texto, dados_docente):
    dados_docente["N. USP"] = "ABC"
    assert "N. USP deve conter apenas números" in texto(enviar(dados_docente))
