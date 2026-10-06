ROTA = "/api/solicitacao"


def enviar(client, dados, **trocas):
    return client.post(ROTA, ={**dados, **trocas}).()


def test_campos_obrigatorios_vazios(client, dados_alunos):
    corpo = enviar(
        client,
        dados_alunos,
        **{"NOME COMPLETO - SEM ABREVIAR": "", "E-MAIL": "", "CEP": ""},
    )
    assert corpo.get("oficio") is None
    assert corpo["erros"] == ["Preencha todos os campos"]


def test_n_usp_aceita_apenas_digitos(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"N. USP": "12a4567"})
    assert corpo["erros"] == ["N. USP deve conter apenas números"]


def test_agencia_aceita_apenas_digitos(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"NÚMERO DA AGÊNCIA": "12a4"})
    assert corpo["erros"] == ["Número da agência deve conter apenas números"]


def test_valor_deve_ser_maior_que_zero(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"VALOR SOLICITADO (R$)": "R$ 0,00"})
    assert corpo["erros"] == ["Valor solicitado deve ser maior que 0"]


def test_email_sem_arroba_ou_sem_dominio(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"E-MAIL": "maria.usp.br"})
    assert corpo["erros"] == ["E-mail inválido"]
    corpo = enviar(client, dados_alunos, **{"E-MAIL": "maria@"})
    assert corpo["erros"] == ["E-mail inválido"]


def test_cpf_fora_do_formato(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})
    assert corpo["erros"] == ["CPF deve estar no formato 000.000.000-00"]


def test_cep_fora_do_formato(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"CEP": "0550809"})
    assert corpo["erros"] == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"DATA DE NASCIMENTO": "1/2/1980"})
    assert corpo["erros"] == ["Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_cpf_com_digito_verificador_incorreto(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})
    assert corpo["erros"] == ["CPF inválido"]


def test_data_de_nascimento_inexistente(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"DATA DE NASCIMENTO": "30/02/1980"})
    assert corpo["erros"] == ["Data de nascimento inválida"]
    corpo = enviar(client, dados_alunos, **{"DATA DE NASCIMENTO": "10/13/1980"})
    assert corpo["erros"] == ["Data de nascimento inválida"]


def test_todas_as_mensagens_que_se_aplicam_aparecem(client, dados_alunos):
    corpo = enviar(
        client,
        dados_alunos,
        **{"N. USP": "12a4567", "E-MAIL": "maria.usp.br", "CEP": "0550809"},
    )
    assert set(corpo["erros"]) == {
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CEP deve estar no formato 00000-000",
    }


def test_validacao_igual_na_aba_docentes(client, dados_docentes):
    corpo = enviar(client, dados_docentes, **{"CEP": "0550809"})
    assert corpo["erros"] == ["CEP deve estar no formato 00000-000"]


def test_com_erro_o_oficio_nao_e_gerado(client, dados_alunos):
    corpo = enviar(client, dados_alunos, **{"E-MAIL": "maria.usp.br"})
    assert corpo.get("oficio") is None
