import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_tab": "alunos",
        "errors": [],
        "data": {},
        "confirmation": False
    })

@app.post("/", response_class=HTMLResponse)
async def submit_form(request: Request):
    form_data = await request.form()
    form_type = form_data.get("form_type", "alunos")
    data = {key: form_data.get(key, "") for key in form_data.keys()}
    errors = validate(data, form_type)
    if errors:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "active_tab": form_type,
            "errors": errors,
            "data": data,
            "confirmation": False
        })
    else:
        oficio = generate_oficio(data, form_type)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "confirmation": True,
            "oficio": oficio
        })

def validate(data, form_type):
    errors = []
    required = [
        'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento',
        'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
        'valor_solicitado', 'detalhamento_pedido', 'apresentacao_trabalho',
        'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
        'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'conta'
    ]
    if form_type == "alunos":
        required.extend(['nivel', 'tipo_auxilio'])
    for field in required:
        val = data.get(field, '').strip()
        if not val:
            errors.append('Preencha todos os campos')
            break

    n_usp = data.get('n_usp', '')
    if n_usp and not n_usp.isdigit():
        if 'N. USP deve conter apenas números' not in errors:
            errors.append('N. USP deve conter apenas números')

    agencia = data.get('agencia', '')
    if agencia and not agencia.isdigit():
        if 'Número da agência deve conter apenas números' not in errors:
            errors.append('Número da agência deve conter apenas números')

    valor_str = data.get('valor_solicitado', '').strip()
    valor = parse_valor(valor_str)
    if valor is not None and valor <= 0:
        errors.append('Valor solicitado deve ser maior que 0')
    elif valor is None and valor_str:
        pass

    email = data.get('email', '')
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors.append('E-mail inválido')

    cpf = data.get('cpf', '')
    if cpf and not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
        errors.append('CPF deve estar no formato 000.000.000-00')

    cep = data.get('cep', '')
    if cep and not re.match(r'^\d{5}-\d{3}$', cep):
        errors.append('CEP deve estar no formato 00000-000')

    data_nasc = data.get('data_nascimento', '')
    if data_nasc and not re.match(r'^\d{2}/\d{2}/\d{4}$', data_nasc):
        errors.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    return errors

def parse_valor(s):
    s = s.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        val = int(round(float(s) * 100))
        return val
    except:
        return None

def generate_oficio(data, form_type):
    lines = []
    lines.append(f"Interessada(o): {data.get('nome_completo','')} - {data.get('n_usp','')}")
    lines.append(f"E-mail: {data.get('email','')}")
    if form_type == "alunos":
        lines.append(f"Assunto: Solicitação de Auxílio Financeiro - {data.get('tipo_auxilio','')}")
    else:
        lines.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
    if form_type == "alunos":
        lines.append(f"Programa: {data.get('programa','')} - {data.get('nivel','')}")
    else:
        lines.append(f"Programa: {data.get('programa','')}")
    lines.append("")
    lines.append(f"A CCP-{data.get('programa','')} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {data.get('nome_evento','')}")
    lines.append(f"Período: {data.get('periodo_evento','')}")
    lines.append(f"Local: {data.get('cidade_evento','')} - {data.get('estado_evento','')} - {data.get('pais_evento','')}")
    link = data.get('link_evento','').strip()
    if link:
        lines.append(f"Link do evento: {link}")
    lines.append(f"Apresentação de trabalho: {data.get('apresentacao_trabalho','')}")
    lines.append(f"Valor solicitado: {data.get('valor_solicitado','')}")
    lines.append(f"Detalhamento: {data.get('detalhamento_pedido','')}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{data.get('logradouro','')}, {data.get('numero','')}")
    comp = data.get('complemento','').strip()
    if comp:
        lines.append(f"Complemento: {comp}")
    lines.append(f"CEP: {data.get('cep','')}")
    lines.append(f"{data.get('bairro','')}, {data.get('cidade','')} - {data.get('estado','')}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data.get('data_nascimento','')}")
    lines.append(f"CPF: {data.get('cpf','')}")
    lines.append(f"RG / RNM: {data.get('rg_rnm','')}")
    lines.append(f"Banco: {data.get('nome_banco','')}")
    lines.append(f"Agência: {data.get('agencia','')}")
    lines.append(f"Conta: {data.get('conta','')}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(lines)
