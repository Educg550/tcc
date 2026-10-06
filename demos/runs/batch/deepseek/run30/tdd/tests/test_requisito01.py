"""Testes do formulário de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


ROTULOS = [
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
    'Enviar solicitação',
]


def _pagina():
    for caminho in ('/', '/index.html'):
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            return resposta.content.decode('utf-8', 'replace')
    raise AssertionError('a página inicial não foi servida')


def _sem_tags(html):
    return re.sub(r'<[^>]*>', '', html)


def _referencias(html):
    return set(re.findall(r'(?:href|src)\s*=\s*"([^"]+)"', html))


def _url(caminho):
    if caminho.startswith('http'):
        return caminho
    return '/' + caminho.lstrip('/')


def test_rotulos_visiveis():
    html = _pagina()
    texto = _sem_tags(html)
    ausentes = [rotulo for rotulo in ROTULOS if rotulo not in texto and rotulo not in html]
    assert ausentes == [], f'rótulos ausentes: {ausentes}'


def test_cabecalho_institucional():
    texto = _sem_tags(_pagina())
    assert 'Universidade de São Paulo' in texto


def test_css_e_js_servidos():
    html = _pagina()
    referencias = _referencias(html)
    css = [u for u in referencias if u.endswith('.css')]
    js = [u for u in referencias if u.endswith('.js')]
    assert css, 'nenhum CSS referenciado na página'
    assert js, 'nenhum JavaScript referenciado na página'
    for caminho in css + js:
        assert client.get(_url(caminho)).status_code == 200, caminho


def test_logo_usp_servido():
    html = _pagina()
    logos = [u for u in _referencias(html) if 'usp-logo' in u]
    assert logos, 'o logotipo da USP não é referenciado na página'
    for caminho in logos:
        assert client.get(_url(caminho)).status_code == 200, caminho


def test_cores_institucionais_no_css():
    html = _pagina()
    css = [u for u in _referencias(html) if u.endswith('.css')]
    assert css
    conteudo = ''
    for caminho in css:
        resposta = client.get(_url(caminho))
        assert resposta.status_code == 200
        conteudo += resposta.content.decode('utf-8', 'replace')
    conteudo = conteudo.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in conteudo, cor


def _rotas_post():
    rotas = []
    for rota in app.routes:
        metodos = getattr(rota, 'methods', None) or set()
        if 'POST' in metodos:
            rotas.append(rota.path)
    return rotas


def _enviar(campos, aba=''):
    rotas = _rotas_post()
    assert rotas, 'a aplicação não expõe nenhuma rota POST de envio'
    caminho = next((p for p in rotas if aba and aba in p.lower()), rotas[0])
    resposta = client.post(caminho, json=campos)
    if resposta.status_code == 422:
        resposta = client.post(caminho, data=campos)
    return resposta


def _corpo(resposta):
    return resposta.content.decode('utf-8', 'replace')


CAMPOS_ALUNOS = {
    'NOME COMPLETO - SEM ABREVIAR': 'Joao da Silva',
    'N. USP': '12345678',
    'PROGRAMA': 'Ciencia da Computacao',
    'NÍVEL': 'Mestrado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'joao@ime.usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'Congresso Brasileiro',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '01/03/2024 a 05/03/2024',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'Sao Paulo',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://evento.example',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Passagens e hospedagem',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Matao',
    'NÚMERO': '1010',
    'COMPLEMENTO': 'Bloco B',
    'BAIRRO': 'Butanta',
    'CEP': '05508-090',
    'CIDADE': 'Sao Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '1234',
    'NÚMERO DA CONTA': '56789-0',
}


def _alunos(**mudancas):
    campos = dict(CAMPOS_ALUNOS)
    campos.update(mudancas)
    return campos


def test_oficio_da_aba_alunos():
    corpo = _corpo(_enviar(_alunos(), aba='aluno'))
    assert 'Interessada(o): Joao da Silva - 12345678' in corpo
    assert 'E-mail: joao@ime.usp.br' in corpo
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in corpo
    assert 'Programa: Ciencia da Computacao - Mestrado' in corpo
    assert 'Evento: Congresso Brasileiro' in corpo
    assert 'Valor solicitado: R$ 1.500,00' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' in corpo


def test_oficio_da_aba_docentes():
    campos = {
        chave: valor
        for chave, valor in CAMPOS_ALUNOS.items()
        if chave not in ('NÍVEL', 'TIPO DE AUXÍLIO')
    }
    corpo = _corpo(_enviar(campos, aba='docente'))
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in corpo
    assert 'Programa: Ciencia da Computacao' in corpo
    assert 'Mestrado' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' in corpo


def test_link_e_complemento_vazios_saem_do_oficio():
    corpo = _corpo(
        _enviar(
            _alunos(
                **{
                    'LINK DO EVENTO, EXAME OU DEFESA': '',
                    'COMPLEMENTO': '',
                }
            )
        )
    )
    assert 'Link do evento:' not in corpo
    assert 'Complemento:' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' in corpo


def test_campos_obrigatorios_vazios():
    corpo = _corpo(_enviar({}))
    assert 'Preencha todos os campos' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_campos_obrigatorios_vazios_uma_unica_vez():
    corpo = _corpo(_enviar({}))
    assert corpo.count('Preencha todos os campos') == 1


def test_n_usp_apenas_numeros():
    corpo = _corpo(_enviar(_alunos(**{'N. USP': '12ab34'})))
    assert 'N. USP deve conter apenas números' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_agencia_apenas_numeros():
    corpo = _corpo(_enviar(_alunos(**{'NÚMERO DA AGÊNCIA': '12a4'})))
    assert 'Número da agência deve conter apenas números' in corpo


def test_valor_solicitado_maior_que_zero():
    corpo = _corpo(_enviar(_alunos(**{'VALOR SOLICITADO (R$)': 'R$ 0,00'})))
    assert 'Valor solicitado deve ser maior que 0' in corpo


def test_email_invalido():
    corpo = _corpo(_enviar(_alunos(**{'E-MAIL': 'joao.ime.usp.br'})))
    assert 'E-mail inválido' in corpo


def test_cpf_fora_do_formato():
    corpo = _corpo(_enviar(_alunos(**{'CPF (SEPARADOS POR PONTOS E TRAÇO)': '12345678909'})))
    assert 'CPF deve estar no formato 000.000.000-00' in corpo


def test_cpf_digitos_verificadores_invalidos():
    corpo = _corpo(_enviar(_alunos(**{'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-00'})))
    assert 'CPF inválido' in corpo


def test_cep_fora_do_formato():
    corpo = _corpo(_enviar(_alunos(**{'CEP': '05508090'})))
    assert 'CEP deve estar no formato 00000-000' in corpo


def test_data_nascimento_fora_do_formato():
    corpo = _corpo(_enviar(_alunos(**{'DATA DE NASCIMENTO': '01021980'})))
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in corpo


def test_data_nascimento_inexistente():
    corpo = _corpo(_enviar(_alunos(**{'DATA DE NASCIMENTO': '31/02/1980'})))
    assert 'Data de nascimento inválida' in corpo


def test_varias_mensagens_de_erro():
    corpo = _corpo(_enviar(_alunos(**{'N. USP': 'abc', 'E-MAIL': 'sem-arroba'})))
    assert 'N. USP deve conter apenas números' in corpo
    assert 'E-mail inválido' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo
