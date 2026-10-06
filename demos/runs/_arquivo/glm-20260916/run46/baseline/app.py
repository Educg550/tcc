import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


if (BASE / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


ROTULOS = {
    "nome_completo": "NOME COMPLETO - SEM ABREVIAR",
    "nusp": "N. USP",
    "programa": "PROGRAMA",
    "nivel": "NÍVEL",
    "tipo_auxilio": "TIPO DE AUXÍLIO",
    "email": "E-MAIL",
    "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "pais_evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "link_evento": "LINK DO EVENTO, EXAME OU DEFESA",
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
    "nome_completo", "nusp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def extrair(dados: dict, chave: str) -> str:
    bruto = dados.get(chave)
    if bruto in (None, ""):
        bruto = dados.get(ROTULOS[chave])
    return "" if bruto is None else str(bruto).strip()


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in re.sub(r"[^0-9]", "", cpf)]
    if len(digitos) != 11:
        return False
    for posicao in range(9, 11):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r"[^0-9]", "", valor) or "0")
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def validar(v: dict, docente: bool) -> list:
    obrigatorios = list(OBRIGATORIOS)
    if not docente:
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not v[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if v["nusp"] and not re.fullmatch(r"[0-9]+", v["nusp"]):
        erros.append("N. USP deve conter apenas números")
    if v["agencia"] and not re.fullmatch(r"[0-9]+", v["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    digitos_valor = re.sub(r"[^0-9]", "", v["valor"])
    if not digitos_valor or int(digitos_valor) == 0:
        erros.append("Valor solicitado deve ser maior que 0")
    partes = v["email"].split("@")
    if len(partes) != 2 or not partes[0] or not partes[1]:
        erros.append("E-mail inválido")

    cpf_ok = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", v["cpf"]))
    if not cpf_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if not re.fullmatch(r"[0-9]{5}-[0-9]{3}", v["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    data_ok = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", v["data_nascimento"]))
    if not data_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_ok and not cpf_valido(v["cpf"]):
        erros.append("CPF inválido")
    if data_ok and not data_valida(v["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(v: dict, docente: bool) -> str:
    if docente:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {v['programa']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {v['tipo_auxilio']}"
        linha_programa = f"Programa: {v['programa']} - {v['nivel']}"

    linhas = [
        f"Interessada(o): {v['nome_completo']} - {v['nusp']}",
        f"E-mail: {v['email']}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{v['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['evento']}",
        f"Período: {v['periodo']}",
        f"Local: {v['cidade_evento']} - {v['estado_evento']} - {v['pais_evento']}",
    ]
    if v["link_evento"]:
        linhas.append(f"Link do evento: {v['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {v['apresentacao']}",
        f"Valor solicitado: {formatar_moeda(v['valor'])}",
        f"Detalhamento: {v['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['logradouro']}, {v['numero']}",
    ]
    if v["complemento"]:
        linhas.append(f"Complemento: {v['complemento']}")
    linhas += [
        f"CEP: {v['cep']}",
        f"{v['bairro']}, {v['cidade']} - {v['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v['data_nascimento']}",
        f"CPF: {v['cpf']}",
        f"RG / RNM: {v['rg']}",
        f"Banco: {v['banco']}",
        f"Agência: {v['agencia']}",
        f"Conta: {v['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
@app.post("/solicitacao")
async def solicitar(request: Request):
    if "application/" in request.headers.get("content-type", ""):
        dados = await request.()
    else:
        dados = dict(await request.form())
    valores = {chave: extrair(dados, chave) for chave in ROTULOS}
    aba = str(dados.get("aba") or dados.get("tipo") or "alunos").strip().lower()
    docente = "docente" in aba
    erros = validar(valores, docente)
    if erros:
        return {"sucesso": False, "erros": erros}
    return {"sucesso": True, "oficio": gerar_oficio(valores, docente)}
