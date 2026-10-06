from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import re
from datetime import date

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str  # 'aluno' ou 'docente'
    nome: str
    n_usp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = None
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True


@app.post('/api/solicitacao')
def processar(s: Solicitacao):
    erros = []

    obrig = ['nome', 'n_usp', 'programa', 'email', 'evento', 'periodo',
             'cidade_evento', 'estado_evento', 'pais_evento', 'valor',
             'detalhamento', 'apresentacao', 'nascimento', 'logradouro',
             'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
             'banco', 'agencia', 'conta']
    if s.tipo == 'aluno':
        obrig += ['nivel', 'tipo_auxilio']

    if any(not getattr(s, f) for f in obrig):
        erros.append('Preencha todos os campos')

    if s.n_usp and not s.n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    if s.agencia and not s.agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    try:
        centavos = int(re.sub(r'\D', '', s.valor))
    except ValueError:
        centavos = 0
    if centavos <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    if s.email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', s.email):
        erros.append('E-mail inválido')

    if s.cpf and not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', s.cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif s.cpf and not validar_cpf(s.cpf):
        erros.append('CPF inválido')

    if s.cep and not re.match(r'^\d{5}-\d{3}$', s.cep):
        erros.append('CEP deve estar no formato 00000-000')

    if s.nascimento and not re.match(r'^\d{2}/\d{2}/\d{4}$', s.nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif s.nascimento:
        m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', s.nascimento)
        d_, m_, y_ = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            date(y_, m_, d_)
        except ValueError:
            erros.append('Data de nascimento inválida')

    if erros:
        return {'ok': False, 'erros': erros}

    def brl(c: int) -> str:
        reais, cents = divmod(c, 100)
        return f'R$ {reais:,}'.replace(',', '.') + f',{cents:02d}'

    linhas = [
        f'Interessada(o): {s.nome} - {s.n_usp}',
        f'E-mail: {s.email}',
    ]
    if s.tipo == 'aluno':
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}')
        linhas.append(f'Programa: {s.programa} - {s.nivel}')
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {s.programa}')
    linhas += [
        '',
        'A CCP-' + s.programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {s.evento}',
        f'Período: {s.periodo}',
        f'Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}',
    ]
    if s.link_evento:
        linhas.append(f'Link do evento: {s.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {s.apresentacao}',
        f'Valor solicitado: {brl(centavos)}',
        f'Detalhamento: {s.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{s.logradouro}, {s.numero}',
    ]
    if s.complemento:
        linhas.append(f'Complemento: {s.complemento}')
    linhas += [
        f'CEP: {s.cep}',
        f'{s.bairro}, {s.cidade} - {s.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {s.nascimento}',
        f'CPF: {s.cpf}',
        f'RG / RNM: {s.rg}',
        f'Banco: {s.banco}',
        f'Agência: {s.agencia}',
        f'Conta: {s.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    return {'ok': True, 'oficio': '\n'.join(linhas)}


app.mount('/', StaticFiles(directory='static', html=True), name='static')
