# Contrato do backend: POST /solicitacao recebe a solicitação em JSON e
# responde com o que a tela mostra — as mensagens de erro ou o ofício pronto.

URL = '/solicitacao'
MENSAGEM_CAMPOS = 'Preencha todos os campos'


def payload_alunos():
    return {
        'aba': 'alunos',
        'nome_completo': 'Maria Souza da Silva',
        'n_usp': '12345678',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_de_auxilio': 'Participação em evento',
        'email': 'maria.souza@usp.br',
        'nome_do_evento': 'Simpósio Brasileiro de Bancos de Dados',
        'periodo_do_evento': '30 de setembro a 3 de outubro de 2025',
        'cidade_do_evento': 'São Paulo',
        'estado_do_evento': 'SP',
        'pais_do_evento': 'Brasil',
        'link_do_evento': 'https://sbd.org.br/2025/',
        'valor_solicitado': '150000',
        'detalhamento_do_pedido': 'Passagem aérea e inscrição no evento.',
        'apresentacao_trabalho': 'Pôster',
        'data_de_nascimento': '01/02/1980',
        'logradouro': 'Rua do Anfiteatro',
        'numero': '181',
        'complemento': 'Sala 214',
        'bairro': 'Butantã',
        'cep': '05508-090',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cpf': '111.444.777-35',
        'rg_rnm': '12.345.678-9',
        'nome_do_banco': 'Banco do Brasil',
        'numero_da_agencia': '1234',
        'numero_da_conta': '98765-4',
    }


def payload_docentes():
    dados = payload_alunos()
    dados['aba'] = 'docentes'
    del dados['nivel']
    del dados['tipo_de_auxilio']
    return dados


def submete(client, dados):
    return client.post(URL, =dados).text


