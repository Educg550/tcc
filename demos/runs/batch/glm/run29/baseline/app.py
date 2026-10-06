'''
Aplicação web de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Backend em FastAPI: valida a solicitação e devolve o ofício já redigido.
Nenhuma persistência - a solicitação se encerra na resposta.
'''
import datetime
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')


class Oficio(BaseModel):
    '''Modelo da resposta: o ofício já formatado, pronto para a tela.'''
    oficio: str


@app.get('/', response_model=Oficio, include_in_schema=False)
def index() -> FileResponse:
    return FileResponse('index.html', media_type='text/html')


def valida_cpf(cpf: str) -> bool:
    '''Checa os dígitos verificadores do CPF em 000.000.000-00.'''
    digitos = [int(d) for d in re.sub(r'\D', '', cpf)]
    for i in (9, 10):
        resto = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, i - 10, -1))) % 11
        if (resto < 2 and digitos[i] != 0) or (resto >= 2 and digitos[i] != 11 - resto):
            return False
    return True


def valida_data(data: str) -> bool:
    '''Checa se a data em dd/mm/aaaa existe no calendário.'''
    try:
        dia, mes, ano = (int(p) for p in data.split('/'))
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formatar_valor(centavos: int) -> str:
    '''Converte centavos em moeda brasileira: 150000 -> R$ 1.500,00.'''
    reais, centavos_str = divmod(centavos, 100)
    partes = []
    while reais >= 1000:
        partes.insert(0, f'{reais % 1000:03d}')
        reais //= 1000
    partes.insert(0, str(reais))
    return f'R$ {".".join(partes)},{centavos_str:02d}'


def gerar_oficio(dados: dict) -> str:
    '''Preenche o ofício com os dados da solicitação validada.'''
    linhas = [
        f'Interessada(o): {dados["nome"]} - {dados["n_usp"]}',
        f'E-mail: {dados["email"]}',
    ]
    if dados.get('tipo_de_auxilio'):
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {dados["tipo_de_auxilio"]}')
        linhas.append(f'Programa: {dados["programa"]} - {dados["nivel"]}')
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {dados["programa"]}')
    linhas += [
        '',
        'A CCP-' + dados['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro',
        'para a interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + dados['nome_evento'],
        'Período: ' + dados['periodo'],
        f'Local: {dados["cidade_evento"]} - {dados["estado_evento"]} - {dados["pais"]}',
    ]
    if dados.get('link'):
        linhas.append('Link do evento: ' + dados['link'])
    linhas += [
        'Apresentação de trabalho: ' + dados['apresentacao'],
        'Valor solicitado: ' + formatar_valor(dados['valor_centavos']),
        'Detalhamento: ' + dados['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        f'{dados["logradouro"]}, {dados["numero"]}',
    ]
    if dados.get('complemento'):
        linhas.append('Complemento: ' + dados['complemento'])
    linhas += [
        'CEP: ' + dados['cep'],
        f'{dados["bairro"]}, {dados["cidade"]} - {dados["estado"]}',
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + dados['data_nascimento'],
        'CPF: ' + dados['cpf'],
        'RG / RNM: ' + dados['rg'],
        'Banco: ' + dados['banco'],
        'Agência: ' + dados['agencia'],
        'Conta: ' + dados['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao', response_model=Oficio)
def receber_solicitacao(dados: dict) -> dict:
    '''Valida a solicitação; com erro devolve a lista de mensagens, senão o ofício.'''
    obrigatorios = [
        'nome', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
        'cidade_evento', 'estado_evento', 'pais', 'valor_centavos', 'detalhamento',
        'apresentacao', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
        'data_nascimento', 'cpf', 'rg', 'banco', 'agencia', 'conta',
    ]
    if dados.get('aluno'):
        obrigatorios += ['nivel', 'tipo_de_auxilio']
    erros = []
    if any(not str(dados.get(campo, '')).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if not re.fullmatch(r'\d+', str(dados.get('n_usp', ''))):
        erros.append('N. USP deve conter apenas números')
    if not re.fullmatch(r'\d+', str(dados.get('agencia', ''))):
        erros.append('Número da agência deve conter apenas números')
    if not (isinstance(dados.get('valor_centavos'), int) and dados['valor_centavos'] > 0):
        erros.append('Valor solicitado deve ser maior que 0')
    email = str(dados.get('email', ''))
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        erros.append('E-mail inválido')
    cpf = str(dados.get('cpf', ''))
    if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif not valida_cpf(cpf):
        erros.append('CPF inválido')
    cep = str(dados.get('cep', ''))
    if not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = str(dados.get('data_nascimento', ''))
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif not valida_data(nascimento):
        erros.append('Data de nascimento inválida')
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(dados)}


app.mount('/', StaticFiles(directory='.'), name='estaticos')
