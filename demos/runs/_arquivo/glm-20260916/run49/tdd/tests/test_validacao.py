def enviar(client, base, **mudancas):
    resposta = client.post("/solicitacao", ={**base, **mudancas})
    assert resposta.status_code == 200
    corpo = resposta.()
    assert corpo["valido"] is False
    assert not corpo.get("oficio")
    return corpo["erros"]


def test_campos_obrigatorios_vazios_geram_uma_mensagem_so(client, dados_alunos):
    vazios = {campo: "" for campo in dados_alunos}
    vazios["aba"] = "alunos"
    erros = enviar(client, vazios)
    assert erros == ["Preencha todos os campos"]


def test_n_usp_deve_conter_so_numeros(client, dados_alunos):
    erros = enviar(client, dados_alunos, n_usp="1234a67")
    assert erros == ["N. USP deve conter apenas números"]


def test_agencia_deve_conter_so_numeros(client, dados_alunos):
    erros = enviar(client, dados_alunos, numero_agencia="12a4")
    assert erros == ["Número da agência deve conter apenas números"]


def test_valor_solicitado_deve_ser_maior_que_zero(client, dados_alunos):
    for valor in ("0", "abc"):
        erros = enviar(client, dados_alunos, valor_solicitado=valor)
        assert erros == ["Valor solicitado deve ser maior que 0"]


def test_email_sem_arroba_ou_sem_dominio(client, dados_alunos):
    for email in ("maria.usp.br", "maria@"):
        erros = enviar(client, dados_alunos, email=email)
        assert erros == ["E-mail inválido"]


def test_cpf_fora_do_formato(client, dados_alunos):
    erros = enviar(client, dados_alunos, cpf="52998224725")
    assert erros == ["CPF deve estar no formato 000.000.000-00"]


def test_cep_fora_do_formato(client, dados_alunos):
    erros = enviar(client, dados_alunos, cep="05508090")
    assert erros == ["CEP deve estar no formato 00000-000"]


def test_data_fora_do_formato(client, dados_alunos):
    erros = enviar(client, dados_alunos, data_nascimento="01021980")
    assert erros == ["Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_cpf_com_digitos_verificadores_errados(client, dados_alunos):
    erros = enviar(client, dados_alunos, cpf="123.456.789-09")
    assert erros == ["CPF inválido"]


def test_data_com_dia_inexistente(client, dados_alunos):
    erros = enviar(client, dados_alunos, data_nascimento="31/02/1980")
    assert erros == ["Data de nascimento inválida"]


def test_data_com_mes_inexistente(client, dados_alunos):
    erros = enviar(client, dados_alunos, data_nascimento="15/13/1980")
    assert erros == ["Data de nascimento inválida"]


def test_todas_as_mensagens_aplicaveis_aparecem(client, dados_alunos):
    erros = enviar(
        client,
        dados_alunos,
        nome_completo="",
        n_usp="12a",
        email="maria.usp.br",
        cpf="52998224725",
        cep="05508090",
    )
    assert sorted(erros) == sorted(
        [
            "Preencha todos os campos",
            "N. USP deve conter apenas números",
            "E-mail inválido",
            "CPF deve estar no formato 000.000.000-00",
            "CEP deve estar no formato 00000-000",
        ]
    )
    assert erros.count("Preencha todos os campos") == 1


def test_validacao_igual_na_aba_docentes(client, dados_docentes):
    erros = enviar(client, dados_docentes, n_usp="12a", email="joao.usp.br")
    assert sorted(erros) == sorted(
        ["N. USP deve conter apenas números", "E-mail inválido"]
    )
