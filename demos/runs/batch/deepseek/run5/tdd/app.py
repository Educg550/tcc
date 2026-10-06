import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

CAMPOS_COMUNS = (
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor_solicitado',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro', 'numero',
    'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
)


def _texto(valor):
    return str(valor) if valor is not None else ''


def _digitos(valor):
    return re.sub(r'\D', '', _texto(valor))


def _moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{centavos:02d}'


def _cpf_valido(digitos):
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[j]) * (posicao + 1 - j) for j in range(posicao))
        resto = soma * 10 % 11
        if (0 if resto == 10 else resto) != int(digitos[posicao]):
            return False
    return True


def _validar(dados, aluno):
    erros = []
    obrigatorios = list(CAMPOS_COMUNS)
    if aluno:
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not _texto(dados.get(campo)).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _texto(dados.get('n_usp')).strip()
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = _texto(dados.get('agencia')).strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = _texto(dados.get('valor_solicitado')).strip()
    if valor and (not _digitos(valor) or int(_digitos(valor)) <= 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = _texto(dados.get('email')).strip()
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        erros.append('E-mail inválido')

    cpf = _digitos(dados.get('cpf'))
    if cpf:
        if len(cpf) != 11:
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = _digitos(dados.get('cep'))
    if cep and len(cep) != 8:
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = _digitos(dados.get('data_nascimento'))
    if nascimento:
        if len(nascimento) != 8:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                date(int(nascimento[4:]), int(nascimento[2:4]), int(nascimento[:2]))
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def _oficio(dados, aluno):
    def campo(nome):
        return _texto(dados.get(nome)).strip()

    programa = campo('programa')
    if aluno:
        assunto = f'Solicitação de Auxílio Financeiro - {campo("tipo_auxilio")}'
        identificacao = f'{programa} - {campo("nivel")}'
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        identificacao = programa

    cpf = _digitos(dados.get('cpf'))
    cep = _digitos(dados.get('cep'))
    nascimento = _digitos(dados.get('data_nascimento'))

    linhas = [
        f'Interessada(o): {campo("nome_completo")} - {campo("n_usp")}',
        f'E-mail: {campo("email")}',
        f'Assunto: {assunto}',
        f'Programa: {identificacao}',
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {campo("nome_evento")}',
        f'Período: {campo("periodo")}',
        f'Local: {campo("cidade_evento")} - {campo("estado_evento")} - {campo("pais_evento")}',
    ]

    if campo('link_evento'):
        linhas.append(f'Link do evento: {campo("link_evento")}')

    linhas += [
        f'Apresentação de trabalho: {campo("apresentacao")}',
        f'Valor solicitado: {_moeda(_digitos(dados.get("valor_solicitado")))}',
        f'Detalhamento: {campo("detalhamento")}',
        '',
        'Endereço da(o) interessada(o)',
        f'{campo("logradouro")}, {campo("numero")}',
    ]

    if campo('complemento'):
        linhas.append(f'Complemento: {campo("complemento")}')

    linhas += [
        f'CEP: {cep[:5]}-{cep[5:]}',
        f'{campo("bairro")}, {campo("cidade")} - {campo("estado")}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {nascimento[:2]}/{nascimento[2:4]}/{nascimento[4:]}',
        f'CPF: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}',
        f'RG / RNM: {campo("rg")}',
        f'Banco: {campo("banco")}',
        f'Agência: {campo("agencia")}',
        f'Conta: {campo("conta")}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    return '\n'.join(linhas)


@app.post('/solicitar')
def solicitar(dados: dict):
    aluno = 'nivel' in dados or 'tipo_auxilio' in dados
    erros = _validar(dados, aluno)
    if erros:
        return JSONResponse({'ok': False, 'erros': erros})
    return JSONResponse({'ok': True, 'oficio': _oficio(dados, aluno)})


@app.get('/')
def pagina_inicial():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js')


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')
