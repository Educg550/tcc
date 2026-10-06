def test_envio_sem_nada_exige_preenchimento_uma_unica_vez(enviar_alunos, rotulos_alunos):
    texto = enviar_alunos({rotulo: "" for rotulo in rotulos_alunos})
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1
    assert "Encaminhe-se" not in texto


def test_n_usp_com_letras_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"N. USP": "1234a67"})
    assert "N. USP deve conter apenas números" in texto
    assert "Encaminhe-se" not in texto


def test_agencia_com_letras_e_rejeitada(enviar_alunos):
    texto = enviar_alunos({"NÚMERO DA AGÊNCIA": "12a4"})
    assert "Número da agência deve conter apenas números" in texto
    assert "Encaminhe-se" not in texto


def test_valor_zero_e_rejeitado(enviar_alunos, valor_zero):
    texto = enviar_alunos({"VALOR SOLICITADO (R$)": valor_zero})
    assert "Valor solicitado deve ser maior que 0" in texto
    assert "Encaminhe-se" not in texto


def test_email_sem_arroba_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"E-MAIL": "maria.usp.br"})
    assert "E-mail inválido" in texto
    assert "Encaminhe-se" not in texto


def test_email_sem_dominio_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"E-MAIL": "maria@"})
    assert "E-mail inválido" in texto
    assert "Encaminhe-se" not in texto


def test_cpf_fora_do_formato_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})
    assert "CPF deve estar no formato 000.000.000-00" in texto
    assert "Encaminhe-se" not in texto


def test_cpf_com_digito_verificador_errado_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})
    assert "CPF inválido" in texto
    assert "CPF deve estar no formato 000.000.000-00" not in texto
    assert "Encaminhe-se" not in texto


def test_cep_fora_do_formato_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"CEP": "05508090"})
    assert "CEP deve estar no formato 00000-000" in texto
    assert "Encaminhe-se" not in texto


def test_data_sem_formato_e_rejeitada(enviar_alunos):
    texto = enviar_alunos({"DATA DE NASCIMENTO": "01021980"})
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto
    assert "Encaminhe-se" not in texto


def test_data_que_nao_existe_e_rejeitada(enviar_alunos):
    texto = enviar_alunos({"DATA DE NASCIMENTO": "31/02/1980"})
    assert "Data de nascimento inválida" in texto
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in texto
    assert "Encaminhe-se" not in texto


def test_mes_fora_do_intervalo_e_rejeitado(enviar_alunos):
    texto = enviar_alunos({"DATA DE NASCIMENTO": "15/13/1980"})
    assert "Data de nascimento inválida" in texto
    assert "Encaminhe-se" not in texto


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(enviar_alunos, valor_zero):
    texto = enviar_alunos(
        {
            "N. USP": "1234a67",
            "E-MAIL": "maria.usp.br",
            "VALOR SOLICITADO (R$)": valor_zero,
        }
    )
    mensagens = [
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "Valor solicitado deve ser maior que 0",
    ]
    linhas = [linha for linha in texto.splitlines() if linha.strip()]
    for mensagem in mensagens:
        assert any(mensagem in linha for linha in linhas), f"mensagem ausente: {mensagem}"
    for linha in linhas:
        juntos = [mensagem for mensagem in mensagens if mensagem in linha]
        assert len(juntos) <= 1, f"mensagens amassadas na mesma linha: {linha}"
    assert "Encaminhe-se" not in texto


def test_validacao_e_igual_na_aba_docentes(enviar_docentes):
    texto = enviar_docentes({"N. USP": "1234a67"})
    assert "N. USP deve conter apenas números" in texto
    assert "Encaminhe-se" not in texto
