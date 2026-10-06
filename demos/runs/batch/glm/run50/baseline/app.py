import re
from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()
app.mount("/", StaticFiles(directory=".", html=True), name="static")

CAMPOS = [
    "nome", "nusp", "programa", "email", "evento", "periodo", "cidade", "estado", "pais",
    "link", "valor", "detalhamento", "apresentacao", "datanasc", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco",
    "agencia", "conta",
]


class Solicitacao(BaseModel):
    perfil: str
    dados: dict


def validar_cpf(cpf):
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    for d in set(cpf):
        if cpf.count(d) == 11:
            return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if digito1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    return digito2 == int(cpf[10])


def validar(dados, perfil):
    erros = []
    obrigatorios = [c for c in CAMPOS if c not in ("link", "complemento")]
    if perfil == "alunos":
        obrigatorios += ["nivel", "tipo"]
    for campo in obrigatorios:
        if not dados.get(campo, "").strip():
            if "Preencha todos os campos" not in erros:
                erros.append("Preencha todos os campos")
    if dados.get("nusp") and not dados["nusp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados.get("agencia") and not dados["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    try:
        valor = int(dados.get("valor", "").replace(".", "").replace(",", ""))
    except ValueError:
        valor = -1
    if dados.get("valor") and valor <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = dados.get("email", "")
    if email and ("@" not in email or "@" in email.split("@")[-1] or not email.split("@")[-1]):
        erros.append("E-mail inválido")
    cpf = dados.get("cpf", "")
    if cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not validar_cpf(re.sub(r"\D", "", cpf)):
        erros.append("CPF inválido")
    cep = dados.get("cep", "")
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")
    datanasc = dados.get("datanasc", "")
    if datanasc and not re.match(r"^\d{2}/\d{2}/\d{4}$", datanasc):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif datanasc:
        try:
            d, m, a = map(int, datanasc.split("/"))
            date(a, m, d)
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(perfil, dados):
    v = dados.get("valor")
    valor = f"R$ {v},00" if "," not in v else "R$ " + v
    linhas = [f"Interessada(o): {dados['nome']} - {dados['nusp']}", f"E-mail: {dados['email']}"]
    if perfil == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    linhas += [
        "",
        "A CCP-" + dados['programa'] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + dados['evento'],
        "Período: " + dados['periodo'],
        "Local: " + dados['cidade'] + " - " + dados['estado'] + " - " + dados['pais'],
    ]
    if dados.get('link'):
        linhas.append("Link do evento: " + dados['link'])
    linhas += [
        "Apresentação de trabalho: " + dados['apresentacao'],
        "Valor solicitado: " + valor,
        "Detalhamento: " + dados['detalhamento'],
        "",
        "Endereço da(o) interessada(o)",
        dados['logradouro'] + ", " + dados['numero'],
    ]
    if dados.get('complemento'):
        linhas.append("Complemento: " + dados['complemento'])
    linhas += [
        "CEP: " + dados['cep'],
        dados['bairro'] + ", " + dados['cidade_end'] + " - " + dados['estado_end'],
        "",
        "Dados para pagamento",
        "Data de nascimento: " + dados['datanasc'],
        "CPF: " + dados['cpf'],
        "RG / RNM: " + dados['rg'],
        "Banco: " + dados['banco'],
        "Agência: " + dados['agencia'],
        "Conta: " + dados['conta'],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber(solicitacao: Solicitacao):
    dados = {c: solicitacao.dados.get(c, "").strip() if isinstance(solicitacao.dados.get(c), str) else solicitacao.dados.get(c, "") for c in solicitacao.dados}
    erros = validar(dados, solicitacao.perfil)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(solicitacao.perfil, dados)}
