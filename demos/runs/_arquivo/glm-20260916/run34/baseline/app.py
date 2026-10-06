import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    origem: str
    dados: dict[str, str]


app = FastAPI()

OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]
OBRIGATORIOS_ALUNOS = ["nivel", "tipo"]


def texto(dados: dict[str, str], chave: str) -> str:
    return (dados.get(chave) or "").strip()


def interpretar_moeda(valor: str) -> int | None:
    limpo = valor.replace("R$", "").replace(".", "").replace(",", "").strip()
    return int(limpo) if limpo.isdigit() else None


def formatar_moeda(centavos: int) -> str:
    digitos = str(centavos).rjust(3, "0")
    reais = digitos[:-2]
    blocos = []
    while len(reais) > 3:
        blocos.insert(0, reais[-3:])
        reais = reais[:-3]
    blocos.insert(0, reais)
    return "R$ " + ".".join(blocos) + "," + digitos[-2:]


def cpf_valido(cpf: str) -> bool:
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    digito1 = (sum(n * p for n, p in zip(numeros[:9], range(10, 1, -1))) * 10) % 11 % 10
    digito2 = (sum(n * p for n, p in zip(numeros[:10], range(11, 1, -1))) * 10) % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(origem: str, dados: dict[str, str]) -> list[str]:
    erros: list[str] = []
    obrigatorios = OBRIGATORIOS + (OBRIGATORIOS_ALUNOS if origem == "alunos" else [])
    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = texto(dados, "nusp")
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor")
    centavos = None
    if valor:
        centavos = interpretar_moeda(valor)
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
            centavos = None

    email = texto(dados, "email")
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0].strip() or not partes[1].strip():
            erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "nascimento")
    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(origem: str, dados: dict[str, str], centavos: int) -> str:
    if origem == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + texto(dados, "tipo")
        programa = "Programa: " + texto(dados, "programa") + " - " + texto(dados, "nivel")
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + texto(dados, "programa")

    linhas = [
        "Interessada(o): " + texto(dados, "nome") + " - " + texto(dados, "nusp"),
        "E-mail: " + texto(dados, "email"),
        assunto,
        programa,
        "",
        "A CCP-" + texto(dados, "programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + texto(dados, "evento"),
        "Período: " + texto(dados, "periodo"),
        "Local: " + texto(dados, "cidade_evento") + " - " + texto(dados, "estado_evento") + " - " + texto(dados, "pais_evento"),
    ]
    link = texto(dados, "link")
    if link:
        linhas.append("Link do evento: " + link)
    linhas.extend([
        "Apresentação de trabalho: " + texto(dados, "apresentacao"),
        "Valor solicitado: " + formatar_moeda(centavos),
        "Detalhamento: " + texto(dados, "detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        texto(dados, "logradouro") + ", " + texto(dados, "numero"),
    ])
    complemento = texto(dados, "complemento")
    if complemento:
        linhas.append("Complemento: " + complemento)
    linhas.extend([
        "CEP: " + texto(dados, "cep"),
        texto(dados, "bairro") + ", " + texto(dados, "cidade") + " - " + texto(dados, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + texto(dados, "nascimento"),
        "CPF: " + texto(dados, "cpf"),
        "RG / RNM: " + texto(dados, "rg"),
        "Banco: " + texto(dados, "banco"),
        "Agência: " + texto(dados, "agencia"),
        "Conta: " + texto(dados, "conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao.origem, solicitacao.dados)
    if erros:
        return {"erros": erros}
    centavos = interpretar_moeda(texto(solicitacao.dados, "valor"))
    return {"oficio": gerar_oficio(solicitacao.origem, solicitacao.dados, centavos)}


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
