import 
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent


def _pegar(dados, *chaves):
    for chave in chaves:
        valor = dados.get(chave)
        if valor is not None:
            texto = str(valor).strip()
            if texto:
                return texto
    return ''


def _centavos(valor):
    digitos = re.sub(r'\D', '', valor)
    return int(digitos) if digitos else 0


def _moeda(centavos):
    reais = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {reais},{centavos % 100:02d}'


def _cpf_valido(cpf):
    digitos = re.sub(r'\D', '', cpf)

    def digito(parte, peso):
        soma = sum(int(caractere) * (peso - posicao) for posicao, caractere in enumerate(parte))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    calculado = f'{digito(digitos[:9], 10)}{digito(digitos[:10], 11)}'
    return len(digitos) == 11 and calculado == digitos[9:]


app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação do IME-USP')


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')


@app.post('/solicitar')
async def solicitar(request: Request):
    corpo = await request.body()
    try:
        dados = .loads(corpo)
        if not isinstance(dados, dict):
            dados = {}
    except ValueError:
        dados = {chave: lista[0] for chave, lista in parse_qs(corpo.decode('utf-8', 'replace')).items()}

    valores = {
        'nome': _pegar(dados, 'nome', 'nome_completo_sem_abreviar'),
        'nusp': _pegar(dados, 'n_usp', 'nusp', 'numero_usp'),
        'programa': _pegar(dados, 'programa'),
        'nivel': _pegar(dados, 'nivel'),
        'auxilio': _pegar(dados, 'auxilio', 'tipo_de_auxilio', 'tipo_auxilio'),
        'email': _pegar(dados, 'email'),
        'evento': _pegar(dados, 'evento', 'nome_do_evento'),
        'periodo': _pegar(dados, 'periodo'),
        'cidade_evento': _pegar(dados, 'cidade_evento'),
        'estado_evento': _pegar(dados, 'estado_evento'),
        'pais': _pegar(dados, 'pais'),
        'link': _pegar(dados, 'link', 'link_evento'),
        'valor': _pegar(dados, 'valor', 'valor_solicitado'),
        'detalhamento': _pegar(dados, 'detalhamento', 'detalhamento_pedido'),
        'apresentacao': _pegar(dados, 'apresentacao'),
        'nascimento': _pegar(dados, 'nascimento', 'data_nascimento', 'data_de_nascimento'),
        'logradouro': _pegar(dados, 'logradouro'),
        'numero': _pegar(dados, 'numero'),
        'complemento': _pegar(dados, 'complemento'),
        'bairro': _pegar(dados, 'bairro'),
        'cep': _pegar(dados, 'cep'),
        'cidade': _pegar(dados, 'cidade'),
        'estado': _pegar(dados, 'estado'),
        'cpf': _pegar(dados, 'cpf'),
        'rg': _pegar(dados, 'rg', 'rg_rnm', 'rnm'),
        'banco': _pegar(dados, 'banco'),
        'agencia': _pegar(dados, 'agencia'),
        'conta': _pegar(dados, 'conta'),
    }

    aba = str(dados.get('aba') or '').strip().lower()
    docente = aba == 'docentes' or (not aba and not valores['nivel'] and not valores['auxilio'])

    erros = []
    obrigatorios = [
        'nome', 'nusp', 'programa', 'email', 'evento', 'periodo', 'cidade_evento',
        'estado_evento', 'pais', 'valor', 'detalhamento', 'apresentacao', 'nascimento',
        'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
        'banco', 'agencia', 'conta',
    ]
    if not docente:
        obrigatorios += ['nivel', 'auxilio']
    if any(not valores[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if valores['nusp'] and not valores['nusp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if valores['agencia'] and not valores['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if valores['valor'] and _centavos(valores['valor']) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    local, arroba, dominio = valores['email'].partition('@')
    if valores['email'] and (not arroba or not local or not dominio):
        erros.append('E-mail inválido')

    if valores['cpf'] and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', valores['cpf']):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif valores['cpf'] and not _cpf_valido(valores['cpf']):
        erros.append('CPF inválido')

    if valores['cep'] and not re.fullmatch(r'\d{5}-\d{3}', valores['cep']):
        erros.append('CEP deve estar no formato 00000-000')

    if valores['nascimento'] and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', valores['nascimento']):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif valores['nascimento']:
        try:
            datetime.strptime(valores['nascimento'], '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    if erros:
        return {'ok': False, 'erros': erros}

    if docente:
        identidade = [
            'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
            'Programa: {programa}',
        ]
    else:
        identidade = [
            'Assunto: Solicitação de Auxílio Financeiro - {auxilio}',
            'Programa: {programa} - {nivel}',
        ]

    partes = [
        'Interessada(o): {nome} - {nusp}',
        'E-mail: {email}',
        *identidade,
        '',
        'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: {evento}',
        'Período: {periodo}',
        'Local: {cidade_evento} - {estado_evento} - {pais}',
    ]
    if valores['link']:
        partes.append('Link do evento: {link}')
    partes += [
        'Apresentação de trabalho: {apresentacao}',
        'Valor solicitado: ' + _moeda(_centavos(valores['valor'])),
        'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        '{logradouro}, {numero}',
    ]
    if valores['complemento']:
        partes.append('Complemento: {complemento}')
    partes += [
        'CEP: {cep}',
        '{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        'Data de nascimento: {nascimento}',
        'CPF: {cpf}',
        'RG / RNM: {rg}',
        'Banco: {banco}',
        'Agência: {agencia}',
        'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    oficio = '\n'.join(parte.format(**valores) for parte in partes)
    return {'ok': True, 'oficio': oficio}


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')
