# Solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

OBRIGATORIOS = {
    'alunos': [
        'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
        'evento', 'periodo', 'cidade', 'estado', 'pais', 'valor',
        'detalhamento', 'apresentacao', 'nascimento', 'logradouro', 'numero',
        'bairro', 'cep', 'cidade_end', 'estado_end', 'cpf', 'rg', 'banco',
        'agencia', 'conta',
    ],
    'docentes': [
        'nome_completo', 'n_usp', 'programa', 'email', 'evento', 'periodo',
        'cidade', 'estado', 'pais', 'valor', 'detalhamento', 'apresentacao',
        'nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade_end',
        'estado_end', 'cpf', 'rg', 'banco', 'agencia', 'conta',
    ],
}


class Solicitacao(BaseModel):
    aba: str = 'alunos'
    dados: dict = {}


app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')
app.mount('/assets', StaticFiles(directory=str(BASE / 'assets')), name='assets')


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html', media_type='text/html; charset=utf-8')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css; charset=utf-8')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js', media_type='text/javascript; charset=utf-8')


def _texto(dados, chave):
    valor = (dados or {}).get(chave)
    return '' if valor is None else str(valor).strip()


def _digitos(texto):
    return re.sub('[^0-9]', '', texto)


def _cpf_valido(digitos):
    def verificador(parcial):
        soma = sum(int(d) * (len(parcial) + 1 - i) for i, d in enumerate(parcial))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    return verificador(digitos[:9]) == digitos[9] and verificador(digitos[:10]) == digitos[10]


def _data_valida(digitos):
    try:
        datetime.date(int(digitos[4:]), int(digitos[2:4]), int(digitos[:2]))
    except ValueError:
        return False
    return True


def validar(dados, aba):
    obrigatorios = OBRIGATORIOS.get(aba, OBRIGATORIOS['alunos'])
    erros = []
    if any(not _texto(dados, chave) for chave in obrigatorios):
        erros.append('Preencha todos os campos')
    n_usp = _texto(dados, 'n_usp')
    if n_usp and not re.fullmatch('[0-9]+', n_usp):
        erros.append('N. USP deve conter apenas números')
    agencia = _texto(dados, 'agencia')
    if agencia and not re.fullmatch('[0-9]+', agencia):
        erros.append('Número da agência deve conter apenas números')
    valor = _texto(dados, 'valor')
    if valor and (not _digitos(valor) or int(_digitos(valor)) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    email = _texto(dados, 'email')
    if email:
        local, _, dominio = email.partition('@')
        if not local or not dominio or '@' in dominio:
            erros.append('E-mail inválido')
    cpf = _texto(dados, 'cpf')
    if cpf:
        digitos = _digitos(cpf)
        if len(digitos) != 11:
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(digitos):
            erros.append('CPF inválido')
    cep = _texto(dados, 'cep')
    if cep and len(_digitos(cep)) != 8:
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = _texto(dados, 'nascimento')
    if nascimento:
        digitos = _digitos(nascimento)
        if len(digitos) != 8:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not _data_valida(digitos):
            erros.append('Data de nascimento inválida')
    return erros


def _moeda(digitos):
    centavos = int(digitos)
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def _cpf_formatado(digitos):
    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


def _cep_formatado(digitos):
    return f'{digitos[:5]}-{digitos[5:]}'


def _data_formatada(digitos):
    return f'{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}'


def gerar_oficio(aba, dados):
    v = {}
    for chave in (
        'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
        'evento', 'periodo', 'cidade', 'estado', 'pais', 'link', 'valor',
        'detalhamento', 'apresentacao', 'nascimento', 'logradouro', 'numero',
        'complemento', 'bairro', 'cep', 'cidade_end', 'estado_end', 'cpf',
        'rg', 'banco', 'agencia', 'conta',
    ):
        v[chave] = _texto(dados, chave)

    linhas = [
        'Interessada(o): ' + v['nome_completo'] + ' - ' + v['n_usp'],
        'E-mail: ' + v['email'],
    ]
    if aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: ' + v['programa'])
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - ' + v['tipo_auxilio'])
        linhas.append('Programa: ' + v['programa'] + ' - ' + v['nivel'])
    linhas += [
        '',
        'A CCP-' + v['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + v['evento'],
        'Período: ' + v['periodo'],
        'Local: ' + v['cidade'] + ' - ' + v['estado'] + ' - ' + v['pais'],
    ]
    if v['link']:
        linhas.append('Link do evento: ' + v['link'])
    linhas += [
        'Apresentação de trabalho: ' + v['apresentacao'],
        'Valor solicitado: ' + _moeda(_digitos(v['valor'])),
        'Detalhamento: ' + v['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        v['logradouro'] + ', ' + v['numero'],
    ]
    if v['complemento']:
        linhas.append('Complemento: ' + v['complemento'])
    linhas += [
        'CEP: ' + _cep_formatado(_digitos(v['cep'])),
        v['bairro'] + ', ' + v['cidade_end'] + ' - ' + v['estado_end'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + _data_formatada(_digitos(v['nascimento'])),
        'CPF: ' + _cpf_formatado(_digitos(v['cpf'])),
        'RG / RNM: ' + v['rg'],
        'Banco: ' + v['banco'],
        'Agência: ' + v['agencia'],
        'Conta: ' + v['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/validar')
def api_validar(solicitacao: Solicitacao):
    erros = validar(solicitacao.dados, solicitacao.aba)
    if erros:
        return {'valido': False, 'erros': erros, 'oficio': ''}
    aba = 'docentes' if solicitacao.aba == 'docentes' else 'alunos'
    return {'valido': True, 'erros': [], 'oficio': gerar_oficio(aba, solicitacao.dados)}
