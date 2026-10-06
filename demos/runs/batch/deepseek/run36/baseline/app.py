"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
import unicodedata
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS = {
    "aba": "ABA",
    "nome_completo": "NOME COMPLETO - SEM ABREVIAR",
    "n_usp": "N. USP",
    "programa": "PROGRAMA",
    "nivel": "NÍVEL",
    "tipo_auxilio": "TIPO DE AUXÍLIO",
    "email": "E-MAIL",
    "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "pais_evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "link": "LINK DO EVENTO, EXAME OU DEFESA",
    "valor": "VALOR SOLICITADO (R$)",
    "detalhamento": "DETALHAMENTO DO PEDIDO",
    "apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "data_nascimento": "DATA DE NASCIMENTO",
    "logradouro": "LOGRADOURO",
    "numero": "NÚMERO",
    "complemento": "COMPLEMENTO",
    "bairro": "BAIRRO",
    "cep": "CEP",
    "cidade": "CIDADE",
    "estado": "ESTADO",
    "cpf": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "rg": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "banco": "NOME DO BANCO",
    "agencia": "NÚMERO DA AGÊNCIA",
    "conta": "NÚMERO DA CONTA",
}

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _norm(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


ALIASES = {}
for _canonica, _rotulo in CAMPOS.items():
    ALIASES[_norm(_canonica)] = _canonica
    ALIASES[_norm(_rotulo)] = _canonica
ALIASES.update({
    "formulario": "aba",
    "tipo_de_solicitante": "aba",
    "tipo_solicitante": "aba",
    "valor_solicitado": "valor",
    "nome_do_evento": "evento",
    "cidade_do_evento": "cidade_evento",
    "estado_do_evento": "estado_evento",
    "pais_do_evento": "pais_evento",
    "link_do_evento": "link",
    "data_de_nascimento": "data_nascimento",
    "numero_da_agencia": "agencia",
    "numero_da_conta": "conta",
    "nome_do_banco": "banco",
    "apresentacao_de_trabalho": "apresentacao",
})


def _so_digitos(valor):
    return bool(re.fullmatch(r"[0-9]+", valor))


def _centavos(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return int(digitos) if digitos else 0


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ {}.{:02d}".format("{:,}".format(reais).replace(",", "."), resto)


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[posicao]:
            return False
    return True


def _data_valida(valor):
    dia, mes, ano = (int(parte) for parte in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(dados, aba):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not dados.get(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados["n_usp"] and not _so_digitos(dados["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if dados["agencia"] and not _so_digitos(dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if dados["valor"] and _centavos(dados["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados["email"]):
        erros.append("E-mail inválido")

    if dados["cpf"]:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(dados["cpf"]):
            erros.append("CPF inválido")

    if dados["cep"] and not re.fullmatch(r"\d{5}-\d{3}", dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    if dados["data_nascimento"]:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(dados["data_nascimento"]):
            erros.append("Data de nascimento inválida")

    return erros


def _montar(dados, aba):
    linhas = [
        "Interessada(o): {} - {}".format(dados["nome_completo"], dados["n_usp"]),
        "E-mail: {}".format(dados["email"]),
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(dados["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(dados["programa"], dados["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(dados["programa"]))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(dados["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(dados["evento"]),
        "Período: {}".format(dados["periodo"]),
        "Local: {} - {} - {}".format(dados["cidade_evento"], dados["estado_evento"], dados["pais_evento"]),
    ]
    if dados["link"]:
        linhas.append("Link do evento: {}".format(dados["link"]))

    linhas += [
        "Apresentação de trabalho: {}".format(dados["apresentacao"]),
        "Valor solicitado: {}".format(_moeda(_centavos(dados["valor"]))),
        "Detalhamento: {}".format(dados["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(dados["logradouro"], dados["numero"]),
    ]
    if dados["complemento"]:
        linhas.append("Complemento: {}".format(dados["complemento"]))

    linhas += [
        "CEP: {}".format(dados["cep"]),
        "{}, {} - {}".format(dados["bairro"], dados["cidade"], dados["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(dados["data_nascimento"]),
        "CPF: {}".format(dados["cpf"]),
        "RG / RNM: {}".format(dados["rg"]),
        "Banco: {}".format(dados["banco"]),
        "Agência: {}".format(dados["agencia"]),
        "Conta: {}".format(dados["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def _ler(request):
    corpo = {}
    try:
        if "application/json" in request.headers.get("content-type", ""):
            corpo = await request.json()
        else:
            corpo = dict(await request.form())
    except Exception:
        corpo = {}
    if not isinstance(corpo, dict):
        corpo = {}
    return corpo


@app.post("/api/solicitacao")
@app.post("/{caminho:path}")
async def solicitar(request: Request, caminho: str = ""):
    corpo = await _ler(request)

    dados = {canonica: "" for canonica in CAMPOS}
    for chave, valor in corpo.items():
        canonica = ALIASES.get(_norm(chave))
        if canonica:
            dados[canonica] = str(valor).strip()

    aba = _norm(dados["aba"])
    if aba not in ("alunos", "docentes"):
        aba = "alunos" if (dados["nivel"] or dados["tipo_auxilio"]) else "docentes"

    erros = _validar(dados, aba)
    if erros:
        return JSONResponse({"ok": False, "erros": erros, "oficio": None})
    return JSONResponse({"ok": True, "erros": [], "oficio": _montar(dados, aba)})


app.mount("/", StaticFiles(directory=".", html=True), name="estaticos")
