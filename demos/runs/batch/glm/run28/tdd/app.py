"""API de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI()


class ErroValidacao(Exception):
    """Erro de validação do formulário."""


@app.post("/api/validar")
async def validar(dados: dict) -> JSONResponse:
    """Valida os dados enviados e devolve o ofício pronto, se tudo estiver certo."""
    try:
        mensagens_erro = _validar_dados(dados)
    except ErroValidacao:
        mensagens_erro = ["Preencha todos os campos"]

    if mensagens_erro:
        return JSONResponse({"ok": False, "erros": mensagens_erro}, status_code=422)

    return JSONResponse({"ok": True, "erros": [], "oficio": _gerar_oficio(dados)})


def _validar_dados(dados: dict) -> list[str]:
    """Valida os campos preenchidos."""
    erros = []

    if _ha_campo_vazio(dados):
        erros.append("Preencha todos os campos")

    numero_usp = str(dados.get("numero_usp", ""))
    if not numero_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", ""))
    if not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("valor", ""))
    if not valor.isdigit() or int(valor or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", ""))
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", ""))
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = str(dados.get("cep", ""))
    if not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nascimento = str(dados.get("data_nascimento", ""))
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_valida(data_nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def _ha_campo_vazio(dados: dict) -> bool:
    """Verifica se há algum campo obrigatório vazio."""
    obrigatorios = [
        "nome", "numero_usp", "programa", "nivel", "tipo_auxilio", "email",
        "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
        "pais_evento", "detalhamento", "apresentacao", "logradouro", "numero",
        "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
        "conta", "data_nascimento", "valor",
    ]
    return any(not str(dados.get(campo, "")).strip() for campo in obrigatorios)


def _cpf_valido(cpf: str) -> bool:
    """Verifica se os dígitos verificadores estão corretos."""
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False

    for i in range(9, 11):
        soma = sum(digitos[j] * (10 - j if i == 9 else 11 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[i]:
            return False
    return True


def _data_valida(data_str: str) -> bool:
    """Verifica se a data existe."""
    try:
        dia, mes, ano = (int(p) for p in data_str.split("/"))
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def _formatar_moeda(valor_centavos: int) -> str:
    """Formata em moeda brasileira."""
    partes = f"{valor_centavos // 100:,}".split(",")
    return f"R$ {'.'.join(partes)},{valor_centavos % 100:02d}"


def _gerar_oficio(dados: dict) -> str:
    """Gera o ofício pronto para encaminhamento à CCP."""
    tipo = dados.get("tipo", "aluno")
    assunto = (
        f"Assunto: Solicitação de Auxílio Financeiro - {dados.get('tipo_auxilio', '')}"
        if tipo == "aluno"
        else "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
    )
    programa = (
        f"Programa: {dados.get('programa', '')} - {dados.get('nivel', '')}"
        if tipo == "aluno"
        else f"Programa: {dados.get('programa', '')}"
    )

    link = str(dados.get("link", "")).strip()
    complemento = str(dados.get("complemento", "")).strip()

    linhas = [
        f"Interessada(o): {dados.get('nome', '')} - {dados.get('numero_usp', '')}",
        f"E-mail: {dados.get('email', '')}",
        assunto,
        programa,
        "",
        "A CCP-" + dados.get("programa", "") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + dados.get("nome_evento", ""),
        "Período: " + dados.get("periodo_evento", ""),
        "Local: " + dados.get("cidade_evento", "") + " - " + dados.get("estado_evento", "") + " - " + dados.get("pais_evento", ""),
    ]

    if link:
        linhas.append("Link do evento: " + link)

    linhas.extend([
        "Apresentação de trabalho: " + dados.get("apresentacao", ""),
        "Valor solicitado: " + _formatar_moeda(int(dados.get("valor", "0"))),
        "Detalhamento: " + dados.get("detalhamento", ""),
        "",
        "Endereço da(o) interessada(o)",
        dados.get("logradouro", "") + ", " + dados.get("numero", ""),
    ])

    if complemento:
        linhas.append("Complemento: " + complemento)

    linhas.extend([
        "CEP: " + dados.get("cep", ""),
        dados.get("bairro", "") + ", " + dados.get("cidade", "") + " - " + dados.get("estado", ""),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + dados.get("data_nascimento", ""),
        "CPF: " + dados.get("cpf", ""),
        "RG / RNM: " + dados.get("rg", ""),
        "Banco: " + dados.get("banco", ""),
        "Agência: " + dados.get("agencia", ""),
        "Conta: " + dados.get("conta", ""),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])

    return "\n".join(linhas)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
