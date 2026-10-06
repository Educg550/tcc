import re

import pytest

CAMINHOS_HOME = ['/', '/index.html']
CAMINHOS_CSS = ['/style.css', '/static/style.css', '/css/style.css']
CAMINHOS_JS = ['/app.js', '/static/app.js', '/js/app.js']
CAMINHOS_LOGO = [
    '/assets/usp-logo.png',
    '/static/assets/usp-logo.png',
    '/static/usp-logo.png',
    '/usp-logo.png',
]

# O requisito não fixa o caminho nem o formato da chamada ao backend; os
# candidatos mais naturais são tentados antes de o teste falhar.
ENDPOINTS = [
    '/solicitacao',
    '/api/solicitacao',
    '/solicitacoes',
    '/api/solicitacoes',
    '/solicitar',
    '/validar',
    '/enviar',
    '/submeter',
    '/submit',
    '/oficio',
    '/api/oficio',
    '/auxilio',
    '/api/auxilio',
    '/',
]

BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'NÍVEL',
    'TIPO DE AUXÍLIO',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

OPCOES = [
    'Mestrado',
    'Doutorado',
    'Participação em evento',
    'Banca de exame ou defesa',
    'Outro',
    'Pôster',
    'Apresentação oral',
    'Outra',
    'Não irá apresentar trabalho',
]

