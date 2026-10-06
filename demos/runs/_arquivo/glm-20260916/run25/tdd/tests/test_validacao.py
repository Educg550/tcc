def test_campo_obrigatorio_vazio_produz_mensagem_unica(solicitar):
    oficio, erros = solicitar(sem=("nome",))
    assert oficio is None
    assert erros is not None
    assert erros.count("Preencha todos os campos") == 1


def test_varios_obrigatorios_vazios_produzem_mensagem_unica(solicitar):
    oficio, erros = solicitar(sem=("nome", "logradouro", "cpf"))
    assert oficio is None
    assert erros is not None
    assert erros.count("Preencha todos os campos") == 1


def test_n_usp_deve_conter_apenas_numeros(solicitar):
    oficio, erros = solicitar(trocas={"nusp": "87a5432"})
    assert oficio is None
    assert erros is not None
    assert "N. USP deve conter apenas números" in erros


def test_agencia_deve_conter_apenas_numeros(solicitar):
    oficio, erros = solicitar(trocas={"agencia": "12a4"})
    assert oficio is None
    assert erros is not None
    assert "Número da agência deve conter apenas números" in erros


def test_valor_solicitado_deve_ser_maior_que_zero(solicitar, estilo_solicitacao):
    zero = 0 if estilo_solicitacao() == "numerico" else "R$ 0,00"
    oficio, erros = solicitar(trocas={"valor": zero})
    assert oficio is None
    assert erros is not None
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_sem_arroba_e_invalido(solicitar):
    oficio, erros = solicitar(trocas={"email": "maria.souza"})
    assert oficio is None
    assert erros is not None
    assert "E-mail inválido" in erros


def test_email_sem_dominio_e_invalido(solicitar):
    oficio, erros = solicitar(trocas={"email": "maria.souza@"})
    assert oficio is None
    assert erros is not None
    assert "E-mail inválido" in erros


def test_cep_fora_do_formato(solicitar):
    oficio, erros = solicitar(trocas={"cep": "0550809"})
    assert oficio is None
    assert erros is not None
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_fora_do_formato(solicitar):
    oficio, erros = solicitar(trocas={"nascimento": "1990-02-01"})
    assert oficio is None
    assert erros is not None
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_data_inexistente(solicitar):
    oficio, erros = solicitar(trocas={"nascimento": "31/02/1990"})
    assert oficio is None
    assert erros == ["Data de nascimento inválida"]


def test_cpf_fora_do_formato(solicitar):
    oficio, erros = solicitar(trocas={"cpf": "11144477735"})
    assert oficio is None
    assert erros is not None
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cpf_com_digito_verificador_invalido(solicitar):
    oficio, erros = solicitar(trocas={"cpf": "123.456.789-00"})
    assert oficio is None
    assert erros == ["CPF inválido"]


def test_varios_erros_aparecem_juntos(solicitar):
    oficio, erros = solicitar(
        trocas={
            "nusp": "87a5432",
            "cep": "0550809",
            "email": "maria.souza",
        }
    )
    assert oficio is None
    assert erros is not None
    for mensagem in (
        "N. USP deve conter apenas números",
        "CEP deve estar no formato 00000-000",
        "E-mail inválido",
    ):
        assert mensagem in erros


def test_campo_vazio_e_erro_especifico_convivem(solicitar):
    oficio, erros = solicitar(sem=("nome",), trocas={"nusp": "87a5432"})
    assert oficio is None
    assert erros is not None
    assert erros.count("Preencha todos os campos") == 1
    assert "N. USP deve conter apenas números" in erros
