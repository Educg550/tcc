from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()


def _digits(value):
    return ''.join(c for c in value if c.isdigit())


def _currency(cents):
    inteiro, cent = divmod(cents, 100)
    s = str(inteiro)
    miles = s[-3:] if len(s) <= 3 else ''
    s = s[:len(s) - 3]
    while s:
        miles = '.' + s[-3:] + miles
        s = s[:-3]
    return 'R$ ' + miles + ',' + str(cent).zfill(2)


def _cpf_valido(cpf):
    if len(set(cpf)) == 1:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = soma * 10 % 11
    if d1 == 10:
        d1 = 0
    if d1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = soma * 10 % 11
    if d2 == 10:
        d2 = 0
    return d2 == int(cpf[10])


def _data_valida(data):
    try:
        dia, mes, ano = (int(p) for p in data.split('/'))
    except ValueError:
        return False
    dias = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= mes <= 12 and 1 <= dia <= dias[mes - 1]


def _linha(rotulo, valor):
    if valor == '':
        return []
    return [f'{rotulo}: {valor}']


def oficio(s, aba):
    linhas = ['Dados do evento', f'Evento: {s["nome_evento"]}',
              f'Período: {s["periodo"]}',
              f'Local: {s["cidade_evento"]} - {s["estado_evento"]} - {s["pais_evento"]}']
    if s['link'] != '':
        linhas.append(f'Link do evento: {s["link"]}')
    linhas += [f'Apresentação de trabalho: {s["apresentacao"]}',
               f'Valor solicitado: {s["valor"]}',
               f'Detalhamento: {s["detalhamento"]}', '', 'Endereço da(o) interessada(o)',
               f'{s["logradouro"]}, {s["numero"]}']
    if s['complemento'] != '':
        linhas.append(f'Complemento: {s["complemento"]}')
    linhas += [f'CEP: {s["cep"]}', f'{s["bairro"]}, {s["cidade"]} - {s["estado"]}', '',
               'Dados para pagamento', f'Data de nascimento: {s["nascimento"]}',
               f'CPF: {s["cpf"]}', f'RG / RNM: {s["rg"]}', f'Banco: {s["banco"]}',
               f'Agência: {s["agencia"]}', f'Conta: {s["conta"]}', '',
               'Encaminhe-se ao Serviço Financeiro para providências.']
    topo = ['Interessada(o): ' + s['nome'] + ' - ' + s['nusp'], 'E-mail: ' + s['email']]
    if aba == 'DOCENTES':
        topo += ['Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
                 'Programa: ' + s['programa'], '',
                 'A CCP-' + s['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
                 'interessada(o) acima, conforme segue:', '']
    else:
        topo += ['Assunto: Solicitação de Auxílio Financeiro - ' + s['tipo_auxilio'],
                 'Programa: ' + s['programa'] + ' - ' + s['nivel'], '',
                 'A CCP-' + s['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
                 'interessada(o) acima, conforme segue:', '']
    return '\n'.join(topo + linhas)


@app.get('/')
async def inicio():
    return FileResponse(BASE / 'index.html')


@app.post('/solicitacao')
async def solicitacao(aba: str = 'ALUNOS', nome: str = '', nusp: str = '',
                      programa: str = '', nivel: str = '', tipo_auxilio: str = '',
                      email: str = '', nome_evento: str = '', periodo: str = '',
                      cidade_evento: str = '', estado_evento: str = '',
                      pais_evento: str = '', link: str = '', valor: str = '',
                      detalhamento: str = '', apresentacao: str = '', nascimento: str = '',
                      logradouro: str = '', numero: str = '', complemento: str = '',
                      bairro: str = '', cep: str = '', cidade: str = '', estado: str = '',
                      cpf: str = '', rg: str = '', banco: str = '', agencia: str = '',
                      conta: str = ''):
    obrigatorios = [nome, nusp, programa, email, nome_evento, periodo, cidade_evento,
                    estado_evento, pais_evento, valor, detalhamento, apresentacao,
                    nascimento, logradouro, numero, bairro, cep, cidade, estado, cpf, rg,
                    banco, agencia, conta]
    if aba != 'DOCENTES':
        obrigatorios += [nivel, tipo_auxilio]
    erros = []
    if any(t.strip() == '' for t in obrigatorios):
        erros.append('Preencha todos os campos')
    if nusp.strip() != '' and not nusp.strip().isdigit():
        erros.append('N. USP deve conter apenas números')
    if agencia.strip() != '' and not agencia.strip().isdigit():
        erros.append('Número da agência deve conter apenas números')
    digitos = _digits(valor)
    if digitos != '' and int(digitos) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    email = email.strip()
    if email != '':
        _, _, dominio = email.partition('@')
        if '.' not in dominio or dominio.startswith('.') or dominio.endswith('.'):
            erros.append('E-mail inválido')
    if cpf.strip() != '':
        if not _digits(cpf) or len(_digits(cpf)) != 11:
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(_digits(cpf)):
            erros.append('CPF inválido')
    if cep.strip() != '':
        if not _digits(cep) or len(_digits(cep)) != 8:
            erros.append('CEP deve estar no formato 00000-000')
    if nascimento.strip() != '':
        if len(nascimento.strip()) != 10 or nascimento.strip()[2] != '/' or nascimento.strip()[5] != '/' or not _digits(nascimento) or len(_digits(nascimento)) != 8:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not _data_valida(nascimento.strip()):
            erros.append('Data de nascimento inválida')
    if erros:
        return {'ok': False, 'erros': erros}
    s = {'nome': nome.strip(), 'nusp': nusp.strip(), 'programa': programa.strip(),
         'nivel': nivel.strip(), 'tipo_auxilio': tipo_auxilio.strip(), 'email': email,
         'nome_evento': nome_evento.strip(), 'periodo': periodo.strip(),
         'cidade_evento': cidade_evento.strip(), 'estado_evento': estado_evento.strip(),
         'pais_evento': pais_evento.strip(), 'link': link.strip(),
         'valor': _currency(int(digitos)), 'detalhamento': detalhamento.strip(),
         'apresentacao': apresentacao.strip(), 'nascimento': nascimento.strip(),
         'logradouro': logradouro.strip(), 'numero': numero.strip(),
         'complemento': complemento.strip(), 'bairro': bairro.strip(),
         'cep': cep.strip(), 'cidade': cidade.strip(), 'estado': estado.strip(),
         'cpf': cpf.strip(), 'rg': rg.strip(), 'banco': banco.strip(),
         'agencia': agencia.strip(), 'conta': conta.strip()}
    return {'ok': True, 'erros': [], 'oficio': oficio(s, aba)}


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')
