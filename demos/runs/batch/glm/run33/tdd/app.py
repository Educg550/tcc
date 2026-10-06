import re
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    nome: str
    n_usp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade: str
    estado: str
    pais: str
    link: str = ""
    valor_centavos: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade_res: str
    estado_res: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


CAMPOS_OBRIGATORIOS = [
    "aba", "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento", "periodo", "cidade", "estado", "pais", "valor_centavos",
    "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade_res", "estado_res", "cpf", "rg", "banco",
    "agencia", "conta",
]


def formatar_valor(centavos: int) -> str:
    texto = str(centavos)
    parte_inteira = texto[:-2] if len(texto) > 2 else "0"
    centavos_str = texto[-2:].rjust(2, "0")
    grupos = []
    while len(parte_inteira) > 3:
        grupos.insert(0, parte_inteira[-3:])
        parte_inteira = parte_inteira[:-3]
    grupos.insert(0, parte_inteira)
    return f"R$ {'.'.join(grupos)},{centavos_str}"


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(d) * (10 - i) for i, d in enumerate(digitos[:9]))
    dv1 = (soma * 10 % 11) % 10
    if dv1 != int(digitos[9]):
        return False
    soma = sum(int(d) * (11 - i) for i, d in enumerate(digitos[:10]))
    dv2 = (soma * 10 % 11) % 10
    return dv2 == int(digitos[10])


def data_valida(nascimento: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", nascimento)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12:
        return False
    dias_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return 1 <= dia <= dias_mes


def validar(d: Solicitacao) -> list[str]:
    erros = []
    faltando = [
        c for c in CAMPOS_OBRIGATORIOS
        if (c == "nivel" or c == "tipo_auxilio") and d.aba == "alunos" and not getattr(d, c)
        or c not in ("nivel", "tipo_auxilio") and not getattr(d, c)
    ]
    if faltando:
        erros.append("Preencha todos os campos")
    if d.n_usp and not d.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.agencia and not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if d.valor_centavos and (not d.valor_centavos.isdigit() or int(d.valor_centavos) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if d.email and ("@" not in d.email or not d.email.split("@")[-1].strip()):
        erros.append("E-mail inválido")
    if d.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif d.cpf and not cpf_valido(d.cpf):
        erros.append("CPF inválido")
    if d.cep and not re.fullmatch(r"\d{5}-\d{3}", d.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if d.nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif d.nascimento and not data_valida(d.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(d: Solicitacao) -> str:
    valor = formatar_valor(int(d.valor_centavos))
    hoje = date.today().strftime("%d/%m/%Y")
    linhas = [
        f"Interessada(o): {d.nome} - {d.n_usp}",
        f"E-mail: {d.email}",
    ]
    if d.aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}")
        linhas.append(f"Programa: {d.programa} - {d.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d.programa}")
    linhas += [
        "",
        f"São Paulo, {hoje}",
        "",
        f"A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.evento}",
        f"Período: {d.periodo}",
        f"Local: {d.cidade} - {d.estado} - {d.pais}",
    ]
    if d.link:
        linhas.append(f"Link do evento: {d.link}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {d.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro}, {d.numero}",
    ]
    if d.complemento:
        linhas.append(f"Complemento: {d.complemento}")
    linhas += [
        f"CEP: {d.cep}",
        f"{d.bairro}, {d.cidade_res} - {d.estado_res}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.nascimento}",
        f"CPF: {d.cpf}",
        f"RG / RNM: {d.rg}",
        f"Banco: {d.banco}",
        f"Agência: {d.agencia}",
        f"Conta: {d.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/validar")
def api_validar(d: Solicitacao):
    if d.aba not in ("alunos", "docentes"):
        raise HTTPException(status_code=400, detail="Aba inválida")
    erros = validar(d)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(d)}


@app.get("/")
def index():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory="."), name="static")
