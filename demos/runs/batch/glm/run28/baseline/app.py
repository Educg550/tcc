from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

#  verificações que o backend precisa fazer
def validar_cpf(cpf: str) -> bool:
    """confere os dígitos verificadores do cpf"""
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    def digito(numeros: str) -> int:
        soma = sum(int(n) * (len(numeros) + 1 - i) for i, n in enumerate(numeros))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto
    return digitos[9] == str(digito(digitos[:9])) and digitos[10] == str(digito(digitos[:10]))

@app.post("/validar")
async def validar(dados: dict):
    """devolve a lista de erros ou o texto do ofício"""
    erros = []
    obrigatorios = [
        "nome", "nusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "trabalho", "logradouro", "numero", "bairro",
        "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
        "data_nascimento",
    ]
    if dados.get("aba") == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    for campo in obrigatorios:
        if not dados.get(campo, "").strip():
            erros.append("Preencha todos os campos")
            break
    if not re.fullmatch(r'\d+', dados.get("nusp", "")):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r'\d+', dados.get("agencia", "")):
        erros.append("Número da agência deve conter apenas números")
    valor_raw = re.sub(r'\D', '', dados.get("valor", ""))
    try:
        valor_cents = int(valor_raw)
    except ValueError:
        valor_cents = 0
    if valor_cents <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = dados.get("email", "")
    if "@" not in email or email.split("@")[-1].strip() == "" or "." not in email.split("@")[-1]:
        erros.append("E-mail inválido")
    if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', dados.get("cpf", "")):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not validar_cpf(dados["cpf"]):
        erros.append("CPF inválido")
    if not re.fullmatch(r'\d{5}-\d{3}', dados.get("cep", "")):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', dados.get("data_nascimento", "")):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            import datetime
            datetime.datetime.strptime(dados["data_nascimento"], "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    #  monta o ofício
    valor_fmt = "R$ " + format(valor_cents / 100, ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['nusp']}",
        f"E-mail: {dados['email']}",
    ]
    if dados.get("aba") == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    linhas += [
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados.get("link", "").strip():
        linhas.append(f"Link do evento: {dados['link']}")
    linhas += [
        f"Apresentação de trabalho: {dados['trabalho']}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados.get("complemento", "").strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return JSONResponse({"ok": True, "oficio": "\n".join(linhas), "erros": []})

@app.get("/")
def raiz():
    with open("index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

from fastapi.responses import HTMLResponse
