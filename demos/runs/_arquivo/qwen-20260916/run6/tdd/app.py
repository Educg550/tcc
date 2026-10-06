import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse

app = FastAPI()

# Static files mapping
static_files = {
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/app.js": "app.js",
    "/assets/usp-logo.png": "assets/usp-logo.png",
}

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/{path:path}")
async def read_static(path: str):
    filename = os.path.join("", path)
    if filename in static_files:
        return FileResponse(static_files[filename])
    # Handle /assets/usp-logo.png etc
    if path.startswith("assets/"):
        full_path = os.path.join("", path)
        if os.path.exists(full_path):
            return FileResponse(full_path)
    # Fallback for simple filename
    if os.path.exists(filename):
        return FileResponse(filename)
    return {"error": "Not found"}

# Validation helpers
def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r"[^0-9]", "", cpf)
    if len(cpf) != 11:
        return False
    # Check all same digits
    if cpf == cpf[0] * 11:
        return False
    
    # Verify first check digit
    sum = 0
    for i in range(9):
        sum += int(cpf[i]) * (10 - i)
    d1 = (10 * sum) % 11
    if d1 == 10 or d1 == 11:
        d1 = 0
    if int(cpf[9]) != d1:
        return False
        
    # Verify second check digit
    sum = 0
    for i in range(10):
        sum += int(cpf[i]) * (11 - i)
    d2 = (10 * sum) % 11
    if d2 == 10 or d2 == 11:
        d2 = 0
    if int(cpf[10]) != d2:
        return False
        
    return True

def validate_date(date_str: str) -> tuple[bool, bool]:
    """Returns (format_ok, date_valid)"""
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return False, False
    
    parts = date_str.split("/")
    try:
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
    except ValueError:
        return True, False
        
    if month < 1 or month > 12:
        return True, False
        
    # Days in month (approximate for validation)
    days_in_month = [31, 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28, 
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if day < 1 or day > days_in_month[month - 1]:
        return True, False
        
    return True, True

def validate_valor(valor_str: str) -> bool:
    if not valor_str or valor_str == "0":
        return False
    # Check if it's a number > 0
    # Remove 'R$ ', ' ' and '.' but keep ','
    cleaned = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        val = float(cleaned)
        return val > 0
    except ValueError:
        return False

@app.post("/api/solicitar")
async def solicitar(request: Request):
    data = await request.json()
    aba = data.get("aba", "")
    
    erros = []
    
    # Required fields check
    required_fields_alunos = [
        "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", 
        "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento", 
        "valor", "detalhamento", "apresentar", "nascimento", "logradouro", 
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", 
        "agencia", "conta"
    ]
    
    required_fields_docentes = [
        "nome", "nusp", "programa", "email", 
        "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento", 
        "valor", "detalhamento", "apresentar", "nascimento", "logradouro", 
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", 
        "agencia", "conta"
    ]
    
    fields = required_fields_alunos if aba == "alunos" else required_fields_docentes
    
    for field in fields:
        if not data.get(field):
            erros.append("Preencha todos os campos")
            break # Only one message for empty fields
            
    # Specific validations
    nusp = data.get("nusp", "")
    if nusp and not re.match(r"^\d+$", nusp):
        erros.append("N. USP deve conter apenas números")
        
    agencia = data.get("agencia", "")
    if agencia and not re.match(r"^\d+$", agencia):
        erros.append("Número da agência deve conter apenas números")
        
    valor = data.get("valor", "")
    if valor and not validate_valor(valor):
        erros.append("Valor solicitado deve ser maior que 0")
        
    email = data.get("email", "")
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        erros.append("E-mail inválido")
        
    cpf = data.get("cpf", "")
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}\-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not validate_cpf(cpf):
            erros.append("CPF inválido")
            
    cep = data.get("cep", "")
    if cep:
        if not re.match(r"^\d{5}\-\d{3}$", cep):
            erros.append("CEP deve estar no formato 00000-000")
            
    nascimento = data.get("nascimento", "")
    if nascimento:
        fmt_ok, valid = validate_date(nascimento)
        if not fmt_ok:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not valid:
            erros.append("Data de nascimento inválida")
            
    if erros:
        return {"erros": erros, "oficio": ""}
        
    # Generate ofício
    nome = data.get("nome", "")
    nusp_val = data.get("nusp", "")
    email_val = data.get("email", "")
    programa = data.get("programa", "")
    tipo_auxilio = data.get("tipo_auxilio", "")
    nivel = data.get("nivel", "")
    evento = data.get("evento", "")
    periodo = data.get("periodo", "")
    cidade_evento = data.get("cidade_evento", "")
    estado_evento = data.get("estado_evento", "")
    pais_evento = data.get("pais_evento", "")
    link_evento = data.get("link_evento", "")
    apresentar = data.get("apresentar", "")
    valor_oficio = data.get("valor", "")
    detalhamento = data.get("detalhamento", "")
    logradouro = data.get("logradouro", "")
    numero = data.get("numero", "")
    complemento = data.get("complemento", "")
    bairro = data.get("bairro", "")
    cep_val = data.get("cep", "")
    cidade = data.get("cidade", "")
    estado = data.get("estado", "")
    nascimento_val = data.get("nascimento", "")
    cpf_val = data.get("cpf", "")
    rg = data.get("rg", "")
    banco = data.get("banco", "")
    agencia_val = data.get("agencia", "")
    conta = data.get("conta", "")
    
    linhas = []
    linhas.append(f"Interessada(o): {nome} - {nusp_val}")
    linhas.append(f"E-mail: {email_val}")
    
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}")
        linhas.append(f"Programa: {programa} - {nivel}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
        
    linhas.append("")
    linhas.append(f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {evento}")
    linhas.append(f"Período: {periodo}")
    linhas.append(f"Local: {cidade_evento} - {estado_evento} - {pais_evento}")
    
    if link_evento:
        linhas.append(f"Link do evento: {link_evento}")
        
    linhas.append(f"Apresentação de trabalho: {apresentar}")
    linhas.append(f"Valor solicitado: {valor_oficio}")
    linhas.append(f"Detalhamento: {detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{logradouro}, {numero}")
    
    if complemento:
        linhas.append(f"Complemento: {complemento}")
        
    linhas.append(f"CEP: {cep_val}")
    linhas.append(f"{bairro}, {cidade} - {estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {nascimento_val}")
    linhas.append(f"CPF: {cpf_val}")
    linhas.append(f"RG / RNM: {rg}")
    linhas.append(f"Banco: {banco}")
    linhas.append(f"Agência: {agencia_val}")
    linhas.append(f"Conta: {conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    
    return {"erros": [], "oficio": linhas}