import json
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory=Path(__file__).resolve().parent / "assets"), name="assets")

CAMPOS_ALUNO = [
    "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", "evento_nome",
    "evento_periodo", "evento_cidade", "evento_estado", "evento_pais", "evento_link",
    "valor", "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
    "agencia", "conta",
]
CAMPOS_DOCENTE = [c for c in CAMPOS_ALUNO if c not in ("nivel", "tipo_auxilio")]


def valida(d):
    obrigatorios = [c for c in (CAMPOS_DOCENTE if d.get("aba") == "docentes" else CAMPOS_ALUNO)
                    if c not in ("evento_link", "complemento")]
    erros = []
    if any(not str(d.get(c, "")).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not d.get("nusp", "").isdigit():
        erros.append("N. USP deve conter apenas números")
    if not d.get("agencia", "").isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not re.fullmatch(r"[0-9]+", d.get("valor", "")) or int(d.get("valor", "0") or 0) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in d.get("email", "") or d.get("email", "").rsplit("@", 1)[1].strip(".") == "":
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.get("cpf", "")):
        erros.append("CPF deve estar no formato 000.000.000-00")
    else:
        n = [int(c) for c in re.sub(r"\D", "", d["cpf"])]
        dv = sum((10 - i) * n[i] for i in range(9)) % 11
        dv = 0 if dv < 2 else 11 - dv
        dv2 = sum((11 - i) * n[i] for i in range(10)) % 11
        dv2 = 0 if dv2 < 2 else 11 - dv2
        if dv != n[9] or dv2 != n[10]:
            erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", d.get("cep", "")):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/\d{4}", d.get("nascimento", "")):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = (int(p) for p in d["nascimento"].split("/"))
        if dia > [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28,
                  31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]:
            erros.append("Data de nascimento inválida")
    return erros


OFICIO = """Interessada(o): {nome} - {nusp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - {auxilio}
Programa: {programa}

A CCP-{sigla} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {evento_nome}
Período: {evento_periodo}
Local: {evento_cidade} - {evento_estado} - {evento_pais}
Link do evento: {evento_link}
Apresentação de trabalho: {apresentacao}
Valor solicitado: {valor}
Detalhamento: {detalhamento}

Endereço da(o) interessada(o)
{logradouro}, {numero}
Complemento: {complemento}
CEP: {cep}
{bairro}, {cidade} - {estado}

Dados para pagamento
Data de nascimento: {nascimento}
CPF: {cpf}
RG / RNM: {rg}
Banco: {banco}
Agência: {agencia}
Conta: {conta}

Encaminhe-se ao Serviço Financeiro para providências."""


def oficio(d):
    docente = d.get("aba") == "docentes"
    linhas = OFICIO.format(
        nome=d["nome"].strip(),
        nusp=d["nusp"].strip(),
        email=d["email"].strip(),
        auxilio="Verba do programa" if docente else d["tipo_auxilio"],
        programa=(d["programa"].strip() + ("" if docente else " - " + d["nivel"])),
        sigla=re.sub(r"[^A-Za-z0-9\u00C0-\u017F]", "", d["programa"]).upper()[:3] or d["programa"].strip(),
        evento_nome=d["evento_nome"].strip(),
        evento_periodo=d["evento_periodo"].strip(),
        evento_cidade=d["evento_cidade"].strip(),
        evento_estado=d["evento_estado"].strip(),
        evento_pais=d["evento_pais"].strip(),
        evento_link=d.get("evento_link", "").strip(),
        apresentacao=d["apresentacao"],
        valor="R$ " + "".join(reversed(["".join(("{:,}".format(int(c) + int(v[0]) if c.isdigit() else c, "").rjust(3, "0"), ",.", )
                                       for c, v in zip(reversed("{0:011d}".format(int(d["valor"]))),
                                                       zip(["."] + ["."] * 20, [0] * 20))])).rstrip(".,").replace(",.", ","),
        detalhamento=d["detalhamento"].strip(),
        logradouro=d["logradouro"].strip(),
        numero=d["numero"].strip(),
        complemento=d.get("complemento", "").strip(),
        cep=d["cep"].strip(),
        bairro=d["bairro"].strip(),
        cidade=d["cidade"].strip(),
        estado=d["estado"].strip(),
        nascimento=d["nascimento"].strip(),
        cpf=d["cpf"].strip(),
        rg=d["rg"].strip(),
        banco=d["banco"].strip(),
        agencia=d["agencia"].strip(),
        conta=d["conta"].strip(),
    ).split("\n")
    return "\n".join(l for l in linhas
                     if not ((l.startswith("Link do evento:") or l.startswith("Complemento:")) and not l.split(":", 1)[1].strip()))


@app.get("/", response_class=HTMLResponse)
def home():
    return (Path(__file__).resolve().parent / "index.html").read_text(encoding="utf-8")


@app.post("/solicitacao")
async def solicita():
    try:
        d = await app.request_body if False else None
    except Exception:
        d = None
    return None
