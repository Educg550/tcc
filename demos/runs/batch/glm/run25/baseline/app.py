"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    perfil: str
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


REQUIRED_ALUNOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao", "nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
    "agencia", "conta",
]
REQUIRED_DOCENTES = [f for f in REQUIRED_ALUNOS if f not in ("nivel", "tipo_auxilio")]


def valida(data: Solicitacao):
    """Devolve (erros, oficio)."""
    erros = []
    aluno = data.perfil == "alunos"
    requeridos = REQUIRED_ALUNOS if aluno else REQUIRED_DOCENTES
    if any(not getattr(data, f).strip() for f in requeridos):
        erros.append("Preencha todos os campos")
    if data.n_usp and not data.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if data.agencia and not data.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    centavos = data.valor.replace(".", "").replace(",", "").replace("R$", "").replace("$", "").strip()
    if data.valor.strip() and (not centavos.isdigit() or int(centavos) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    email = data.email.strip()
    if email and ("@" not in email or email.startswith("@") or "@" not in email.split("@", 1)[1] or not email.split("@", 1)[1].split(".")[-1]):
        erros.append("E-mail inválido")
    if data.cpf.strip() and data.cpf.strip() != "000.000.000-00":
        erros.append("CPF deve estar no formato 000.000.000-00")
    if data.cep.strip() and data.cep.strip() != "00000-000":
        erros.append("CEP deve estar no formato 00000-000")
    if data.nascimento.strip() and data.nascimento.strip() != "00/00/0000":
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if data.cpf.strip() == "000.000.000-00" and not cpf_valido(data.cpf.strip()):
        erros.append("CPF inválido")
    if data.nascimento.strip() == "00/00/0000" and not data_valida(data.nascimento.strip()):
        erros.append("Data de nascimento inválida")
    return erros


def cpf_valido(cpf: str) -> bool:
    digitos = [int(d) for d in cpf if d.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1)))
        resto = soma * 10 % 11
        if resto != digitos[i]:
            return False
    return True


def data_valida(txt: str) -> bool:
    try:
        dia, mes, ano = (int(p) for p in txt.split("/"))
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def moeda(centavos: str) -> str:
    return "R$ " + f"{int(centavos):,}".replace(",", ".") + ",00"


@app.post("/api/solicitar")
def solicitar(data: Solicitacao):
    erros = valida(data)
    if erros:
        return {"ok": False, "erros": erros}
    aluno = data.perfil == "alunos"
    tipo = data.tipo_auxilio if aluno else "Verba do programa"
    linha_nivel = f"{data.programa} - {data.nivel}" if aluno else data.programa
    valor_fmt = moeda(data.valor.replace(".", "").replace(",", "").replace("R$", "").strip())
    linhas = [
        f"Interessada(o): {data.nome} - {data.n_usp}",
        f"E-mail: {data.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {tipo}",
        f"Programa: {linha_nivel}",
        "",
        "A CCP-" + data.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {data.evento}",
        f"Período: {data.periodo}",
        f"Local: {data.cidade_evento} - {data.estado_evento} - {data.pais_evento}",
    ]
    if data.link_evento.strip():
        linhas.append(f"Link do evento: {data.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {data.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {data.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{data.logradouro}, {data.numero}",
    ]
    if data.complemento.strip():
        linhas.append(f"Complemento: {data.complemento}")
    linhas += [
        f"CEP: {data.cep}",
        f"{data.bairro}, {data.cidade} - {data.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data.nascimento}",
        f"CPF: {data.cpf}",
        f"RG / RNM: {data.rg}",
        f"Banco: {data.banco}",
        f"Agência: {data.agencia}",
        f"Conta: {data.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return {"ok": True, "erros": [], "oficio": "\n".join(linhas)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
