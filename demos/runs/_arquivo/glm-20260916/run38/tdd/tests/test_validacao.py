from conftest import enviar, payload_de_aluno


def _enviar_com(client, nomes, rotulo, valor):
    payload = payload_de_aluno(nomes)
    payload[nomes[rotulo]] = valor
    return enviar(client, payload).text


def test_tudo_vazio_pede_preencher_uma_vez(client, nomes):
    payload = {campo: '' for campo in payload_de_aluno(nomes)}
    texto = enviar(client, payload).text
    assert 'Preencha todos os campos' in texto
    assert texto.count('Preencha todos os campos') == 1


def test_n_usp_com_letra(client, nomes):
    texto = _enviar_com(client, nomes, 'N. USP', '12a4567')
    assert 'N. USP deve conter apenas números' in texto
    assert 'Preencha todos os campos' not in texto


def test_agencia_com_letra(client, nomes):
    texto = _enviar_com(client, nomes, 'NÚMERO DA AGÊNCIA', '12a4')
    assert 'Número da agência deve conter apenas números' in texto
    assert 'Preencha todos os campos' not in texto


def test_valor_zero(client, nomes):
    texto = _enviar_com(client, nomes, 'VALOR SOLICITADO (R$)', 'R$ 0,00')
    assert 'Valor solicitado deve ser maior que 0' in texto
    assert 'Preencha todos os campos' not in texto


def test_email_sem_arroba(client, nomes):
    texto = _enviar_com(client, nomes, 'E-MAIL', 'maria.usp.br')
    assert 'E-mail inválido' in texto
    assert 'Preencha todos os campos' not in texto


def test_email_sem_dominio(client, nomes):
    texto = _enviar_com(client, nomes, 'E-MAIL', 'maria@')
    assert 'E-mail inválido' in texto


def test_cpf_fora_do_formato(client, nomes):
    texto = _enviar_com(client, nomes, 'CPF (SEPARADOS POR PONTOS E TRAÇO)', '12345678909')
    assert 'CPF deve estar no formato 000.000.000-00' in texto
    assert 'CPF inválido' not in texto


def test_cpf_com_digito_verificador_errado(client, nomes):
    texto = _enviar_com(client, nomes, 'CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-00')
    assert 'CPF inválido' in texto
    assert 'deve estar no formato' not in texto


def test_cep_fora_do_formato(client, nomes):
    texto = _enviar_com(client, nomes, 'CEP', '0550809')
    assert 'CEP deve estar no formato 00000-000' in texto


def test_data_fora_do_formato(client, nomes):
    texto = _enviar_com(client, nomes, 'DATA DE NASCIMENTO', '01021980')
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in texto


def test_data_inexistente(client, nomes):
    texto = _enviar_com(client, nomes, 'DATA DE NASCIMENTO', '31/02/2000')
    assert 'Data de nascimento inválida' in texto
    assert 'deve estar no formato' not in texto


def test_mes_inexistente(client, nomes):
    texto = _enviar_com(client, nomes, 'DATA DE NASCIMENTO', '15/13/2000')
    assert 'Data de nascimento inválida' in texto


def test_varios_erros_aparecem_juntos(client, nomes):
    payload = payload_de_aluno(nomes)
    payload[nomes['N. USP']] = '12a4567'
    payload[nomes['E-MAIL']] = 'maria.usp.br'
    texto = enviar(client, payload).text
    assert 'N. USP deve conter apenas números' in texto
    assert 'E-mail inválido' in texto
    assert 'Preencha todos os campos' not in texto
