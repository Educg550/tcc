import re
from datetime import datetime
from pathlib import Path
from unicodedata import normalize
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

raiz = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação do IME-USP')


def _candidatos(rotulo, apelidos):
    sem_acento = normalize('NFKD', rotulo).encode('ascii', 'ignore').decode()
    base = re.sub(r'[^0-9a-z]+', '_', sem_acento.lower()).strip('_')
    chaves = []
    for chave in list(apelidos) + [rotulo, rotulo.lower(), sem_acento,
                                   sem_acento.lower(), base, base.upper()]:
        if chave not in chaves:
            chaves.append(chave)
    return chaves


CAMPOS = {
    'nome': _candidatos('NOME COMPLETO - SEM ABREVIAR',
                        ['nome', 'nome_completo', 'nomeCompleto',
                         'nome_completo_sem_abreviar']),
    'n_usp': _candidatos('N. USP',
                         ['n_usp', 'nUsp', 'nusp', 'numero_usp', 'num_usp',
                          'numeroUSP', 'numusp']),
    'programa': _candidatos('PROGRAMA', ['programa']),
    'nivel': _candidatos('NÍVEL', ['nivel', 'nível', 'grau']),
    'tipo_auxilio': _candidatos('TIPO DE AUXÍLIO',
                                ['tipo_auxilio', 'tipo_de_auxilio', 'tipoAuxilio',
                                 'auxilio']),
    'email': _candidatos('E-MAIL', ['email', 'e_mail', 'e-mail', 'eMail']),
    'evento': _candidatos('NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
                          ['evento', 'nome_evento', 'nome_do_evento', 'nomeEvento']),
    'periodo': _candidatos('PERÍODO DO EVENTO, EXAME OU DEFESA',
                           ['periodo', 'periodo_evento', 'periodo_do_evento',
                            'periodoEvento']),
    'cidade_evento': _candidatos('CIDADE DO EVENTO, EXAME OU DEFESA',
                                 ['cidade_evento', 'cidade_do_evento', 'cidadeEvento']),
    'estado_evento': _candidatos('ESTADO DO EVENTO, EXAME OU DEFESA',
                                 ['estado_evento', 'estado_do_evento', 'estadoEvento',
                                  'uf_evento']),
    'pais_evento': _candidatos('PAÍS DO EVENTO, EXAME OU DEFESA',
                               ['pais_evento', 'pais_do_evento', 'paisEvento', 'pais']),
    'link': _candidatos('LINK DO EVENTO, EXAME OU DEFESA',
                        ['link', 'link_evento', 'link_do_evento', 'url', 'url_evento']),
    'valor': _candidatos('VALOR SOLICITADO (R$)',
                         ['valor', 'valor_solicitado', 'valorSolicitado',
                          'valor_solicitado_rs']),
    'detalhamento': _candidatos('DETALHAMENTO DO PEDIDO',
                                ['detalhamento', 'detalhamento_pedido',
                                 'detalhamento_do_pedido', 'detalhamentoPedido',
                                 'descricao']),
    'apresentacao': _candidatos('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
                                ['apresentacao', 'apresentacao_trabalho',
                                 'apresentacao_de_trabalho', 'ira_apresentar_trabalho',
                                 'trabalho']),
    'data_nascimento': _candidatos('DATA DE NASCIMENTO',
                                   ['data_nascimento', 'data_de_nascimento',
                                    'nascimento', 'dataDeNascimento']),
    'logradouro': _candidatos('LOGRADOURO', ['logradouro', 'endereco']),
    'numero': _candidatos('NÚMERO',
                          ['numero', 'numero_endereco', 'num_endereco', 'numeroEndereco']),
    'complemento': _candidatos('COMPLEMENTO', ['complemento']),
    'bairro': _candidatos('BAIRRO', ['bairro']),
    'cep': _candidatos('CEP', ['cep']),
    'cidade': _candidatos('CIDADE', ['cidade']),
    'estado': _candidatos('ESTADO', ['estado', 'uf']),
    'cpf': _candidatos('CPF (SEPARADOS POR PONTOS E TRAÇO)',
                       ['cpf', 'numero_cpf', 'numero_de_cpf']),
    'rg_rnm': _candidatos('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
                          ['rg_rnm', 'rg', 'rnm', 'rg_ou_rnm', 'rgRnm']),
    'banco': _candidatos('NOME DO BANCO',
                         ['banco', 'nome_banco', 'nome_do_banco', 'nomeBanco']),
    'agencia': _candidatos('NÚMERO DA AGÊNCIA',
                           ['agencia', 'numero_agencia', 'num_agencia',
                            'numero_da_agencia', 'numeroAgencia']),
    'conta': _candidatos('NÚMERO DA CONTA',
                         ['conta', 'numero_conta', 'num_conta', 'numero_da_conta',
                          'numeroConta']),
}

