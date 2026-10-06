from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")
app.mount("/", StaticFiles(directory=Path(__file__).parent, html=True), name="static")


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf[:9]]
    soma = sum((10 - i) * d for i, d in enumerate(digitos))
    primeiro = (11 - soma % 11) % 10
    if primeiro != digitos[8]:
        return False
    soma = sum((11 - i) * d for i, d in enumerate(digitos[:9]))
    segundo = (11 - soma % 11) % 10
    return segundo == int(cpf[9])


@app.post("/solicitacao")
async def solicitacao(request: Request) -> JSONResponse:
    dados = await request.json()
    aba = dados.get("aba", "alunos")

    campos_obrigatorios = [
        "nome", "nusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
        "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "alunos":
        campos_obrigatorios += ["nivel", "tipo_auxilio"]

    erros: list[str] = []

    if any(not str(dados.get(campo, "")).strip() for campo in campos_obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = str(dados.get("nusp", "")).strip()
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", "")).strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor_digitos = "".join(c for c in str(dados.get("valor", "")) if c.isdigit())
    if valor_digitos and int(valor_digitos) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", "")).strip()
    if email:
        antes, _, depois = email.partition("@")
        if not antes or not depois or "." not in depois:
            erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", "")).strip()
    if cpf:
        cpf_digitos = "".join(c for c in cpf if c.isdigit())
        if len(cpf_digitos) != 11:
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf_digitos):
            erros.append("CPF inválido")

    cep = str(dados.get("cep", "")).strip()
    if cep and not (
        len(cep) == 9 and cep[:5].isdigit() and cep[5] == "-" and cep[6:].isdigit()
    ):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = str(dados.get("nascimento", "")).strip()
    if nascimento:
        import datetime

        formato_ok = (
            len(nascimento) == 10
            and nascimento[:2].isdigit()
            and nascimento[2] == "/"
            and nascimento[3:5].isdigit()
            and nascimento[5] == "/"
            and nascimento[6:].isdigit()
        )
        if not formato_ok:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(nascimento[0:2]), int(nascimento[3:5]), int(nascimento[6:10]))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse({"erros": erros}, status_code=422)

    valor_centavos = int(valor_digitos)
    inteiro = valor_centavos // 100
    centavos = valor_centavos % 100
    inteiro_fmt = "{:,}".format(inteiro).replace(",", ".")
    valor_fmt = "R$ {},{:02d}".format(inteiro_fmt, centavos)

    linhas = [
        "Interessada(o): {} - {}".format(str(dados["nome"]).strip(), nusp),
        "E-mail: {}".format(email),
        "Assunto: Solicitação de Auxílio Financeiro - {}".format(
            str(dados["tipo_auxilio"]) if aba == "alunos" else "Verba do programa"
        ),
        "Programa: {} - {}".format(str(dados["programa"]), str(dados["nivel"])).rstrip(" -")
        if aba == "alunos"
        else "Programa: {}".format(str(dados["programa"])),
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            str(dados["programa"])
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(str(dados["evento"])),
        "Período: {}".format(str(dados["periodo"])),
        "Local: {} - {} - {}".format(
            str(dados["cidade_evento"]), str(dados["estado_evento"]), str(dados["pais_evento"])
        ),
    ]

    link = str(dados.get("link", "")).strip()
    if link:
        linhas.append("Link do evento: {}".format(link))

    linhas += [
        "Apresentação de trabalho: {}".format(str(dados["apresentacao"])),
        "Valor solicitado: {}".format(valor_fmt),
        "Detalhamento: {}".format(str(dados["detalhamento"])),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(str(dados["logradouro"]), str(dados["numero"])),
    ]

    complemento = str(dados.get("complemento", "")).strip()
    if complemento:
        linhas.append("Complemento: {}".format(complemento))

    linhas += [
        "CEP: {}".format(cep),
        "{}, {} - {}".format(str(dados["bairro"]), str(dados["cidade"]), str(dados["estado"])),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(nascimento),
        "CPF: {}".format(cpf),
        "RG / RNM: {}".format(str(dados["rg"])),
        "Banco: {}".format(str(dados["banco"])),
        "Agência: {}".format(agencia),
        "Conta: {}".format(str(dados["conta"])),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return JSONResponse({"oficio": "\n".join(linhas)})
