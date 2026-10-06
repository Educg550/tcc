import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    tipo: str = ''
    nome: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    evento: str = ''
    periodo: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link: str = ''
    valor: str = ''
    detalhamento: str = ''
    apresentacao: str = ''
    nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rg: str = ''
    banco: str = ''
    agencia: str = ''
    conta: str = ''


def _digito_cpf(numeros: list[int], peso_inicial: int) -> int:
    soma = sum(n * p for n, p in zip(numeros, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in cpf if c.isdigit()]
    if len(numeros) != 11:
        return False
    return numeros[9] == _digito_cpf(numeros[:9], 10) and numeros[10] == _digito_cpf(numeros[:10], 11)


def _data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def _moeda(texto: str) -> str:
    centavos = int(re.sub(r'\D', '', texto) or '0')
    reais = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {reais},{centavos % 100:02d}'


def _validar(d: Solicitacao) -> list[str]:
    erros = []
    obrigatorios = [d.nome, d.n_usp, d.programa, d.email, d.evento, d.periodo,
                    d.cidade_evento, d.estado_evento, d.pais_evento, d.valor,
                    d.detalhamento, d.apresentacao, d.nascimento, d.logradouro,
                    d.numero, d.bairro, d.cep, d.cidade, d.estado, d.cpf, d.rg,
                    d.banco, d.agencia, d.conta]
    if d.tipo != 'docentes':
        obrigatorios += [d.nivel, d.tipo_auxilio]
    if any(not campo for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if d.n_usp and not d.n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')
    if d.agencia and not d.agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')
    if d.valor:
        centavos = re.sub(r'\D', '', d.valor)
        if not centavos or int(centavos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if d.email:
        local, arroba, dominio = d.email.partition('@')
        if not (arroba and local and dominio):
            erros.append('E-mail inválido')
    cpf_no_formato = bool(re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', d.cpf))
    if d.cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if d.cep and not re.fullmatch(r'\d{5}-\d{3}', d.cep):
        erros.append('CEP deve estar no formato 00000-000')
    data_no_formato = bool(re.fullmatch(r'\d{2}/\d{2}/\d{4}', d.nascimento))
    if d.nascimento and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_no_formato and not _cpf_valido(d.cpf):
        erros.append('CPF inválido')
    if data_no_formato and not _data_valida(d.nascimento):
        erros.append('Data de nascimento inválida')
    return erros


def _oficio(d: Solicitacao) -> str:
    linhas = [
        f'Interessada(o): {d.nome} - {d.n_usp}',
        f'E-mail: {d.email}',
    ]
    if d.tipo == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {d.programa}')
    else:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}')
        linhas.append(f'Programa: {d.programa} - {d.nivel}')
    linhas += [
        '',
        f'A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d.evento}',
        f'Período: {d.periodo}',
        f'Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}',
    ]
    if d.link:
        linhas.append(f'Link do evento: {d.link}')
    linhas += [
        f'Apresentação de trabalho: {d.apresentacao}',
        f'Valor solicitado: {_moeda(d.valor)}',
        f'Detalhamento: {d.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{d.logradouro}, {d.numero}',
    ]
    if d.complemento:
        linhas.append(f'Complemento: {d.complemento}')
    linhas += [
        f'CEP: {d.cep}',
        f'{d.bairro}, {d.cidade} - {d.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {d.nascimento}',
        f'CPF: {d.cpf}',
        f'RG / RNM: {d.rg}',
        f'Banco: {d.banco}',
        f'Agência: {d.agencia}',
        f'Conta: {d.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')


@app.post('/solicitacao')
async def receber_solicitacao(dados: Solicitacao):
    dados = dados.model_copy(update={k: v.strip() for k, v in dados.model_dump().items()})
    erros = _validar(dados)
    if erros:
        return {'erros': erros}
    return {'oficio': _oficio(dados)}


app.mount('/', StaticFiles(directory=RAIZ, html=True), name='estaticos')
