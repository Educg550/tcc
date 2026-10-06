'''Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.'''

import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app

client = TestClient(app)

ROTULOS = [
    'SOLICITANTE E EVENTO',
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
    'ENDEREÇO DO SOLICITANTE',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
    'Enviar solicitação',
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


def _pagina():
    resposta = client.get('/')
    assert resposta.status_code == 200
    return resposta.text


def test_pagina_inicial_tem_as_abas_alunos_e_docentes():
    html = _pagina()
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


@pytest.mark.parametrize('rotulo', ROTULOS)
def test_rotulos_visiveis_na_pagina(rotulo):
    assert rotulo in _pagina()


@pytest.mark.parametrize('opcao', OPCOES)
def test_opcoes_visiveis_na_pagina(opcao):
    assert opcao in _pagina()


def test_cabecalho_institucional_da_usp():
    html = _pagina()
    assert 'assets/usp-logo.png' in html
    assert 'Universidade de São Paulo' in html


def test_brasao_nao_aparece():
    for texto in (_pagina(), client.get('/style.css').text):
        assert 'brasao' not in texto.lower()
        assert 'escudo' not in texto.lower()


def test_estaticos_sao_servidos():
    for caminho in ('/style.css', '/app.js', '/assets/usp-logo.png'):
        assert client.get(caminho).status_code == 200


def test_cores_da_universidade_no_css():
    css = client.get('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css


def test_css_usa_fonte_sem_serifa():
    css = client.get('/style.css').text
    assert 'sans-serif' in css or 'Open Sans' in css


def test_sem_recurso_de_rede():
    for caminho in ('/', '/style.css', '/app.js'):
        texto = client.get(caminho).text.lower()
        for proibido in ('cdn.', 'cdnjs', 'googleapis', 'unpkg', 'jsdelivr'):
            assert proibido not in texto


_CAMPOS = {
    'nome': ('nome', 'nome_completo', 'nomeCompleto'),
    'n_usp': ('n_usp', 'nusp', 'numero_usp', 'num_usp'),
    'programa': ('programa', 'curso'),
    'nivel': ('nivel', 'nivel_curso', 'grau'),
    'tipo_auxilio': ('tipo_auxilio', 'tipo_de_auxilio', 'tipoAuxilio', 'auxilio'),
    'email': ('email', 'e_mail', 'e-mail'),
    'evento': ('evento', 'nome_evento', 'nome_do_evento', 'banca'),
    'periodo': ('periodo', 'periodo_evento', 'periodo_do_evento'),
    'evento_cidade': ('cidade_evento', 'cidade_do_evento'),
    'evento_estado': ('estado_evento', 'estado_do_evento'),
    'evento_pais': ('pais', 'pais_evento', 'pais_do_evento'),
    'link': ('link', 'link_evento', 'link_do_evento', 'url_evento'),
    'valor': ('valor', 'valor_solicitado', 'valor_solicitado_reais'),
    'detalhamento': ('detalhamento', 'detalhamento_pedido', 'detalhes'),
    'apresentacao': ('apresentacao', 'apresentacao_trabalho', 'tipo_apresentacao'),
    'nascimento': ('data_nascimento', 'nascimento', 'data_de_nascimento'),
    'logradouro': ('logradouro', 'rua'),
    'numero': ('numero', 'numero_endereco'),
    'complemento': ('complemento',),
    'bairro': ('bairro',),
    'cep': ('cep', 'codigo_postal'),
    'cidade': ('cidade', 'cidade_residencial', 'municipio'),
    'estado': ('estado', 'estado_residencial', 'uf'),
    'cpf': ('cpf',),
    'rg': ('rg', 'rg_rnm', 'rnm'),
    'banco': ('banco', 'nome_banco', 'nome_do_banco'),
    'agencia': ('agencia', 'numero_agencia', 'num_agencia'),
    'conta': ('conta', 'numero_conta', 'num_conta'),
    'aba': ('aba', 'formulario', 'tipo_solicitante', 'perfil'),
}

_VALIDOS = {
    'nome': 'Zzq Maria da Silva Teste',
    'n_usp': '12345678',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.teste@ime.usp.br',
    'evento': 'Congresso Zzq de Computação',
    'periodo': '10 a 15 de março de 2025',
    'evento_cidade': 'São Paulo',
    'evento_estado': 'SP',
    'evento_pais': 'Brasil',
    'link': 'https://evento.zzq.test',
    'detalhamento': 'Passagem aérea e hospedagem.',
    'apresentacao': 'Pôster',
    'nascimento': '01/02/1980',
    'logradouro': 'Rua do Matão',
    'numero': '1010',
    'complemento': 'Bloco B',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '56789-0',
    'aba': 'alunos',
}

_VALORES = {'digitos': '150000', 'formatado': 'R$ 1.500,00'}

_PADRAO = [
    '/solicitar',
    '/solicitacao',
    '/solicitacoes',
    '/api/solicitar',
    '/api/solicitacao',
    '/enviar',
    '/api/enviar',
    '/submit',
    '/oficio',
    '/api/oficio',
    '/gerar-oficio',
    '/auxilio',
    '/api/auxilio',
]

_ENVIO = {}


def _strings(valor):
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, dict):
        return [s for v in valor.values() for s in _strings(v)]
    if isinstance(valor, list):
        return [s for v in valor for s in _strings(v)]
    return []


def _texto(resposta):
    try:
        conteudo = resposta.json()
    except ValueError:
        return resposta.text
    return '\n'.join(_strings(conteudo))


def _dados(valores):
    dados = {}
    for logico, valor in valores.items():
        for nome in _CAMPOS[logico]:
            dados[nome] = valor
    return dados


def _requisita(url, codificacao, dados):
    if codificacao == 'form':
        return client.post(url, data=dados)
    return client.post(url, json=dados)


def _urls():
    achadas = []
    for pagina in ('/', '/app.js'):
        resposta = client.get(pagina)
        if resposta.status_code != 200:
            continue
        for url in re.findall(r'(/[A-Za-z0-9_/-]+)', resposta.text):
            if url not in achadas:
                achadas.append(url)
    return achadas + [url for url in _PADRAO if url not in achadas]


def _descobre():
    if _ENVIO:
        return _ENVIO
    for url in _urls():
        for codificacao in ('form', 'json'):
            for formato in ('digitos', 'formatado'):
                valores = dict(_VALIDOS, valor=_VALORES[formato])
                resposta = _requisita(url, codificacao, _dados(valores))
                if 200 <= resposta.status_code < 300 and 'Encaminh' in _texto(resposta):
                    _ENVIO.update(url=url, codificacao=codificacao, formato=formato)
                    return _ENVIO
    pytest.fail('não foi possível encontrar o endpoint que gera o ofício')


def _envia(**alteracoes):
    envio = _descobre()
    valores = dict(_VALIDOS, valor=_VALORES[envio['formato']])
    valores.update(alteracoes)
    return _requisita(envio['url'], envio['codificacao'], _dados(valores))


def _resposta(**alteracoes):
    return _texto(_envia(**alteracoes))


def test_oficio_da_aba_alunos():
    texto = _resposta()
    assert 'Interessada(o): Zzq Maria da Silva Teste - 12345678' in texto
    assert 'E-mail: maria.teste@ime.usp.br' in texto
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in texto
    assert 'Programa: Ciência da Computação - Mestrado' in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto
    assert 'Link do evento: https://evento.zzq.test' in texto
    assert 'Complemento: Bloco B' in texto
    assert 'Apresentação de trabalho: Pôster' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto
    assert 'Preencha todos os campos' not in texto


def test_oficio_da_aba_docentes():
    texto = _resposta(aba='docentes', nivel='', tipo_auxilio='')
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'Mestrado' not in texto
    assert 'Participação em evento' not in texto


def test_linhas_opcionais_vazias_saem_do_oficio():
    texto = _resposta(link='', complemento='')
    assert 'Interessada(o): Zzq Maria da Silva Teste' in texto
    assert 'Link do evento' not in texto
    assert 'Complemento' not in texto


def test_campo_obrigatorio_vazio_mostra_o_erro_e_nao_gera_oficio():
    texto = _resposta(nome='')
    assert 'Preencha todos os campos' in texto
    assert 'Interessada(o):' not in texto


def test_n_usp_com_letras():
    assert 'N. USP deve conter apenas números' in _resposta(n_usp='12abc')


def test_agencia_com_letras():
    assert 'Número da agência deve conter apenas números' in _resposta(agencia='12ab')


def test_email_invalido():
    assert 'E-mail inválido' in _resposta(email='maria.ime.usp.br')


def test_cpf_fora_do_formato():
    assert 'CPF deve estar no formato 000.000.000-00' in _resposta(cpf='12345678909')


def test_cpf_com_digitos_verificadores_invalidos():
    assert 'CPF inválido' in _resposta(cpf='111.111.111-11')


def test_cep_fora_do_formato():
    assert 'CEP deve estar no formato 00000-000' in _resposta(cep='123')


def test_data_de_nascimento_fora_do_formato():
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in _resposta(nascimento='01021980')


def test_data_de_nascimento_inexistente():
    assert 'Data de nascimento inválida' in _resposta(nascimento='31/02/1980')


def test_valor_solicitado_igual_a_zero():
    assert 'Valor solicitado deve ser maior que 0' in _resposta(valor='0')


def test_varios_erros_aparecem_juntos_e_sem_oficio():
    texto = _resposta(nome='', n_usp='abc', email='sem-arroba')
    assert 'Preencha todos os campos' in texto
    assert 'N. USP deve conter apenas números' in texto
    assert 'E-mail inválido' in texto
    assert 'Interessada(o):' not in texto
