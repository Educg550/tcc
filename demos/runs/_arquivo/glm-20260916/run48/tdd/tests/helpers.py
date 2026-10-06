ENDPOINT = '/api/solicitacao'

MSG_CAMPOS = 'Preencha todos os campos'


def dados_alunos(**substituicoes):
    dados = {
        'aba': 'alunos',
        'nome_completo': 'Maria da Silva',
        'n_usp': '1234567',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_de_auxilio': 'Participação em evento',
        'email': 'maria@usp.br',
        'nome_do_evento': 'Simpósio de Computação',
        'periodo_do_evento': '10 e 11 de março de 2025',
        'cidade_do_evento': 'Rio de Janeiro',
        'estado_do_evento': 'RJ',
        'pais_do_evento': 'Brasil',
        'link_do_evento': 'https://simposio.example.br',
        'valor_solicitado': '150000',
        'detalhamento_do_pedido': 'Passagem aérea e inscrição no evento.',
        'ira_apresentar_trabalho': 'Pôster',
        'data_de_nascimento': '01/02/1980',
        'logradouro': 'Rua do Anfiteatro',
        'numero': '123',
        'complemento': 'Apto 4',
        'bairro': 'Butantã',
        'cep': '05508-090',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cpf': '123.456.789-09',
        'rg_rnm': '12.345.678-9',
        'nome_do_banco': 'Banco do Brasil',
        'numero_da_agencia': '1234',
        'numero_da_conta': '98765-4',
    }
    dados.update(substituicoes)
    return dados


def dados_docentes(**substituicoes):
    dados = dados_alunos()
    dados['aba'] = 'docentes'
    del dados['nivel']
    del dados['tipo_de_auxilio']
    dados.update(substituicoes)
    return dados


def _textos(obj):
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        valores = obj.values()
    elif isinstance(obj, (list, tuple)):
        valores = obj
    else:
        return []
    textos = []
    for valor in valores:
        textos.extend(_textos(valor))
    return textos


def corpo(resposta):
    try:
        dados = resposta.()
    except ValueError:
        return resposta.text
    return '\n'.join(_textos(dados))