MENSAGENS = [
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

# Cada chave lógica lista os nomes que um backend pode esperar; todos os
# apelidos recebem o mesmo valor, então o teste não depende do nome escolhido.
ALIASES = {
    'aba': ['aba', 'tipo', 'perfil', 'tipo_solicitante', 'formulario'],
    'nome': ['nome_completo', 'nome', 'NOME COMPLETO - SEM ABREVIAR'],
    'n_usp': ['n_usp', 'numero_usp', 'nUSP', 'N. USP'],
    'programa': ['programa', 'PROGRAMA'],
    'nivel': ['nivel', 'NÍVEL'],
    'tipo_auxilio': ['tipo_auxilio', 'TIPO DE AUXÍLIO'],
    'email': ['email', 'e_mail', 'E-MAIL'],
    'nome_evento': ['nome_evento', 'evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'],
    'periodo_evento': ['periodo_evento', 'periodo', 'PERÍODO DO EVENTO, EXAME OU DEFESA'],
    'cidade_evento': ['cidade_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA'],
    'estado_evento': ['estado_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA'],
    'pais_evento': ['pais_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA'],
    'link_evento': ['link_evento', 'link', 'LINK DO EVENTO, EXAME OU DEFESA'],
    'valor_solicitado': ['valor_solicitado', 'valor', 'VALOR SOLICITADO (R$)'],
    'detalhamento': ['detalhamento', 'DETALHAMENTO DO PEDIDO'],
    'apresentacao': ['apresentacao_trabalho', 'apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'],
    'data_nascimento': ['data_nascimento', 'nascimento', 'DATA DE NASCIMENTO'],
    'logradouro': ['logradouro', 'LOGRADOURO'],
    'numero': ['numero', 'NÚMERO'],
    'complemento': ['complemento', 'COMPLEMENTO'],
    'bairro': ['bairro', 'BAIRRO'],
    'cep': ['cep', 'CEP'],
    'cidade': ['cidade', 'CIDADE'],
    'estado': ['estado', 'ESTADO'],
    'cpf': ['cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)'],
    'rg_rnm': ['rg_rnm', 'rg', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'],
    'nome_banco': ['nome_banco', 'banco', 'NOME DO BANCO'],
    'agencia': ['agencia', 'numero_agencia', 'NÚMERO DA AGÊNCIA'],
    'conta': ['conta', 'numero_conta', 'NÚMERO DA CONTA'],
}

DADOS_VALIDOS_ALUNOS = {
    'aba': 'ALUNOS',
    'nome': 'Maria Souza Silva',
    'n_usp': '12345678',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria@usp.br',
    'nome_evento': 'Simpósio de Computação do IME',
    'periodo_evento': '10 a 12 de março de 2025',
    'cidade_evento': 'São Paulo',
    'estado_evento': 'SP',
    'pais_evento': 'Brasil',
    'link_evento': 'https://simposio.ime.usp.br',
    'valor_solicitado': '150000',
    'detalhamento': 'Passagens e diárias para participação no evento.',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '101',
    'complemento': 'Sala 222',
    'bairro': 'Cidade Universitária',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'nome_banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '98765-4',
}

OFICIO_ALUNOS = [
    'Interessada(o): Maria Souza Silva - 12345678',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'Dados do evento',
    'Evento: Simpósio de Computação do IME',
    'Período: 10 a 12 de março de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://simposio.ime.usp.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagens e diárias para participação no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 101',
    'Complemento: Sala 222',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def obter_estatico(client, caminhos):
    for caminho in caminhos:
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            return resposta
    pytest.fail(f'nenhum destes caminhos foi servido: {caminhos}')


def home(client):
    return obter_estatico(client, CAMINHOS_HOME).text


def payload(dados_logicos):
    corpo = {}
    for chave, valor in dados_logicos.items():
        for alias in ALIASES[chave]:
            corpo[alias] = valor
    return corpo


def enviar(client, dados_logicos):
    corpo = payload(dados_logicos)
    recusada = None
    for modo in ('', 'form'):
        for caminho in ENDPOINTS:
            if modo == '':
                resposta = client.post(caminho, =corpo)
            else:
                resposta = client.post(caminho, data=corpo)
            if resposta.status_code in (404, 405):
                continue
            if resposta.status_code == 422:
                if recusada is None:
                    recusada = resposta
                continue
            return resposta
    if recusada is not None:
        return recusada
    pytest.fail('nenhum endpoint de solicitação foi encontrado')


def conteudo(resposta):
    texto = resposta.text.replace('\r', '').replace('\n', '\n')
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), texto)


def dados(**substituicoes):
    novos = dict(DADOS_VALIDOS_ALUNOS)
    novos.update(substituicoes)
    return novos


def dados_docentes():
    docente = dados()
    docente['aba'] = 'DOCENTES'
    docente['nivel'] = ''
    docente['tipo_auxilio'] = ''
    return docente


def test_pagina_inicial_e_servida_como_html(client):
    resposta = obter_estatico(client, CAMINHOS_HOME)
    assert 'text/html' in resposta.headers['content-type']


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = home(client)
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_cada_aba_tem_botao_enviar(client):
    pagina = home(client) + obter_estatico(client, CAMINHOS_JS).text
    assert 'Enviar solicitação' in pagina
    assert pagina.count('Enviar solicitação') >= 2


def test_titulo_da_confirmacao(client):
    pagina = home(client) + obter_estatico(client, CAMINHOS_JS).text
    assert 'Solicitação registrada' in pagina


def test_cabecalho_institucional_da_usp(client):
    html = home(client)
    assert 'Universidade de São Paulo' in html
    assert 'usp-logo.png' in html


def test_tres_blocos_nessa_ordem(client):
    html = home(client)
    posicoes = [html.index(bloco) for bloco in BLOCOS]
    assert posicoes == sorted(posicoes)


def test_rotulos_exatos_e_opcoes_no_formulario(client):
    html = home(client)
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo
    for opcao in OPCOES:
        assert opcao in html, opcao


def test_nivel_e_tipo_de_auxilio_somente_na_aba_alunos(client):
    html = home(client)
    assert html.count('NÍVEL') == 1
    assert html.count('TIPO DE AUXÍLIO') == 1
    assert html.count('NOME COMPLETO - SEM ABREVIAR') == 2
    assert html.count('CIDADE DO EVENTO, EXAME OU DEFESA') == 2


def test_todo_campo_tem_placeholder_de_exemplo(client):
    pagina = home(client) + obter_estatico(client, CAMINHOS_JS).text
    assert pagina.count('placeholder') >= 20


def test_logo_e_arquivos_estaticos_servidos(client):
    logo = obter_estatico(client, CAMINHOS_LOGO)
    assert 'image' in logo.headers.get('content-type', '')
    obter_estatico(client, CAMINHOS_CSS)
    obter_estatico(client, CAMINHOS_JS)


def test_identidade_visual_usp_sem_recurso_remoto(client):
    html = home(client)
    css = obter_estatico(client, CAMINHOS_CSS).text
    minusculo = css.lower()
    assert '#1094ab' in minusculo
    assert '#64c4d2' in minusculo or '#fcb421' in minusculo
    assert 'open sans' in minusculo or 'sans-serif' in minusculo
    assert 'http://' not in css and 'https://' not in css
    for atributo in ('src="http', "src='http", 'href="http', "href='http", '@import'):
        assert atributo not in html


def test_envio_valido_de_alunos_gera_oficio_completo(client):
    texto = conteudo(enviar(client, dados()))
    for trecho in OFICIO_ALUNOS:
        assert trecho in texto, trecho
    for mensagem in MENSAGENS:
        assert mensagem not in texto
    assert '<<' not in texto


def test_envio_valido_de_docentes_gera_oficio_de_docentes(client):
    texto = conteudo(enviar(client, dados_docentes()))
    assert 'Interessada(o): Maria Souza Silva - 12345678' in texto
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação\n' in texto
    assert 'Mestrado' not in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto
    for mensagem in MENSAGENS:
        assert mensagem not in texto


def test_link_do_evento_vazio_sai_do_oficio(client):
    texto = conteudo(enviar(client, dados(link_evento='')))
    assert 'Link do evento' not in texto
    assert 'Evento: Simpósio de Computação do IME' in texto


def test_complemento_vazio_sai_do_oficio(client):
    texto = conteudo(enviar(client, dados(complemento='')))
    assert 'Complemento' not in texto
    assert 'CEP: 05508-090' in texto


def test_campo_obrigatorio_vazio_impede_o_oficio(client):
    texto = conteudo(enviar(client, dados(nome='')))
    assert 'Preencha todos os campos' in texto
    assert 'Interessada(o):' not in texto


def test_todos_vazios_mostram_a_mensagem_uma_unica_vez(client):
    vazios = {chave: '' for chave in DADOS_VALIDOS_ALUNOS}
    texto = conteudo(enviar(client, vazios))
    assert texto.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in texto


def test_n_usp_deve_conter_apenas_numeros(client):
    texto = conteudo(enviar(client, dados(n_usp='12a45678')))
    assert 'N. USP deve conter apenas números' in texto
    assert 'Preencha todos os campos' not in texto
    assert 'Interessada(o):' not in texto


def test_agencia_deve_conter_apenas_numeros(client):
    texto = conteudo(enviar(client, dados(agencia='12a4')))
    assert 'Número da agência deve conter apenas números' in texto
    assert 'Interessada(o):' not in texto


def test_valor_solicitado_zero_e_recusado(client):
    texto = conteudo(enviar(client, dados(valor_solicitado='0')))
    assert 'Valor solicitado deve ser maior que 0' in texto
    assert 'Interessada(o):' not in texto


@pytest.mark.parametrize('email', ['maria.usp.br', 'maria@'])
def test_email_invalido(client, email):
    texto = conteudo(enviar(client, dados(email=email)))
    assert 'E-mail inválido' in texto
    assert 'Interessada(o):' not in texto


@pytest.mark.parametrize('cpf', ['123456789', '123.456.7890', '123456789099'])
def test_cpf_fora_do_formato(client, cpf):
    texto = conteudo(enviar(client, dados(cpf=cpf)))
    assert 'CPF deve estar no formato 000.000.000-00' in texto
    assert 'Interessada(o):' not in texto


def test_cpf_com_digito_verificador_errado(client):
    texto = conteudo(enviar(client, dados(cpf='123.456.789-00')))
    assert 'CPF inválido' in texto
    assert 'CPF deve estar no formato 000.000.000-00' not in texto
    assert 'Interessada(o):' not in texto


@pytest.mark.parametrize('cep', ['5508909', '05508-0900', '05508_090'])
def test_cep_fora_do_formato(client, cep):
    texto = conteudo(enviar(client, dados(cep=cep)))
    assert 'CEP deve estar no formato 00000-000' in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_fora_do_formato(client):
    texto = conteudo(enviar(client, dados(data_nascimento='01-02-1980')))
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in texto
    assert 'Interessada(o):' not in texto


@pytest.mark.parametrize('data', ['31/02/1980', '01/13/1980', '00/05/1980'])
def test_data_de_nascimento_inexistente(client, data):
    texto = conteudo(enviar(client, dados(data_nascimento=data)))
    assert 'Data de nascimento inválida' in texto
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' not in texto
    assert 'Interessada(o):' not in texto


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(client):
    texto = conteudo(enviar(client, dados(n_usp='12a45678', email='maria.usp.br', cep='5508909')))
    assert 'N. USP deve conter apenas números' in texto
    assert 'E-mail inválido' in texto
    assert 'CEP deve estar no formato 00000-000' in texto
    assert 'Preencha todos os campos' not in texto
    assert 'Interessada(o):' not in texto
