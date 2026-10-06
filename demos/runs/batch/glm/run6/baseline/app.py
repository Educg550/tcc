import calendar
import re

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = ""
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: int = 0
    detalhamento: str = ""
    apresentacao: str = ""
    nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade_end: str = ""
    estado_end: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


def formatar_valor(centavos: int) -> str:
    inteiro = centavos // 100
    txt = str(inteiro)
    grupos = []
    while len(txt) > 3:
        grupos.insert(0, txt[-3:])
        txt = txt[:-3]
    grupos.insert(0, txt)
    return "R$ " + ".".join(grupos) + ",%02d" % (centavos % 100)


def cpf_valido(cpf: str) -> bool:
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or d == d[::-1]:
        return False
    for i in (9, 10):
        s = sum(d[k] * (i + 1 - k) for k in range(i))
        r = (s * 10) % 11 % 10
        if r != d[i]:
            return False
    return True


def validar(s: Solicitacao):
    erros = []
    campos = [s.nome, s.nusp, s.programa, s.email, s.nome_evento, s.periodo,
              s.cidade_evento, s.estado_evento, s.pais_evento, s.detalhamento,
              s.apresentacao, s.nascimento, s.logradouro, s.numero, s.bairro,
              s.cep, s.cidade_end, s.estado_end, s.cpf, s.rg, s.banco,
              s.agencia, s.conta]
    if s.tipo == "alunos":
        campos += [s.nivel, s.tipo_auxilio]
    if any(not c.strip() for c in campos):
        erros.append("Preencha todos os campos")
    if s.valor <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if s.nusp and not s.nusp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.email:
        local, sep, dominio = s.email.strip().partition("@")
        if not sep or not local or not dominio.strip():
            erros.append("E-mail inválido")
    if s.cpf.strip():
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(s.cpf):
            erros.append("CPF inválido")
    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if s.nascimento.strip():
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.nascimento.strip()):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            d, m, a = (int(x) for x in s.nascimento.strip().split("/"))
            try:
                ultimo = calendar.monthrange(a, m)[1]
            except ValueError:
                ultimo = 0
            if not 1 <= m <= 12 or not 1 <= d <= ultimo:
                erros.append("Data de nascimento inválida")
    return erros


def montar_oficio(s: Solicitacao) -> str:
    linhas = [
        "Interessada(o): %s - %s" % (s.nome.strip(), s.nusp.strip()),
        "E-mail: %s" % s.email.strip(),
    ]
    if s.tipo == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - %s" % s.tipo_auxilio.strip())
        linhas.append("Programa: %s - %s" % (s.programa.strip(), s.nivel.strip()))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: %s" % s.programa.strip())
    linhas += [
        "",
        "A CCP-%s aprovou na data de hoje, a solicitação de auxílio financeiro para a" % s.programa.strip(),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: %s" % s.nome_evento.strip(),
        "Período: %s" % s.periodo.strip(),
        "Local: %s - %s - %s" % (s.cidade_evento.strip(), s.estado_evento.strip(), s.pais_evento.strip()),
    ]
    if s.link_evento.strip():
        linhas.append("Link do evento: %s" % s.link_evento.strip())
    linhas += [
        "Apresentação de trabalho: %s" % s.apresentacao.strip(),
        "Valor solicitado: %s" % formatar_valor(s.valor),
        "Detalhamento: %s" % s.detalhamento.strip(),
        "",
        "Endereço da(o) interessada(o)",
        "%s, %s" % (s.logradouro.strip(), s.numero.strip()),
    ]
    if s.complemento.strip():
        linhas.append("Complemento: %s" % s.complemento.strip())
    linhas += [
        "CEP: %s" % s.cep.strip(),
        "%s, %s - %s" % (s.bairro.strip(), s.cidade_end.strip(), s.estado_end.strip()),
        "",
        "Dados para pagamento",
        "Data de nascimento: %s" % s.nascimento.strip(),
        "CPF: %s" % s.cpf.strip(),
        "RG / RNM: %s" % s.rg.strip(),
        "Banco: %s" % s.banco.strip(),
        "Agência: %s" % s.agencia.strip(),
        "Conta: %s" % s.conta.strip(),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": montar_oficio(s)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
