import re
import calendar
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")

CAMPOS_ALUNOS = [
    "nome", "nusp", "programa", "nivel", "auxilio", "email", "evento",
    "periodo", "cidade", "estado", "pais", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade-end", "estado-end", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "auxilio")]
OPCIONAIS = {"link", "complemento"}


def _cpf_valido(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False
    total = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = (total * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(digitos[9]):
        return False
    total = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = (total * 10) % 11
    if resto == 10:
        resto = 0
    return resto == int(digitos[10])


def _centavos(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return int(digitos) if digitos else 0


def _formatar_valor(valor):
    centavos = _centavos(valor)
    return "R$ " + f"{centavos // 100:,}".replace(",", ".") + "," + f"{centavos % 100:02d}"


def _formatar_cpf(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return digitos[:3] + "." + digitos[3:6] + "." + digitos[6:9] + "-" + digitos[9:11]


def _formatar_data(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return digitos[:2] + "/" + digitos[2:4] + "/" + digitos[4:8]


def _formatar_cep(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return digitos[:5] + "-" + digitos[5:8]


def _erros(aba, dados):
    erros = []
    campos = CAMPOS_ALUNOS if aba == "alunos" else CAMPOS_DOCENTES
    obrigat_vazios = [c for c in campos if not (dados.get(c) or "").strip()]
    if obrigat_vazios:
        erros.append("Preencha todos os campos")
    if (dados.get("nusp") or "").strip() and not re.fullmatch(r"\d+", (dados.get("nusp") or "").strip()):
        erros.append("N. USP deve conter apenas números")
    agencia = (dados.get("agencia") or "").strip()
    if agencia and not re.fullmatch(r"\d+", agencia):
        erros.append("Número da agência deve conter apenas números")
    if (dados.get("valor") or "").strip() and _centavos(dados.get("valor")) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = (dados.get("email") or "").strip()
    if email:
        padrao_email = "[^@\\s]+@[^@\\s]+\\.[A-Za-zÀ-ÿ]{2,}"
        if not re.fullmatch(padrao_email, email):
            erros.append("E-mail inválido")
    cpf = (dados.get("cpf") or "").strip()
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")
    cep = (dados.get("cep") or "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}|\d{8}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = (dados.get("nascimento") or "").strip()
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}|\d{8}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            digitos = re.sub(r"\D", "", nascimento)
            dia, mes, ano = int(digitos[:2]), int(digitos[2:4]), int(digitos[4:8])
            if not (1 <= mes <= 12 and 1 <= dia <= calendar.monthrange(ano, mes)[1]):
                erros.append("Data de nascimento inválida")
    return erros


def _gerar_oficio(aba, dados):
    valor_fmt = _formatar_valor(dados.get("valor", ""))
    cpf_fmt = _formatar_cpf(dados.get("cpf", ""))
    data_fmt = _formatar_data(dados.get("nascimento", ""))
    cep_fmt = _formatar_cep(dados.get("cep", ""))
    if aba == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + dados.get("auxilio", "")
        programa = "Programa: " + dados.get("programa", "") + " - " + dados.get("nivel", "")
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + dados.get("programa", "")
    linhas = [
        "Interessada(o): " + dados.get("nome", "") + " - " + dados.get("nusp", ""),
        "E-mail: " + dados.get("email", ""),
        assunto,
        programa,
        "",
        "A CCP-" + dados.get("programa", "") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + dados.get("evento", ""),
        "Período: " + dados.get("periodo", ""),
        "Local: " + dados.get("cidade", "") + " - " + dados.get("estado", "") + " - " + dados.get("pais", ""),
    ]
    link = (dados.get("link") or "").strip()
    if link:
        linhas.append("Link do evento: " + link)
    linhas.extend([
        "Apresentação de trabalho: " + dados.get("apresentacao", ""),
        "Valor solicitado: " + valor_fmt,
        "Detalhamento: " + dados.get("detalhamento", ""),
        "",
        "Endereço da(o) interessada(o)",
        dados.get("logradouro", "") + ", " + dados.get("numero", ""),
    ])
    complemento = (dados.get("complemento") or "").strip()
    if complemento:
        linhas.append("Complemento: " + complemento)
    linhas.extend([
        "CEP: " + cep_fmt,
        dados.get("bairro", "") + ", " + dados.get("cidade-end", "") + " - " + dados.get("estado-end", ""),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + data_fmt,
        "CPF: " + cpf_fmt,
        "RG / RNM: " + dados.get("rg", ""),
        "Banco: " + dados.get("banco", ""),
        "Agência: " + dados.get("agencia", ""),
        "Conta: " + dados.get("conta", ""),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.get("/", response_class=HTMLResponse)
async def index():
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/solicitacao")
async def solicitacao(request: Request):
    form = await request.form()
    dados = {chave: str(valor).strip() for chave, valor in form.items()}
    aba = dados.get("aba", "alunos")
    erros = _erros(aba, dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _gerar_oficio(aba, dados)}
