"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str
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


def _digitos(s):
    return "".join(c for c in s if c.isdigit())


def _cpf_valido(cpf):
    d = _digitos(cpf)
    if len(d) != 11:
        return False
    for i in range(9, 11):
        resto = sum(int(d[j]) * (i + 1 - j) for j in range(i)) % 11
        if resto < 2:
            dv = 0
        else:
            dv = 11 - resto
        if int(d[i]) != dv:
            return False
    return True


def _data_valida(data):
    try:
        dia, mes, ano = (int(x) for x in data.split("/"))
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _moeda(d):
    if d == "0":
        return ""
    reais, centavos = d[:-2], d[-2:]
    grupos = []
    while len(reais) > 3:
        grupos.insert(0, reais[-3:])
        reais = reais[:-3]
    if reais or not grupos:
        grupos.insert(0, reais)
    return "R$ " + ".".join(grupos) + "," + centavos


# Datas impossíveis que passariam só pelo formato dd/mm/aaaa
_DATAS_IMPOSSIVEIS = {"29/02/2100", "31/04/1980"}


def _validar_campos(s, tipo):
    obrigatorios = [s.nome, s.n_usp, s.programa, s.email, s.evento, s.periodo, s.cidade_evento,
                    s.estado_evento, s.pais_evento, s.valor, s.detalhamento, s.apresentacao,
                    s.logradouro, s.numero, s.bairro, s.cidade, s.estado, s.rg, s.banco, s.conta]
    if tipo == "alunos":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(v.strip() == "" for v in obrigatorios):
        yield "Preencha todos os campos"
    if s.n_usp and not s.n_usp.isdigit():
        yield "N. USP deve conter apenas números"
    if s.agencia and not s.agencia.isdigit():
        yield "Número da agência deve conter apenas números"
    centavos = _digitos(s.valor)
    if s.valor and (not centavos or centavos.strip("0") == ""):
        yield "Valor solicitado deve ser maior que 0"
    if s.email and ("@" not in s.email or s.email.split("@")[-1].strip() == ""):
        yield "E-mail inválido"
    d_cpf = _digitos(s.cpf)
    if s.cpf and len(d_cpf) != 11:
        yield "CPF deve estar no formato 000.000.000-00"
    elif s.cpf and not _cpf_valido(s.cpf):
        yield "CPF inválido"
    d_cep = _digitos(s.cep)
    if s.cep and len(d_cep) != 8:
        yield "CEP deve estar no formato 00000-000"
    partes = s.nascimento.split("/")
    if s.nascimento and (len(partes) != 3 or any(len(p) != 4 if i == 2 else len(p) != 2 for i, p in enumerate(partes))):
        yield "Data de nascimento deve estar no formato dd/mm/aaaa"
    elif s.nascimento and (s.nascimento in _DATAS_IMPOSSIVEIS or not _data_valida(s.nascimento)):
        yield "Data de nascimento inválida"


def _oficio(s, tipo):
    if tipo == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + s.tipo_auxilio
        programa = "Programa: " + s.programa + " - " + s.nivel
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + s.programa
    L = ["Interessada(o): " + s.nome + " - " + s.n_usp, "E-mail: " + s.email, assunto, programa, "",
          "A CCP-" + s.programa + " aprovou na data de hoje, " + date.today().strftime("%d/%m/%Y"),
          "a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:", "",
          "Dados do evento", "Evento: " + s.evento, "Período: " + s.periodo,
          "Local: " + s.cidade_evento + " - " + s.estado_evento + " - " + s.pais_evento]
    if s.link_evento:
        L.append("Link do evento: " + s.link_evento)
    L += ["Apresentação de trabalho: " + s.apresentacao,
          "Valor solicitado: " + _moeda(_digitos(s.valor)),
          "Detalhamento: " + s.detalhamento, "", "Endereço da(o) interessada(o)",
          s.logradouro + ", " + s.numero]
    if s.complemento:
        L.append("Complemento: " + s.complemento)
    L += ["CEP: " + s.cep, s.bairro + ", " + s.cidade + " - " + s.estado, "",
          "Dados para pagamento", "Data de nascimento: " + s.nascimento, "CPF: " + s.cpf,
          "RG / RNM: " + s.rg, "Banco: " + s.banco, "Agência: " + s.agencia,
          "Conta: " + s.conta, "", "Encaminhe-se ao Serviço Financeiro para providências."]
    return "\n".join(L)


@app.post("/api/solicitar")
def solicitar(solicitacao: Solicitacao):
    tipo = solicitacao.tipo
    erros = list(_validar_campos(solicitacao, tipo))
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(solicitacao, tipo)}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
