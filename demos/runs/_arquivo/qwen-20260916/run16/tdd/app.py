import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).parent

app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="statics")


def _validar_cpf(cpf):
    if not re.match(r'^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$', cpf):
        return "CPF deve estar no formato 000.000.000-00"
    numeros = [int(i) for i in re.findall(r'\\d', cpf)]
    
    soma = 0
    for i in range(9):
        soma += numeros[i] * (10 - i)
    resto = 11 - (soma % 11)
    if resto > 9:
        resto = 0
    if resto != numeros[9]:
        return "CPF inválido"
        
    soma = 0
    for i in range(10):
        soma += numeros[i] * (11 - i)
    resto = 11 - (soma % 11)
    if resto > 9:
        resto = 0
    if resto != numeros[10]:
        return "CPF inválido"


def _validar_data(data):
    if not re.match(r'^\\d{2}/\\d{2}/\\d{4}$', data):
        return "Data de nascimento deve estar no formato dd/mm/aaaa"
    dia, mes, ano = map(int, data.split('/'))
    try:
        import datetime
        datetime.date(ano, mes, dia)
    except ValueError:
        return "Data de nascimento inválida"


@app.post("/solicitacao")
async def solicitacao(dados: dict):
    erros = []
    
    aba = dados.get("aba", "alunos")
    
    campos_obrigatorios = [
        "nome_completo", "numero_usp", "programa", "email", "nome_evento", "periodo", "cidade_evento",
        "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao", "data_nascimento",
        "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"
    ]
    
    if aba == "alunos":
        campos_obrigatorios.extend(["nivel", "tipo_auxilio"])
        
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            erros.append("Preencha todos os campos")
            break

    if re.match(r'^\\d+$', dados.get("numero_usp", "")) is None:
        erros.append("N. USP deve conter apenas números")

    if re.match(r'^\\d+$', dados.get("agencia", "")) is None:
        erros.append("Número da agência deve conter apenas números")

    valor_str = dados.get("valor", "").replace(".", "").replace(",", ".").replace("R$", "").strip()
    try:
        valor_num = float(valor_str) if valor_str else 0.0
        if valor_num <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    except ValueError:
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "")
    if "@" not in email or not email.split("@")[-1]:
        erros.append("E-mail inválido")

    cpf_erro = _validar_cpf(dados.get("cpf", ""))
    if cpf_erro:
        erros.append(cpf_erro)

    if re.match(r'^\\d{5}-\\d{3}$', dados.get("cep", "")) is None:
        erros.append("CEP deve estar no formato 00000-000")

    data_erro = _validar_data(dados.get("data_nascimento", ""))
    if data_erro:
        erros.append(data_erro)

    if erros:
        return JSONResponse(content={"erros": list(set(erros))}, status_code=422)
        
    # Gera ofício
    link = dados.get("link_evento", "")
    complemento = dados.get("complemento", "")
    
    valor_formatado = f"R$ {valor_num/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    linhas = []
    
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {dados.get('tipo_auxilio')}"
        programa = f"Programa: {dados.get('programa')} - {dados.get('nivel')}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados.get('programa')}"

    linhas.append(f"Interessada(o): {dados.get('nome_completo')} - {dados.get('numero_usp')}")
    linhas.append(f"E-mail: {dados.get('email')}")
    linhas.append(f"Assunto: {assunto}")
    linhas.append(programa)
    linhas.append("")
    linhas.append("A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(dados.get('programa')))
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados.get('nome_evento')}")
    linhas.append(f"Período: {dados.get('periodo')}")
    linhas.append(f"Local: {dados.get('cidade_evento')} - {dados.get('estado_evento')} - {dados.get('pais_evento')}")
    
    if link:
        linhas.append(f"Link do evento: {link}")
        
    linhas.append(f"Apresentação de trabalho: {dados.get('apresentacao')}")
    linhas.append(f"Valor solicitado: {valor_formatado}")
    linhas.append(f"Detalhamento: {dados.get('detalhamento')}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados.get('logradouro')}, {dados.get('numero')}")
    
    if complemento:
        linhas.append(f"Complemento: {complemento}")
        
    linhas.append(f"CEP: {dados.get('cep')}")
    linhas.append(f"{dados.get('bairro')}, {dados.get('cidade')} - {dados.get('estado')}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {dados.get('data_nascimento')}")
    linhas.append(f"CPF: {dados.get('cpf')}")
    linhas.append(f"RG / RNM: {dados.get('rg')}")
    linhas.append(f"Banco: {dados.get('banco')}")
    linhas.append(f"Agência: {dados.get('agencia')}")
    linhas.append(f"Conta: {dados.get('conta')}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    
    oficio = "\n".join(linhas)
    return JSONResponse(content={"oficio": oficio}, status_code=200)
