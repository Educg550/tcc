import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent


class Solicitacao(BaseModel):
    tipo: str
    campos: dict[str, str]


CAMPOS_ALUNOS = [
    'nome', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email', 'evento',
    'periodo', 'cidade_evento', 'estado_evento', 'pais_evento', 'link_evento',
    'valor', 'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
    'banco', 'agencia', 'conta',
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ('nivel', 'tipo_auxilio')]

app = FastAPI()


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False

    def digito(base: list, peso: int) -> int:
        resto = 11 - (sum(v * (peso - i) for i, v in enumerate(base)) % 11)
        return 0 if resto > 9 else resto

    return digito(digitos[:9], 10) == digitos[9] and digito(digitos[:10], 11) == digitos[10]


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r'\D', '', valor) or '0')
    reais, resto = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def validar(campos: dict, obrigatorios: list) -> list:
    erros = []
    if any(not campos.get(c) for c in obrigatorios):
        erros.append('Preencha todos os campos')
    if campos.get('n_usp') and not campos['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if campos.get('agencia') and not campos['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    digitos_valor = re.sub(r'\D', '', campos.get('valor', ''))
    if campos.get('valor') and (not digitos_valor or int(digitos_valor) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    if campos.get('email') and not re.fullmatch(r'[^@\s]+@[^@\s]+', campos['email']):
        erros.append('E-mail inválido')
    cpf = campos.get('cpf', '')
    if cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not cpf_valido(cpf):
        erros.append('CPF inválido')
    if campos.get('cep') and not re.fullmatch(r'\d{5}-\d{3}', campos['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    data = campos.get('data_nascimento', '')
    if data and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(campos: dict, alunos: bool) -> str:
    def campo(chave):
        return campos.get(chave, '')

    assunto = campo('tipo_auxilio') if alunos else 'Verba do programa'
    linha_programa = 'Programa: ' + campo('programa')
    if alunos:
        linha_programa += ' - ' + campo('nivel')
    linhas = [
        'Interessada(o): ' + campo('nome') + ' - ' + campo('n_usp'),
        'E-mail: ' + campo('email'),
        'Assunto: Solicitação de Auxílio Financeiro - ' + assunto,
        linha_programa,
        '',
        'A CCP-' + campo('programa') + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + campo('evento'),
        'Período: ' + campo('periodo'),
        'Local: ' + campo('cidade_evento') + ' - ' + campo('estado_evento') + ' - ' + campo('pais_evento'),
    ]
    if campo('link_evento'):
        linhas.append('Link do evento: ' + campo('link_evento'))
    linhas += [
        'Apresentação de trabalho: ' + campo('apresentacao'),
        'Valor solicitado: ' + formatar_moeda(campo('valor')),
        'Detalhamento: ' + campo('detalhamento'),
        '',
        'Endereço da(o) interessada(o)',
        campo('logradouro') + ', ' + campo('numero'),
    ]
    if campo('complemento'):
        linhas.append('Complemento: ' + campo('complemento'))
    linhas += [
        'CEP: ' + campo('cep'),
        campo('bairro') + ', ' + campo('cidade') + ' - ' + campo('estado'),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + campo('data_nascimento'),
        'CPF: ' + campo('cpf'),
        'RG / RNM: ' + campo('rg'),
        'Banco: ' + campo('banco'),
        'Agência: ' + campo('agencia'),
        'Conta: ' + campo('conta'),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def solicitar(req: Solicitacao):
    campos = {chave: (valor or '').strip() for chave, valor in req.campos.items()}
    alunos = req.tipo == 'alunos'
    erros = validar(campos, CAMPOS_ALUNOS if alunos else CAMPOS_DOCENTES)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(campos, alunos)}


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
app.mount('/', StaticFiles(directory=RAIZ, html=True), name='raiz')
