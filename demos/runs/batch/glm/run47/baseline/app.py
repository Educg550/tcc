"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Endereco(BaseModel):
    """Bloco ENDEREÇO DO SOLICITANTE."""

    nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""


class Pagamento(BaseModel):
    """Bloco INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO."""

    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


class Solicitacao(BaseModel):
    """Uma solicitação de auxílio, de aluno ou de docente."""

    perfil: str = "alunos"
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    endereco: Endereco = Endereco()
    pagamento: Pagamento = Pagamento()


# --- Validação de CPF e de data ---------------------------------------


def digitos(cpf: str) -> list[int]:
    """Os onze dígitos de um CPF já no formato 000.000.000-00."""
    return [int(c) for c in cpf if c.isdigit()]


def cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores contra os nove primeiros."""
    d = digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in (9, 10):
        resto = sum(d[j] * (i + 1 - j) for j in range(i)) % 11
        if (resto < 2 and d[i] != 0) or (resto >= 2 and d[i] != 11 - resto):
            return False
    return True


def dias_do_mes(ano: int, mes: int) -> int:
    """Quantos dias tem o mês, com o ano bissexto no lugar."""
    if mes == 2:
        return 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28
    return 30 if mes in (4, 6, 9, 11) else 31


def data_valida(valor: str) -> bool:
    """dd/mm/aaaa que denote um dia que existiu de verdade."""
    partes = valor.split("/")
    if len(partes) != 3 or not all(p.isdigit() for p in partes):
        return False
    dia, mes, ano = (int(p) for p in partes)
    return 1 <= mes <= 12 and 1 <= dia <= dias_do_mes(ano, mes)


# --- Validação da solicitação --------------------------------------------

CAMPOS_ALUNOS = [
    "nome", "n_usp", "programa", "nivel", "tipo", "email", "evento",
    "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao",
]
CAMPOS_DOCENTES = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao",
]
CAMPOS_ENDERECO = ["nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado"]
CAMPOS_PAGAMENTO = ["cpf", "rg", "banco", "agencia", "conta"]

ERROS = [
    ("obrigatorio", "Preencha todos os campos"),
    ("n_usp", "N. USP deve conter apenas números"),
    ("agencia", "Número da agência deve conter apenas números"),
    ("valor", "Valor solicitado deve ser maior que 0"),
    ("email", "E-mail inválido"),
    ("cpf", "CPF deve estar no formato 000.000.000-00"),
    ("cep", "CEP deve estar no formato 00000-000"),
    ("nascimento", "Data de nascimento deve estar no formato dd/mm/aaaa"),
    ("cpf", "CPF inválido"),
    ("nascimento", "Data de nascimento inválida"),
]


def validar(s: Solicitacao) -> list[str]:
    """Devolve as mensagens de erro que se aplicam à solicitação."""
    erros = []

    def campo(nome: str) -> str:
        return getattr(s, nome) or getattr(s.endereco, nome, None) or getattr(s.pagamento, nome, None)

    if any(not campo(c).strip() for c in CAMPOS_ALUNOS if c in ("nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao")):
        pass  # marcador; a checagem real está logo abaixo

    base = CAMPOS_DOCENTES if s.perfil == "docentes" else CAMPOS_ALUNOS
    exigidos = base + CAMPOS_ENDERECO + CAMPOS_PAGAMENTO
    if any(not campo(c).strip() for c in exigidos):
        erros.append("Preencha todos os campos")
    if not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.pagamento.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not s.valor.isdigit() or int(s.valor or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = s.email.strip()
    if "@" not in email or email.endswith("@") or "." not in email.split("@", 1)[1]:
        erros.append("E-mail inválido")
    if len(digitos(s.pagamento.cpf)) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(s.pagamento.cpf):
        erros.append("CPF inválido")
    if len(s.endereco.cep) != 9:
        erros.append("CEP deve estar no formato 00000-000")
    if len(s.endereco.nascimento) != 10:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not data_valida(s.endereco.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


# --- Geração do ofício ----------------------------------------------------


def moeda(centavos: str) -> str:
    """150000 -> R$ 1.500,00."""
    d = (centavos or "0").lstrip("0") or "0"
    reais, cents = d[:-2] or "0", d[-2:]
    grupos = []
    while len(reais) > 3:
        grupos.insert(0, reais[-3:])
        reais = reais[:-3]
    grupos.insert(0, reais)
    return f"R$ {'.'.join(grupos)},{cents}"


def oficio(s: Solicitacao) -> str:
    """O ofício pronto, com os marcadores substituídos pelos dados."""
    e, p = s.endereco, s.pagamento
    if s.perfil == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link.strip():
        linhas.append(f"Link do evento: {s.link}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {moeda(s.valor)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{e.logradouro}, {e.numero}",
    ]
    if e.complemento.strip():
        linhas.append(f"Complemento: {e.complemento}")
    linhas += [
        f"CEP: {e.cep}",
        f"{e.bairro}, {e.cidade} - {e.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {e.nascimento}",
        f"CPF: {p.cpf}",
        f"RG / RNM: {p.rg}",
        f"Banco: {p.banco}",
        f"Agência: {p.agencia}",
        f"Conta: {p.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def enviar(s: Solicitacao) -> dict:
    """Recebe a solicitação e devolve os erros ou o ofício pronto."""
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "erros": [], "oficio": oficio(s)}


app.mount("/", StaticFiles(directory="frontend", html=True), name="estaticos")
