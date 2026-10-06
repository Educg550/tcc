'''Testes da aplicação de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Fronteira HTTP exercitada com o cliente de teste do FastAPI:

- Páginas/arquivos estáticos: GET /, /style.css, /app.js e /assets/usp-logo.png.
- Envio da solicitação: POST com JSON cujas chaves são os campos do formulário em
  snake_case, mais a chave 'aba' ('ALUNOS' ou 'DOCENTES'). O backend responde
  {'oficio': ...} quando a solicitação é válida e {'erros': [...]} quando não é.
  A rota POST é descoberta pela especificação OpenAPI da própria aplicação.
'''

import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


def rota_solicitacao(client):
    if getattr(rota_solicitacao, 'cache', None) is None:
        spec = client.get('/openapi.').()
        caminhos = [c for c, ops in spec['paths'].items() if 'post' in ops]
        preferidas = [c for c in caminhos if 'solicit' in c or 'auxilio' in c]
        candidatas = preferidas or caminhos
        assert candidatas, 'O backend não expõe rota POST para receber a solicitação'
        rota_solicitacao.cache = candidatas[0]
    return rota_solicitacao.cache


def enviar(client, dados):
    return client.post(rota_solicitacao(client), =dados)


def oficio_da(resposta):
    corpo = resposta.()
    assert 'oficio' in corpo, resposta.text
    return corpo['oficio']


def erros_da(resposta):
    corpo = resposta.()
    assert 'erros' in corpo, resposta.text
    return corpo['erros']


def dados_validos(**substituicoes):
    dados = {
        'aba': 'ALUNOS',
        'nome_completo': 'Maria de Souza',
        'n_usp': '1234567',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'maria@usp.br',
        'nome_evento': 'Congresso Brasileiro de Computação',
        'periodo_evento': '10/03/2025 a 15/03/2025',
        'cidade_evento': 'São Paulo',
        'estado_evento': 'SP',
        'pais_evento': 'Brasil',
        'link_evento': 'https://evento.org.br/2025',
        'valor_solicitado': '150000',
        'detalhamento': 'Passagens aéreas e inscrição no evento.',
        'apresentacao_trabalho': 'Pôster',
        'data_nascimento': '01/02/1980',
        'logradouro': 'Rua do Anfiteatro',
        'numero': '375',
        'complemento': 'Sala 5',
        'bairro': 'Butantã',
        'cep': '05508-090',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cpf': '123.456.789-09',
        'rg_rnm': '12.345.678-9',
        'nome_banco': 'Banco do Brasil',
        'agencia': '1234',
        'conta': '98765-4',
    }
    dados.update(substituicoes)
    return dados


def dados_docentes(**substituicoes):
    dados = dados_validos(aba='DOCENTES', **substituicoes)
    del dados['nivel']
    del dados['tipo_auxilio']
    return dados


ROTULOS_EM_ORDEM = [
    'ALUNOS',
    'DOCENTES',
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
]


def test_pagina_inicial_responde(client):
    assert client.get('/').status_code == 200


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = client.get('/').text
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_rotulos_exatos_na_ordem(client):
    html = client.get('/').text
    pos = -1
    for rotulo in ROTULOS_EM_ORDEM:
        achou = html.find(rotulo, pos + 1)
        assert achou > pos, f'Rótulo ausente ou fora de ordem: {rotulo!r}'
        pos = achou


def test_cada_aba_tem_seu_botao_enviar(client):
    html = client.get('/').text
    assert html.count('Enviar solicitação') >= 2


def test_opcoes_das_selecoes(client):
    html = client.get('/').text
    for opcao in (
        'Mestrado',
        'Doutorado',
        'Participação em evento',
        'Banca de exame ou defesa',
        'Outro',
        'Pôster',
        'Apresentação oral',
        'Outra',
        'Não irá apresentar trabalho',
    ):
        assert opcao in html, f'Opção ausente: {opcao!r}'


def test_todo_campo_tem_placeholder_de_exemplo(client):
    html = client.get('/').text
    placeholders = re.findall(r'placeholder="([^"]+)"', html)
    assert len(placeholders) >= 50
    for placeholder in placeholders:
        assert placeholder not in ROTULOS_EM_ORDEM


def test_cabecalho_institucional(client):
    html = client.get('/').text
    assert 'Universidade de São Paulo' in html
    assert 'assets/usp-logo.png' in html


def test_index_referencia_css_e_script(client):
    html = client.get('/').text
    assert 'style.css' in html
    assert 'app.js' in html
    assert client.get('/style.css').status_code == 200
    assert client.get('/app.js').status_code == 200


def test_logo_e_servida_como_imagem(client):
    resposta = client.get('/assets/usp-logo.png')
    assert resposta.status_code == 200
    assert resposta.headers['content-type'].startswith('image/')


