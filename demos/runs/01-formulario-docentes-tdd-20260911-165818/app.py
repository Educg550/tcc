from pathlib import Path
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


@app.get("/style.css")
def style_css():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def app_js():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


CAMPOS_COMUNS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

CAMPOS_ALUNOS_EXTRA = ["NÍVEL", "TIPO DE AUXÍLIO"]


def campo_vazio(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, str) and valor.strip() == "":
        return True
    return False


def validar(dados: dict) -> list[str]:
    erros = []
    aba = dados.get("aba")
    campos_obrigatorios = list(CAMPOS_COMUNS)
    if aba == "alunos":
        campos_obrigatorios += CAMPOS_ALUNOS_EXTRA

    if any(campo_vazio(dados.get(campo)) for campo in campos_obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados.get("N. USP")
    if not campo_vazio(n_usp) and not str(n_usp).isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("NÚMERO DA AGÊNCIA")
    if not campo_vazio(agencia) and not str(agencia).isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("VALOR SOLICITADO (R$)")
    valor_valido = (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and valor > 0
    )
    if not valor_valido:
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("E-MAIL")
    if not campo_vazio(email) and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email)):
        erros.append("E-mail inválido")

    cpf = dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if not campo_vazio(cpf) and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", str(cpf)):
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = dados.get("CEP")
    if not campo_vazio(cep) and not re.match(r"^\d{5}-\d{3}$", str(cep)):
        erros.append("CEP deve estar no formato 00000-000")

    data_nasc = dados.get("DATA DE NASCIMENTO")
    if not campo_vazio(data_nasc) and not re.match(r"^\d{2}/\d{2}/\d{4}$", str(data_nasc)):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    return erros


def formatar_valor(valor) -> str:
    centavos_totais = round(float(valor) * 100)
    reais, centavos = divmod(centavos_totais, 100)
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


def gerar_oficio(d: dict, aba: str) -> str:
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {d['TIPO DE AUXÍLIO']}"
        programa_linha = f"Programa: {d['PROGRAMA']} - {d['NÍVEL']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {d['PROGRAMA']}"

    linhas = [
        f"Interessada(o): {d['NOME COMPLETO - SEM ABREVIAR']} - {d['N. USP']}",
        f"E-mail: {d['E-MAIL']}",
        f"Assunto: {assunto}",
        programa_linha,
        "",
        f"A CCP-{d['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {d['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {d['CIDADE DO EVENTO, EXAME OU DEFESA']} - {d['ESTADO DO EVENTO, EXAME OU DEFESA']} - {d['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]

    link = d.get("LINK DO EVENTO, EXAME OU DEFESA") or ""
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas.append(f"Apresentação de trabalho: {d['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}")
    linhas.append(f"Valor solicitado: {formatar_valor(d['VALOR SOLICITADO (R$)'])}")
    linhas.append(f"Detalhamento: {d['DETALHAMENTO DO PEDIDO']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['LOGRADOURO']}, {d['NÚMERO']}")

    complemento = d.get("COMPLEMENTO") or ""
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas.append(f"CEP: {d['CEP']}")
    linhas.append(f"{d['BAIRRO']}, {d['CIDADE']} - {d['ESTADO']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d['DATA DE NASCIMENTO']}")
    linhas.append(f"CPF: {d['CPF (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"RG / RNM: {d['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"Banco: {d['NOME DO BANCO']}")
    linhas.append(f"Agência: {d['NÚMERO DA AGÊNCIA']}")
    linhas.append(f"Conta: {d['NÚMERO DA CONTA']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitacao(dados: dict):
    aba = dados.get("aba")
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados, aba)}
