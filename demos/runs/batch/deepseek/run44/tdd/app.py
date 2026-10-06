import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def home():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilos():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
)


def _texto(dados, campo):
    return str(dados.get(campo) or "").strip()


def _valor_em_centavos(valor):
    digitos = re.sub(r"\D", "", str(valor or ""))
    return int(digitos) if digitos else 0


def _moeda(centavos):
    reais, cents = divmod(centavos, 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{cents:02d}"


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[n]) * ((i + 1) - n) for n in range(i))
        dv = (soma * 10) % 11
        if dv == 10:
            dv = 0
        if dv != int(d[i]):
            return False
    return True


def _validar(dados, aba):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba != "docentes":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not _texto(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor_solicitado")
    if valor and _valor_em_centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "data_nascimento")
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, aba):
    programa = _texto(dados, "programa")
    if aba == "docentes":
        assunto = "Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = _texto(dados, "tipo_auxilio")
        linha_programa = f"Programa: {programa} - {_texto(dados, 'nivel')}"

    linhas = [
        f"Interessada(o): {_texto(dados, 'nome_completo')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'evento')}",
        f"Período: {_texto(dados, 'periodo')}",
        f"Local: {_texto(dados, 'cidade_evento')} - {_texto(dados, 'estado_evento')} - {_texto(dados, 'pais_evento')}",
    ]

    link = _texto(dados, "link_evento")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao')}",
        f"Valor solicitado: {_moeda(_valor_em_centavos(_texto(dados, 'valor_solicitado')))}",
        f"Detalhamento: {_texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados, 'logradouro')}, {_texto(dados, 'numero')}",
    ]

    complemento = _texto(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {_texto(dados, 'cep')}",
        f"{_texto(dados, 'bairro')}, {_texto(dados, 'cidade')} - {_texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_texto(dados, 'data_nascimento')}",
        f"CPF: {_texto(dados, 'cpf')}",
        f"RG / RNM: {_texto(dados, 'rg')}",
        f"Banco: {_texto(dados, 'banco')}",
        f"Agência: {_texto(dados, 'agencia')}",
        f"Conta: {_texto(dados, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    aba = _texto(dados, "aba") or "alunos"
    erros = _validar(dados, aba)
    if erros:
        return JSONResponse({"erros": erros, "aba": aba})
    return JSONResponse({"oficio": _oficio(dados, aba)})