def test_identidade_visual_no_css(client):
    css = client.get('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css
    assert 'open sans' in css
    assert 'sans-serif' in css


def test_oficio_da_aba_alunos(client):
    resposta = enviar(client, dados_validos())
    assert resposta.status_code == 200
    oficio = oficio_da(resposta)
    for linha in (
        'Interessada(o): Maria de Souza - 1234567',
        'E-mail: maria@usp.br',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
        'Programa: Ciência da Computação - Mestrado',
        'Dados do evento',
        'Evento: Congresso Brasileiro de Computação',
        'Período: 10/03/2025 a 15/03/2025',
        'Local: São Paulo - SP - Brasil',
        'Link do evento: https://evento.org.br/2025',
        'Apresentação de trabalho: Pôster',
        'Valor solicitado: R$ 1.500,00',
        'Detalhamento: Passagens aéreas e inscrição no evento.',
        'Endereço da(o) interessada(o)',
        'Rua do Anfiteatro, 375',
        'Complemento: Sala 5',
        'CEP: 05508-090',
        'Butantã, São Paulo - SP',
        'Dados para pagamento',
        'Data de nascimento: 01/02/1980',
        'CPF: 123.456.789-09',
        'RG / RNM: 12.345.678-9',
        'Banco: Banco do Brasil',
        'Agência: 1234',
        'Conta: 98765-4',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ):
        assert linha in oficio, f'Linha ausente do ofício: {linha!r}'
    paragrafo = re.sub(r'\s+', ' ', oficio)
    assert (
        'A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de '
        'auxílio financeiro para a interessada(o) acima, conforme segue:' in paragrafo
    )


def test_oficio_da_aba_docentes(client):
    resposta = enviar(client, dados_docentes())
    assert resposta.status_code == 200
    oficio = oficio_da(resposta)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    linhas_de_programa = [l for l in oficio.splitlines() if l.startswith('Programa:')]
    assert linhas_de_programa == ['Programa: Ciência da Computação']
    assert 'Interessada(o): Maria de Souza - 1234567' in oficio
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in oficio


def test_valor_e_assunto_formatados_no_oficio(client):
    oficio = oficio_da(
        enviar(client, dados_validos(valor_solicitado='1500', tipo_auxilio='Outro'))
    )
    assert 'Valor solicitado: R$ 15,00' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Outro' in oficio
    oficio = oficio_da(enviar(client, dados_validos(valor_solicitado='150000000')))
    assert 'Valor solicitado: R$ 1.500.000,00' in oficio


def test_campos_opcionais_vazios_saiem_do_oficio(client):
    oficio = oficio_da(enviar(client, dados_validos(link_evento='', complemento='')))
    assert 'Link do evento' not in oficio
    assert 'Complemento' not in oficio
    assert 'Local: São Paulo - SP - Brasil' in oficio
    assert 'Rua do Anfiteatro, 375' in oficio
    assert 'CEP: 05508-090' in oficio


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem(client):
    erros = erros_da(enviar(client, dados_validos(nome_completo='')))
    assert erros.count('Preencha todos os campos') == 1


def test_n_usp_deve_conter_apenas_numeros(client):
    erros = erros_da(enviar(client, dados_validos(n_usp='12a45')))
    assert 'N. USP deve conter apenas números' in erros


def test_agencia_deve_conter_apenas_numeros(client):
    erros = erros_da(enviar(client, dados_validos(agencia='12x4')))
    assert 'Número da agência deve conter apenas números' in erros


def test_valor_solicitado_deve_ser_maior_que_zero(client):
    erros = erros_da(enviar(client, dados_validos(valor_solicitado='0')))
    assert 'Valor solicitado deve ser maior que 0' in erros


def test_email_invalido(client):
    erros = erros_da(enviar(client, dados_validos(email='maria.usp.br')))
    assert 'E-mail inválido' in erros


def test_cpf_fora_do_formato(client):
    erros = erros_da(enviar(client, dados_validos(cpf='12345678909')))
    assert 'CPF deve estar no formato 000.000.000-00' in erros


def test_cep_fora_do_formato(client):
    erros = erros_da(enviar(client, dados_validos(cep='05508090')))
    assert 'CEP deve estar no formato 00000-000' in erros


def test_data_nascimento_fora_do_formato(client):
    erros = erros_da(enviar(client, dados_validos(data_nascimento='01-02-1980')))
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in erros


def test_cpf_com_digito_verificador_errado(client):
    erros = erros_da(enviar(client, dados_validos(cpf='123.456.789-00')))
    assert 'CPF inválido' in erros


def test_data_nascimento_inexistente(client):
    erros = erros_da(enviar(client, dados_validos(data_nascimento='31/02/2000')))
    assert 'Data de nascimento inválida' in erros


def test_todas_as_mensagens_de_erro_aparecem_juntas(client):
    erros = erros_da(
        enviar(
            client,
            dados_validos(n_usp='12a45', email='maria.usp.br', cep='05508090'),
        )
    )
    assert 'N. USP deve conter apenas números' in erros
    assert 'E-mail inválido' in erros
    assert 'CEP deve estar no formato 00000-000' in erros


def test_com_erro_o_oficio_nao_e_gerado(client):
    resposta = enviar(client, dados_validos(email='maria.usp.br'))
    assert 'Interessada(o):' not in resposta.text


def test_validacao_vale_na_aba_docentes(client):
    erros = erros_da(enviar(client, dados_docentes(email='maria.usp.br')))
    assert 'E-mail inválido' in erros
