import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")


class Solicitacao(BaseModel):
    aba: str
    dados: dict


@app.post("/api/solicitacao")
async def criar_solicitacao(s: Solicitacao):
    return validar(s.aba, s.dados)


def validar(aba, d):
    erros = []
    campos_texto = [
        "nome", "nusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
        "apresentacao", "logradouro", "numero", "bairro", "cep", "cidade",
        "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "alunos":
        campos_texto += ["nivel", "tipo_auxilio"]
    vazio = [c for c in campos_texto if not str(d.get(c, "")).strip()]
    if vazio:
        erros.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", str(d.get("nusp", ""))):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", str(d.get("agencia", ""))):
        erros.append("Número da agência deve conter apenas números")
    if not re.fullmatch(r"\d+", str(d.get("valor", ""))) or int(d.get("valor") or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(d.get("email", ""))
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", str(d.get("cpf", ""))):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(str(d["cpf"])):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", str(d.get("cep", ""))):
        erros.append("CEP deve estar no formato 00000-000")
    nasc = str(d.get("nascimento", ""))
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not data_valida(nasc):
        erros.append("Data de nascimento inválida")
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(aba, d)}


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * (10 - j if i == 9 else 11 - j) for j in range(i))
        resto = soma % 11
        if (resto < 2 and digitos[i] != 0) or (resto >= 2 and digitos[i] != 11 - resto):
            return False
    return True


def data_valida(s):
    try:
        date.fromisoformat("-".join([s[4:8], s[2:4], s[0:2]]))
        return True
    except ValueError:
        return False


def gerar_oficio(aba, d):
    valor = formatar_valor(int(d["valor"]))
    linhas = []
    linhas.append(f"Interessada(o): {d['nome']} - {d['nusp']}")
    linhas.append(f"E-mail: {d['email']}")
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}")
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    linhas.append("")
    linhas.append("A CCP-" + d['programa'] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d['evento']}")
    linhas.append(f"Período: {d['periodo']}")
    linhas.append(f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}")
    if d.get("link"):
        linhas.append(f"Link do evento: {d['link']}")
    linhas.append(f"Apresentação de trabalho: {d['apresentacao']}")
    linhas.append(f"Valor solicitado: {valor}")
    linhas.append(f"Detalhamento: {d['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['logradouro']}, {d['numero']}")
    if d.get("complemento"):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas.append(f"CEP: {d['cep']}")
    linhas.append(f"{d['bairro']}, {d['cidade']} - {d['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d['nascimento']}")
    linhas.append(f"CPF: {d['cpf']}")
    linhas.append(f"RG / RNM: {d['rg']}")
    linhas.append(f"Banco: {d['banco']}")
    linages_ag = f"Agência: {d['agencia']}"
    linhas.append(linages_ag)
    linhas.append(f"Conta: {d['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


def formatar_valor(centavos):
    reais = centavos // 100
    cent = centavos % 100
    s = str(reais)
    grupos = []
    while s:
        grupos.insert(0, s[-3:])
        s = s[:-3]
    return "R$ " + ".".join(grupos) + f",{cent:02d}"
