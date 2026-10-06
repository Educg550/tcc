"""Backend FastAPI do formulário de solicitação de auxílio financeiro."""

import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    nascimento: str


class Pagamento(BaseModel):
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


class Solicitacao(BaseModel):
    perfil: str
    nome: str
    nusp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento_nome: str
    evento_periodo: str
    evento_cidade: str
    evento_estado: str
    evento_pais: str
    evento_link: str = ""
    valor_centavos: int
    detalhamento: str
    apresentacao: str
    endereco: Endereco
    pagamento: Pagamento


def _cpf_valido(cpf: str) -> bool:
    digitos = "".join(c for c in cpf if c.isdigit())
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(d) * (i + 1 - j) for j, d in enumerate(digitos[:i]))
        resto = soma % 11
        if resto < 2:
            if digitos[i] != "0":
                return False
        elif str(resto) != digitos[i]:
            return False
    return True


def _data_valida(data: str) -> bool:
    try:
        datetime.datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _validar(s: Solicitacao) -> list[str]:
    erros = []
    faltando = not s.nome or not s.nusp or not s.programa or not s.email
    faltando = faltando or not s.evento_nome or not s.evento_periodo
    faltando = faltando or not s.evento_cidade or not s.evento_estado or not s.evento_pais
    faltando = faltando or s.valor_centavos <= 0 or not s.detalhamento or not s.apresentacao
    if s.perfil == "alunos":
        faltando = faltando or not s.nivel or not s.tipo_auxilio
    if not faltando:
        e = s.endereco
        if not (e.logradouro and e.numero and e.bairro and e.cidade and e.estado and e.nascimento):
            faltando = True
        p = s.pagamento
        if not (p.cpf and p.rg and p.banco and p.agencia and p.conta):
            faltando = True
    if faltando:
        erros.append("Preencha todos os campos")
    if not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.pagamento.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor_centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = s.email
    if "@" not in email or not email.split("@")[-1].strip() or " " in email:
        erros.append("E-mail inválido")
    if len(s.pagamento.cpf) != 14 or not _cpf_valido(s.pagamento.cpf):
        if len(s.pagamento.cpf) != 14:
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            erros.append("CPF inválido")
    if len(s.endereco.cep) != 9:
        erros.append("CEP deve estar no formato 00000-000")
    if len(s.endereco.nascimento) != 10:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_valida(s.endereco.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def _moeda(centavos: int) -> str:
    reais, resto = divmod(centavos, 100)
    texto = str(reais)
    grupos = []
    while len(texto) > 3:
        grupos.insert(0, texto[-3:])
        texto = texto[:-3]
    grupos.insert(0, texto)
    return f"R$ {'.'.join(grupos)},{resto:02d}"


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = _validar(s)
    if erros:
        return {"ok": False, "erros": erros}

    if s.perfil == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
        tipo = "Verba do programa"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
        tipo = s.tipo_auxilio

    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento_nome}",
        f"Período: {s.evento_periodo}",
        f"Local: {s.evento_cidade} - {s.evento_estado} - {s.evento_pais}",
    ]
    if s.evento_link:
        linhas.append(f"Link do evento: {s.evento_link}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {_moeda(s.valor_centavos)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.endereco.logradouro}, {s.endereco.numero}",
    ]
    if s.endereco.complemento:
        linhas.append(f"Complemento: {s.endereco.complemento}")
    linhas += [
        f"CEP: {s.endereco.cep}",
        f"{s.endereco.bairro}, {s.endereco.cidade} - {s.endereco.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.endereco.nascimento}",
        f"CPF: {s.pagamento.cpf}",
        f"RG / RNM: {s.pagamento.rg}",
        f"Banco: {s.pagamento.banco}",
        f"Agência: {s.pagamento.agencia}",
        f"Conta: {s.pagamento.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return {"ok": True, "titulo": "Solicitação registrada", "oficio": "\n".join(linhas), "tipo_auxilio": tipo}
