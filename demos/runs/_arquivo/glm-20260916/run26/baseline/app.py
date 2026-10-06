import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

CAMPOS = [
    "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "link_evento", "valor_solicitado", "detalhamento",
    "apresentacao_trabalho", "data_nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm",
    "nome_banco", "agencia", "numero_conta",
]
OPCIONAIS = {"link_evento", "complemento"}
EXCLUSIVOS_DE_ALUNOS = {"nivel", "tipo_auxilio"}

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação do IME-USP")


@app.post("/solicitacao")
async def receber_solicitacao(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    docentes = dados.get("aba") == "docentes"
    valores = {}
    for campo in CAMPOS:
        if docentes and campo in EXCLUSIVOS_DE_ALUNOS:
            continue
        bruto = dados.get(campo, "")
        valores[campo] = bruto.strip() if isinstance(bruto, str) else str(bruto).strip()
    erros = validar(valores)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": redigir_oficio(valores, docentes)})


def validar(v):
    erros = []
    if any(not v[c] for c in CAMPOS if c not in OPCIONAIS and c in v):
        erros.append("Preencha todos os campos")

    if v.get("n_usp") and not re.fullmatch(r"\d+", v["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if v.get("agencia") and not re.fullmatch(r"\d+", v["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    if v.get("valor_solicitado"):
        centavos = centavos_do_valor(v["valor_solicitado"])
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = v.get("email", "")
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")

    cpf_no_formato = False
    if v.get("cpf"):
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", v["cpf"]):
            cpf_no_formato = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    if v.get("cep") and not re.fullmatch(r"\d{5}-\d{3}", v["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    data_no_formato = False
    if v.get("data_nascimento"):
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", v["data_nascimento"]):
            data_no_formato = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(v["cpf"]):
        erros.append("CPF inválido")

    if data_no_formato and not data_existente(v["data_nascimento"]):
        erros.append("Data de nascimento inválida")

    return erros


def centavos_do_valor(texto):
    limpo = texto.replace("R$", "")
    limpo = "".join(limpo.split())
    limpo = limpo.replace(".", "").replace(",", ".")
    if not limpo:
        return None
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        return None
    centavos = valor * 100
    if centavos != centavos.to_integral_value():
        return None
    return int(centavos)


def cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False

    def digito_verificador(base, peso_inicial):
        soma = sum(int(caractere) * peso for caractere, peso in zip(base, range(peso_inicial, 1, -1)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    esperado = "{}{}".format(digito_verificador(digitos[:9], 10), digito_verificador(digitos[:10], 11))
    return digitos[9:] == esperado


def data_existente(texto):
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def moeda(centavos):
    reais, cent = divmod(centavos, 100)
    parte_inteira = "{:,}".format(reais).replace(",", ".")
    return "R$ {},{:02d}".format(parte_inteira, cent)


def redigir_oficio(v, docentes):
    if docentes:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {v['programa']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {v['tipo_auxilio']}"
        linha_programa = f"Programa: {v['programa']} - {v['nivel']}"

    centavos = centavos_do_valor(v["valor_solicitado"])
    valor_formatado = moeda(centavos) if centavos is not None else v["valor_solicitado"]

    linhas = [
        f"Interessada(o): {v['nome_completo']} - {v['n_usp']}",
        f"E-mail: {v['email']}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{v['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['nome_evento']}",
        f"Período: {v['periodo_evento']}",
        f"Local: {v['cidade_evento']} - {v['estado_evento']} - {v['pais_evento']}",
    ]
    if v.get("link_evento"):
        linhas.append(f"Link do evento: {v['link_evento']}")
    linhas.extend([
        f"Apresentação de trabalho: {v['apresentacao_trabalho']}",
        f"Valor solicitado: {valor_formatado}",
        f"Detalhamento: {v['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['logradouro']}, {v['numero']}",
    ])
    if v.get("complemento"):
        linhas.append(f"Complemento: {v['complemento']}")
    linhas.extend([
        f"CEP: {v['cep']}",
        f"{v['bairro']}, {v['cidade']} - {v['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v['data_nascimento']}",
        f"CPF: {v['cpf']}",
        f"RG / RNM: {v['rg_rnm']}",
        f"Banco: {v['nome_banco']}",
        f"Agência: {v['agencia']}",
        f"Conta: {v['numero_conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="site")
