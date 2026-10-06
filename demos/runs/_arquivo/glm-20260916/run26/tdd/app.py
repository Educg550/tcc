import re
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação do IME-USP')


class Solicitacao(BaseModel):
    aba: str = 'alunos'
    nome_completo: str = ''
    numero_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    nome_evento: str = ''
    periodo_evento: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link_evento: str = ''
    valor_solicitado: Union[str, int, float] = ''
    detalhamento: str = ''
    apresentacao_trabalho: str = ''
    data_nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rg: str = ''
    nome_banco: str = ''
    numero_agencia: str = ''
    numero_conta: str = ''


OBRIGATORIOS = (
    'aba', 'nome_completo', 'numero_usp', 'programa', 'email', 'nome_evento',
    'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
    'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
    'estado', 'cpf', 'rg', 'nome_banco', 'numero_agencia', 'numero_conta',
)
SO_DE_ALUNOS = ('nivel', 'tipo_auxilio')


def _docentes(aba: str) -> bool:
    return aba.strip().lower() in ('docentes', 'docente', 'professor')


def _centavos(valor) -> int | None:
    texto = str(valor).upper().replace('R$', '').replace(' ', '')
    if not texto or '-' in texto:
        return None
    if ',' in texto:
        reais, _, centavos = texto.partition(',')
        reais = re.sub('[^0-9]', '', reais) or '0'
        centavos = (re.sub('[^0-9]', '', centavos) + '00')[:2]
        return int(reais) * 100 + int(centavos)
    digitos = re.sub('[^0-9]', '', texto)
    return int(digitos) if digitos else None


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in cpf if c in '0123456789']
    if len(numeros) != 11:
        return False
    for passo in (9, 10):
        soma = sum(numeros[i] * (passo + 1 - i) for i in range(passo))
        if numeros[passo] != (soma * 10) % 11 % 10:
            return False
    return True


def _erros(s: Solicitacao) -> list:
    campos = OBRIGATORIOS if _docentes(s.aba) else OBRIGATORIOS + SO_DE_ALUNOS
    erros = []
    if any(not getattr(s, campo, '').strip() for campo in campos):
        erros.append('Preencha todos os campos')
    if s.numero_usp.strip() and not re.fullmatch('[0-9]+', s.numero_usp.strip()):
        erros.append('N. USP deve conter apenas números')
    if s.numero_agencia.strip() and not re.fullmatch('[0-9]+', s.numero_agencia.strip()):
        erros.append('Número da agência deve conter apenas números')
    if str(s.valor_solicitado).strip():
        centavos = _centavos(s.valor_solicitado)
        if centavos is None or centavos <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if s.email.strip():
        partes = s.email.strip().split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')
    cpf = s.cpf.strip()
    if cpf:
        if not re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')
    if s.cep.strip() and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', s.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = s.data_nascimento.strip()
    if nascimento:
        if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def _moeda(centavos: int) -> str:
    texto = str(centavos).rjust(3, '0')
    inteira, centavos_txt = texto[:-2], texto[-2:]
    partes = []
    while len(inteira) > 3:
        partes.insert(0, inteira[-3:])
        inteira = inteira[:-3]
    partes.insert(0, inteira)
    return 'R$ ' + '.'.join(partes) + ',' + centavos_txt


def _oficio(s: Solicitacao) -> str:
    docente = _docentes(s.aba)
    programa = s.programa.strip()
    linhas = [
        'Interessada(o): ' + s.nome_completo.strip() + ' - ' + s.numero_usp.strip(),
        'E-mail: ' + s.email.strip(),
        'Assunto: Solicitação de Auxílio Financeiro - '
        + ('Verba do programa' if docente else s.tipo_auxilio.strip()),
        'Programa: ' + programa + ('' if docente else ' - ' + s.nivel.strip()),
        '',
        'A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + s.nome_evento.strip(),
        'Período: ' + s.periodo_evento.strip(),
        'Local: ' + s.cidade_evento.strip() + ' - ' + s.estado_evento.strip() + ' - ' + s.pais_evento.strip(),
    ]
    if s.link_evento.strip():
        linhas.append('Link do evento: ' + s.link_evento.strip())
    linhas.extend([
        'Apresentação de trabalho: ' + s.apresentacao_trabalho.strip(),
        'Valor solicitado: ' + _moeda(_centavos(s.valor_solicitado) or 0),
        'Detalhamento: ' + s.detalhamento.strip(),
        '',
        'Endereço da(o) interessada(o)',
        s.logradouro.strip() + ', ' + s.numero.strip(),
    ])
    if s.complemento.strip():
        linhas.append('Complemento: ' + s.complemento.strip())
    linhas.extend([
        'CEP: ' + s.cep.strip(),
        s.bairro.strip() + ', ' + s.cidade.strip() + ' - ' + s.estado.strip(),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + s.data_nascimento.strip(),
        'CPF: ' + s.cpf.strip(),
        'RG / RNM: ' + s.rg.strip(),
        'Banco: ' + s.nome_banco.strip(),
        'Agência: ' + s.numero_agencia.strip(),
        'Conta: ' + s.numero_conta.strip(),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def registrar_solicitacao(solicitacao: Solicitacao):
    erros = _erros(solicitacao)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': _oficio(solicitacao)}


if (BASE / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')


@app.get('/', include_in_schema=False)
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css', include_in_schema=False)
def folha_de_estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js', include_in_schema=False)
def roteiro():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')
