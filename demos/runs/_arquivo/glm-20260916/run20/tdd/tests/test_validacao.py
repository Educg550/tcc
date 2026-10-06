from conftest import VAZIOS, algum, mensagem_unica, nenhum


def test_envio_vazio_pedindo_todos_os_campos(enviar):
    respostas = enviar(VAZIOS)
    assert respostas, 'o backend não respondeu ao envio do formulário vazio'
    assert mensagem_unica(respostas, 'Preencha todos os campos')
    assert nenhum(respostas, 'Interessada(o):')
    assert nenhum(respostas, 'CPF inválido')
    assert nenhum(respostas, 'Data de nascimento inválida')


def test_n_usp_com_letras(enviar):
    respostas = enviar({'n_usp': '98765a4'})
    assert algum(respostas, 'N. USP deve conter apenas números')
    assert nenhum(respostas, 'Preencha todos os campos')


def test_agencia_com_letras(enviar):
    respostas = enviar({'agencia': '12a4'})
    assert algum(respostas, 'Número da agência deve conter apenas números')


def test_valor_zero(enviar):
    respostas = enviar({'valor': 'R$ 0,00'})
    assert algum(respostas, 'Valor solicitado deve ser maior que 0')


def test_email_sem_arroba(enviar):
    respostas = enviar({'email': 'maria.usp.br'})
    assert algum(respostas, 'E-mail inválido')


def test_email_sem_dominio(enviar):
    respostas = enviar({'email': 'maria@'})
    assert algum(respostas, 'E-mail inválido')


def test_cpf_fora_do_formato(enviar):
    respostas = enviar({'cpf': '1234567890'})
    assert algum(respostas, 'CPF deve estar no formato 000.000.000-00')
    assert nenhum(respostas, 'CPF inválido')


def test_cpf_com_digito_verificador_errado(enviar):
    respostas = enviar({'cpf': '123.456.789-00'})
    assert algum(respostas, 'CPF inválido')
    assert nenhum(respostas, 'CPF deve estar no formato 000.000.000-00')


def test_cep_fora_do_formato(enviar):
    respostas = enviar({'cep': '0550809'})
    assert algum(respostas, 'CEP deve estar no formato 00000-000')


def test_data_de_nascimento_fora_do_formato(enviar):
    respostas = enviar({'data_nascimento': '01-02-1980'})
    assert algum(respostas, 'Data de nascimento deve estar no formato dd/mm/aaaa')
    assert nenhum(respostas, 'Data de nascimento inválida')


def test_data_de_nascimento_que_nao_existe(enviar):
    respostas = enviar({'data_nascimento': '31/02/1980'})
    assert algum(respostas, 'Data de nascimento inválida')
    assert nenhum(respostas, 'Data de nascimento deve estar no formato dd/mm/aaaa')


def test_erros_acumulados_na_mesma_resposta(enviar):
    respostas = enviar({'n_usp': '98a', 'email': 'maria.usp.br',
                        'cpf': '123.456.789-00'})
    assert algum(respostas, 'N. USP deve conter apenas números')
    assert algum(respostas, 'E-mail inválido')
    assert algum(respostas, 'CPF inválido')
    assert nenhum(respostas, 'Preencha todos os campos')
    assert nenhum(respostas, 'Interessada(o):')
