"""Backend da aplicação de auxílio financeiro da Pós-Graduação do IME-USP."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

CAMPOS_OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_do_evento",
    "periodo_do_evento",
    "cidade_do_evento",
    "estado_do_evento",
    "pais_do_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_de_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]

CAMPOS_OBRIGATORIOS_ALUNO = CAMPOS_OBRIGATORIOS + ["nivel", "tipo_de_auxilio"]


def validar_cpf(cpf: str) -> bool:
    """Valida os dois dígitos verificadores do CPF."""
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    if cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum((10 - j if i == 9 else 11 - j) * int(cpf[j]) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[i]):
            return False
    return True


def formatar(valor: int) -> str:
    """Formata os centavos como moeda brasileira: 150000 -> 'R$ 1.500,00'."""
    texto = str(valor)
    centavos = texto[-2:].rjust(2, "0")
    reais = texto[:-2] or "0"
    partes = []
    while len(reais) > 3:
        partes.insert(0, reais[-3:])
        reais = reais[:-3]
    partes.insert(0, reais)
    return "R$ " + ".".join(partes) + "," + centavos


def validar_formulario(dados: dict) -> list:
    erros = []
    obrigatórios = CAMPOS_OBRIGATORIOS_ALUNO if dados.get("perfil") == "aluno" else CAMPOS_OBRIGATORIOS
    if any((dados.get(campo) or "").strip() == "" for campo in obrigatórios):
        erros.append("Preencha todos os campos")
    n_usp = dados.get("n_usp", "")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    agencia = dados.get("agencia", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = dados.get("valor_solicitado", "")
    if valor and (not valor.isdigit() or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    email = dados.get("email", "")
    if email and ("@" not in email or email.split("@")[-1] == ""):
        erros.append("E-mail inválido")
    cpf = dados.get("cpf", "")
    if cpf and (len(cpf) != 11 or not cpf.isdigit()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not validar_cpf(cpf):
        erros.append("CPF inválido")
    cep = dados.get("cep", "")
    if cep and (len(cep) != 8 or not cep.isdigit()):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = dados.get("data_de_nascimento", "")
    if nascimento and (len(nascimento) != 8 or not nascimento.isdigit()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_válida(nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def data_válida(texto: str) -> bool:
    """Verifica se os 8 dígitos formam uma data existente (dd/mm/aaaa)."""
    dia = int(texto[0:2])
    mes = int(texto[2:4])
    ano = int(texto[4:8])
    if mes < 1 or mes > 12:
        return False
    dias_por_mes = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias_por_mes[mes - 1]


def formatar_cpf(cpf: str) -> str:
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"


def formatar_cep(cep: str) -> str:
    return f"{cep[:5]}-{cep[5:8]}"


def formatar_data(data: str) -> str:
    return f"{data[0:2]}/{data[2:4]}/{data[4:8]}"


def gerar_oficio(dados: dict) -> str:
    perfil = dados.get("perfil", "aluno")
    linhas = []
    linhas.append(f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}")
    linhas.append(f"E-mail: {dados['email']}")
    if perfil == "aluno":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_de_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    linhas.append("")
    linhas.append(
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados['nome_do_evento']}")
    linhas.append(f"Período: {dados['periodo_do_evento']}")
    linhas.append(f"Local: {dados['cidade_do_evento']} - {dados['estado_do_evento']} - {dados['pais_do_evento']}")
    link = (dados.get("link_do_evento") or "").strip()
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.append(f"Apresentação de trabalho: {dados['apresentacao']}")
    linhas.append(f"Valor solicitado: {formatar(int(dados['valor_solicitado']))}")
    linhas.append(f"Detalhamento: {dados['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados['logradouro']}, {dados['numero']}")
    complemento = (dados.get("complemento") or "").strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.append(f"CEP: {formatar_cep(dados['cep'])}")
    linhas.append(f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {formatar_data(dados['data_de_nascimento'])}")
    linhas.append(f"CPF: {formatar_cpf(dados['cpf'])}")
    linhas.append(f"RG / RNM: {dados['rg']}")
    linhas.append(f"Banco: {dados['banco']}")
    linhas.append(f"Agência: {dados['agencia']}")
    linhas.append(f"Conta: {dados['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/enviar")
async def enviar(request: Request):
    dados = dict(await request.form())
    perfil = dados.get("perfil", "aluno")
    if perfil not in ("aluno", "docente"):
        perfil = "aluno"
    dados["perfil"] = perfil
    erros = validar_formulario(dados)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return {"oficio": gerar_oficio(dados)}


@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


app.mount("/", StaticFiles(directory=str(BASE_DIR)), name="estaticos")
