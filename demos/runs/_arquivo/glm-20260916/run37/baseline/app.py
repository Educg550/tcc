import re
import unicodedata
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

CAMPOS = {
    "nome": ["nomecompletosemabreviar", "nomecompleto", "nome"],
    "nusp": ["nusp", "numerousp"],
    "programa": ["programa"],
    "nivel": ["nivel"],
    "tipo": ["tipodeauxilio", "tipoauxilio", "tipo"],
    "email": ["email"],
    "evento": ["nomedoeventobancadeexameoudefesa", "nomedoevento", "evento"],
    "periodo": ["periododoeventoexameoudefesa", "periododoevento", "periodo"],
    "cidade_evento": ["cidadedoeventoexameoudefesa", "cidadeevento", "cidadedoevento"],
    "estado_evento": ["estadodoeventoexameoudefesa", "estadoevento", "estadodoevento"],
    "pais_evento": ["paisdoeventoexameoudefesa", "paisdoevento", "pais"],
    "link": ["linkdoeventoexameoudefesa", "linkdoevento", "link"],
    "valor": ["valorsolicitador", "valorsolicitado", "valor"],
    "detalhamento": ["detalhamentodopedido", "detalhamento"],
    "apresentacao": ["irapresentartrabalhonoeventoquetipo", "apresentacao", "apresentartrabalho"],
    "nascimento": ["datadenascimento", "datanascimento", "nascimento"],
    "logradouro": ["logradouro"],
    "numero": ["numero"],
    "complemento": ["complemento"],
    "bairro": ["bairro"],
    "cep": ["cep"],
    "cidade": ["cidade"],
    "estado": ["estado"],
    "cpf": ["cpfseparadosporpontosetraco", "cpf"],
    "rgrnm": ["rgrnmseparadosporpontosetraco", "rgrnm", "rg", "rnm"],
    "banco": ["nomedobanco", "banco"],
    "agencia": ["numerodaagencia", "numeroagencia", "agencia"],
    "conta": ["numerodaconta", "numeroconta", "conta"],
}

OPCIONAIS = {"link", "complemento"}
SO_ALUNOS = {"nivel", "tipo"}


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def _resolver(payload: dict) -> dict:
    recebidos = {}
    for chave, valor in payload.items():
        if isinstance(valor, (str, int, float)) and not isinstance(valor, bool):
            recebidos[_norm(str(chave))] = str(valor).strip()
    return {
        campo: next((recebidos[chave] for chave in chaves if chave in recebidos), "")
        for campo, chaves in CAMPOS.items()
    }


def _digito_verificador(bloco: str) -> str:
    soma = sum(int(digito) * (len(bloco) + 1 - posicao) for posicao, digito in enumerate(bloco))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def _cpf_valido(cpf: str) -> bool:
    return cpf[9] == _digito_verificador(cpf[:9]) and cpf[10] == _digito_verificador(cpf[:10])


def _valor_centavos(valor: str):
    texto = valor.strip()
    if texto[:2].upper() == "R$":
        texto = texto[2:]
    texto = texto.replace(".", "").replace(",", "").replace(" ", "")
    if not texto.isdigit():
        return None
    return int(texto)


def _moeda(centavos: int) -> str:
    milhares = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {milhares},{centavos % 100:02d}"


def _validar(dados: dict, alunos: bool) -> list:
    erros = []
    obrigatorios = [c for c in CAMPOS if c not in OPCIONAIS and (alunos or c not in SO_ALUNOS)]
    if any(not dados[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if dados["nusp"] and not dados["nusp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados["agencia"] and not dados["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    if dados["valor"]:
        centavos = _valor_centavos(dados["valor"])
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and not RE_EMAIL.fullmatch(dados["email"]):
        erros.append("E-mail inválido")
    cpf = dados["cpf"]
    if cpf and not RE_CPF.fullmatch(cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")
    if dados["cep"] and not RE_CEP.fullmatch(dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if dados["nascimento"]:
        if not RE_DATA.fullmatch(dados["nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(dados["nascimento"], "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def _oficio(dados: dict, alunos: bool) -> str:
    if alunos:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['nusp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link"]:
        linhas.append(f"Link do evento: {dados['link']}")
    linhas.extend([
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {_moeda(_valor_centavos(dados['valor']))}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ])
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend([
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rgrnm']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.get("/")
async def index():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
async def estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
async def script():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


@app.post("/api/solicitacao")
@app.post("/solicitacao")
@app.post("/")
async def solicitacao(request: Request):
    try:
        payload = await request.()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    aba = ""
    for chave, valor in payload.items():
        if isinstance(valor, str) and _norm(chave) in ("aba", "perfil", "formulario"):
            aba = valor.strip().lower()
            break
    alunos = "docente" not in aba
    dados = _resolver(payload)
    erros = _validar(dados, alunos)
    if erros:
        return {"valido": False, "erros": erros, "oficio": None}
    return {"valido": True, "erros": [], "oficio": _oficio(dados, alunos)}
