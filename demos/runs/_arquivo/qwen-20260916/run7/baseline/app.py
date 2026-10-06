from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/", StaticFiles(directory=".", html=True), name="static")


def _cpf_valido(cpf: str) -> bool:
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    for pos in (9, 10):
        total = 0
        for i in range(pos):
            total += nums[i] * (pos + 1 - i)
        if (total * 10) % 11 % 10 != nums[pos]:
            return False
    return True


def _data_valida(data: str) -> bool:
    d, m, a = int(data[0:2]), int(data[3:5]), int(data[6:10])
    dias_por_mes = [31, 29 if (a % 4 == 0 and a % 100 != 0) or a % 400 == 0 else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1900 <= a <= 2100 and 1 <= m <= 12 and 1 <= d <= dias_por_mes[m - 1]


CAMPOS_OBRIGATORIOS_ALUNOS = [
    "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]

CAMPOS_OBRIGATORIOS_DOCENTES = [f for f in CAMPOS_OBRIGATORIOS_ALUNOS if f not in ("nivel", "tipo_auxilio")]


def _moeda_centavos(cents: int) -> str:
    inteiro = cents // 100
    resto = cents % 100
    s = str(inteiro)[::-1]
    partes = [s[i:i + 3] for i in range(0, len(s), 3)]
    inteiro_fmt = ".".join(partes)[::-1]
    return f"R$ {inteiro_fmt},{resto:02d}"


@app.post("/api/solicitacao")
async def solicitacao(request: Request):
    dados = await request.json()
    aba = dados.get("aba", "alunos")

    def v(campo: str) -> str:
        return (dados.get(campo) or "").strip()

    obrigatorios = CAMPOS_OBRIGATORIOS_ALUNOS if aba == "alunos" else CAMPOS_OBRIGATORIOS_DOCENTES

    erros: list[str] = []
    faltando = any(not v(c) for c in obrigatorios)
    if faltando:
        erros.append("Preencha todos os campos")

    if v("nusp") and not v("nusp").isdigit():
        erros.append("N. USP deve conter apenas números")
    if v("agencia") and not v("agencia").isdigit():
        erros.append("Número da agência deve conter apenas números")

    if v("valor"):
        digitos = "".join(c for c in v("valor") if c.isdigit())
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = v("email")
    if email:
        domino = email.rsplit("@", 1)
        if len(domino) != 2 or not all([len(domino[0]) > 0, len(domino[1]) > 0, "." in domino[1]]):
            erros.append("E-mail inválido")

    cpf = v("cpf")
    if cpf:
        if len(cpf) != 14 or cpf[3] != "." or cpf[7] != "." or cpf[11] != "-":
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = v("cep")
    if cep and (len(cep) != 9 or cep[5] != "-"):
        erros.append("CEP deve estar no formato 00000-000")

    data = v("nascimento")
    if data:
        if len(data) != 10 or data[2] != "/" or data[5] != "/":
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    digitos = "".join(c for c in v("valor") if c.isdigit())
    valor_fmt = _moeda_centavos(int(digitos))

    linhas_evento = []
    link = v("link")
    if link:
        linhas_evento.append(f"Link do evento: {link}")
    linhas_evento.append(f"Apresentação de trabalho: {v('apresentacao')}")
    linhas_evento.append(f"Valor solicitado: {valor_fmt}")
    linhas_evento.append(f"Detalhamento: {v('detalhamento')}")

    linhas_endereco = [f"{v('logradouro')}, {v('numero')}"]
    complemento = v("complemento")
    if complemento:
        linhas_endereco.append(f"Complemento: {complemento}")
    linhas_endereco.append(f"CEP: {cep}")
    linhas_endereco.append(f"{v('bairro')}, {v('cidade')} - {v('estado')}")

    bloco_evento = "\n".join([
        "Dados do evento",
        f"Evento: {v('evento')}",
        f"Período: {v('periodo')}",
        f"Local: {v('cidade_evento')} - {v('estado_evento')} - {v('pais_evento')}",
    ] + linhas_evento)

    bloco_endereco = "\n".join(["Endereço da(o) interessada(o)"] + linhas_endereco)

    bloco_pagamento = "\n".join([
        "Dados para pagamento",
        f"Data de nascimento: {data}",
        f"CPF: {cpf}",
        f"RG / RNM: {v('rg')}",
        f"Banco: {v('banco')}",
        f"Agência: {v('agencia')}",
        f"Conta: {v('conta')}",
    ])

    corpo = [f"Interessada(o): {v('nome')} - {v('nusp')}", f"E-mail: {email}"]

    if aba == "alunos":
        corpo.append(f"Assunto: Solicitação de Auxílio Financeiro - {v('tipo_auxilio')}")
        corpo.append(f"Programa: {v('programa')} - {v('nivel')}")
        corpo.append("")
        corpo.append(f"A CCP-{v('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:")
    else:
        corpo.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        corpo.append(f"Programa: {v('programa')}")
        corpo.append("")
        corpo.append(f"A CCP-{v('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:")

    corpo.append("")
    corpo.append(bloco_evento)
    corpo.append("")
    corpo.append(bloco_endereco)
    corpo.append("")
    corpo.append(bloco_pagamento)
    corpo.append("")
    corpo.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return {"ok": True, "oficio": "\n".join(corpo)}
