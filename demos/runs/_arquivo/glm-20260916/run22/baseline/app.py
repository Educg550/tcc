import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    aba: str = "alunos"
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


RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+")


def so_digitos(texto: str) -> bool:
    return bool(re.fullmatch(r"\d+", texto))


def cpf_confere(cpf: str) -> bool:
    n = [int(c) for c in re.sub(r"\D", "", cpf)]
    dv1 = sum(a * b for a, b in zip(n[:9], range(10, 1, -1))) % 11
    dv1 = 0 if dv1 < 2 else 11 - dv1
    dv2 = sum(a * b for a, b in zip(n[:10], range(11, 1, -1))) % 11
    dv2 = 0 if dv2 < 2 else 11 - dv2
    return n[9] == dv1 and n[10] == dv2


def data_existe(data_txt: str) -> bool:
    dia, mes, ano = (int(parte) for parte in data_txt.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def moeda(centavos: str) -> str:
    n = str(int(centavos)).zfill(3)
    reais = n[:-2]
    grupos = []
    while len(reais) > 3:
        grupos.append(reais[-3:])
        reais = reais[:-3]
    grupos.append(reais)
    return "R$ " + ".".join(reversed(grupos)) + "," + n[-2:]


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = []
    eh_docente = s.aba == "docentes"

    obrigatorios = [
        s.nome, s.n_usp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta,
    ]
    if not eh_docente:
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not campo.strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not so_digitos(s.n_usp.strip()):
        erros.append("N. USP deve conter apenas números")
    if s.agencia.strip() and not so_digitos(s.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")
    valor = s.valor.strip()
    if valor and (not so_digitos(valor) or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email.strip() and not RE_EMAIL.fullmatch(s.email.strip()):
        erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    if cpf and not RE_CPF.fullmatch(cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_confere(cpf):
        erros.append("CPF inválido")

    if s.cep.strip() and not RE_CEP.fullmatch(s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    data_nascimento = s.data_nascimento.strip()
    if data_nascimento and not RE_DATA.fullmatch(data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data_nascimento and not data_existe(data_nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    if eh_docente:
        assunto = "Verba do programa"
        linha_programa = f"Programa: {s.programa}"
    else:
        assunto = s.tipo_auxilio
        linha_programa = f"Programa: {s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {moeda(valor)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return {"ok": True, "oficio": "\n".join(linhas)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
