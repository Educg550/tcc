import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

OBRIGATORIOS_COMUNS = (
    "nome", "numero_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
)
OBRIGATORIOS_ALUNOS = OBRIGATORIOS_COMUNS + ("nivel", "tipo_auxilio")


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome: str = ""
    numero_usp: str = ""
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


def cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[posicao]:
            return False
    return True


def data_existente(texto: str) -> bool:
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validar(s: Solicitacao) -> list[str]:
    obrigatorios = OBRIGATORIOS_COMUNS if s.aba == "docentes" else OBRIGATORIOS_ALUNOS
    erros = []
    if any(not getattr(s, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if s.numero_usp and not s.numero_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = re.sub(r"\D", "", s.valor)
    if s.valor and (not valor or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and ("@" not in s.email or not s.email.split("@", 1)[1]):
        erros.append("E-mail inválido")
    cpf_no_formato = False
    if s.cpf:
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
            cpf_no_formato = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")
    if s.cep and not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    data_no_formato = False
    if s.data_nascimento:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento):
            data_no_formato = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_no_formato and not cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if data_no_formato and not data_existente(s.data_nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def formatar_valor(digitos_valor: str) -> str:
    inteiro, centavos = divmod(int(digitos_valor), 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(s: Solicitacao) -> str:
    centavos = re.sub(r"\D", "", s.valor)
    if s.aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {s.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        linha_programa = f"Programa: {s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome} - {s.numero_usp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
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
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formatar_valor(centavos)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])
    if s.complemento:
        linhas.append(f"Complemento: {s.complemento}")
    linhas.extend([
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
    ])
    return "\n".join(linhas)


@app.post("/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao)}


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
app.mount("/", StaticFiles(directory=RAIZ, html=True), name="raiz")
