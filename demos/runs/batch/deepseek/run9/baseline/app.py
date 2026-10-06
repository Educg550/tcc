import re
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
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
    data_nascimento: str = ""
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


OBRIGATORIOS_ALUNOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

OBRIGATORIOS_DOCENTES = [c for c in OBRIGATORIOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]


def so_digitos(valor: str) -> bool:
    return bool(valor) and valor.isdigit()


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[n]) * ((i + 1) - n) for n in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def data_valida(data: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12:
        return False
    if dia < 1:
        return False
    dias = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dia <= dias[mes - 1]


def valor_natural(valor: str) -> bool:
    m = re.fullmatch(r"R\$\s*([\d.]+),(\d{2})", valor)
    if not m:
        return False
    reais = m.group(1).replace(".", "")
    centavos = m.group(2)
    return (reais.isdigit() and centavos.isdigit() and (int(reais) > 0 or int(centavos) > 0))


def validar(s: Solicitacao):
    erros = []
    aba = "DOCENTES" if s.aba.upper() == "DOCENTES" else "ALUNOS"
    obrigatorios = OBRIGATORIOS_DOCENTES if aba == "DOCENTES" else OBRIGATORIOS_ALUNOS

    if any(not getattr(s, c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor.strip() and not valor_natural(s.valor.strip()):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s.email.strip()):
        erros.append("E-mail inválido")
    if s.cpf.strip():
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(s.cpf.strip()):
            erros.append("CPF inválido")
    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_nascimento.strip():
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento.strip()):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(s.data_nascimento.strip()):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(s: Solicitacao) -> str:
    aba = "DOCENTES" if s.aba.upper() == "DOCENTES" else "ALUNOS"
    linhas = []
    linhas.append(f"Interessada(o): {s.nome} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if aba == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    linhas.append("")
    linhas.append("A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.evento}")
    linhas.append(f"Período: {s.periodo}")
    linhas.append(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.append(f"Apresentação de trabalho: {s.apresentacao}")
    linhas.append(f"Valor solicitado: {s.valor}")
    linhas.append(f"Detalhamento: {s.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.logradouro}, {s.numero}")
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas.append(f"CEP: {s.cep}")
    linhas.append(f"{s.bairro}, {s.cidade} - {s.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.data_nascimento}")
    linhas.append(f"CPF: {s.cpf}")
    linhas.append(f"RG / RNM: {s.rg}")
    linhas.append(f"Banco: {s.banco}")
    linhas.append(f"Agência: {s.agencia}")
    linhas.append(f"Conta: {s.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(s)}


@app.get("/")
def raiz():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory=".", html=True), name="static")
