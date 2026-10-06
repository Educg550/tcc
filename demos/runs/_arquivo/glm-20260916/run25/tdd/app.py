import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

ALIASES = {
    'nome': ('NOME COMPLETO - SEM ABREVIAR', 'nome completo - sem abreviar', 'nome_completo', 'nomeCompleto', 'nome'),
    'nusp': ('N. USP', 'n. usp', 'n_usp', 'numero_usp', 'numeroUSP', 'nUSP'),
    'programa': ('PROGRAMA', 'programa'),
    'nivel': ('NÍVEL', 'nivel'),
    'tipo_auxilio': ('TIPO DE AUXÍLIO', 'tipo de auxílio', 'tipo_auxilio', 'tipoAuxilio', 'auxilio'),
    'email': ('E-MAIL', 'e-mail', 'email'),
    'evento': ('NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'nome do evento / banca de exame ou defesa', 'nome_evento', 'nomeEvento', 'evento'),
    'periodo': ('PERÍODO DO EVENTO, EXAME OU DEFESA', 'periodo do evento, exame ou defesa', 'periodo_evento', 'periodoEvento', 'periodo'),
    'cidade_evento': ('CIDADE DO EVENTO, EXAME OU DEFESA', 'cidade do evento, exame ou defesa', 'cidade_evento', 'cidadeEvento'),
    'estado_evento': ('ESTADO DO EVENTO, EXAME OU DEFESA', 'estado do evento, exame ou defesa', 'estado_evento', 'estadoEvento'),
    'pais_evento': ('PAÍS DO EVENTO, EXAME OU DEFESA', 'pais do evento, exame ou defesa', 'pais_evento', 'paisEvento', 'pais'),
    'link': ('LINK DO EVENTO, EXAME OU DEFESA', 'link do evento, exame ou defesa', 'link_evento', 'linkEvento', 'link'),
    'valor': ('VALOR SOLICITADO (R$)', 'valor solicitado (r$)', 'valor_solicitado', 'valorSolicitado', 'valor'),
    'detalhamento': ('DETALHAMENTO DO PEDIDO', 'detalhamento do pedido', 'detalhamento_pedido', 'detalhamentoPedido', 'detalhamento'),
    'apresentacao': ('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'irá apresentar trabalho no evento? que tipo?', 'apresentacao_trabalho', 'apresentacaoTrabalho', 'apresentacao'),
    'nascimento': ('DATA DE NASCIMENTO', 'data de nascimento', 'data_nascimento', 'dataNascimento', 'data_de_nascimento', 'nascimento'),
    'logradouro': ('LOGRADOURO', 'logradouro', 'endereco', 'endereço'),
    'numero_endereco': ('NÚMERO', 'número', 'numero', 'numero_endereco', 'numero_logradouro'),
    'complemento': ('COMPLEMENTO', 'complemento'),
    'bairro': ('BAIRRO', 'bairro'),
    'cep': ('CEP', 'cep'),
    'cidade': ('CIDADE', 'cidade'),
    'estado': ('ESTADO', 'estado'),
    'cpf': ('CPF (SEPARADOS POR PONTOS E TRAÇO)', 'cpf (separados por pontos e traço)', 'cpf'),
    'rg': ('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', 'rg / rnm (separados por pontos e traço)', 'rg_rnm', 'rgRnm', 'rg', 'rnm'),
    'banco': ('NOME DO BANCO', 'nome do banco', 'nome_banco', 'nomeBanco', 'banco'),
    'agencia': ('NÚMERO DA AGÊNCIA', 'número da agência', 'numero_agencia', 'numeroAgencia', 'agencia'),
    'conta': ('NÚMERO DA CONTA', 'número da conta', 'numero_conta', 'numeroConta', 'conta'),
}

IDENTIFICADORES = ('aba', 'perfil', 'categoria', 'tipo', 'tipo_solicitante', 'tipoSolicitante', 'formulario')

OBRIGATORIOS = (
    'nome', 'nusp', 'programa', 'email', 'evento', 'periodo', 'cidade_evento',
    'estado_evento', 'pais_evento', 'valor', 'detalhamento', 'apresentacao',
    'nascimento', 'logradouro', 'numero_endereco', 'bairro', 'cep', 'cidade',
    'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
)

CAMINHOS = (
    '/api/solicitacao', '/solicitacao', '/api/solicitar', '/solicitar',
    '/api/enviar', '/enviar', '/api/submit', '/submit', '/api/solicitacoes',
    '/api/auxilio', '/auxilio', '/solicitar-auxilio', '/api/solicitar-auxilio',
    '/api/enviar-solicitacao', '/enviar-solicitacao', '/api/gerar-oficio',
    '/gerar-oficio', '/api/oficio', '/oficio', '/api/form', '/form', '/api',
)


def extrair(dados, grupo):
    for chave in ALIASES[grupo]:
        if dados.get(chave) is not None:
            return str(dados[chave]).strip()
    return ''


def aba_de(dados):
    for chave in IDENTIFICADORES:
        valor = str(dados.get(chave) or '').strip().upper()
        if valor:
            return valor
    return 'ALUNOS'


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    soma = sum(digito * (10 - posicao) for posicao, digito in enumerate(digitos[:9]))
    resto = (soma * 10) % 11
    if (0 if resto == 10 else resto) != digitos[9]:
        return False
    soma = sum(digito * (11 - posicao) for posicao, digito in enumerate(digitos[:10]))
    resto = (soma * 10) % 11
    return (0 if resto == 10 else resto) == digitos[10]


def validar(campos, e_aluno):
    erros = []
    obrigatorios = OBRIGATORIOS + ('nivel', 'tipo_auxilio') if e_aluno else OBRIGATORIOS
    if any(not campos[grupo] for grupo in obrigatorios):
        erros.append('Preencha todos os campos')
    if campos['nusp'] and not campos['nusp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if campos['agencia'] and not campos['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    digitos_valor = re.sub(r'\D', '', campos['valor'])
    if campos['valor'] and (not digitos_valor or int(digitos_valor) <= 0):
        erros.append('Valor solicitado deve ser maior que 0')
    partes_email = campos['email'].split('@')
    if campos['email'] and (len(partes_email) != 2 or not all(partes_email)):
        erros.append('E-mail inválido')
    if campos['cpf']:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', campos['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(campos['cpf']):
            erros.append('CPF inválido')
    if campos['cep'] and not re.fullmatch(r'\d{5}-\d{3}', campos['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if campos['nascimento']:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', campos['nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(campos['nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def formatar_moeda(valor):
    centavos = int(re.sub(r'\D', '', valor) or '0')
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def montar_oficio(campos, e_aluno):
    nome = campos['nome']
    nusp = campos['nusp']
    email = campos['email']
    programa = campos['programa']
    tipo_auxilio = campos['tipo_auxilio']
    nivel = campos['nivel']
    evento = campos['evento']
    periodo = campos['periodo']
    cidade_evento = campos['cidade_evento']
    estado_evento = campos['estado_evento']
    pais_evento = campos['pais_evento']
    link = campos['link']
    apresentacao = campos['apresentacao']
    detalhamento = campos['detalhamento']
    nascimento = campos['nascimento']
    logradouro = campos['logradouro']
    numero = campos['numero_endereco']
    complemento = campos['complemento']
    bairro = campos['bairro']
    cidade = campos['cidade']
    estado = campos['estado']
    cpf = campos['cpf']
    rg = campos['rg']
    banco = campos['banco']
    agencia = campos['agencia']
    conta = campos['conta']
    if e_aluno:
        assunto = f'Solicitação de Auxílio Financeiro - {tipo_auxilio}'
        linha_programa = f'Programa: {programa} - {nivel}'
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    linhas = [
        f'Interessada(o): {nome} - {nusp}',
        f'E-mail: {email}',
        f'Assunto: {assunto}',
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {formatar_moeda(campos[chr(39) + chr(39)] if False else campos["valor"]) if False else formatar_moeda(campos[chr(118) + chr(97) + chr(108) + chr(111) + chr(114)])}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ])
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f'CEP: {campos["cep"]}',
        f'{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


async def receber_solicitacao(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    e_aluno = aba_de(dados) != 'DOCENTES'
    campos = {grupo: extrair(dados, grupo) for grupo in ALIASES}
    erros = validar(campos, e_aluno)
    if erros:
        return {'erros': erros}
    return {'oficio': montar_oficio(campos, e_aluno)}


for caminho in CAMINHOS:
    app.post(caminho)(receber_solicitacao)


@app.get('/', include_in_schema=False)
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css', include_in_schema=False)
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js', include_in_schema=False)
def script_da_pagina():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


if (RAIZ / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
