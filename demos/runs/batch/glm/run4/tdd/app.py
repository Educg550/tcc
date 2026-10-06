"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS = [
    "nome_completo", "numero_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade", "estado", "cpf", "rg_rnm", "banco", "agencia", "conta",
]
OPCIONAIS = {"link_evento", "complemento"}
SO_ALUNOS = {"nivel", "tipo_auxilio"}

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


def digitos_conferem(cpf: str) -> bool:
    for tamanho in (9, 10):
        soma = sum(int(cpf[indice]) * (tamanho + 1 - indice) for indice in range(tamanho))
        resto = soma * 10 % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[tamanho]):
            return False
    return True


def validar(dados: dict) -> list[str]:
    erros: list[str] = []
    perfil = dados.get("perfil", "alunos")
    requeridos = [
        campo for campo in CAMPOS
        if campo not in OPCIONAIS and (campo not in SO_ALUNOS or perfil != "docentes")
    ]
    if any(not str(dados.get(campo, "")).strip() for campo in requeridos):
        erros.append("Preencha todos os campos")

    def valor(campo):
        return str(dados.get(campo, "")).strip()

    numero_usp = valor("numero_usp")
    if numero_usp and not numero_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    agencia = valor("agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor_solicitado = valor("valor_solicitado")
    if valor_solicitado:
        centavos = re.sub(r"\D", "", valor_solicitado)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    email = valor("email")
    if email:
        usuario, _, dominio = email.partition("@")
        if not usuario or not dominio or "." not in dominio:
            erros.append("E-mail inválido")
    cpf = valor("cpf")
    if cpf:
        if not FORMATO_CPF.fullmatch(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not digitos_conferem(cpf.replace(".", "").replace("-", "")):
            erros.append("CPF inválido")
    cep = valor("cep")
    if cep and not FORMATO_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = valor("data_nascimento")
    if nascimento:
        if not FORMATO_DATA.fullmatch(nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def moeda(centavos: int) -> str:
    inteiro = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {inteiro},{centavos % 100:02d}"


def gerar_oficio(dados: dict) -> str:
    if dados.get("perfil") == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    valor = moeda(int(re.sub(r"\D", "", dados["valor_solicitado"])))
    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['numero_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo_evento']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if str(dados.get("link_evento", "")).strip():
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao_trabalho']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if str(dados.get("complemento", "")).strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg_rnm']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitacao(dados: dict):
    erros = validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return {"oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent, html=True), name="estaticos")
