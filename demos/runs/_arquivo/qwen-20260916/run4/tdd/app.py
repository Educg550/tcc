import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

# Serve static files manually since we need to return index.html for /
# and also serve assets, css, js.
# But the tests expect app:app and uvicorn app:app.
# We can use StaticFiles if we mount it, but let's just read files for simplicity and control.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_file(filename: str) -> str:
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

@app.get("/", response_class=HTMLResponse)
async def root():
    return read_file("index.html")

@app.get("/style.css")
async def style():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(read_file("style.css"), media_type="text/css")

@app.get("/app.js")
async def app_js():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(read_file("app.js"), media_type="application/javascript")

@app.get("/assets/{filename}")
async def assets(filename: str):
    path = os.path.join(BASE_DIR, "assets", filename)
    if not os.path.exists(path):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    # Determine media type
    ext = os.path.splitext(filename)[1].lower()
    media_type = "application/octet-stream"
    if ext in (".png", ".jpg", ".jpeg", ".gif"):
        media_type = "image/png" if ext == ".png" else "image/jpeg"
    
    from fastapi.responses import FileResponse
    return FileResponse(path, media_type=media_type)


def validar_cpf(cpf: str) -> bool:
    """Valida o CPF (considera apenas dígitos)."""
    cpf = re.sub(r"[^0-9]", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    def digito(cpf_parcial: str, peso_ini: int) -> int:
        soma = sum(int(c) * (peso_ini - i) for i, c in enumerate(cpf_parcial))
        d = 11 - (soma % 11)
        return 0 if d == 11 else d
    
    if digito(cpf[:9], 10) != int(cpf[9]):
        return False
    if digito(cpf[:10], 11) != int(cpf[10]):
        return False
    return True


@app.post("/solicitacao")
async def solicitacao(dados: Dict[str, Any]):
    erros: List[str] = []
    aba = dados.get("aba", "alunos")
    
    # Campos obrigatórios
    campos_obrigatorios = [
        "nome_completo", "numusp", "programa", "email",
        "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
        "pais_evento", "valor_solicitado", "detalhamento", "apresentar_trabalho",
        "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "nome_banco", "numero_agencia", "numero_conta"
    ]
    
    if aba == "alunos":
        campos_obrigatorios.extend(["nivel", "tipo_auxilio"])
        
    vazio = False
    for campo in campos_obrigatorios:
        val = dados.get(campo)
        if val is None or str(val).strip() == "":
            vazio = True
            
    if vazio:
        erros.append("Preencha todos os campos")

    # Validações específicas
    numusp = str(dados.get("numusp", ""))
    if numusp and not numusp.isdigit():
        erros.append("N. USP deve conter apenas números")
        
    agencia = str(dados.get("numero_agencia", ""))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
        
    valor = str(dados.get("valor_solicitado", "")).strip()
    if valor:
        # Aceita entrada como inteiros (centavos) ou strings formatadas
        # O frontend envia o valor dos centavos? O requisito diz "digitados são os centavos".
        # Os testes enviam "150000" (que é 1500.00). 
        # Teste de erro negativo: "-5"
        try:
            val_num = float(valor)
            if val_num <= 0:
                 erros.append("Valor solicitado deve ser maior que 0")
            else:
                 # Se vier formatado como string, tentamos converter
                 pass
        except ValueError:
            # Se não for número, mas estiver preenchido e não for erro de vazio, 
            # talvez o formato seja inválido, mas o requisito só diz "natural maior que 0".
            # Se for "1.500,00" vindo do backend? Não, o backend recebe a string pura dos centavos 
            # ou a string formatada? 
            # Nos testes, valor_solicitado é enviado como string numérica pura: "150000", "0", "-5".
            # O formatador JS faz a mágica no client.
            # Se vier string que não é número, tratamos como erro? 
            # O requisito diz "número natural maior que 0".
            if valor not in ("", "0", "-1"): # Simplificação para evitar duplicar erro se já foi vazio
                 pass
            # Se não conseguiu converter, e não estava vazio, é inválido?
            # Vamos assumir que se não é número, é erro de valor.
            erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", ""))
    if email:
        if "@" not in email:
            erros.append("E-mail inválido")
        else:
            partes = email.split("@")
            if len(partes) != 2 or not partes[1]: # Sem domínio
                erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", ""))
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            if not validar_cpf(cpf):
                erros.append("CPF inválido")

    cep = str(dados.get("cep", ""))
    if cep:
        if not re.match(r"^\d{5}-\d{3}$", cep):
            erros.append("CEP deve estar no formato 00000-000")

    data_nasc = str(dados.get("data_nascimento", ""))
    if data_nasc:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nasc):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(data_nasc, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    # Se houver erros, retorna
    if erros:
        return {"valido": False, "erros": erros}

    # Gera ofício
    def formatar_valor(v):
        # O valor enviado nos testes é string de dígitos (centavos)
        # "150000" -> 1500.00
        try:
            cents = int(float(v))
            val = cents / 100
            return "R$ {:,.2f}".format(val).replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    nome = dados.get("nome_completo")
    numusp = dados.get("numusp")
    email = dados.get("email")
    programa = dados.get("programa")
    nivel = dados.get("nivel")
    tipo_auxilio = dados.get("tipo_auxilio")
    nome_evento = dados.get("nome_evento")
    periodo = dados.get("periodo_evento")
    cidade_ev = dados.get("cidade_evento")
    estado_ev = dados.get("estado_evento")
    pais_ev = dados.get("pais_evento")
    link = dados.get("link_evento", "").strip()
    valor_formatado = formatar_valor(dados.get("valor_solicitado"))
    detalhamento = dados.get("detalhamento")
    trabalho = dados.get("apresentar_trabalho")
    
    logradouro = dados.get("logradouro")
    numero = dados.get("numero")
    complemento = dados.get("complemento", "").strip()
    cep = dados.get("cep")
    bairro = dados.get("bairro")
    cidade = dados.get("cidade")
    estado = dados.get("estado")
    
    data_nasc = dados.get("data_nascimento")
    cpf = dados.get("cpf")
    rg = dados.get("rg")
    banco = dados.get("nome_banco")
    agencia = dados.get("numero_agencia")
    conta = dados.get("numero_conta")

    assunto = f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}" if aba == "alunos" else "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
    
    if aba == "alunos":
        linha_programa = f"Programa: {programa} - {nivel}"
        tipo_txt = tipo_auxilio
    else:
        linha_programa = f"Programa: {programa}"
        tipo_txt = "Verba do programa"

    oficio = f"""Interessada(o): {nome} - {numusp}
E-mail: {email}
{assunto}
{linha_programa}

A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {nome_evento}
Período: {periodo}
Local: {cidade_ev} - {estado_ev} - {pais_ev}
{f'Link do evento: {link}' if link else ''}
Apresentação de trabalho: {trabalho}
Valor solicitado: {valor_formatado}
Detalhamento: {detalhamento}

Endereço da(o) interessada(o)
{logradouro}, {numero}
{f'Complemento: {complemento}' if complemento else ''}
CEP: {cep}
{bairro}, {cidade} - {estado}

Dados para pagamento
Data de nascimento: {data_nasc}
CPF: {cpf}
RG / RNM: {rg}
Banco: {banco}
Agência: {agencia}
Conta: {conta}

Encaminhe-se ao Serviço Financeiro para providências.""".strip()
    
    # Remove linhas vazias desnecessárias geradas por condicionais vazias
    linhas = [l for l in oficio.split("\n") if l.strip() != "" or l == ""]
    # Reconstruct cleanly to remove empty lines from conditionals
    linhas_limpos = []
    for l in oficio.split("\n"):
        if l == "" and (not linhas_limpos or linhas_limpos[-1] == ""): # Evitar múltiplas quebras
             continue
        linhas_limpos.append(l)
             
    oficio_final = "\n".join(linhas_limpos)

    return {"valido": True, "erros": [], "oficio": oficio_final}
