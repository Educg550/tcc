"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Recebe a solicitação, valida e devolve as mensagens de erro ou o ofício pronto.
Não grava nada: a solicitação se encerra na resposta.
"""

from calendar import monthrange
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

STATIC = Path(__file__).parent

CAMPOS_TEXTO = (
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade", "estado", "pais", "detalhamento", "apresentacao",
    "logradouro", "numero", "bairro", "cidade_res", "estado_res",
    "rg", "banco", "conta",
)


class Solicitacao(BaseModel):
    """Dados comuns às duas abas; tipo e nível só existem na aba ALUNOS."""

    tipo: str  # "alunos" ou "docentes"
    dados: dict


def _tem_campo_vazio(dados, tipo):
    obrigatorios = [
        "nome", "nusp", "programa", "email", "evento", "periodo", "cidade",
        "estado", "pais", "valor", "detalhamento", "apresentacao",
        "logradouro", "numero", "bairro", "cep", "cidade_res", "estado_res",
        "cpf", "rg", "banco", "agencia", "conta", "nascimento",
    ]
    if tipo == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    return any(not str(dados.get(c, "")).strip() for c in obrigatorios)


def _cpf_valido(cpf):
    numeros = [int(d) for d in cpf if d.isdigit()]
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    soma = sum(n * (10 - i) for i, n in enumerate(numeros[:9]))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if numeros[9] != dv1:
        return False
    soma = sum(n * (11 - i) for i, n in enumerate(numeros[:10]))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return numeros[10] == dv2


def _validar(dados, tipo):
    erros = []
    if _tem_campo_vazio(dados, tipo):
        erros.append("Preencha todos os campos")
    nusp = str(dados.get("nusp", ""))
    if not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    agencia = str(dados.get("agencia", ""))
    if not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = str(dados.get("valor", ""))
    if not valor.isdigit() or int(valor or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(dados.get("email", ""))
    if "@" not in email or "@" == email[-1] or "." not in email.split("@", 1)[1]:
        erros.append("E-mail inválido")
    cpf = str(dados.get("cpf", ""))
    if not (len(cpf) == 14 and cpf[3] == "." and cpf[7] == "." and cpf[11] == "-"
            and cpf[:3].isdigit() and cpf[4:7].isdigit() and cpf[8:11].isdigit()
            and cpf[12:].isdigit()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    cep = str(dados.get("cep", ""))
    if not (len(cep) == 9 and cep[:5].isdigit() and cep[5] == "-" and cep[6:].isdigit()):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = str(dados.get("nascimento", ""))
    if not (len(nascimento) == 10 and nascimento[2] == "/" and nascimento[5] == "/"
            and nascimento[:2].isdigit() and nascimento[3:5].isdigit()
            and nascimento[6:].isdigit()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = int(nascimento[:2]), int(nascimento[3:5]), int(nascimento[6:])
        try:
            date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")
    if "CPF deve estar no formato 000.000.000-00" not in erros and not _cpf_valido(cpf):
        erros.append("CPF inválido")
    return erros


def _moeda(centavos):
    texto = f"{centavos:,}".replace(",", ".")
    return f"R$ {texto},00"


def _oficio(dados, tipo):
    linhas = []
    linhas.append(f"Interessada(o): {dados['nome']} - {dados['nusp']}")
    linhas.append(f"E-mail: {dados['email']}")
    if tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    linhas.append("")
    linhas.append(
        "A CCP-" + dados["programa"]
        + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
        + " interessada(o) acima, conforme segue:"
    )
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados['evento']}")
    linhas.append(f"Período: {dados['periodo']}")
    linhas.append(f"Local: {dados['cidade']} - {dados['estado']} - {dados['pais']}")
    if dados.get("link"):
        linhas.append(f"Link do evento: {dados['link']}")
    linhas.append(f"Apresentação de trabalho: {dados['apresentacao']}")
    linhas.append(f"Valor solicitado: {_moeda(int(dados['valor']))}")
    linhas.append(f"Detalhamento: {dados['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados['logradouro']}, {dados['numero']}")
    if dados.get("complemento"):
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.append(f"CEP: {dados['cep']}")
    linhas.append(f"{dados['bairro']}, {dados['cidade_res']} - {dados['estado_res']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {dados['nascimento']}")
    linhas.append(f"CPF: {dados['cpf']}")
    linhas.append(f"RG / RNM: {dados['rg']}")
    linhas.append(f"Banco: {dados['banco']}")
    linhas.append(f"Agência: {dados['agencia']}")
    linhas.append(f"Conta: {dados['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = _validar(s.dados, s.tipo)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(s.dados, s.tipo)}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/style.css")
def css():
    return FileResponse(STATIC / "style.css", media_type="text/css")


@app.get("/app.js")
def js():
    return FileResponse(STATIC / "app.js", media_type="text/javascript")