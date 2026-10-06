import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str = "alunos"
    campos: dict = {}


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


def cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in re.sub(r"\D", "", cpf)]
    resto = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    digito1 = 0 if resto < 2 else 11 - resto
    resto = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    digito2 = 0 if resto < 2 else 11 - resto
    return digitos[9] == digito1 and digitos[10] == digito2


def formatar_moeda(centavos: str) -> str:
    reais, centavos = divmod(int(centavos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def validar(aba: str, c: dict) -> list:
    erros = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if aba == "alunos" else [])
    if any(not c.get(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if c.get("n_usp") and not re.fullmatch(r"[0-9]+", c["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if c.get("agencia") and not re.fullmatch(r"[0-9]+", c["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    if c.get("valor") and (not re.fullmatch(r"[0-9]+", c["valor"]) or int(c["valor"]) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = c.get("email", "")
    if email and (email.count("@") != 1 or not email.split("@")[0] or not email.split("@")[1]):
        erros.append("E-mail inválido")

    cpf = c.get("cpf", "")
    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if c.get("cep") and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", c["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    data = c.get("data_nascimento", "")
    data_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", data))
    if data and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(aba: str, c: dict) -> str:
    if aba == "alunos":
        topo = [
            f"Interessada(o): {c['nome']} - {c['n_usp']}",
            f"E-mail: {c['email']}",
            f"Assunto: Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}",
            f"Programa: {c['programa']} - {c['nivel']}",
        ]
    else:
        topo = [
            f"Interessada(o): {c['nome']} - {c['n_usp']}",
            f"E-mail: {c['email']}",
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {c['programa']}",
        ]

    linhas = [
        *topo,
        "",
        (
            f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio "
            "financeiro para a\ninteressada(o) acima, conforme segue:"
        ),
        "",
        "Dados do evento",
        f"Evento: {c['evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c.get("link_evento"):
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {formatar_moeda(c['valor'])}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c.get("complemento"):
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(s: Solicitacao):
    aba = s.aba.strip().lower()
    campos = {
        chave: (valor if isinstance(valor, str) else "" if valor is None else str(valor)).strip()
        for chave, valor in s.campos.items()
    }
    erros = validar(aba, campos)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(aba, campos)}


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


if (BASE / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
