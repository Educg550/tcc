import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    nome: str = ""
    nusp: str = ""
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


def _digitos(valor):
    return re.fullmatch(r"[0-9]+", valor) is not None


def _valor_valido(valor):
    digitos = re.sub(r"\D", "", valor)
    return bool(digitos) and int(digitos) > 0


def _cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(set(nums)) == 1:
        return False
    for i in (9, 10):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def validar(d, aba):
    erros = []
    obrigatorios = [
        d.nome, d.nusp, d.programa, d.email, d.evento, d.periodo,
        d.cidade_evento, d.estado_evento, d.pais_evento, d.valor,
        d.detalhamento, d.apresentacao, d.data_nascimento, d.logradouro,
        d.numero, d.bairro, d.cep, d.cidade, d.estado, d.cpf, d.rg,
        d.banco, d.agencia, d.conta,
    ]
    if aba != "docentes":
        obrigatorios += [d.nivel, d.tipo_auxilio]
    if any(not valor.strip() for valor in obrigatorios):
        erros.append("Preencha todos os campos")

    if d.nusp and not _digitos(d.nusp):
        erros.append("N. USP deve conter apenas n\u00fameros")
    if d.agencia and not _digitos(d.agencia):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")
    if d.valor and not _valor_valido(d.valor):
        erros.append("Valor solicitado deve ser maior que 0")
    if d.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", d.email):
        erros.append("E-mail inv\u00e1lido")

    if d.cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", d.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(d.cpf):
            erros.append("CPF inv\u00e1lido")

    if d.cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", d.cep):
        erros.append("CEP deve estar no formato 00000-000")

    if d.data_nascimento:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", d.data_nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in d.data_nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def gerar_oficio(d, aba):
    if aba == "docentes":
        assunto = "Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        programa = d.programa
    else:
        assunto = f"Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - {d.tipo_auxilio}"
        programa = f"{d.programa} - {d.nivel}"

    linhas = [
        f"Interessada(o): {d.nome} - {d.nusp}",
        f"E-mail: {d.email}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{d.programa} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.evento}",
        f"Per\u00edodo: {d.periodo}",
        f"Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}",
    ]
    if d.link_evento:
        linhas.append(f"Link do evento: {d.link_evento}")
    linhas.append(f"Apresenta\u00e7\u00e3o de trabalho: {d.apresentacao}")
    linhas.append(f"Valor solicitado: {d.valor}")
    linhas.append(f"Detalhamento: {d.detalhamento}")
    linhas.append("")
    linhas.append("Endere\u00e7o da(o) interessada(o)")
    linhas.append(f"{d.logradouro}, {d.numero}")
    if d.complemento:
        linhas.append(f"Complemento: {d.complemento}")
    linhas.append(f"CEP: {d.cep}")
    linhas.append(f"{d.bairro}, {d.cidade} - {d.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d.data_nascimento}")
    linhas.append(f"CPF: {d.cpf}")
    linhas.append(f"RG / RNM: {d.rg}")
    linhas.append(f"Banco: {d.banco}")
    linhas.append(f"Ag\u00eancia: {d.agencia}")
    linhas.append(f"Conta: {d.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.")
    return "\n".join(linhas)


@app.post("/api/solicitacao/{aba}")
def solicitar(aba: str, dados: Solicitacao):
    erros = validar(dados, aba)
    if erros:
        return JSONResponse(status_code=422, content={"erros": erros})
    return JSONResponse(
        content={
            "titulo": "Solicita\u00e7\u00e3o registrada",
            "oficio": gerar_oficio(dados, aba),
        }
    )


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/", StaticFiles(directory=".", html=True), name="app")
