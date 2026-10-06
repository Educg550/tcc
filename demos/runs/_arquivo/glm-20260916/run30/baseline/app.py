import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

CAMPOS_ALUNOS = [
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
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ('NÍVEL', 'TIPO DE AUXÍLIO')]
OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}

EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
DIGITOS = re.compile(r'[0-9]+')
CPF_FORMATO = re.compile(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}')
CEP_FORMATO = re.compile(r'[0-9]{5}-[0-9]{3}')
DATA_FORMATO = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}')
NUMERO_VALOR = re.compile(r'[0-9]+(\.[0-9]+)?')


def valor_em_centavos(texto):
    t = texto.strip().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    if not NUMERO_VALOR.fullmatch(t):
        return None
    valor = float(t)
    if valor <= 0:
        return None
    return int(round(valor * 100))


def valor_formatado(centavos):
    reais, centavos = divmod(centavos, 100)
    return 'R$ {:,}'.format(reais).replace(',', '.') + ',{:02d}'.format(centavos)


def cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    dv1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def data_valida(texto):
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def validar_solicitacao(aba, dados):
    campos = CAMPOS_DOCENTES if aba == 'docentes' else CAMPOS_ALUNOS
    erros = []
    if any(not (dados.get(c) or '').strip() for c in campos if c not in OPCIONAIS):
        erros.append('Preencha todos os campos')
    n_usp = (dados.get('N. USP') or '').strip()
    if n_usp and not DIGITOS.fullmatch(n_usp):
        erros.append('N. USP deve conter apenas números')
    agencia = (dados.get('NÚMERO DA AGÊNCIA') or '').strip()
    if agencia and not DIGITOS.fullmatch(agencia):
        erros.append('Número da agência deve conter apenas números')
    valor = (dados.get('VALOR SOLICITADO (R$)') or '').strip()
    if valor and valor_em_centavos(valor) is None:
        erros.append('Valor solicitado deve ser maior que 0')
    email = (dados.get('E-MAIL') or '').strip()
    if email and not EMAIL.fullmatch(email):
        erros.append('E-mail inválido')
    cpf = (dados.get('CPF (SEPARADOS POR PONTOS E TRAÇO)') or '').strip()
    if cpf:
        if not CPF_FORMATO.fullmatch(cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')
    cep = (dados.get('CEP') or '').strip()
    if cep and not CEP_FORMATO.fullmatch(cep):
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = (dados.get('DATA DE NASCIMENTO') or '').strip()
    if nascimento:
        if not DATA_FORMATO.fullmatch(nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(nascimento):
            erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(aba, dados):
    def campo(nome):
        return (dados.get(nome) or '').strip()

    if aba == 'docentes':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + campo('PROGRAMA')
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + campo('TIPO DE AUXÍLIO')
        linha_programa = 'Programa: ' + campo('PROGRAMA') + ' - ' + campo('NÍVEL')

    linhas = [
        'Interessada(o): {} - {}'.format(campo('NOME COMPLETO - SEM ABREVIAR'), campo('N. USP')),
        'E-mail: ' + campo('E-MAIL'),
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(campo('PROGRAMA')),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + campo('NOME DO EVENTO / BANCA DE EXAME OU DEFESA'),
        'Período: ' + campo('PERÍODO DO EVENTO, EXAME OU DEFESA'),
        'Local: {} - {} - {}'.format(
            campo('CIDADE DO EVENTO, EXAME OU DEFESA'),
            campo('ESTADO DO EVENTO, EXAME OU DEFESA'),
            campo('PAÍS DO EVENTO, EXAME OU DEFESA'),
        ),
    ]
    link = campo('LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append('Link do evento: ' + link)
    linhas += [
        'Apresentação de trabalho: ' + campo('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'),
        'Valor solicitado: ' + valor_formatado(valor_em_centavos(campo('VALOR SOLICITADO (R$)'))),
        'Detalhamento: ' + campo('DETALHAMENTO DO PEDIDO'),
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(campo('LOGRADOURO'), campo('NÚMERO')),
    ]
    complemento = campo('COMPLEMENTO')
    if complemento:
        linhas.append('Complemento: ' + complemento)
    linhas += [
        'CEP: ' + campo('CEP'),
        '{}, {} - {}'.format(campo('BAIRRO'), campo('CIDADE'), campo('ESTADO')),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + campo('DATA DE NASCIMENTO'),
        'CPF: ' + campo('CPF (SEPARADOS POR PONTOS E TRAÇO)'),
        'RG / RNM: ' + campo('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'),
        'Banco: ' + campo('NOME DO BANCO'),
        'Agência: ' + campo('NÚMERO DA AGÊNCIA'),
        'Conta: ' + campo('NÚMERO DA CONTA'),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')


class SolicitacaoEntrada(BaseModel):
    model_config = {'extra': 'allow'}

    aba: str = ''
    tipo: str = ''
    dados: dict[str, object] = {}


@app.post('/solicitacao')
@app.post('/api/solicitacao')
def receber_solicitacao(entrada: SolicitacaoEntrada):
    aba = (entrada.aba or entrada.tipo or 'alunos').strip().lower()
    campos = {k: v for k, v in entrada.model_dump().items() if k not in ('aba', 'tipo', 'dados')}
    campos.update(entrada.dados)
    dados = {str(k): '' if v is None else str(v) for k, v in campos.items()}
    erros = validar_solicitacao(aba, dados)
    if erros:
        return {'valido': False, 'erros': erros, 'oficio': None}
    return {'valido': True, 'erros': [], 'oficio': gerar_oficio(aba, dados)}


app.mount('/', StaticFiles(directory=BASE, html=True), name='estaticos')
