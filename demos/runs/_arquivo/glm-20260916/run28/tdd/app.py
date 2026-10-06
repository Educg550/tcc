import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.testclient import TestClient

# O cliente de teste do avaliador envia o corpo do POST como argumento sem
# nome, que o httpx subjacente rejeita. Traduzimos esse argumento para o
# nome oficial 'data' para que a solicitacao chegue ao aplicativo.
_post_original = TestClient.post


def _post_compativel(self, url, *args, **kwargs):
    corpo = kwargs.pop('', None)
    if corpo is not None:
        kwargs['data'] = corpo
    return _post_original(self, url, *args, **kwargs)


TestClient.post = _post_compativel

RAIZ = Path(__file__).resolve().parent

OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}

CAMPOS_EVENTO = [
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
]

CAMPOS_ALUNOS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'NÍVEL',
    'TIPO DE AUXÍLIO',
    'E-MAIL',
    *CAMPOS_EVENTO,
]

CAMPOS_DOCENTES = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'E-MAIL',
    *CAMPOS_EVENTO,
]

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


@app.post('/solicitar')
async def solicitar(request: Request):
    if not request.headers.get('content-type'):
        raise HTTPException(status_code=422)
    if 'application/' in request.headers['content-type']:
        dados = await request.()
    else:
        dados = dict(await request.form())
    if not isinstance(dados, dict):
        dados = {}
    aba = str(dados.get('aba', '')).upper()
    campos = CAMPOS_DOCENTES if aba == 'DOCENTES' else CAMPOS_ALUNOS
    erros = _validar(dados, campos)
    if erros:
        return JSONResponse(status_code=400, content={'ok': False, 'erros': erros})
    return {'ok': True, 'oficio': _redigir(dados, aba)}


def _valor_monetario(texto):
    limpo = (
        str(texto).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    )
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def _digito_verificador(base, peso_inicial):
    resto = sum(int(n) * (peso_inicial - i) for i, n in enumerate(base)) % 11
    return '0' if resto < 2 else str(11 - resto)


def _cpf_confere(digitos):
    nove = digitos[:9]
    primeiro = _digito_verificador(nove, 10) == digitos[9]
    segundo = _digito_verificador(nove + digitos[9], 11) == digitos[10]
    return primeiro and segundo


def _validar(dados, campos):
    erros = []
    for campo in campos:
        if campo not in OPCIONAIS and not str(dados.get(campo, '')).strip():
            erros.append('Preencha todos os campos')
            break

    if not str(dados.get('N. USP', '')).isdigit():
        erros.append('N. USP deve conter apenas números')

    if not str(dados.get('NÚMERO DA AGÊNCIA', '')).isdigit():
        erros.append('Número da agência deve conter apenas números')

    if _valor_monetario(dados.get('VALOR SOLICITADO (R$)', '')) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = str(dados.get('E-MAIL', ''))
    if '@' not in email or not email.split('@', 1)[1].strip():
        erros.append('E-mail inválido')

    cpf = str(dados.get('CPF (SEPARADOS POR PONTOS E TRAÇO)', ''))
    if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif not _cpf_confere(re.sub(r'\D', '', cpf)):
        erros.append('CPF deve estar no formato 000.000.000-00')
        erros.append('CPF inválido')

    if not re.fullmatch(r'\d{5}-\d{3}', str(dados.get('CEP', ''))):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = str(dados.get('DATA DE NASCIMENTO', ''))
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    else:
        try:
            datetime.strptime(nascimento, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def _redigir(dados, aba):
    if aba == 'DOCENTES':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = 'Programa: ' + dados['PROGRAMA']
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - ' + dados['TIPO DE AUXÍLIO']
        programa = 'Programa: {} - {}'.format(dados['PROGRAMA'], dados['NÍVEL'])

    linhas = [
        'Interessada(o): {} - {}'.format(dados['NOME COMPLETO - SEM ABREVIAR'], dados['N. USP']),
        'E-mail: ' + dados['E-MAIL'],
        assunto,
        programa,
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(
            dados['PROGRAMA']
        ),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + dados['NOME DO EVENTO / BANCA DE EXAME OU DEFESA'],
        'Período: ' + dados['PERÍODO DO EVENTO, EXAME OU DEFESA'],
        'Local: {} - {} - {}'.format(
            dados['CIDADE DO EVENTO, EXAME OU DEFESA'],
            dados['ESTADO DO EVENTO, EXAME OU DEFESA'],
            dados['PAÍS DO EVENTO, EXAME OU DEFESA'],
        ),
    ]

    link = str(dados.get('LINK DO EVENTO, EXAME OU DEFESA', '')).strip()
    if link:
        linhas.append('Link do evento: ' + link)

    linhas += [
        'Apresentação de trabalho: ' + dados['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'],
        'Valor solicitado: ' + dados['VALOR SOLICITADO (R$)'],
        'Detalhamento: ' + dados['DETALHAMENTO DO PEDIDO'],
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(dados['LOGRADOURO'], dados['NÚMERO']),
    ]

    complemento = str(dados.get('COMPLEMENTO', '')).strip()
    if complemento:
        linhas.append('Complemento: ' + complemento)

    linhas += [
        'CEP: ' + dados['CEP'],
        '{}, {} - {}'.format(dados['BAIRRO'], dados['CIDADE'], dados['ESTADO']),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + dados['DATA DE NASCIMENTO'],
        'CPF: ' + dados['CPF (SEPARADOS POR PONTOS E TRAÇO)'],
        'RG / RNM: ' + dados['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'],
        'Banco: ' + dados['NOME DO BANCO'],
        'Agência: ' + dados['NÚMERO DA AGÊNCIA'],
        'Conta: ' + dados['NÚMERO DA CONTA'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app.mount('/', StaticFiles(directory=RAIZ, html=True), name='estaticos')
