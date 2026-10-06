"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")

CAMPOS = {
    "nome": ("nome_completo_sem_abreviar", "nome_completo", "nome", "NOME COMPLETO - SEM ABREVIAR"),
    "n_usp": ("n_usp", "nusp", "numero_usp", "num_usp", "N. USP"),
    "programa": ("programa", "PROGRAMA"),
    "nivel": ("nivel", "NÍVEL"),
    "tipo_auxilio": ("tipo_auxilio", "tipo_de_auxilio", "TIPO DE AUXÍLIO"),
    "email": ("email", "e_mail", "E-MAIL"),
    "evento": ("evento", "nome_evento", "nome_do_evento_banca_de_exame_ou_defesa", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    "periodo": ("periodo", "periodo_evento", "periodo_do_evento_exame_ou_defesa", "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    "cidade_evento": ("cidade_evento", "cidade_do_evento_exame_ou_defesa", "CIDADE DO EVENTO, EXAME OU DEFESA"),
    "estado_evento": ("estado_evento", "estado_do_evento_exame_ou_defesa", "ESTADO DO EVENTO, EXAME OU DEFESA"),
    "pais_evento": ("pais_evento", "pais_do_evento_exame_ou_defesa", "PAÍS DO EVENTO, EXAME OU DEFESA"),
    "link_evento": ("link_evento", "link_do_evento_exame_ou_defesa", "LINK DO EVENTO, EXAME OU DEFESA"),
    "valor": ("valor_solicitado", "valor", "VALOR SOLICITADO (R$)"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido", "DETALHAMENTO DO PEDIDO"),
    "apresentacao": ("apresentacao", "apresentacao_trabalho", "ira_apresentar_trabalho_no_evento_que_tipo", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
    "data_nascimento": ("data_nascimento", "data_de_nascimento", "DATA DE NASCIMENTO"),
    "logradouro": ("logradouro", "LOGRADOURO"),
    "numero": ("numero", "NÚMERO"),
    "complemento": ("complemento", "COMPLEMENTO"),
    "bairro": ("bairro", "BAIRRO"),
    "cep": ("cep", "CEP"),
    "cidade": ("cidade", "CIDADE"),
    "estado": ("estado", "ESTADO"),
    "cpf": ("cpf", "cpf_separados_por_pontos_e_traco", "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
    "rg": ("rg_rnm", "rg", "rg_rnm_separados_por_pontos_e_traco", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
    "banco": ("banco", "nome_do_banco", "NOME DO BANCO"),
    "agencia": ("agencia", "numero_da_agencia", "NÚMERO DA AGÊNCIA"),
    "conta": ("conta", "numero_da_conta", "NÚMERO DA CONTA"),
}

OPCIONAIS = ("link_evento", "complemento")
APENAS_ALUNOS = ("nivel", "tipo_auxilio")


def _valor(dados, campo):
    for chave in CAMPOS[campo]:
        valor = dados.get(chave)
        if valor is not None:
            return str(valor)
    return ""


def _e_docente(dados):
    for chave in ("aba", "tipo_solicitante", "formulario", "tab"):
        if "DOCENTE" in str(dados.get(chave, "")).upper():
            return True
    return False


def _valor_numerico_valido(texto):
    limpo = re.sub(r"[^\d,.]", "", texto).replace(".", "").replace(",", ".")
    try:
        return float(limpo) > 0
    except ValueError:
        return False


def _cpf_valido(cpf):
    digitos = [int(digito) for digito in re.sub(r"\D", "", cpf)]
    for n in (9, 10):
        soma = sum(digitos[i] * (n + 1 - i) for i in range(n))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != digitos[n]:
            return False
    return True


def _data_valida(texto):
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _validar(dados, docente):
    valores = {campo: _valor(dados, campo) for campo in CAMPOS}
    erros = []

    obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if docente:
        obrigatorios = [campo for campo in obrigatorios if campo not in APENAS_ALUNOS]
    if any(not valores[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = valores["n_usp"].strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = valores["agencia"].strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = valores["valor"].strip()
    if valor and not _valor_numerico_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = valores["email"].strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = valores["cpf"].strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = valores["cep"].strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = valores["data_nascimento"].strip()
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return valores, erros


def _oficio(valores, docente):
    linhas = [
        "Interessada(o): " + valores["nome"] + " - " + valores["n_usp"],
        "E-mail: " + valores["email"],
    ]
    if docente:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: " + valores["programa"])
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - " + valores["tipo_auxilio"])
        linhas.append("Programa: " + valores["programa"] + " - " + valores["nivel"])
    linhas.append("")
    linhas.append("A CCP-" + valores["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: " + valores["evento"])
    linhas.append("Período: " + valores["periodo"])
    linhas.append("Local: " + valores["cidade_evento"] + " - " + valores["estado_evento"] + " - " + valores["pais_evento"])
    if valores["link_evento"].strip():
        linhas.append("Link do evento: " + valores["link_evento"])
    linhas.append("Apresentação de trabalho: " + valores["apresentacao"])
    linhas.append("Valor solicitado: " + valores["valor"])
    linhas.append("Detalhamento: " + valores["detalhamento"])
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(valores["logradouro"] + ", " + valores["numero"])
    if valores["complemento"].strip():
        linhas.append("Complemento: " + valores["complemento"])
    linhas.append("CEP: " + valores["cep"])
    linhas.append(valores["bairro"] + ", " + valores["cidade"] + " - " + valores["estado"])
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: " + valores["data_nascimento"])
    linhas.append("CPF: " + valores["cpf"])
    linhas.append("RG / RNM: " + valores["rg"])
    linhas.append("Banco: " + valores["banco"])
    linhas.append("Agência: " + valores["agencia"])
    linhas.append("Conta: " + valores["conta"])
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


async def _corpo(request):
    try:
        dados = await request.json()
        if isinstance(dados, dict):
            return dados
    except Exception:
        pass
    try:
        return dict(await request.form())
    except Exception:
        return {}


@app.get("/", response_class=HTMLResponse)
def pagina():
    return (RAIZ / "index.html").read_text(encoding="utf-8")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="application/javascript")


@app.post("/solicitacao")
async def solicitar(request: Request):
    dados = await _corpo(request)
    docente = _e_docente(dados)
    valores, erros = _validar(dados, docente)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": _oficio(valores, docente)})
