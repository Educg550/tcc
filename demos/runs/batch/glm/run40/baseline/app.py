import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/", StaticFiles(directory="static"), name="static")


def formata_brl(cents: int) -> str:
    return "R$ " + f"{cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def valida_cpf_digitos(digitos: str) -> bool:
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum((10 - i) * int(d) for i, d in enumerate(digitos[:9]))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if d1 != int(digitos[9]):
        return False
    soma = sum((11 - i) * int(d) for i, d in enumerate(digitos[:10]))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    return d2 == int(digitos[10])


class Solicitacao(BaseModel):
    aba: str
    nome: str
    nusp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ""
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def validador_cpf_campo() -> str:
    class Validador(str):
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return v

    return Validador


class Cpf(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


class DataNascimento(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


class Cep(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


class Valor(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


def valida_dados(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    if (
        not s.nome.strip()
        or not s.nusp.strip()
        or not s.programa.strip()
        or not s.email.strip()
        or not s.evento.strip()
        or not s.periodo.strip()
        or not s.cidade_evento.strip()
        or not s.estado_evento.strip()
        or not s.pais_evento.strip()
        or not s.detalhamento.strip()
        or not s.apresentacao.strip()
        or not s.logradouro.strip()
        or not s.numero.strip()
        or not s.bairro.strip()
        or not s.cep.strip()
        or not s.cidade.strip()
        or not s.estado.strip()
        or not s.cpf.strip()
        or not s.rg.strip()
        or not s.banco.strip()
        or not s.agencia.strip()
        or not s.conta.strip()
        or not s.nascimento.strip()
        or not s.valor.strip()
        or (s.aba == "alunos" and not s.nivel.strip())
        or (s.aba == "alunos" and not s.tipo_auxilio.strip())
    ):
        erros.append("Preencha todos os campos")
    if not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    try:
        cents = int(s.valor)
    except ValueError:
        cents = -1
    if cents <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in s.email or not re.search(r"@.+\..+$", s.email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not valida_cpf_digitos(re.sub(r"\D", "", s.cpf)):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s.nascimento)
    if not m:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def gera_oficio(s: Solicitacao) -> str:
    e = "\n"
    if s.aba == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + s.tipo_auxilio
        programa = "Programa: " + s.programa + " - " + s.nivel
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + s.programa
    local = " - ".join([s.cidade_evento, s.estado_evento, s.pais_evento])
    valor_fmt = formata_brl(int(s.valor))
    if not s.complemento.strip():
        complemento = ""
    else:
        complemento = "Complemento: " + s.complemento + "\n"
    if not s.link_evento.strip():
        link = ""
    else:
        link = "Link do evento: " + s.link_evento + "\n"
    return (
        "Interessada(o): "
        + s.nome
        + " - "
        + s.nusp
        + e
        + "E-mail: "
        + s.email
        + e
        + assunto
        + e
        + programa
        + e
        + e
        + "A CCP-"
        + s.programa
        + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
        + " interessada(o) acima, conforme segue:"
        + e
        + e
        + "Dados do evento"
        + e
        + "Evento: "
        + s.evento
        + e
        + "Período: "
        + s.periodo
        + e
        + "Local: "
        + local
        + e
        + link
        + "Apresentação de trabalho: "
        + s.apresentacao
        + e
        + "Valor solicitado: "
        + valor_fmt
        + e
        + "Detalhamento: "
        + s.detalhamento
        + e
        + e
        + "Endereço da(o) interessada(o)"
        + e
        + s.logradouro
        + ", "
        + s.numero
        + e
        + complemento
        + "CEP: "
        + s.cep
        + e
        + s.bairro
        + ", "
        + s.cidade
        + " - "
        + s.estado
        + e
        + e
        + "Dados para pagamento"
        + e
        + "Data de nascimento: "
        + s.nascimento
        + e
        + "CPF: "
        + s.cpf
        + e
        + "RG / RNM: "
        + s.rg
        + e
        + "Banco: "
        + s.banco
        + e
        + "Agência: "
        + s.agencia
        + e
        + "Conta: "
        + s.conta
        + e
        + e
        + "Encaminhe-se ao Serviço Financeiro para providências."
    )


@app.post("/api/solicitar")
async def solicitar(s: Solicitacao) -> JSONResponse:
    erros = valida_dados(s)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": gera_oficio(s)})
