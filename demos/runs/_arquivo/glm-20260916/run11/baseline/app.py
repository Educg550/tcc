import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}

CAMPOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
CAMPOS_DOCENTES = [campo for campo in CAMPOS if campo not in ("NÍVEL", "TIPO DE AUXÍLIO")]


class Solicitacao(BaseModel):
    aba: Literal["alunos", "docentes"]
    campos: dict[str, str]


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    for passo in (9, 10):
        soma = sum(int(digitos[i]) * (passo + 1 - i) for i in range(passo))
        if (soma * 10) % 11 % 10 != int(digitos[passo]):
            return False
    return True


def validar(aba: str, campos: dict[str, str]) -> list[str]:
    obrigatorios = [c for c in (CAMPOS if aba == "alunos" else CAMPOS_DOCENTES) if c not in OPCIONAIS]
    erros = []
    if any(not campos.get(c, "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("N. USP", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("NÚMERO DA AGÊNCIA", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("VALOR SOLICITADO (R$)", "").strip()
    centavos = re.sub(r"\D", "", valor)
    if valor and (not centavos or int(centavos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("E-MAIL", "").strip()
    if email:
        local, _, dominio = email.partition("@")
        if not local or not dominio:
            erros.append("E-mail inválido")

    cpf = campos.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "").strip()
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = campos.get("CEP", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("DATA DE NASCIMENTO", "").strip()
    nascimento_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento_no_formato:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def formatar_valor(valor: str) -> str:
    reais, centavos = divmod(int(re.sub(r"\D", "", valor)), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(aba: str, c: dict[str, str]) -> str:
    if aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {c['TIPO DE AUXÍLIO']}"
        programa = f"Programa: {c['PROGRAMA']} - {c['NÍVEL']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c['PROGRAMA']}"

    linhas = [
        f"Interessada(o): {c['NOME COMPLETO - SEM ABREVIAR']} - {c['N. USP']}",
        f"E-mail: {c['E-MAIL']}",
        assunto,
        programa,
        "",
        f"A CCP-{c['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {c['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        (
            f"Local: {c['CIDADE DO EVENTO, EXAME OU DEFESA']}"
            f" - {c['ESTADO DO EVENTO, EXAME OU DEFESA']}"
            f" - {c['PAÍS DO EVENTO, EXAME OU DEFESA']}"
        ),
    ]
    if c.get("LINK DO EVENTO, EXAME OU DEFESA", "").strip():
        linhas.append(f"Link do evento: {c['LINK DO EVENTO, EXAME OU DEFESA'].strip()}")
    linhas += [
        f"Apresentação de trabalho: {c['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {formatar_valor(c['VALOR SOLICITADO (R$)'])}",
        f"Detalhamento: {c['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['LOGRADOURO']}, {c['NÚMERO']}",
    ]
    if c.get("COMPLEMENTO", "").strip():
        linhas.append(f"Complemento: {c['COMPLEMENTO'].strip()}")
    linhas += [
        f"CEP: {c['CEP']}",
        f"{c['BAIRRO']}, {c['CIDADE']} - {c['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['DATA DE NASCIMENTO']}",
        f"CPF: {c['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {c['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {c['NOME DO BANCO']}",
        f"Agência: {c['NÚMERO DA AGÊNCIA']}",
        f"Conta: {c['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao.aba, solicitacao.campos)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao.aba, solicitacao.campos)}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent, html=True), name="static")
