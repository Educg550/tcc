from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import re

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

templates = Jinja2Templates(directory="templates")

def format_valor(raw: str) -> str:
    cents = int(raw)
    reais = cents // 100
    centavos = cents % 100
    formatted_reais = f"{reais:,}".replace(",", ".")
    return f"R$ {formatted_reais},{centavos:02d}"

def format_cpf(raw: str) -> str:
    if len(raw) != 11:
        return raw
    return f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"

def format_cep(raw: str) -> str:
    if len(raw) != 8:
        return raw
    return f"{raw[:5]}-{raw[5:]}"

def format_data(raw: str) -> str:
    if len(raw) != 8:
        return raw
    return f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"

def validate(data, is_alunos):
    errors = []
    required_fields = {
        'nome', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
        'cidade', 'estado_evento', 'pais', 'valor', 'detalhamento', 'apresentacao',
        'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
        'cidade_endereco', 'estado_endereco', 'cpf', 'rg', 'banco', 'agencia', 'conta'
    }
    if is_alunos:
        required_fields.update({'nivel', 'tipo_auxilio'})
    
    missing_any = False
    for field in required_fields:
        val = data.get(field, '').strip()
        if not val:
            missing_any = True
    if missing_any:
        errors.append("Preencha todos os campos")
    
    n_usp = data.get('n_usp', '').strip()
    if n_usp and not n_usp.isdigit():
        errors.append("N. USP deve conter apenas números")
    
    agencia = data.get('agencia', '').strip()
    if agencia and not agencia.isdigit():
        errors.append("Número da agência deve conter apenas números")
    
    valor = data.get('valor', '').strip()
    if valor:
        val_clean = re.sub(r'\D', '', valor)
        if not val_clean or not val_clean.isdigit() or int(val_clean) <= 0:
            errors.append("Valor solicitado deve ser maior que 0")
    
    email = data.get('email', '').strip()
    if email:
        if '@' not in email or '.' not in email.split('@')[-1]:
            errors.append("E-mail inválido")
    
    cpf = data.get('cpf', '').strip()
    if cpf:
        cpf_clean = re.sub(r'\D', '', cpf)
        if len(cpf_clean) != 11 or not cpf_clean.isdigit():
            errors.append("CPF deve estar no formato 000.000.000-00")
    
    cep = data.get('cep', '').strip()
    if cep:
        cep_clean = re.sub(r'\D', '', cep)
        if len(cep_clean) != 8 or not cep_clean.isdigit():
            errors.append("CEP deve estar no formato 00000-000")
    
    data_nasc = data.get('data_nascimento', '').strip()
    if data_nasc:
        nasc_clean = re.sub(r'\D', '', data_nasc)
        if len(nasc_clean) != 8 or not nasc_clean.isdigit():
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    
    return errors

def generate_oficio(data, is_alunos):
    def strip_or_empty(key):
        return data.get(key, '').strip()
    
    nome = strip_or_empty('nome')
    n_usp = strip_or_empty('n_usp')
    email = strip_or_empty('email')
    programa = strip_or_empty('programa')
    if is_alunos:
        tipo_auxilio = strip_or_empty('tipo_auxilio')
        nivel = strip_or_empty('nivel')
    nome_evento = strip_or_empty('nome_evento')
    periodo = strip_or_empty('periodo')
    cidade = strip_or_empty('cidade')
    estado_evento = strip_or_empty('estado_evento')
    pais = strip_or_empty('pais')
    link_evento = strip_or_empty('link_evento')
    valor_raw = strip_or_empty('valor')
    valor_clean = re.sub(r'\D', '', valor_raw)
    valor_formatado = format_valor(valor_clean) if valor_clean else ''
    detalhamento = strip_or_empty('detalhamento')
    apresentacao = strip_or_empty('apresentacao')
    data_nasc_raw = strip_or_empty('data_nascimento')
    data_nasc_clean = re.sub(r'\D', '', data_nasc_raw)
    data_nasc_formatted = format_data(data_nasc_clean) if len(data_nasc_clean)==8 else data_nasc_raw
    logradouro = strip_or_empty('logradouro')
    numero = strip_or_empty('numero')
    complemento = strip_or_empty('complemento')
    bairro = strip_or_empty('bairro')
    cep_raw = strip_or_empty('cep')
    cep_clean = re.sub(r'\D', '', cep_raw)
    cep_formatted = format_cep(cep_clean) if len(cep_clean)==8 else cep_raw
    cidade_endereco = strip_or_empty('cidade_endereco')
    estado_endereco = strip_or_empty('estado_endereco')
    cpf_raw = strip_or_empty('cpf')
    cpf_clean = re.sub(r'\D', '', cpf_raw)
    cpf_formatted = format_cpf(cpf_clean) if len(cpf_clean)==11 else cpf_raw
    rg = strip_or_empty('rg')
    banco = strip_or_empty('banco')
    agencia = strip_or_empty('agencia')
    conta = strip_or_empty('conta')

    lines = []
    lines.append(f"Interessada(o): {nome} - {n_usp}")
    lines.append(f"E-mail: {email}")
    if is_alunos:
        lines.append(f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}")
        lines.append(f"Programa: {programa} - {nivel}")
    else:
        lines.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        lines.append(f"Programa: {programa}")
    lines.append("")
    lines.append(f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {nome_evento}")
    lines.append(f"Período: {periodo}")
    lines.append(f"Local: {cidade} - {estado_evento} - {pais}")
    if link_evento:
        lines.append(f"Link do evento: {link_evento}")
    lines.append(f"Apresentação de trabalho: {apresentacao}")
    lines.append(f"Valor solicitado: {valor_formatado}")
    lines.append(f"Detalhamento: {detalhamento}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{logradouro}, {numero}")
    if complemento:
        lines.append(f"Complemento: {complemento}")
    lines.append(f"CEP: {cep_formatted}")
    lines.append(f"{bairro}, {cidade_endereco} - {estado_endereco}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data_nasc_formatted}")
    lines.append(f"CPF: {cpf_formatted}")
    lines.append(f"RG / RNM: {rg}")
    lines.append(f"Banco: {banco}")
    lines.append(f"Agência: {agencia}")
    lines.append(f"Conta: {conta}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    
    return "\n".join(lines)

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "errors": [], "data": {}, "result": None, "tab": "alunos"})

@app.post("/", response_class=HTMLResponse)
async def submit(request: Request):
    form_data = await request.form()
    data = dict(form_data)
    is_alunos = 'nivel' in data
    errors = validate(data, is_alunos)
    tab = "alunos" if is_alunos else "docentes"
    if errors:
        return templates.TemplateResponse("index.html", {"request": request, "errors": errors, "data": data, "result": None, "tab": tab})
    else:
        oficio = generate_oficio(data, is_alunos)
        return templates.TemplateResponse("index.html", {"request": request, "errors": [], "data": data, "result": oficio, "tab": tab})
