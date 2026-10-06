from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re

app = FastAPI()


class Submission(BaseModel):
    # bloco solicitante e evento
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentar_trabalho: str = ""
    # endereco
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    # pagamento
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""
    # qual formulario
    tipo_formulario: str = "alunos"


def _only_digits(s: str) -> bool:
    return bool(s) and s.isdigit()


def _cpf_valido(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11:
        return False
    if digits == digits[0] * 11:
        return False
    for i in range(2):
        s = sum(int(digits[j]) * (10 + i - j) for j in range(9 + i))
        d = (s * 10) % 11
        if d == 10:
            d = 0
        if d != int(digits[9 + i]):
            return False
    return True


def _data_valida(data: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mo < 1 or mo > 12:
        return False
    dias = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dias[mo - 1]


def _formata_valor(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return ""
    n = int(digits)
    reais = n // 100
    centavos = n % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


def _valor_numero(raw: str) -> int:
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return 0
    return int(digits)


OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentar_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


@app.post("/api/solicitar")
def solicitar(sub: Submission):
    erros = []

    # campos vazios
    vazio = False
    for campo in OBRIGATORIOS:
        valor = getattr(sub, campo, "")
        if not (valor and str(valor).strip()):
            vazio = True
            break
    if vazio:
        erros.append("Preencha todos os campos")

    if sub.n_usp.strip() and not _only_digits(sub.n_usp.strip()):
        erros.append("N. USP deve conter apenas números")
    if sub.agencia.strip() and not _only_digits(sub.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    if sub.valor_solicitado.strip():
        if _valor_numero(sub.valor_solicitado) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = sub.email.strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = sub.cpf.strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = sub.cep.strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    dn = sub.data_nascimento.strip()
    if dn:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dn):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(dn):
            erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    # montar ofício
    docentes = sub.tipo_formulario == "docentes"
    if docentes:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {sub.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {sub.tipo_auxilio}"
        linha_programa = f"Programa: {sub.programa} - {sub.nivel}"

    valor_fmt = _formata_valor(sub.valor_solicitado)

    linhas = [
        f"Interessada(o): {sub.nome_completo} - {sub.n_usp}",
        f"E-mail: {sub.email}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(sub.programa),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {sub.nome_evento}",
        f"Período: {sub.periodo_evento}",
        f"Local: {sub.cidade_evento} - {sub.estado_evento} - {sub.pais_evento}",
    ]
    if sub.link_evento.strip():
        linhas.append(f"Link do evento: {sub.link_evento}")
    linhas.append(f"Apresentação de trabalho: {sub.apresentar_trabalho}")
    linhas.append(f"Valor solicitado: {valor_fmt}")
    linhas.append(f"Detalhamento: {sub.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{sub.logradouro}, {sub.numero}")
    if sub.complemento.strip():
        linhas.append(f"Complemento: {sub.complemento}")
    linhas.append(f"CEP: {sub.cep}")
    linhas.append(f"{sub.bairro}, {sub.cidade} - {sub.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {sub.data_nascimento}")
    linhas.append(f"CPF: {sub.cpf}")
    linhas.append(f"RG / RNM: {sub.rg}")
    linhas.append(f"Banco: {sub.banco}")
    linhas.append(f"Agência: {sub.agencia}")
    linhas.append(f"Conta: {sub.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return {"ok": True, "oficio": "\n".join(linhas)}


@app.get("/")
def index():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory=".", html=True), name="static")
