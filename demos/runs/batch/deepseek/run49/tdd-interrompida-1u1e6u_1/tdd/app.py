import datetime
import os

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_banco",
    "numero_agencia",
    "numero_conta",
]

EXTRAS_ALUNOS = ["nivel", "tipo_auxilio"]


def _texto(dados, chave):
    valor = dados.get(chave)
    if valor is None:
        return ""
    return str(valor).strip()


def _eh_alunos(dados):
    return bool(_texto(dados, "nivel") or _texto(dados, "tipo_auxilio"))


def _parse_valor(texto):
    if not texto:
        return None
    texto = texto.strip()
    if texto.startswith("R$"):
        numero = texto[2:].strip().replace(".", "").replace(",", ".")
        try:
            return int(round(float(numero) * 100))
        except ValueError:
            return None
    if texto.isdigit():
        return int(texto)
    return None


def _fmt_valor(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _normaliza_data(texto):
    if len(texto) == 8 and texto.isdigit():
        return texto[:2] + "/" + texto[2:4] + "/" + texto[4:]
    return texto


def _normaliza_cep(texto):
    if len(texto) == 8 and texto.isdigit():
        return texto[:5] + "-" + texto[5:]
    return texto


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    for tamanho in (9, 10):
        soma = sum(digitos[i] * (tamanho + 1 - i) for i in range(tamanho))
        dv = (soma * 10) % 11
        if dv == 10:
            dv = 0
        if dv != digitos[tamanho]:
            return False
    return True


def _cpf_formato_valido(cpf):
    return (
        len(cpf) == 14
        and cpf[3] == "."
        and cpf[7] == "."
        and cpf[11] == "-"
        and cpf[:3].isdigit()
        and cpf[4:7].isdigit()
        and cpf[8:11].isdigit()
        and cpf[12:].isdigit()
    )


def _cep_formato_valido(cep):
    return (
        len(cep) == 9
        and cep[5] == "-"
        and cep[:5].isdigit()
        and cep[6:].isdigit()
    )


def _data_formato_valida(data):
    return (
        len(data) == 10
        and data[2] == "/"
        and data[5] == "/"
        and data[:2].isdigit()
        and data[3:5].isdigit()
        and data[6:].isdigit()
    )


def _email_valido(email):
    if email.count("@") != 1:
        return False
    usuario, dominio = email.split("@")
    partes = dominio.split(".")
    return bool(usuario) and len(partes) >= 2 and all(partes)


def _validar(dados):
    erros = []
    obrigatorios = OBRIGATORIOS + (EXTRAS_ALUNOS if _eh_alunos(dados) else [])

    if any(_texto(dados, campo) == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "numero_agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor_texto = _texto(dados, "valor_solicitado")
    valor = _parse_valor(valor_texto)
    if valor_texto and (valor is None or valor <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not _email_valido(email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not _cpf_formato_valido(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not _cep_formato_valido(_normaliza_cep(cep)):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "data_nascimento")
    if data:
        data = _normaliza_data(data)
        if not _data_formato_valida(data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in data.split("/"))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    programa = _texto(dados, "programa")

    linhas = [
        "Interessada(o): " + _texto(dados, "nome_completo") + " - " + _texto(dados, "n_usp"),
        "E-mail: " + _texto(dados, "email"),
    ]
    if _eh_alunos(dados):
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - " + _texto(dados, "tipo_auxilio")
        )
        linhas.append("Programa: " + programa + " - " + _texto(dados, "nivel"))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: " + programa)

    linhas.append("")
    linhas.append(
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: " + _texto(dados, "nome_evento"))
    linhas.append("Período: " + _texto(dados, "periodo_evento"))
    linhas.append(
        "Local: "
        + _texto(dados, "cidade_evento")
        + " - "
        + _texto(dados, "estado_evento")
        + " - "
        + _texto(dados, "pais_evento")
    )
    if _texto(dados, "link_evento"):
        linhas.append("Link do evento: " + _texto(dados, "link_evento"))
    linhas.append("Apresentação de trabalho: " + _texto(dados, "apresentacao"))
    linhas.append(
        "Valor solicitado: " + _fmt_valor(_parse_valor(_texto(dados, "valor_solicitado")) or 0)
    )
    linhas.append("Detalhamento: " + _texto(dados, "detalhamento"))
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(_texto(dados, "logradouro") + ", " + _texto(dados, "numero"))
    if _texto(dados, "complemento"):
        linhas.append("Complemento: " + _texto(dados, "complemento"))
    linhas.append("CEP: " + _normaliza_cep(_texto(dados, "cep")))
    linhas.append(
        _texto(dados, "bairro")
        + ", "
        + _texto(dados, "cidade")
        + " - "
        + _texto(dados, "estado")
    )
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: " + _normaliza_data(_texto(dados, "data_nascimento")))
    linhas.append("CPF: " + _texto(dados, "cpf"))
    linhas.append("RG / RNM: " + _texto(dados, "rg_rnm"))
    linhas.append("Banco: " + _texto(dados, "nome_banco"))
    linhas.append("Agência: " + _texto(dados, "numero_agencia"))
    linhas.append("Conta: " + _texto(dados, "numero_conta"))
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return chr(10).join(linhas)


@app.post("/solicitar")
def solicitar(dados: dict = Body(...)):
    erros = _validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return {"titulo": "Solicitação registrada", "oficio": _oficio(dados)}


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
