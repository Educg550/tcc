ROTA = "/solicitacao"


def _erros(client, form):
    resposta = client.post(ROTA, json=form)
    dados = resposta.json()
    assert "oficio" not in dados
    return dados["erros"]


def test_dois_campos_vazios_uma_unica_mensagem(client, form_alunos):
    form_alunos["nome"] = ""
    form_alunos["logradouro"] = ""
    assert _erros(client, form_alunos) == ["Preencha todos os campos"]


def test_selecao_obrigatoria_vazia(client, form_alunos):
    form_alunos["nivel"] = ""
    assert _erros(client, form_alunos) == ["Preencha todos os campos"]


def test_n_usp_com_pontuacao(client, form_alunos):
    form_alunos["n_usp"] = "12.345"
    assert _erros(client, form_alunos) == ["N. USP deve conter apenas números"]


def test_agencia_com_letras(client, form_alunos):
    form_alunos["agencia"] = "12a4"
    assert _erros(client, form_alunos) == [
        "Número da agência deve conter apenas números"
    ]


def test_valor_zero(client, form_alunos):
    form_alunos["valor"] = "R$ 0,00"
    assert _erros(client, form_alunos) == ["Valor solicitado deve ser maior que 0"]


def test_valor_nao_numerico(client, form_alunos):
    form_alunos["valor"] = "abc"
    assert _erros(client, form_alunos) == ["Valor solicitado deve ser maior que 0"]


def test_email_sem_arroba(client, form_alunos):
    form_alunos["email"] = "maria.ime.usp.br"
    assert _erros(client, form_alunos) == ["E-mail inválido"]


def test_email_sem_dominio(client, form_alunos):
    form_alunos["email"] = "maria@"
    assert _erros(client, form_alunos) == ["E-mail inválido"]


def test_cpf_sem_pontuacao(client, form_alunos):
    form_alunos["cpf"] = "12345678909"
    assert _erros(client, form_alunos) == [
        "CPF deve estar no formato 000.000.000-00"
    ]


def test_cpf_com_digitos_verificadores_errados(client, form_alunos):
    form_alunos["cpf"] = "123.456.789-00"
    assert _erros(client, form_alunos) == ["CPF inválido"]


def test_cep_sem_hifen(client, form_alunos):
    form_alunos["cep"] = "05508090"
    assert _erros(client, form_alunos) == ["CEP deve estar no formato 00000-000"]


def test_data_sem_barras(client, form_alunos):
    form_alunos["data_nascimento"] = "01021980"
    assert _erros(client, form_alunos) == [
        "Data de nascimento deve estar no formato dd/mm/aaaa"
    ]


def test_data_de_fevereiro_com_31_dias(client, form_alunos):
    form_alunos["data_nascimento"] = "31/02/2020"
    assert _erros(client, form_alunos) == ["Data de nascimento inválida"]


def test_data_com_mes_inexistente(client, form_alunos):
    form_alunos["data_nascimento"] = "01/13/1980"
    assert _erros(client, form_alunos) == ["Data de nascimento inválida"]


def test_todos_os_erros_de_uma_vez(client, form_alunos):
    form_alunos.update(
        {
            "nome": "",
            "n_usp": "12a3456",
            "email": "maria.ime.usp.br",
            "valor": "abc",
            "agencia": "12a",
            "cpf": "12345678909",
            "cep": "0550890",
            "data_nascimento": "01021980",
        }
    )
    esperados = sorted(
        [
            "Preencha todos os campos",
            "N. USP deve conter apenas números",
            "Número da agência deve conter apenas números",
            "Valor solicitado deve ser maior que 0",
            "E-mail inválido",
            "CPF deve estar no formato 000.000.000-00",
            "CEP deve estar no formato 00000-000",
            "Data de nascimento deve estar no formato dd/mm/aaaa",
        ]
    )
    assert sorted(_erros(client, form_alunos)) == esperados


def test_validacao_igual_na_aba_docentes(client, form_docentes):
    form_docentes["cpf"] = "123.456.789-00"
    assert _erros(client, form_docentes) == ["CPF inválido"]
