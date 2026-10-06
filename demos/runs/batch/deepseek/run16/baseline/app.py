import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome_completo: str = ""
    n_usp: str = ""
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
    valor_solicitado: str = ""
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
    nome_banco: str = ""
    agencia: str = ""
    conta: str = ""


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    for i in (9, 10):
        soma = sum(numeros[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[i]:
            return False
    return True


def _data_valida(data: str) -> bool:
    dia, mes, ano = data.split("/")
    try:
        datetime(int(ano), int(mes), int(dia))
        return True
    except ValueError:
        return False


def _moeda(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    numero = int(digitos) if digitos else 0
    inteiro = f"{numero // 100:,}".replace(",", ".")
    return f"R$ {inteiro},{numero % 100:02d}"


def validar(d: Solicitacao):
    erros = []
    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
        "bairro", "cep", "cidade", "estado", "cpf", "rg", "nome_banco",
        "agencia", "conta",
    ]
    if d.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    campos = d.model_dump()
    if any(not campos[c].strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if d.n_usp.strip() and not d.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")

    if d.agencia.strip() and not d.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")

    if d.valor_solicitado.strip():
        digitos = re.sub(r"\D", "", d.valor_solicitado)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if d.email.strip() and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", d.email.strip()):
        erros.append("E-mail inválido")

    cpf = d.cpf.strip()
    cpf_formato = bool(re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf))
    if cpf and not cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = d.cep.strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = d.data_nascimento.strip()
    data_formato = bool(re.match(r"^\d{2}/\d{2}/\d{4}$", data))
    if data and not data_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formato and not _data_valida(data):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d: Solicitacao) -> str:
    if d.aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {d.tipo_auxilio.strip()}"
        programa = f"{d.programa.strip()} - {d.nivel.strip()}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = d.programa.strip()

    linhas = [
        f"Interessada(o): {d.nome_completo.strip()} - {d.n_usp.strip()}",
        f"E-mail: {d.email.strip()}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{d.programa.strip()} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.nome_evento.strip()}",
        f"Período: {d.periodo.strip()}",
        f"Local: {d.cidade_evento.strip()} - {d.estado_evento.strip()} - {d.pais_evento.strip()}",
    ]
    if d.link_evento.strip():
        linhas.append(f"Link do evento: {d.link_evento.strip()}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao.strip()}",
        f"Valor solicitado: {_moeda(d.valor_solicitado)}",
        f"Detalhamento: {d.detalhamento.strip()}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro.strip()}, {d.numero.strip()}",
    ]
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento.strip()}")
    linhas += [
        f"CEP: {d.cep.strip()}",
        f"{d.bairro.strip()}, {d.cidade.strip()} - {d.estado.strip()}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.data_nascimento.strip()}",
        f"CPF: {d.cpf.strip()}",
        f"RG / RNM: {d.rg.strip()}",
        f"Banco: {d.nome_banco.strip()}",
        f"Agência: {d.agencia.strip()}",
        f"Conta: {d.conta.strip()}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
