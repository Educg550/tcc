import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class Solicitacao(BaseModel):
    perfil: str = 'alunos'
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
    link_evento: str = ''
    valor: str = ''
    detalhamento: str = ''
    apresentacao: str = ''
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
    banco: str = ''
    agencia: str = ''
    conta: str = ''


app = FastAPI()


def _so_digitos(texto):
    return re.fullmatch(r'[0-9]+', texto) is not None


def _digito_verificador(digitos):
    soma = sum(int(d) * p for d, p in zip(digitos, range(len(digitos) + 1, 1, -1)))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def _cpf_confere(cpf):
    num = re.sub(r'[^0-9]', '', cpf)
    if len(num) != 11:
        return False
    return num[-2:] == _digito_verificador(num[:9]) + _digito_verificador(num[:10])


def _centavos(valor):
    texto = valor.strip()
    if not texto:
        return None
    if _so_digitos(texto):
        return int(texto)
    texto = texto.replace('R$', '').replace(' ', '')
    if re.fullmatch(r'[0-9]{1,3}(\.[0-9]{3})*,[0-9]{2}', texto) is None:
        return None
    return int(texto.replace('.', '').replace(',', ''))


def _moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{cent:02d}'


def _email_valido(email):
    return re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) is not None


def _data_valida(texto):
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def _erros(d):
    erros = []
    obrigatorios = [
        'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo',
        'cidade_evento', 'estado_evento', 'pais_evento', 'valor',
        'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
        'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm',
        'banco', 'agencia', 'conta',
    ]
    if d.perfil != 'docentes':
        obrigatorios += ['nivel', 'tipo_auxilio']
    dados = d.model_dump()
    if any(not str(dados[c]).strip() for c in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = d.n_usp.strip()
    if n_usp and not _so_digitos(n_usp):
        erros.append('N. USP deve conter apenas números')

    agencia = d.agencia.strip()
    if agencia and not _so_digitos(agencia):
        erros.append('Número da agência deve conter apenas números')

    if d.valor.strip():
        centavos = _centavos(d.valor)
        if centavos is None or centavos <= 0:
            erros.append('Valor solicitado deve ser maior que 0')

    if d.email.strip() and not _email_valido(d.email.strip()):
        erros.append('E-mail inválido')

    cpf = d.cpf.strip()
    if cpf and re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf) is None:
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not _cpf_confere(cpf):
        erros.append('CPF inválido')

    cep = d.cep.strip()
    if cep and re.fullmatch(r'[0-9]{5}-[0-9]{3}', cep) is None:
        erros.append('CEP deve estar no formato 00000-000')

    data = d.data_nascimento.strip()
    if data and re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', data) is None:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data and not _data_valida(data):
        erros.append('Data de nascimento inválida')

    return erros


def _oficio(d, centavos):
    if d.perfil == 'docentes':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + d.programa.strip()
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + d.tipo_auxilio.strip()
        linha_programa = 'Programa: ' + d.programa.strip() + ' - ' + d.nivel.strip()
    linhas = [
        'Interessada(o): ' + d.nome.strip() + ' - ' + d.n_usp.strip(),
        'E-mail: ' + d.email.strip(),
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-' + d.programa.strip() + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + d.evento.strip(),
        'Período: ' + d.periodo.strip(),
        'Local: ' + d.cidade_evento.strip() + ' - ' + d.estado_evento.strip() + ' - ' + d.pais_evento.strip(),
    ]
    if d.link_evento.strip():
        linhas.append('Link do evento: ' + d.link_evento.strip())
    linhas += [
        'Apresentação de trabalho: ' + d.apresentacao.strip(),
        'Valor solicitado: ' + _moeda(centavos),
        'Detalhamento: ' + d.detalhamento.strip(),
        '',
        'Endereço da(o) interessada(o)',
        d.logradouro.strip() + ', ' + d.numero.strip(),
    ]
    if d.complemento.strip():
        linhas.append('Complemento: ' + d.complemento.strip())
    linhas += [
        'CEP: ' + d.cep.strip(),
        d.bairro.strip() + ', ' + d.cidade.strip() + ' - ' + d.estado.strip(),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + d.data_nascimento.strip(),
        'CPF: ' + d.cpf.strip(),
        'RG / RNM: ' + d.rg_rnm.strip(),
        'Banco: ' + d.banco.strip(),
        'Agência: ' + d.agencia.strip(),
        'Conta: ' + d.conta.strip(),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def registrar(d: Solicitacao):
    erros = _erros(d)
    if erros:
        return {'valido': False, 'erros': erros}
    return {'valido': True, 'oficio': _oficio(d, _centavos(d.valor))}


app.mount('/', StaticFiles(directory='.', html=True), name='estaticos')
