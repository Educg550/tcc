import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Servir os arquivos estáticos (css, js, assets)
app.mount("/assets", StaticFiles(directory="assets", name="assets"), name="assets")

# Helper para servir o HTML raiz
@app.get("/")
def read_root():
    return FileResponse("index.html")

class Solicitacao(BaseModel):
    nome: str
    nusp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link: Optional[str] = ""
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
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

def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if not cpf or len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = 0
        pos = i + 1
        for num in cpf[:i]:
            soma += int(num) * pos
            pos -= 1
        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0
        if int(cpf[i]) != digito:
            return False
    return True

def formatar_valor(valor: str) -> str:
    try:
        cents = int(valor)
        reais = cents // 100
        cents_part = cents % 100
        milhar = "{:,}".format(reais)
        milhar = milhar.replace(",", ".")
        return f"R$ {milhar},{cents_part:02d}"
    except:
        return valor

def formatar_data_br(data_str):
    try:
        dia, mes, ano = data_str.split('/')
        return f"{int(dia):02d}/{int(mes):02d}/{ano}"
    except:
        return data_str

def validar_data(data_str):
    try:
        if len(data_str) != 10 or data_str[2] != '/' or data_str[5] != '/':
            return False
        dia, mes, ano = map(int, data_str.split('/'))
        if ano < 1000 or ano > 9999: return False
        if mes < 1 or mes > 12: return False
        if dia < 1: return False
        if mes == 2:
            bissexto = (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0)
            return dia <= (29 if bissexto else 28)
        if mes in (4, 6, 9, 11):
            return dia <= 30
        return dia <= 31
    except:
        return False

@app.post("/solicitacao")
def processar_solicitacao(dados: Solicitacao):
    erros = []
    # 1. Campos obrigatórios
    d = dados.dict()
    for k in d:
        if k not in ('nivel', 'tipo_auxilio', 'link', 'complemento'):
            if not d[k] or d[k].strip() == "":
                erros.append("Preencha todos os campos")
                break

    # 2. N. USP
    if dados.nusp and not dados.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
        
    # 3. Agência
    if dados.agencia and not dados.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
        
    # 4. Valor (R$)
    if dados.valor:
        try:
            v = int(dados.valor)
            if v <= 0:
                erros.append("Valor solicitado deve ser maior que 0")
        except:
            erros.append("Valor solicitado deve ser maior que 0")
            
    # 5. Email
    if dados.email and ("@" not in dados.email or not dados.email.split("@")[-1]):
        erros.append("E-mail inválido")
        
    # 6. CPF format
    if dados.cpf and not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', dados.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif dados.cpf and not validar_cpf(dados.cpf):
        erros.append("CPF inválido")
        
    # 7. CEP format
    if dados.cep and not re.match(r'^\d{5}-\d{3}$', dados.cep):
        erros.append("CEP deve estar no formato 00000-000")
        
    # 8. Data de nascimento format and value
    if dados.nascimento:
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', dados.nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not validar_data(dados.nascimento):
            erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse(content={"erros": erros})
        
    # Geração do Ofício
    tipo = dados.tipo_auxilio if dados.tipo_auxilio else "Verba do programa"
    nivel_str = f" - {dados.nivel}" if dados.nivel else ""
    programa_assunto = f"Programa: {dados.programa}{nivel_str}"
    assunto = f"Assunto: Solicitação de Auxílio Financeiro - {tipo}"
    valor_formatado = formatar_valor(dados.valor)
    data_formatada = formatar_data_br(dados.nascimento)
    
    linhas = [
        f"Interessada(o): {dados.nome} - {dados.nusp}",
        f"E-mail: {dados.email}",
        assunto,
        programa_assunto,
        "",
        f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.evento}",
        f"Período: {dados.periodo}",
        f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}"
    ]
    if dados.link:
        linhas.append(f"Link do evento: {dados.link}")
        
    linhas.extend([
        f"Apresentação de trabalho: {dados.apresentacao}",
        f"Valor solicitado: {valor_formatado}",
        f"Detalhamento: {dados.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.logradouro}, {dados.numero}"
    ])
    if dados.complemento:
        linhas.append(f"Complemento: {dados.complemento}")
        
    linhas.extend([
        f"CEP: {dados.cep}",
        f"{dados.bairro}, {dados.cidade} - {dados.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data_formatada}",
        f"CPF: {dados.cpf}",
        f"RG / RNM: {dados.rg}",
        f"Banco: {dados.banco}",
        f"Agência: {dados.agencia}",
        f"Conta: {dados.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências."
    ])
    
    oficio = "\n".join(linhas)
    return JSONResponse(content={"erros": [], "oficio": oficio})
