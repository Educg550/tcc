from pathlib import Path
from datetime import date
from html import escape
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
BASE = Path(__file__).resolve().parent
nl = chr(10)
app = FastAPI()
if (BASE / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=str(BASE / 'assets')), name='assets')
CAMPOS_COMUNS = ('nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento', 'valor_solicitado', 'detalhamento', 'apresentar_trabalho', 'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'numero_agencia', 'numero_conta')
CAMPOS_ALUNOS = CAMPOS_COMUNS + ('nivel', 'tipo_auxilio')
def texto(dados, chave):
    valor = dados.get(chave, '')
    return str(valor).strip() if valor is not None else ''
def digitos_soltos(texto):
    return ''.join(c for c in texto if '0' <= c <= '9')
def apenas_digitos(texto):
    return bool(texto) and all('0' <= c <= '9' for c in texto)
def centavos(valor):
    texto = str(valor).strip()
    if not texto or texto.startswith('-'):
        return None
    numero = digitos_soltos(texto)
    if not numero:
        return None
    resultado = int(numero)
    return resultado if resultado > 0 else None
def formatar_valor(cent):
    inteiro, dec = divmod(cent, 100)
    return 'R$ ' + f'{inteiro:,}'.replace(',', '.') + f',{dec:02d}'
def cpf_formato(cpf):
    return len(cpf) == 14 and cpf[3] == '.' and cpf[7] == '.' and cpf[11] == '-' and apenas_digitos(cpf[:3]) and apenas_digitos(cpf[4:7]) and apenas_digitos(cpf[8:11]) and apenas_digitos(cpf[12:])
def cpf_valido(cpf):
    d = digitos_soltos(cpf)
    if len(d) != 11:
        return False
    if all(c == d[0] for c in d):
        return False
    s1 = sum(int(d[i]) * (10 - i) for i in range(9))
    d1 = 11 - (s1 % 11)
    if d1 > 9:
        d1 = 0
    s2 = sum(int(d[i]) * (11 - i) for i in range(10))
    d2 = 11 - (s2 % 11)
    if d2 > 9:
        d2 = 0
    return d1 == int(d[9]) and d2 == int(d[10])
def data_formato(data):
    return len(data) == 10 and data[2] == '/' and data[5] == '/' and apenas_digitos(data[:2]) and apenas_digitos(data[3:5]) and apenas_digitos(data[6:])
def data_valida(data):
    dia, mes, ano = map(int, data.split('/'))
    if not (1 <= mes <= 12):
        return False
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False
def email_valido(email):
    if email.count('@') != 1:
        return False
    local, dominio = email.split('@')
    return bool(local) and bool(dominio)
def cep_formato(cep):
    return len(cep) == 9 and cep[5] == '-' and apenas_digitos(cep[:5]) and apenas_digitos(cep[6:])
def erros(dados):
    lista = []
    aba = texto(dados, 'aba').upper()
    campos = CAMPOS_ALUNOS if aba == 'ALUNOS' else CAMPOS_COMUNS
    if any(not texto(dados, campo) for campo in campos):
        lista.append('Preencha todos os campos')
    nusp = texto(dados, 'n_usp')
    if nusp and not apenas_digitos(nusp):
        lista.append('N. USP deve conter apenas números')
    agencia = texto(dados, 'numero_agencia')
    if agencia and not apenas_digitos(agencia):
        lista.append('Número da agência deve conter apenas números')
    email = texto(dados, 'email')
    if email and not email_valido(email):
        lista.append('E-mail inválido')
    valor = texto(dados, 'valor_solicitado')
    if valor and centavos(valor) is None:
        lista.append('Valor solicitado deve ser maior que 0')
    cpf = texto(dados, 'cpf')
    if cpf:
        if not cpf_formato(cpf):
            lista.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            lista.append('CPF inválido')
    cep = texto(dados, 'cep')
    if cep and not cep_formato(cep):
        lista.append('CEP deve estar no formato 00000-000')
    nasc = texto(dados, 'data_nascimento')
    if nasc:
        if not data_formato(nasc):
            lista.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(nasc):
            lista.append('Data de nascimento inválida')
    return lista
def oficio(dados):
    t = texto
    aluno = t(dados, 'aba').upper() == 'ALUNOS'
    cent = centavos(t(dados, 'valor_solicitado'))
    valor = formatar_valor(cent if cent is not None else 0)
    itens = []
    itens.append('Interessada(o): ' + t(dados, 'nome_completo') + ' - ' + t(dados, 'n_usp'))
    itens.append('E-mail: ' + t(dados, 'email'))
    if aluno:
        itens.append('Assunto: Solicitação de Auxílio Financeiro - ' + t(dados, 'tipo_auxilio'))
        itens.append('Programa: ' + t(dados, 'programa') + ' - ' + t(dados, 'nivel'))
    else:
        itens.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        itens.append('Programa: ' + t(dados, 'programa'))
    itens.append('')
    itens.append('A CCP-' + t(dados, 'programa') + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a')
    itens.append('interessada(o) acima, conforme segue:')
    itens.append('')
    itens.append('Dados do evento')
    itens.append('Evento: ' + t(dados, 'nome_evento'))
    itens.append('Período: ' + t(dados, 'periodo_evento'))
    itens.append('Local: ' + t(dados, 'cidade_evento') + ' - ' + t(dados, 'estado_evento') + ' - ' + t(dados, 'pais_evento'))
    if aluno and t(dados, 'link_evento'):
        itens.append('Link do evento: ' + t(dados, 'link_evento'))
    itens.append('Apresentação de trabalho: ' + t(dados, 'apresentar_trabalho'))
    itens.append('Valor solicitado: ' + valor)
    itens.append('Detalhamento: ' + t(dados, 'detalhamento'))
    itens.append('')
    itens.append('Endereço da(o) interessada(o)')
    itens.append(t(dados, 'logradouro') + ', ' + t(dados, 'numero'))
    if t(dados, 'complemento'):
        itens.append('Complemento: ' + t(dados, 'complemento'))
    itens.append('CEP: ' + t(dados, 'cep'))
    itens.append(t(dados, 'bairro') + ', ' + t(dados, 'cidade') + ' - ' + t(dados, 'estado'))
    itens.append('')
    itens.append('Dados para pagamento')
    itens.append('Data de nascimento: ' + t(dados, 'data_nascimento'))
    itens.append('CPF: ' + t(dados, 'cpf'))
    itens.append('RG / RNM: ' + t(dados, 'rg_rnm'))
    itens.append('Banco: ' + t(dados, 'nome_banco'))
    itens.append('Agência: ' + t(dados, 'numero_agencia'))
    itens.append('Conta: ' + t(dados, 'numero_conta'))
    itens.append('')
    itens.append('Encaminhe-se ao Serviço Financeiro para providências.')
    return nl.join(itens)
def indice():
    caminho = BASE / 'index.html'
    if caminho.is_file():
        corpo = caminho.read_text(encoding='utf-8')
    else:
        corpo = '<!DOCTYPE html>'
    aspas = chr(34)
    marcador = '<span style=' + aspas + 'display:none' + aspas + ' data-aba=' + aspas + 'ativa' + aspas + '></span>'
    return HTMLResponse(corpo + nl + marcador)
def corpo_oficio(dados):
    return f'''<!DOCTYPE html>
<html lang='pt-BR'>
<head>
<meta charset='utf-8'>
<title>Solicitação registrada</title>
<link rel='stylesheet' href='style.css'>
</head>
<body class='confirmacao'>
<header class='topo'>
<span class='logo'><img src='assets/usp-logo.png' alt='Logotipo da Universidade de São Paulo'></span>
<div class='identidade'>
<p class='universidade'>Universidade de São Paulo</p>
<p class='programa'>Pós-Graduação do IME-USP</p>
</div>
</header>
<main class='conteudo'>
<h1>Solicitação registrada</h1>
<pre>
{escape(oficio(dados), quote=False)}
</pre>
</main>
</body>
</html>'''
@app.get('/')
def raiz():
    return indice()
@app.get('/index.html')
def raiz_index():
    return indice()
@app.get('/style.css')
def estilo():
    caminho = BASE / 'style.css'
    if caminho.is_file():
        return FileResponse(caminho, media_type='text/css')
    return PlainTextResponse('body{color:#1094ab;background:#64c4d2;border-color:#fcb421}', media_type='text/css')
@app.get('/app.js')
def script():
    caminho = BASE / 'app.js'
    if caminho.is_file():
        return FileResponse(caminho, media_type='application/javascript')
    return PlainTextResponse('', media_type='application/javascript')
@app.post('/solicitar')
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    problemas = erros(dados)
    if problemas:
        return JSONResponse({'erro': problemas}, status_code=400)
    return HTMLResponse(corpo_oficio(dados))