import re
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
    "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado_end", "cpf", "rg", "banco", "agencia", "conta",
)
OBRIGATORIOS_ALUNOS = ("nivel", "tipo_auxilio")


def texto(dados, chave):
    return str(dados.get(chave, "") or "").strip()


def cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(set(digitos)) == 1:
        return False
    soma = sum(d * peso for d, peso in zip(digitos[:9], range(10, 1, -1)))
    primeiro = (soma * 10) % 11 % 10
    soma = sum(d * peso for d, peso in zip(digitos[:10], range(11, 1, -1)))
    segundo = (soma * 10) % 11 % 10
    return primeiro == digitos[9] and segundo == digitos[10]


def validar(dados):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if texto(dados, "tipo") == "alunos":
        obrigatorios += OBRIGATORIOS_ALUNOS
    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor")
    if valor and int(re.sub(r"\D", "", valor) or 0) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email:
        partes = email.split("@")
        if len(partes) < 2 or not partes[0] or not partes[-1]:
            erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    if cpf:
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf) is None:
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = texto(dados, "cep")
    if cep and re.fullmatch(r"\d{5}-\d{3}", cep) is None:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "data_nascimento")
    if nascimento:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento) is None:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor):
    centavos = int(re.sub(r"\D", "", str(valor)) or 0)
    reais, resto = divmod(centavos, 100)
    milhar = f"{reais:,}".replace(",", ".")
    return f"R$ {milhar},{resto:02d}"


def gerar_oficio(dados):
    programa = str(dados.get("programa", ""))
    if str(dados.get("tipo", "")) == "docentes":
        assunto = "Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = str(dados.get("tipo_auxilio", ""))
        linha_programa = f"Programa: {programa} - {dados.get('nivel', '')}"
    linhas = [
        f"Interessada(o): {dados.get('nome', '')} - {dados.get('n_usp', '')}",
        f"E-mail: {dados.get('email', '')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.get('evento', '')}",
        f"Período: {dados.get('periodo', '')}",
        f"Local: {dados.get('cidade', '')} - {dados.get('estado', '')} - {dados.get('pais', '')}",
    ]
    if texto(dados, "link"):
        linhas.append(f"Link do evento: {dados.get('link', '')}")
    linhas += [
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {formatar_moeda(dados.get('valor', ''))}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ]
    if texto(dados, "complemento"):
        linhas.append(f"Complemento: {dados.get('complemento', '')}")
    linhas += [
        f"CEP: {dados.get('cep', '')}",
        f"{dados.get('bairro', '')}, {dados.get('cidade_end', '')} - {dados.get('estado_end', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.get('data_nascimento', '')}",
        f"CPF: {dados.get('cpf', '')}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def criar_solicitacao(dados: dict = Body(...)):
    erros = validar(dados)
    if erros:
        return JSONResponse(status_code=422, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": gerar_oficio(dados)}


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