def test_solicitacao_valida_de_alunos_gera_oficio(client):
    resposta = client.post(URL, =payload_alunos())
    assert resposta.status_code == 200
    texto = resposta.text
    linhas = [
        'Interessada(o): Maria Souza da Silva - 12345678',
        'E-mail: maria.souza@usp.br',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
        'Programa: Ciência da Computação - Mestrado',
        'A CCP-Ciência da Computação aprovou',
        'Dados do evento',
        'Evento: Simpósio Brasileiro de Bancos de Dados',
        'Período: 30 de setembro a 3 de outubro de 2025',
        'Local: São Paulo - SP - Brasil',
        'Link do evento: https://sbd.org.br/2025/',
        'Apresentação de trabalho: Pôster',
        'Valor solicitado: R$ 1.500,00',
        'Detalhamento: Passagem aérea e inscrição no evento.',
        'Endereço da(o) interessada(o)',
        'Rua do Anfiteatro, 181',
        'Complemento: Sala 214',
        'CEP: 05508-090',
        'Butantã, São Paulo - SP',
        'Dados para pagamento',
        'Data de nascimento: 01/02/1980',
        'CPF: 111.444.777-35',
        'RG / RNM: 12.345.678-9',
        'Banco: Banco do Brasil',
        'Agência: 1234',
        'Conta: 98765-4',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    for linha in linhas:
        assert linha in texto, linha
    assert '<<' not in texto
    assert MENSAGEM_CAMPOS not in texto


def test_solicitacao_valida_de_docentes_gera_oficio_variante(client):
    texto = submete(client, payload_docentes())
    assert 'Interessada(o): Maria Souza da Silva - 12345678' in texto
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'A CCP-Ciência da Computação aprovou' in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto
    assert 'Mestrado' not in texto
    assert 'Participação em evento' not in texto
    assert '<<' not in texto


def test_campos_opcionais_vazios_tiram_a_linha_do_oficio(client):
    dados = payload_alunos()
    dados['link_do_evento'] = ''
    dados['complemento'] = ''
    texto = submete(client, dados)
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert 'CEP: 05508-090' in texto
    assert 'Interessada(o): Maria Souza da Silva - 12345678' in texto


def test_valor_aparece_formatado_como_moeda(client):
    for digitos, moeda in (
        ('1500', 'R$ 15,00'),
        ('150000', 'R$ 1.500,00'),
        ('150000000', 'R$ 1.500.000,00'),
    ):
        dados = payload_alunos()
        dados['valor_solicitado'] = digitos
        texto = submete(client, dados)
        assert 'Valor solicitado: ' + moeda in texto


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem(client):
    dados = payload_alunos()
    dados['nome_completo'] = ''
    dados['nome_do_banco'] = ''
    texto = submete(client, dados)
    assert texto.count(MENSAGEM_CAMPOS) == 1
    assert 'Interessada(o):' not in texto


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(client):
    dados = payload_alunos()
    dados['n_usp'] = '1234A678'
    dados['numero_da_agencia'] = '12A4'
    dados['valor_solicitado'] = '0'
    dados['email'] = 'maria.souza.usp.br'
    dados['cpf'] = '123.456.789-10'
    dados['cep'] = '05508090'
    dados['data_de_nascimento'] = '31/02/1980'
    texto = submete(client, dados)
    for mensagem in (
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF inválido',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento inválida',
    ):
        assert mensagem in texto, mensagem
    assert MENSAGEM_CAMPOS not in texto
    assert 'Interessada(o):' not in texto


def test_n_usp_deve_conter_apenas_numeros(client):
    dados = payload_alunos()
    dados['n_usp'] = '1234A678'
    texto = submete(client, dados)
    assert 'N. USP deve conter apenas números' in texto
    assert 'Interessada(o):' not in texto


def test_numero_da_agencia_deve_conter_apenas_numeros(client):
    dados = payload_alunos()
    dados['numero_da_agencia'] = '12A4'
    texto = submete(client, dados)
    assert 'Número da agência deve conter apenas números' in texto
    assert 'Interessada(o):' not in texto


def test_valor_solicitado_deve_ser_maior_que_zero(client):
    dados = payload_alunos()
    dados['valor_solicitado'] = '0'
    texto = submete(client, dados)
    assert 'Valor solicitado deve ser maior que 0' in texto
    assert 'Interessada(o):' not in texto


def test_email_invalido(client):
    dados = payload_alunos()
    dados['email'] = 'maria.souza.usp.br'
    texto = submete(client, dados)
    assert 'E-mail inválido' in texto
    assert 'Interessada(o):' not in texto


def test_cpf_fora_do_formato(client):
    dados = payload_alunos()
    dados['cpf'] = '111444777'
    texto = submete(client, dados)
    assert 'CPF deve estar no formato 000.000.000-00' in texto
    assert 'CPF inválido' not in texto
    assert 'Interessada(o):' not in texto


def test_cpf_com_digito_verificador_errado(client):
    dados = payload_alunos()
    dados['cpf'] = '123.456.789-10'
    texto = submete(client, dados)
    assert 'CPF inválido' in texto
    assert 'Interessada(o):' not in texto


def test_cep_fora_do_formato(client):
    dados = payload_alunos()
    dados['cep'] = '05508090'
    texto = submete(client, dados)
    assert 'CEP deve estar no formato 00000-000' in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_fora_do_formato(client):
    dados = payload_alunos()
    dados['data_de_nascimento'] = '1980-02-01'
    texto = submete(client, dados)
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in texto
    assert 'Data de nascimento inválida' not in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_inexistente(client):
    dados = payload_alunos()
    dados['data_de_nascimento'] = '31/02/1980'
    texto = submete(client, dados)
    assert 'Data de nascimento inválida' in texto
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' not in texto
    assert 'Interessada(o):' not in texto


def test_docentes_tambem_passa_pela_validacao(client):
    dados = payload_docentes()
    for chave in dados:
        if chave != 'aba':
            dados[chave] = ''
    texto = submete(client, dados)
    assert MENSAGEM_CAMPOS in texto
    assert 'Interessada(o):' not in texto
