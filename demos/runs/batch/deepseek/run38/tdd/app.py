import datetime
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
@app.get("/index.html")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


CHAVES_DA_ABA = [
    "aba",
    "aba_ativa",
    "formulario",
    "formulário",
    "tipo_formulario",
    "tipoFormulario",
    "tipo_solicitacao",
]

ALIASES = {
    "nome": ["NOME COMPLETO - SEM ABREVIAR", "nome", "nome_completo"],
    "n_usp": ["N. USP", "n_usp", "nusp", "numero_usp"],
    "programa": ["PROGRAMA", "programa"],
    "nivel": ["NÍVEL", "nivel"],
    "tipo_auxilio": ["TIPO DE AUXÍLIO", "tipo_auxilio", "tipo_de_auxilio"],
    "email": ["E-MAIL", "email", "e_mail"],
    "evento": ["NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "nome_evento", "evento"],
    "periodo": ["PERÍODO DO EVENTO, EXAME OU DEFESA", "periodo", "periodo_evento"],
    "cidade_evento": ["CIDADE DO EVENTO, EXAME OU DEFESA", "cidade_evento"],
    "estado_evento": ["ESTADO DO EVENTO, EXAME OU DEFESA", "estado_evento"],
    "pais_evento": ["PAÍS DO EVENTO, EXAME OU DEFESA", "pais_evento"],
    "link_evento": ["LINK DO EVENTO, EXAME OU DEFESA", "link_evento"],
    "valor": ["VALOR SOLICITADO (R$)", "valor", "valor_solicitado"],
    "detalhamento": ["DETALHAMENTO DO PEDIDO", "detalhamento"],
    "apresentar": [
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "apresentar",
        "apresentacao",
        "tipo_apresentacao",
    ],
    "data_nascimento": ["DATA DE NASCIMENTO", "data_nascimento"],
    "logradouro": ["LOGRADOURO", "logradouro"],
    "numero": ["NÚMERO", "numero"],
    "complemento": ["COMPLEMENTO", "complemento"],
    "bairro": ["BAIRRO", "bairro"],
    "cep": ["CEP", "cep"],
    "cidade": ["CIDADE", "cidade"],
    "estado": ["ESTADO", "estado"],
    "cpf": ["CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf"],
    "rg": ["RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "rg"],
    "banco": ["NOME DO BANCO", "banco", "nome_banco"],
    "agencia": ["NÚMERO DA AGÊNCIA", "agencia", "numero_agencia"],
    "conta": ["NÚMERO DA CONTA", "conta", "numero_conta"],
}

OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentar",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]


async def ler_corpo(request):
    try:
        corpo = await request.json()
    except Exception:
        corpo = dict(await request.form())
    return corpo if isinstance(corpo, dict) else {}


def pegar(dados, campo):
    for chave in ALIASES[campo]:
        valor = dados.get(chave)
        if valor:
            return str(valor).strip()
    return ""


def em_reais(valor):
    limpo = valor.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def email_valido(valor):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor))


def cpf_valido(valor):
    digitos = [int(c) for c in valor if c.isdigit()]
    if len(digitos) != 11:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * (i + 1 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[i]:
            return False
    return True


def data_valida(valor):
    try:
        dia, mes, ano = (int(parte) for parte in valor.split("/"))
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(aba, campos):
    erros = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if aba == "alunos" else [])
    if any(not campos[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if campos["n_usp"] and not campos["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if campos["agencia"] and not campos["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    if campos["valor"] and em_reais(campos["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if campos["email"] and not email_valido(campos["email"]):
        erros.append("E-mail inválido")
    if campos["cpf"]:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", campos["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(campos["cpf"]):
            erros.append("CPF inválido")
    if campos["cep"] and not re.fullmatch(r"\d{5}-\d{3}", campos["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if campos["data_nascimento"]:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", campos["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(campos["data_nascimento"]):
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(aba, c):
    linhas = [
        f"Interessada(o): {c['nome']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}")
        linhas.append(f"Programa: {c['programa']} - {c['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {c['programa']}")
    linhas += [
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link_evento"]:
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas.append(f"Apresentação de trabalho: {c['apresentar']}")
    linhas.append(f"Valor solicitado: {c['valor']}")
    linhas.append(f"Detalhamento: {c['detalhamento']}")
    linhas += [
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c["complemento"]:
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    dados = await ler_corpo(request)
    aba = "alunos"
    for chave in CHAVES_DA_ABA:
        valor = dados.get(chave)
        if isinstance(valor, str) and "docente" in valor.lower():
            aba = "docentes"
            break
    campos = {campo: pegar(dados, campo) for campo in ALIASES}
    erros = validar(aba, campos)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": gerar_oficio(aba, campos)})
