import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Solicitacao(BaseModel):
    aba: str
    nome_completo: str
    n_usp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    nome_evento: str
    periodo_evento: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = None
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str

def valida_cpf(cpf: str) -> bool:
    numeros = [int(x) for x in cpf if x.isdigit()]
    if len(numeros) != 11:
        return False
    if len(set(numeros)) == 1:
        return False
    
    # Primeiro digito verificador
    soma = sum(numeros[i] * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11
    if dv1 == 10:
        dv1 = 0
    if dv1 != numeros[9]:
        return False
    
    # Segundo digito verificador
    soma = sum(numeros[i] * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11
    if dv2 == 10:
        dv2 = 0
    if dv2 != numeros[10]:
        return False
        
    return True

def valida_data(data: str) -> bool:
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', data)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12:
        return False
    dias_no_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias_no_mes[mes - 1]

def valida_cep(cep: str) -> bool:
    return bool(re.match(r'^\d{5}-\d{3}$', cep))

def valida_email(email: str) -> bool:
    if '@' not in email:
        return False
    partes = email.split('@')
    if len(partes) != 2:
        return False
    usuario, dominio = partes
    if not usuario or not dominio:
        return False
    if '.' not in dominio:
        return False
    return True

def valida_valor(valor: str) -> Optional[str]:
    try:
        v = int(valor)
        if v > 0:
            return v
        return None
    except ValueError:
        return None

def formata_valor(centavos: int) -> str:
    inteiro = centavos // 100
    fracao = centavos % 100
    inteiro_str = f"{inteiro:,}".replace(",", ".")
    return f"R$ {inteiro_str},{fracao:02d}"

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.post("/solicitacao")
def cria_solicitacao(s: Solicitacao):
    erros = []
    
    campos_obrigatorios = [
        s.nome_completo, s.n_usp, s.programa, s.email, s.nome_evento,
        s.periodo_evento, s.cidade_evento, s.estado_evento, s.pais_evento,
        s.valor_solicitado, s.detalhamento, s.apresentacao, s.data_nascimento,
        s.logradouro, s.numero, s.bairro, s.cep, s.cidade, s.estado,
        s.cpf, s.rg, s.banco, s.agencia, s.conta
    ]
    if s.aba == "ALUNOS":
        campos_obrigatorios.append(s.nivel)
        campos_obrigatorios.append(s.tipo_auxilio)
        
    if any(not c for c in campos_obrigatorios):
        erros.append("Preencha todos os campos")
        
    if s.aba == "ALUNOS":
        if s.nivel not in ["Mestrado", "Doutorado", None]:
             erros.append("Preencha todos os campos") # Simplificação, valida no empty acima

    if s.n_usp and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
        
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
        
    v = valida_valor(s.valor_solicitado)
    if v is None:
        erros.append("Valor solicitado deve ser maior que 0")
        
    if s.email and not valida_email(s.email):
        erros.append("E-mail inválido")
        
    if s.cpf:
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', s.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not valida_cpf(s.cpf):
            erros.append("CPF inválido")
            
    if s.cep:
        if not valida_cep(s.cep):
            erros.append("CEP deve estar no formato 00000-000")
            
    if s.data_nascimento:
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', s.data_nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not valida_data(s.data_nascimento):
            erros.append("Data de nascimento inválida")
            
    if erros:
        return {"erros": erros}
        
    link_l = s.link_evento if s.link_evento else ""
    comp_l = s.complemento if s.complemento else ""
    
    oficio_linhas = []
    oficio_linhas.append(f"Interessada(o): {s.nome_completo} - {s.n_usp}")
    oficio_linhas.append(f"E-mail: {s.email}")
    
    if s.aba == "ALUNOS":
        oficio_linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        oficio_linhas.append(f"Programa: {s.programa} - {s.nivel}")
    else:
        oficio_linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        oficio_linhas.append(f"Programa: {s.programa}")
        
    oficio_linhas.append("")
    oficio_linhas.append("A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(s.programa))
    oficio_linhas.append("interessada(o) acima, conforme segue:")
    oficio_linhas.append("")
    oficio_linhas.append("Dados do evento")
    oficio_linhas.append(f"Evento: {s.nome_evento}")
    oficio_linhas.append(f"Período: {s.periodo_evento}")
    oficio_linhas.append(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if link_l:
        oficio_linhas.append(f"Link do evento: {link_l}")
    oficio_linhas.append(f"Apresentação de trabalho: {s.apresentacao}")
    oficio_linhas.append(f"Valor solicitado: {formata_valor(v)}")
    oficio_linhas.append(f"Detalhamento: {s.detalhamento}")
    oficio_linhas.append("")
    oficio_linhas.append("Endereço da(o) interessada(o)")
    oficio_linhas.append(f"{s.logradouro}, {s.numero}")
    if comp_l:
        oficio_linhas.append(f"Complemento: {comp_l}")
    oficio_linhas.append(f"CEP: {s.cep}")
    oficio_linhas.append(f"{s.bairro}, {s.cidade} - {s.estado}")
    oficio_linhas.append("")
    oficio_linhas.append("Dados para pagamento")
    oficio_linhas.append(f"Data de nascimento: {s.data_nascimento}")
    oficio_linhas.append(f"CPF: {s.cpf}")
    oficio_linhas.append(f"RG / RNM: {s.rg}")
    oficio_linhas.append(f"Banco: {s.banco}")
    oficio_linhas.append(f"Agência: {s.agencia}")
    oficio_linhas.append(f"Conta: {s.conta}")
    oficio_linhas.append("")
    oficio_linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    
    oficio = "\n".join(oficio_linhas)
    return {"oficio": oficio}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
