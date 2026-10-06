import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent
OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    dv1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return dv1 == digitos[9] and dv2 == digitos[10]


def _moeda(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor) or "0"
    total = int(digitos)
    return f"R$ {total // 100:,}".replace(",", ".") + f",{total % 100:02d}"


def _validar(perfil: str, campos: dict) -> list[str]:
    erros = []
    if any(not str(v).strip() for k, v in campos.items() if k not in OPCIONAIS):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("N. USP", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("NÚMERO DA AGÊNCIA", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("VALOR SOLICITADO (R$)", "").strip()
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("E-MAIL", "").strip()
    if email and ("@" not in email or not email.split("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = campos.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "").strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = campos.get("CEP", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("DATA DE NASCIMENTO", "").strip()
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _montar_oficio(perfil: str, c: dict) -> str:
    linhas = [
        f'Interessada(o): {c["NOME COMPLETO - SEM ABREVIAR"]} - {c["N. USP"]}',
        f'E-mail: {c["E-MAIL"]}',
    ]
    if perfil == "ALUNOS":
        linhas += [
            f'Assunto: Solicitação de Auxílio Financeiro - {c["TIPO DE AUXÍLIO"]}',
            f'Programa: {c["PROGRAMA"]} - {c["NÍVEL"]}',
        ]
    else:
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f'Programa: {c["PROGRAMA"]}',
        ]
    linhas += [
        "",
        f'A CCP-{c["PROGRAMA"]} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f'Evento: {c["NOME DO EVENTO / BANCA DE EXAME OU DEFESA"]}',
        f'Período: {c["PERÍODO DO EVENTO, EXAME OU DEFESA"]}',
        f'Local: {c["CIDADE DO EVENTO, EXAME OU DEFESA"]} - '
        f'{c["ESTADO DO EVENTO, EXAME OU DEFESA"]} - {c["PAÍS DO EVENTO, EXAME OU DEFESA"]}',
    ]
    link = c.get("LINK DO EVENTO, EXAME OU DEFESA", "").strip()
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f'Apresentação de trabalho: {c["IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"]}',
        f'Valor solicitado: {_moeda(c["VALOR SOLICITADO (R$)"])}',
        f'Detalhamento: {c["DETALHAMENTO DO PEDIDO"]}',
        "",
        "Endereço da(o) interessada(o)",
        f'{c["LOGRADOURO"]}, {c["NÚMERO"]}',
    ]
    complemento = c.get("COMPLEMENTO", "").strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f'CEP: {c["CEP"]}',
        f'{c["BAIRRO"]}, {c["CIDADE"]} - {c["ESTADO"]}',
        "",
        "Dados para pagamento",
        f'Data de nascimento: {c["DATA DE NASCIMENTO"]}',
        f'CPF: {c["CPF (SEPARADOS POR PONTOS E TRAÇO)"]}',
        f'RG / RNM: {c["RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"]}',
        f'Banco: {c["NOME DO BANCO"]}',
        f'Agência: {c["NÚMERO DA AGÊNCIA"]}',
        f'Conta: {c["NÚMERO DA CONTA"]}',
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(dados: dict):
    perfil = dados.get("perfil", "")
    campos = dados.get("campos", {})
    erros = _validar(perfil, campos)
    if erros:
        return {"erros": erros}
    return {"oficio": _montar_oficio(perfil, campos)}


@app.get("/", include_in_schema=False)
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
