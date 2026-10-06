import re
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# Mount static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Helper for CPF validation
def is_valid_cpf(cpf: str) -> bool:
    cpf = re.sub(r'[^\d]', '', cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    
    # First digit
    sm = 0
    w = 10
    for i in range(9):
        sm += int(cpf[i]) * w
        w -= 1
    d1 = (sm * 10) % 11
    if d1 == 10:
        d1 = 0
    if int(cpf[9]) != d1:
        return False
    
    # Second digit
    sm = 0
    w = 11
    for i in range(10):
        sm += int(cpf[i]) * w
        w -= 1
    d2 = (sm * 10) % 11
    if d2 == 10:
        d2 = 0
    if int(cpf[10]) != d2:
        return False
        
    return True

def format_brl(cents: int) -> str:
    s = f"{cents:03d}"
    int_part = s[:-2]
    dec_part = s[-2:]
    # Format int part with dots for thousands
    formatted_int = re.sub(r'(?<=\d)(?=(\d{3})+(?!\d))', '.', int_part)
    return f"R$ {formatted_int},{dec_part}"

class Solicitacao(BaseModel):
    tipo: str
    nome: str
    numusp: str
    programa: str
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = ""
    valor: int
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str
    # Alunos specific
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None

@app.post("/solicitar")
async def solicitar(dados: Solicitacao):
    erros: List[str] = []
    
    # Check required fields (except optional ones)
    required_fields = [
        "nome", "numusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "detalhamento",
        "apresentacao", "data_nascimento", "logradouro", "numero",
        "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
        "agencia", "conta"
    ]
    
    # Add level and tipo_auxilio for alunos
    if dados.tipo == "alunos":
        if not dados.nivel:
            required_fields.append("nivel")
        if not dados.tipo_auxilio:
            required_fields.append("tipo_auxilio")
            
    empty_field_found = False
    for field in required_fields:
        val = getattr(dados, field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            empty_field_found = True
            break
            
    if empty_field_found:
        erros.append("Preencha todos os campos")
        return {"sucesso": False, "erros": erros}

    # N. USP validation
    if not dados.numusp.isdigit():
        erros.append("N. USP deve conter apenas numeros")
        
    # Agência validation
    if not dados.agencia.isdigit():
        erros.append("Numero da agencia deve conter apenas numeros")
        
    # Valor validation
    if dados.valor <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
        
    # Email validation
    if "@" not in dados.email or dados.email.split("@")[1] == "" or "." not in dados.email.split("@")[1]:
        # Simple check: must have @ and domain
        if "@" not in dados.email or len(dados.email.split("@")) < 2 or dados.email.split("@")[-1] == "":
             erros.append("E-mail invalido")
    
    # CPF Format
    cpf_pattern = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
    if not re.match(cpf_pattern, dados.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    else:
        if not is_valid_cpf(dados.cpf):
            erros.append("CPF invalido")

    # CEP Format
    cep_pattern = r'^\d{5}-\d{3}$'
    if not re.match(cep_pattern, dados.cep):
        erros.append("CEP deve estar no formato 00000-000")

    # Date Format
    date_pattern = r'^\d{2}/\d{2}/\d{4}$'
    if not re.match(date_pattern, dados.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            d, m, y = map(int, dados.data_nascimento.split('/'))
            if m < 1 or m > 12 or d < 1:
                erros.append("Data de nascimento invalida")
            else:
                # Simple month day validation
                days_in_month = [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                if d > days_in_month[m - 1]:
                    erros.append("Data de nascimento invalida")
        except ValueError:
            erros.append("Data de nascimento invalida")

    if erros:
        return {"sucesso": False, "erros": list(set(erros))}

    # Generate Oficio
    
    subject = f"Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}" if dados.tipo == "alunos" else "Solicitação de Auxílio Financeiro - Verba do programa"
    program_line = f"Programa: {dados.programa} - {dados.nivel}" if dados.tipo == "alunos" else f"Programa: {dados.programa}"
    
    valor_formatado = format_brl(dados.valor)
    
    lines = []
    lines.append(f"Interessada(o): {dados.nome} - {dados.numusp}")
    lines.append(f"E-mail: {dados.email}")
    lines.append(f"Assunto: {subject}")
    lines.append(program_line)
    lines.append("")
    lines.append("A CCP-" + dados.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {dados.evento}")
    lines.append(f"Período: {dados.periodo}")
    lines.append(f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}")
    if dados.link_evento and dados.link_evento.strip() != "":
        lines.append(f"Link do evento: {dados.link_evento}")
    lines.append(f"Apresentação de trabalho: {dados.apresentacao}")
    lines.append(f"Valor solicitado: {valor_formatado}")
    lines.append(f"Detalhamento: {dados.detalhamento}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{dados.logradouro}, {dados.numero}")
    if dados.complemento and dados.complemento.strip() != "":
        lines.append(f"Complemento: {dados.complemento}")
    lines.append(f"CEP: {dados.cep}")
    lines.append(f"{dados.bairro}, {dados.cidade} - {dados.estado}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {dados.data_nascimento}")
    lines.append(f"CPF: {dados.cpf}")
    lines.append(f"RG / RNM: {dados.rg}")
    lines.append(f"Banco: {dados.banco}")
    lines.append(f"Agência: {dados.agencia}")
    lines.append(f"Conta: {dados.conta}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")

    oficio = "\n".join(lines)
    
    return {"sucesso": True, "oficio": oficio}

@app.get("/")
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
