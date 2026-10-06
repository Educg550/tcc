import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]

CAMPOS_ALUNOS = ["nivel", "tipo_auxilio"]


def _texto(dados, campo):
    return str(dados.get(campo) or "").strip()


def _digitos(valor):
    return re.sub(r"\D", "", valor)


def _cpf_valido(cpf):
    d = _digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d[n]) * ((i + 1) - n) for n in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(d[i]):
            return False
    return True


def _data_valida(texto):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", texto)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mes <= 12 or dia < 1:
        return False
    bissexto = ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)
    por_mes = [31, 29 if bissexto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dia <= por_mes[mes - 1]


def validar(aba, dados):
    erros = []
    obrigatorios = CAMPOS_OBRIGATORIOS + (CAMPOS_ALUNOS if aba == "alunos" else [])
    if any(not _texto(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor")
    if valor and int(_digitos(valor) or "0") <= 0:
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

    nascimento = _texto(dados, "data_nascimento")
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def formatar_valor(valor):
    digitos = _digitos(valor)
    if not digitos:
        return ""
    centavos = int(digitos) % 100
    reais = int(digitos) // 100
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(aba, dados):
    programa = _texto(dados, "programa")
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {_texto(dados, 'tipo_auxilio')}"
        identificacao = f"{programa} - {_texto(dados, 'nivel')}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        identificacao = programa

    linhas = [
        f"Interessada(o): {_texto(dados, 'nome')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
        f"Assunto: {assunto}",
        f"Programa: {identificacao}",
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'evento')}",
        f"Período: {_texto(dados, 'periodo')}",
        f"Local: {_texto(dados, 'cidade_evento')} - {_texto(dados, 'estado_evento')} - {_texto(dados, 'pais_evento')}",
    ]
    if _texto(dados, "link_evento"):
        linhas.append(f"Link do evento: {_texto(dados, 'link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao')}",
        f"Valor solicitado: {formatar_valor(_texto(dados, 'valor'))}",
        f"Detalhamento: {_texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados, 'logradouro')}, {_texto(dados, 'numero')}",
    ]
    if _texto(dados, "complemento"):
        linhas.append(f"Complemento: {_texto(dados, 'complemento')}")
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


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    dados = await request.json()
    aba = dados.get("aba") if dados.get("aba") in ("alunos", "docentes") else "alunos"
    erros = validar(aba, dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(aba, dados)}


app.mount("/", StaticFiles(directory=str(BASE), html=True), name="static")