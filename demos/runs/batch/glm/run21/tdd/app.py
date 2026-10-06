import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


OBRIGATORIOS_COMUNS = [
    "nome_completo", "n_usp", "programa", "email",
    "nome_do_evento", "periodo_do_evento", "cidade_do_evento",
    "estado_do_evento", "pais_do_evento", "valor_solicitado",
    "detalhamento_do_pedido", "apresentacao_de_trabalho",
    "data_de_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_do_banco",
    "numero_da_agencia", "numero_da_conta",
]
OBRIGATORIOS_ALUNOS = ["nivel", "tipo_de_auxilio"]


def texto(dados, campo):
    return str(dados.get(campo) or "").strip()


def so_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def cpf_valido(digitos):
    if digitos == digitos[0] * 11:
        return False

    def verificador(parcial, peso):
        soma = sum(int(d) * (peso - i) for i, d in enumerate(parcial))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    return (
        verificador(digitos[:9], 10) == int(digitos[9])
        and verificador(digitos[:10], 11) == int(digitos[10])
    )


def validar(dados):
    aba = dados.get("aba", "alunos")
    erros = []
    obrigatorios = OBRIGATORIOS_COMUNS + (OBRIGATORIOS_ALUNOS if aba == "alunos" else [])
    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "numero_da_agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = so_digitos(texto(dados, "valor_solicitado"))
    if not valor or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email and ("@" not in email or not email.rsplit("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = so_digitos(texto(dados, "cpf"))
    if cpf and len(cpf) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = so_digitos(texto(dados, "cep"))
    if cep and len(cep) != 8:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = so_digitos(texto(dados, "data_de_nascimento"))
    if nascimento and len(nascimento) != 8:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento:
        try:
            date(int(nascimento[4:]), int(nascimento[2:4]), int(nascimento[:2]))
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def formatar_valor(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def formatar_cpf(digitos):
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def formatar_cep(digitos):
    return f"{digitos[:5]}-{digitos[5:]}"


def formatar_data(digitos):
    return f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"


def gerar_oficio(dados, aba):
    programa = texto(dados, "programa")
    linhas = [
        "Interessada(o): " + texto(dados, "nome_completo") + " - " + texto(dados, "n_usp"),
        "E-mail: " + texto(dados, "email"),
    ]
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: " + programa)
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - " + texto(dados, "tipo_de_auxilio"))
        linhas.append("Programa: " + programa + " - " + texto(dados, "nivel"))
    linhas += [
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + texto(dados, "nome_do_evento"),
        "Período: " + texto(dados, "periodo_do_evento"),
        "Local: " + texto(dados, "cidade_do_evento") + " - " + texto(dados, "estado_do_evento") + " - " + texto(dados, "pais_do_evento"),
    ]
    link = texto(dados, "link_do_evento")
    if link:
        linhas.append("Link do evento: " + link)
    linhas += [
        "Apresentação de trabalho: " + texto(dados, "apresentacao_de_trabalho"),
        "Valor solicitado: " + formatar_valor(so_digitos(texto(dados, "valor_solicitado"))),
        "Detalhamento: " + texto(dados, "detalhamento_do_pedido"),
        "",
        "Endereço da(o) interessada(o)",
        texto(dados, "logradouro") + ", " + texto(dados, "numero"),
    ]
    complemento = texto(dados, "complemento")
    if complemento:
        linhas.append("Complemento: " + complemento)
    linhas += [
        "CEP: " + formatar_cep(so_digitos(texto(dados, "cep"))),
        texto(dados, "bairro") + ", " + texto(dados, "cidade") + " - " + texto(dados, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + formatar_data(so_digitos(texto(dados, "data_de_nascimento"))),
        "CPF: " + formatar_cpf(so_digitos(texto(dados, "cpf"))),
        "RG / RNM: " + texto(dados, "rg_rnm"),
        "Banco: " + texto(dados, "nome_do_banco"),
        "Agência: " + texto(dados, "numero_da_agencia"),
        "Conta: " + texto(dados, "numero_da_conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    aba = dados.get("aba", "alunos")
    erros = validar(dados)
    if erros:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "aba": aba, "erros": erros},
        )
    return {
        "ok": True,
        "aba": aba,
        "titulo": "Solicitação registrada",
        "oficio": gerar_oficio(dados, aba),
    }
