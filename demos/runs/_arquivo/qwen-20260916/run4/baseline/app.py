import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
def home() -> HTMLResponse:
    html = Path("index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.post("/api/solicitacao")
async def solicitacao(request: Request):
    dados = await request.json()
    aba = dados.get("aba", "alunos")
    erros: list[str] = []

    obrig = [
        "nome", "nusp", "programa", "email", "evento_nome", "evento_periodo",
        "evento_cidade", "evento_estado", "evento_pais", "valor", "detalhamento",
        "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "alunos":
        obrig = obrig + ["nivel", "tipo_auxilio"]

    def v(campo: str) -> str:
        val = dados.get(campo)
        return "" if val is None else str(val).strip()

    if any(not v(c) for c in obrig):
        erros.append("Preencha todos os campos")

    if v("nusp") and not re.fullmatch(r"\d+", v("nusp")):
        erros.append("N. USP deve conter apenas números")

    if v("agencia") and not re.fullmatch(r"\d+", v("agencia")):
        erros.append("Número da agência deve conter apenas números")

    if v("valor") and not (re.fullmatch(r"\d+", v("valor")) and int(v("valor")) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if v("email") and not re.fullmatch(r"[^@\s]+@[^@\s\.]+(\.[^@\s\.]+)+", v("email")):
        erros.append("E-mail inválido")

    cpf = v("cpf")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")

    if v("cep") and not re.fullmatch(r"\d{5}-\d{3}", v("cep")):
        erros.append("CEP deve estar no formato 00000-000")

    nac = v("nascimento")
    data_valida = False
    if nac:
        m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", nac)
        if m:
            d, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
            dias = [31, 29 if (a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if 1 <= mo <= 12 and 1 <= d <= dias[mo - 1]:
                data_valida = True
        if not data_valida:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        dig = re.sub(r"\D", "", cpf)
        base = dig[:9]
        s = sum(int(base[i]) * (10 - i) for i in range(9)) % 11
        d1 = 0 if s < 2 else 11 - s
        s2 = sum(int(base[i]) * (11 - i) for i in range(9)) + d1 * 2
        s2 = s2 % 11
        d2 = 0 if s2 < 2 else 11 - s2
        if d1 != int(dig[9]) or d2 != int(dig[10]):
            erros.append("CPF inválido")

    if not data_valida and nac:
        pass

    if erros:
        return {"ok": False, "erros": erros}

    def brl(cents: int) -> str:
        inteiro, dec = divmod(cents, 100)
        s = f"{inteiro:,}".replace(",", ".")
        return f"R$ {s},{dec:02d}"

    def esc(s: str) -> str:
        return s

    nome = v("nome")
    nusp = v("nusp")
    email = v("email")
    programa = v("programa")

    if aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {v('tipo_auxilio')}"
        prog_linha = f"Programa: {programa} - {v('nivel')}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        prog_linha = f"Programa: {programa}"

    evento_nome = v("evento_nome")
    periodo = v("evento_periodo")
    ecidade = v("evento_cidade")
    eestado = v("evento_estado")
    epais = v("evento_pais")
    link = v("link")
    apresentacao = v("apresentacao")
    valor = brl(int(v("valor")))
    detalhamento = v("detalhamento")

    logradouro = v("logradouro")
    numero = v("numero")
    complemento = v("complemento")
    cep = v("cep")
    bairro = v("bairro")
    cidade = v("cidade")
    estado = v("estado")

    nascimento = nac
    cpf_f = cpf
    rg = v("rg")
    banco = v("banco")
    agencia = v("agencia")
    conta = v("conta")

    linhas = [
        f"Interessada(o): {nome} - {nusp}",
        f"E-mail: {email}",
        assunto,
        prog_linha,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {evento_nome}",
        f"Período: {periodo}",
        f"Local: {ecidade} - {eestado} - {epais}",
    ]

    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {apresentacao}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{logradouro}, {numero}",
    ]

    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {cep}",
        f"{bairro}, {cidade} - {estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {nascimento}",
        f"CPF: {cpf_f}",
        f"RG / RNM: {rg}",
        f"Banco: {banco}",
        f"Agência: {agencia}",
        f"Conta: {conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return {"ok": True, "oficio": "\n".join(linhas)}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
