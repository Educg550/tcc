import re

MENSAGENS_DE_ERRO = [
    'Preencha todos os campos',
    'N. USP deve conter apenas números',
    'Número da agência deve conter apenas números',
    'Valor solicitado deve ser maior que 0',
    'E-mail inválido',
    'CPF deve estar no formato 000.000.000-00',
    'CEP deve estar no formato 00000-000',
    'Data de nascimento deve estar no formato dd/mm/aaaa',
    'CPF inválido',
    'Data de nascimento inválida',
]

ALIASES = {
    'nome_completo': ['nome_completo', 'nomeCompleto', 'nome', 'NOME COMPLETO - SEM ABREVIAR'],
    'numero_usp': ['numero_usp', 'numeroUsp', 'numeroUSP', 'n_usp', 'nUsp', 'num_usp', 'N. USP'],
    'programa': ['programa', 'PROGRAMA'],
    'nivel': ['nivel', 'nível', 'NÍVEL'],
    'tipo_auxilio': ['tipo_auxilio', 'tipoAuxilio', 'tipo_de_auxilio', 'tipoDeAuxilio', 'TIPO DE AUXÍLIO'],
    'email': ['email', 'e_mail', 'eMail', 'E-MAIL'],
    'nome_evento': ['nome_evento', 'nomeEvento', 'evento', 'nome_do_evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'],
    'periodo_evento': ['periodo_evento', 'periodoEvento', 'periodo', 'periodo_do_evento', 'PERÍODO DO EVENTO, EXAME OU DEFESA'],
    'cidade_evento': ['cidade_evento', 'cidadeEvento', 'cidade_do_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA'],
    'estado_evento': ['estado_evento', 'estadoEvento', 'estado_do_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA'],
    'pais_evento': ['pais_evento', 'paisEvento', 'pais', 'pais_do_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA'],
    'link_evento': ['link_evento', 'linkEvento', 'link', 'url_evento', 'link_do_evento', 'LINK DO EVENTO, EXAME OU DEFESA'],
    'valor_solicitado': ['valor_solicitado', 'valorSolicitado', 'valor', 'VALOR SOLICITADO (R$)'],
    'detalhamento': ['detalhamento', 'detalhamento_pedido', 'detalhamentoPedido', 'DETALHAMENTO DO PEDIDO'],
    'apresentacao_trabalho': ['apresentacao_trabalho', 'apresentacaoTrabalho', 'apresentacao', 'ira_apresentar_trabalho', 'trabalho', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'],
    'data_nascimento': ['data_nascimento', 'dataNascimento', 'data_de_nascimento', 'nascimento', 'DATA DE NASCIMENTO'],
    'logradouro': ['logradouro', 'endereco', 'LOGRADOURO'],
    'numero_endereco': ['numero', 'numero_endereco', 'numeroEndereco', 'NÚMERO'],
    'complemento': ['complemento', 'COMPLEMENTO'],
    'bairro': ['bairro', 'BAIRRO'],
    'cep': ['cep', 'CEP'],
    'cidade_endereco': ['cidade', 'cidade_endereco', 'cidadeEndereco', 'CIDADE'],
    'estado_endereco': ['estado', 'estado_endereco', 'estadoEndereco', 'ESTADO'],
    'cpf': ['cpf', 'numero_cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)'],
    'rg_rnm': ['rg_rnm', 'rgRnm', 'rg', 'rnm', 'rg_ou_rnm', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'],
    'nome_banco': ['nome_banco', 'banco', 'nomeBanco', 'NOME DO BANCO'],
    'numero_agencia': ['numero_agencia', 'agencia', 'numeroAgencia', 'numero_da_agencia', 'NÚMERO DA AGÊNCIA'],
    'numero_conta': ['numero_conta', 'conta', 'numeroConta', 'numero_da_conta', 'NÚMERO DA CONTA'],
}

DADOS_ALUNOS = {
    'nome_completo': 'Maria da Silva',
    'numero_usp': '1234567',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria@usp.br',
    'nome_evento': 'SBBD',
    'periodo_evento': '1 a 4 de outubro de 2025',
    'cidade_evento': 'São Paulo',
    'estado_evento': 'SP',
    'pais_evento': 'Brasil',
    'link_evento': 'https://sbbd.org.br',
    'valor_solicitado': 'R$ 1.500,00',
    'detalhamento': 'Passagens aéreas e inscrição no evento.',
    'apresentacao_trabalho': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero_endereco': '181',
    'complemento': 'Sala 214',
    'bairro': 'Cidade Universitária',
    'cep': '05508-090',
    'cidade_endereco': 'São Paulo',
    'estado_endereco': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'nome_banco': 'Banco do Brasil',
    'numero_agencia': '1234',
    'numero_conta': '12345-6',
}

DADOS_DOCENTES = {
    chave: valor
    for chave, valor in DADOS_ALUNOS.items()
    if chave not in ('nivel', 'tipo_auxilio')
}

EXTRAS_ALUNOS = {
    'aba': 'alunos',
    'perfil': 'aluno',
    'origem': 'alunos',
    'formulario': 'alunos',
    'tipo_solicitante': 'aluno',
}

EXTRAS_DOCENTES = {
    'aba': 'docentes',
    'perfil': 'docente',
    'origem': 'docentes',
    'formulario': 'docentes',
    'tipo_solicitante': 'docente',
}

BARRA = chr(92)


def montar_payload(dados, extras=None):
    corpo = {}
    for chave, valor in dados.items():
        for nome in ALIASES[chave]:
            corpo[nome] = valor
    for nome, valor in (extras or {}).items():
        corpo[nome] = valor
    return corpo


def substituir(dados, **alteracoes):
    novo = dict(dados)
    novo.update(alteracoes)
    return novo


def texto_resposta(resposta):
    texto = resposta.text
    texto = re.sub(BARRA + BARRA + 'u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), texto)
    texto = texto.replace('
', '
')
    return texto.replace(BARRA + 'n', '
')


def _rotas_post(client):
    rotas = []
    for rota in client.app.routes:
        if 'POST' in (getattr(rota, 'methods', None) or set()):
            rotas.append(rota.path)
    return rotas


def post_solicitacao(client, dados, marcador):
    conclusivas = []
    ultima = None
    for caminho in _rotas_post(client):
        for kwargs in ({'data': dados}, {'': dados}):
            resposta = client.post(caminho, **kwargs)
            ultima = resposta
            texto = texto_resposta(resposta)
            conclusiva = 'Interessada(o):' in texto or any(m in texto for m in MENSAGENS_DE_ERRO)
            if conclusiva:
                if marcador in texto:
                    return resposta
                conclusivas.append(resposta)
    if conclusivas:
        return conclusivas[0]
    return ultima