CHAVES_DE_ABA = ['aba', 'formulario', 'form', 'origem', 'perfil', 'categoria',
                 'papel', 'modo', 'secao', 'tipo_solicitacao', 'tipo_formulario',
                 'tipo_de_solicitacao', 'tipo_solicitante']


async def _corpo(request: Request):
    if '' in request.headers.get('content-type', ''):
        try:
            dados = await request.()
        except ValueError:
            return {}
        return dados if isinstance(dados, dict) else {}
    formulario = parse_qs((await request.body()).decode('utf-8', 'replace'),
                          keep_blank_values=True)
    return {chave: valores[0] for chave, valores in formulario.items()}


def _valor(dados, campo):
    for chave in CAMPOS[campo]:
        if chave in dados:
            return str(dados[chave]).strip()
    return ''


def _aba(dados):
    for chave in CHAVES_DE_ABA:
        if str(dados.get(chave, '')).strip().upper() in ('DOCENTES', 'DOCENTE'):
            return 'DOCENTES'
    return 'ALUNOS'


def _moeda(centavos):
    inteiro, resto = divmod(centavos, 100)
    return 'R$ ' + f'{inteiro:,}'.replace(',', '.') + f',{resto:02d}'


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    resto = sum(digito * peso for digito, peso
                in zip(digitos[:9], range(10, 1, -1))) % 11
    if (0 if resto < 2 else 11 - resto) != digitos[9]:
        return False
    resto = sum(digito * peso for digito, peso
                in zip(digitos[:10], range(11, 1, -1))) % 11
    return (0 if resto < 2 else 11 - resto) == digitos[10]


def _oficio(f, aba):
    if aba == 'DOCENTES':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + f['programa']
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + f['tipo_auxilio']
        linha_programa = 'Programa: ' + f['programa'] + ' - ' + f['nivel']
    linhas = [
        'Interessada(o): ' + f['nome'] + ' - ' + f['n_usp'],
        'E-mail: ' + f['email'],
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-' + f['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + f['evento'],
        'Período: ' + f['periodo'],
        'Local: ' + f['cidade_evento'] + ' - ' + f['estado_evento'] + ' - ' + f['pais_evento'],
    ]
    if f['link']:
        linhas.append('Link do evento: ' + f['link'])
    linhas += [
        'Apresentação de trabalho: ' + f['apresentacao'],
        'Valor solicitado: ' + _moeda(int(re.sub(r'\D', '', f['valor']))),
        'Detalhamento: ' + f['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        f['logradouro'] + ', ' + f['numero'],
    ]
    if f['complemento']:
        linhas.append('Complemento: ' + f['complemento'])
    linhas += [
        'CEP: ' + f['cep'],
        f['bairro'] + ', ' + f['cidade'] + ' - ' + f['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + f['data_nascimento'],
        'CPF: ' + f['cpf'],
        'RG / RNM: ' + f['rg_rnm'],
        'Banco: ' + f['banco'],
        'Agência: ' + f['agencia'],
        'Conta: ' + f['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
async def solicitacao(request: Request):
    dados = await _corpo(request)
    aba = _aba(dados)
    f = {campo: _valor(dados, campo) for campo in CAMPOS}
    obrigatorios = [campo for campo in CAMPOS
                    if campo not in ('link', 'complemento', 'nivel', 'tipo_auxilio')]
    if aba == 'ALUNOS':
        obrigatorios += ['nivel', 'tipo_auxilio']
    erros = []
    if any(not f[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if f['n_usp'] and not f['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if f['agencia'] and not f['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if f['valor']:
        digitos = re.sub(r'\D', '', f['valor'])
        if not digitos or int(digitos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if f['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+', f['email']):
        erros.append('E-mail inválido')
    if f['cpf']:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', f['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(f['cpf']):
            erros.append('CPF inválido')
    if f['cep'] and not re.fullmatch(r'\d{5}-\d{3}', f['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if f['data_nascimento']:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', f['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(f['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    if erros:
        return JSONResponse({'erros': erros}, status_code=400)
    return {'oficio': _oficio(f, aba)}


app.mount('/assets', StaticFiles(directory=raiz / 'assets'), name='assets')
app.mount('/', StaticFiles(directory=raiz, html=True), name='raiz')
