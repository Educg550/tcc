import re
import calendar
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")

RE_NOME = re.compile(r"name=\"([a-z0-9_]+)\"")
CAMPOS_OBRIGATORIOS = set(RE_NOME.findall((BASE_DIR / "index.html").read_text(encoding="utf-8")))
CAMPOS_OBRIGATORIOS.discard("nivel")
CAMPOS_OBRIGATORIOS.discard("tipo_auxilio")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(set(nums)) == 1:
        return False
    for i in range(2):
        total = sum(n * (len(nums) - 1 - j) for j, n in enumerate(nums)) % 11
        d = 0 if total < 2 else 11 - total
        if d != nums[9 + i]:
            return False
        nums.append(d)
    return True


def _data_valida(data):
    m = RE_DATA.match(data)
    if not m:
        return False
    dia, mes, ano = (int(x) for x in m.groups())
    if not 1 <= mes <= 12:
        return False
    return 1 <= dia <= calendar.monthrange(ano, mes)[1]


def _parse_valor(valor):
    digitos = re.sub(r"[^0-9]", "", valor)
    if not digitos:
        return None
    centavos = int(digitos)
    if centavos <= 0:
        return None
    return centavos


def _moeda(centavos):
    reais, c = divmod(centavos, 100)
    s = f"{reais:,}".replace(",", ".")
    return f"R$ {s},{c:02d}"


def validar(aba, d):
    erros = []
    nomes = ["nome", "num_usp", "programa", "email", "nome_evento", "periodo",
             "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
             "apresentar", "data_nascimento", "logradouro", "numero", "bairro", "cep",
             "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"]
    if aba == "alunos":
        nomes += ["nivel", "tipo_auxilio"]
    if any(not str(d.get(c, "")).strip() for c in nomes):
        erros.append("Preencha todos os campos")
    if d.get("num_usp", "").strip() and not d["num_usp"].strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.get("agencia", "").strip() and not d["agencia"].strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    v = d.get("valor", "").strip()
    if v:
        if _parse_valor(v) is None:
            erros.append("Valor solicitado deve ser maior que 0")
    if d.get("email", "").strip():
        if "@" not in d["email"] or len(d["email"].rsplit("@", 1)[-1]) < 1:
            erros.append("E-mail inválido")
    cpf = d.get("cpf", "").strip()
    if cpf:
        if not RE_CPF.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")
    cep = d.get("cep", "").strip()
    if cep and not RE_CEP.match(cep):
        erros.append("CEP deve estar no formato 00000-000")
    data = d.get("data_nascimento", "").strip()
    if data:
        if not RE_DATA.match(data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")
    return erros


def _linha(rotulo, valor):
    return f"{rotulo} {valor}"


def gerar_oficio(aba, d):
    nome = d["nome"].strip()
    num_usp = d["num_usp"].strip()
    programa = d["programa"].strip()
    email = d["email"].strip()
    valor = _moeda(_parse_valor(d["valor"].strip()))

    linhas = [
        f"Interessada(o): {nome} - {num_usp}",
        f"E-mail: {email}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio'].strip()}")
        linhas.append(f"Programa: {programa} - {d['nivel'].strip()}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    linhas.append("")
    linhas.append("A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: " + d["nome_evento"].strip())
    linhas.append("Período: " + d["periodo"].strip())
    linhas.append(f"Local: {d['cidade_evento'].strip()} - {d['estado_evento'].strip()} - {d['pais_evento'].strip()}")
    link = d.get("link_evento", "").strip()
    if link:
        linhas.append("Link do evento: " + link)
    linhas.append("Apresentação de trabalho: " + d["apresentar"].strip())
    linhas.append("Valor solicitado: " + valor)
    linhas.append("Detalhamento: " + d["detalhamento"].strip())
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['logradouro'].strip()}, {d['numero'].strip()}")
    comp = d.get("complemento", "").strip()
    if comp:
        linhas.append("Complemento: " + comp)
    linhas.append("CEP: " + d["cep"].strip())
    linhas.append(f"{d['bairro'].strip()}, {d['cidade'].strip()} - {d['estado'].strip()}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: " + d["data_nascimento"].strip())
    linhas.append("CPF: " + d["cpf"].strip())
    linhas.append("RG / RNM: " + d["rg"].strip())
    linhas.append("Banco: " + d["banco"].strip())
    linhas.append("Agência: " + d["agencia"].strip())
    linhas.append("Conta: " + d["conta"].strip())
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.get("/")
def index():
    return FileResponse(str(BASE_DIR / "index.html"))


from fastapi.responses import FileResponse


@app.post("/api/solicitar")
async def solicitar(request):
    body = await request.json()
    aba = body.get("aba", "alunos")
    erros = validar(aba, body)
    if erros:
        return JSONResponse({"errors": erros, "oficio": ""})
    return JSONResponse({"errors": [], "oficio": gerar_oficio(aba, body)})


app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
