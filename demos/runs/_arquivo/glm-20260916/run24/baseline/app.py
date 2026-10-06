import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    tipo: str = ''
    nome_completo: str = ''
    n_usp: str = ''
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
    valor_solicitado: str = ''
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
    rg_rnm: str = ''
    nome_banco: str = ''
    agencia: str = ''
    numero_conta: str = ''


CPF_FORMATO = re.compile(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
CEP_FORMATO = re.compile(r'^\d{5}-\d{3}$')
DATA_FORMATO = re.compile(r'^\d{2}/\d{2}/\d{4}$')


def cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf]
    dv1 = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    dv1 = 0 if dv1 < 2 else 11 - dv1
    dv2 = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    dv2 = 0 if dv2 < 2 else 11 - dv2
    return digitos[9] == dv1 and digitos[10] == dv2


def moeda(centavos: int) -> str:
    parte_inteira, centavos_finais = divmod(centavos, 100)
    return f'R$ {parte_inteira:,}'.replace(',', '.') + f',{centavos_finais:02d}'


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    obrigatorios = [
        'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento',
        'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
        'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
        'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
        'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'numero_conta',
    ]
    if s.tipo != 'docentes':
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not getattr(s, campo).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append('N. USP deve conter apenas números')

    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append('Número da agência deve conter apenas números')

    digitos_valor = re.sub(r'\D', '', s.valor_solicitado)
    if s.valor_solicitado.strip() and (not digitos_valor or int(digitos_valor) <= 0):
        erros.append('Valor solicitado deve ser maior que 0')

    if s.email.strip() and ('@' not in s.email or not s.email.split('@', 1)[1].strip()):
        erros.append('E-mail inválido')

    cpf = s.cpf.strip()
    cpf_no_formato = bool(CPF_FORMATO.match(cpf))
    if cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')

    if s.cep.strip() and not CEP_FORMATO.match(s.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')

    data = s.data_nascimento.strip()
    data_no_formato = bool(DATA_FORMATO.match(data))
    if data and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if cpf_no_formato and not cpf_valido(cpf.replace('.', '').replace('-', '')):
        erros.append('CPF inválido')

    if data_no_formato:
        dia, mes, ano = (int(parte) for parte in data.split('/'))
        try:
            datetime(ano, mes, dia)
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(s: Solicitacao, centavos: int) -> str:
    linhas = [
        f'Interessada(o): {s.nome_completo} - {s.n_usp}',
        f'E-mail: {s.email}',
    ]
    if s.tipo == 'docentes':
        linhas += [
            'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
            f'Programa: {s.programa}',
        ]
    else:
        linhas += [
            f'Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}',
            f'Programa: {s.programa} - {s.nivel}',
        ]
    linhas += [
        '',
        f'A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {s.nome_evento}',
        f'Período: {s.periodo_evento}',
        f'Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}',
    ]
    if s.link_evento:
        linhas.append(f'Link do evento: {s.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {s.apresentacao_trabalho}',
        f'Valor solicitado: {moeda(centavos)}',
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
        f'Data de nascimento: {s.data_nascimento}',
        f'CPF: {s.cpf}',
        f'RG / RNM: {s.rg_rnm}',
        f'Banco: {s.nome_banco}',
        f'Agência: {s.agencia}',
        f'Conta: {s.numero_conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')


@app.post('/api/solicitar')
def solicitar(s: Solicitacao) -> dict:
    s = Solicitacao(**{campo: valor.strip() for campo, valor in s.model_dump().items()})
    erros = validar(s)
    if erros:
        return {'erros': erros}
    centavos = int(re.sub(r'\D', '', s.valor_solicitado))
    return {'oficio': gerar_oficio(s, centavos)}


app.mount('/', StaticFiles(directory=RAIZ, html=True), name='estaticos')
