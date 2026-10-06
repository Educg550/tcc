import re
from datetime import datetime
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')

CAMPOS = {
    'nome_completo': ('nome_completo', 'NOME COMPLETO - SEM ABREVIAR'),
    'n_usp': ('n_usp', 'numero_usp', 'N. USP'),
    'programa': ('programa', 'PROGRAMA'),
    'email': ('email', 'E-MAIL'),
    'nome_evento': ('nome_evento', 'nome_do_evento', 'evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'),
    'periodo_evento': ('periodo_evento', 'periodo_do_evento', 'periodo', 'PERÍODO DO EVENTO, EXAME OU DEFESA'),
    'cidade_evento': ('cidade_evento', 'cidade_do_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA'),
    'estado_evento': ('estado_evento', 'estado_do_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA'),
    'pais_evento': ('pais_evento', 'pais_do_evento', 'PAÍS DO EVENTO, EXAME OU DEFESA'),
    'link_evento': ('link_evento', 'link_do_evento', 'link', 'LINK DO EVENTO, EXAME OU DEFESA'),
    'valor_solicitado': ('valor_solicitado', 'valor', 'VALOR SOLICITADO (R$)'),
    'detalhamento': ('detalhamento', 'detalhamento_do_pedido', 'DETALHAMENTO DO PEDIDO'),
    'apresentacao': ('apresentacao_trabalho', 'ira_apresentar_trabalho', 'apresentacao', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'),
    'data_nascimento': ('data_nascimento', 'data_de_nascimento', 'DATA DE NASCIMENTO'),
    'logradouro': ('logradouro', 'endereco', 'LOGRADOURO'),
    'numero': ('numero', 'numero_endereco', 'NÚMERO'),
    'complemento': ('complemento', 'COMPLEMENTO'),
    'bairro': ('bairro', 'BAIRRO'),
    'cep': ('cep', 'CEP'),
    'cidade': ('cidade', 'CIDADE'),
    'estado': ('estado', 'ESTADO'),
    'cpf': ('cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)'),
    'rg_rnm': ('rg_rnm', 'rg', 'rnm', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'),
    'nome_banco': ('nome_banco', 'nome_do_banco', 'banco', 'NOME DO BANCO'),
    'agencia': ('agencia', 'numero_da_agencia', 'numero_agencia', 'NÚMERO DA AGÊNCIA'),
    'conta': ('conta', 'numero_da_conta', 'numero_conta', 'NÚMERO DA CONTA'),
}

OPCIONAIS = ('link_evento', 'complemento')

DISCRIMINADORES = ('aba', 'perfil', 'categoria', 'tipo_solicitante', 'tipo_de_solicitante')


def ler(payload, chaves):
    for chave in chaves:
        valor = payload.get(chave)
        if valor is None:
            continue
        valor = str(valor).strip()
        if valor:
            return valor
    return ''


def centavos_de(texto):
    return int(re.sub(r'\D', '', texto) or '0')


def moeda(valor_em_centavos):
    reais, resto = divmod(valor_em_centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def cpf_confere(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    corpo = digitos[:9]
    digito1 = (sum(digito * peso for digito, peso in zip(corpo, range(10, 1, -1))) * 10) % 11 % 10
    decimo = corpo + [digito1]
    digito2 = (sum(digito * peso for digito, peso in zip(decimo, range(11, 1, -1))) * 10) % 11 % 10
    return digitos[9] == digito1 and digitos[10] == digito2


def validar(dados, docentes):
    erros = []
    obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if not docentes:
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not dados[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if dados['n_usp'] and not dados['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if dados['agencia'] and not dados['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if dados['valor_solicitado'] and centavos_de(dados['valor_solicitado']) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    if dados['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', dados['email']):
        erros.append('E-mail inválido')
    if dados['cpf']:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', dados['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_confere(dados['cpf']):
            erros.append('CPF inválido')
    if dados['cep'] and not re.fullmatch(r'\d{5}-\d{3}', dados['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if dados['data_nascimento']:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', dados['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(dados['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def oficio(dados, docentes):
    programa = dados['programa']
    if docentes:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    else:
        nivel = dados['nivel']
        assunto = 'Solicitação de Auxílio Financeiro - ' + dados['tipo_auxilio']
        linha_programa = f'Programa: {programa} - {nivel}'
    nome = dados['nome_completo']
    n_usp = dados['n_usp']
    email = dados['email']
    nome_evento = dados['nome_evento']
    periodo = dados['periodo_evento']
    local = ' - '.join([dados['cidade_evento'], dados['estado_evento'], dados['pais_evento']])
    valor = moeda(centavos_de(dados['valor_solicitado']))
    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {nome_evento}',
        f'Período: {periodo}',
        f'Local: {local}',
    ]
    if dados['link_evento']:
        linhas.append('Link do evento: ' + dados['link_evento'])
    linhas += [
        'Apresentação de trabalho: ' + dados['apresentacao'],
        'Valor solicitado: ' + valor,
        'Detalhamento: ' + dados['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        dados['logradouro'] + ', ' + dados['numero'],
    ]
    if dados['complemento']:
        linhas.append('Complemento: ' + dados['complemento'])
    linhas += [
        'CEP: ' + dados['cep'],
        dados['bairro'] + ', ' + dados['cidade'] + ' - ' + dados['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + dados['data_nascimento'],
        'CPF: ' + dados['cpf'],
        'RG / RNM: ' + dados['rg_rnm'],
        'Banco: ' + dados['nome_banco'],
        'Agência: ' + dados['agencia'],
        'Conta: ' + dados['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def registrar(payload: dict = Body(...)):
    docentes = any('docent' in str(payload.get(chave, '')).lower() for chave in DISCRIMINADORES)
    dados = {nome: ler(payload, chaves) for nome, chaves in CAMPOS.items()}
    if not docentes:
        dados['nivel'] = ler(payload, ('nivel', 'NÍVEL'))
        dados['tipo_auxilio'] = ler(payload, ('tipo_auxilio', 'tipo_de_auxilio', 'TIPO DE AUXÍLIO'))
    erros = validar(dados, docentes)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': oficio(dados, docentes)}
