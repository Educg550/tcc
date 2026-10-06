import base64
import 
import os
import re
from datetime import date

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, Response

RAIZ = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

ALIASES = {
    "NOME COMPLETO - SEM ABREVIAR": "nome_completo",
    "N. USP": "numero_usp",
    "PROGRAMA": "programa",
    "NÍVEL": "nivel",
    "TIPO DE AUXÍLIO": "tipo_auxilio",
    "E-MAIL": "email",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "nome_evento",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "periodo_evento",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "cidade_evento",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "estado_evento",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "pais_evento",
    "LINK DO EVENTO, EXAME OU DEFESA": "link_evento",
    "VALOR SOLICITADO (R$)": "valor_solicitado",
    "DETALHAMENTO DO PEDIDO": "detalhamento",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "apresentacao_trabalho",
    "DATA DE NASCIMENTO": "data_nascimento",
    "LOGRADOURO": "logradouro",
    "NÚMERO": "numero",
    "COMPLEMENTO": "complemento",
    "BAIRRO": "bairro",
    "CEP": "cep",
    "CIDADE": "cidade",
    "ESTADO": "estado",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "cpf",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "rg_rnm",
    "NOME DO BANCO": "nome_banco",
    "NÚMERO DA AGÊNCIA": "numero_agencia",
    "NÚMERO DA CONTA": "numero_conta",
}

OPCIONAIS = {"link_evento", "complemento"}
CAMPOS_DE_ALUNO = ("NÍVEL", "nivel", "TIPO DE AUXÍLIO", "tipo_auxilio")
MARCADORES_DE_ABA = (
    "aba",
    "tipo",
    "formulario",
    "tipo_solicitante",
    "categoria",
    "origem",
    "perfil",
    "solicitante",
)

LOGO_RESERVA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _estatico(nome, tipo):
    caminho = os.path.join(RAIZ, nome)
    if os.path.isfile(caminho):
        return FileResponse(caminho, media_type=tipo)
    return Response(status_code=204)


@app.get("/")
def index():
    return _estatico("index.html", "text/html")


@app.get("/index.html")
def index_html():
    return _estatico("index.html", "text/html")


@app.get("/style.css")
def folha_de_estilo():
    return _estatico("style.css", "text/css")


@app.get("/app.js")
def script():
    return _estatico("app.js", "text/javascript")


@app.get("/favicon.ico")
def favicon():
    return _estatico("favicon.ico", "image/x-icon")


@app.get("/assets/usp-logo.png")
def logo():
    caminho = os.path.join(RAIZ, "assets", "usp-logo.png")
    if os.path.isfile(caminho):
        return FileResponse(caminho, media_type="image/png")
    return Response(content=LOGO_RESERVA, media_type="image/png")


def _valor(dados, rotulo):
    bruto = dados.get(ALIASES[rotulo])
    if bruto is None:
        bruto = dados.get(rotulo)
    if bruto is None:
        return ""
    return str(bruto).strip()


def _e_docente(dados):
    for marcador in MARCADORES_DE_ABA:
        if str(dados.get(marcador, "")).strip().lower() in ("docente", "docentes"):
            return True
    return not any(chave in dados for chave in CAMPOS_DE_ALUNO)


def _centavos(texto):
    numero = texto.replace("R$", "").replace(" ", "")
    if "," in numero:
        reais, _, centimos = numero.partition(",")
        reais = reais.replace(".", "")
        centimos = (centimos + "00")[:2]
        if not reais.isdigit() or not centimos.isdigit():
            return None
        return int(reais) * 100 + int(centimos)
    reais = numero.replace(".", "")
    if not reais.isdigit():
        return None
    return int(reais) * 100


def _moeda(centavos):
    reais, centimos = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centimos:02d}"


def _digito_verificador(digitos, peso_inicial):
    soma = sum(d * p for d, p in zip(digitos, range(peso_inicial, 1, -1)))
    digito = 11 - soma % 11
    return digito if digito <= 9 else 0


def _cpf_valido(texto):
    digitos = [int(c) for c in texto if c.isdigit()]
    if len(digitos) != 11:
        return False
    return digitos[9] == _digito_verificador(digitos[:9], 10) and digitos[10] == _digito_verificador(digitos[:10], 11)


def _(conteudo):
    return Response(.dumps(conteudo, ensure_ascii=False), media_type="application/")


def _oficio(v, docente, centavos):
    assunto = "Verba do programa" if docente else v["TIPO DE AUXÍLIO"]
    programa = v["PROGRAMA"]
    linhas = [
        f"Interessada(o): {v['NOME COMPLETO - SEM ABREVIAR']} - {v['N. USP']}",
        f"E-mail: {v['E-MAIL']}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {programa}" if docente else f"Programa: {programa} - {v['NÍVEL']}",
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {v['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {v['CIDADE DO EVENTO, EXAME OU DEFESA']} - {v['ESTADO DO EVENTO, EXAME OU DEFESA']} - {v['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    if v["LINK DO EVENTO, EXAME OU DEFESA"]:
        linhas.append(f"Link do evento: {v['LINK DO EVENTO, EXAME OU DEFESA']}")
    linhas += [
        f"Apresentação de trabalho: {v['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {_moeda(centavos)}",
        f"Detalhamento: {v['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['LOGRADOURO']}, {v['NÚMERO']}",
    ]
    if v["COMPLEMENTO"]:
        linhas.append(f"Complemento: {v['COMPLEMENTO']}")
    linhas += [
        f"CEP: {v['CEP']}",
        f"{v['BAIRRO']}, {v['CIDADE']} - {v['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v['DATA DE NASCIMENTO']}",
        f"CPF: {v['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {v['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {v['NOME DO BANCO']}",
        f"Agência: {v['NÚMERO DA AGÊNCIA']}",
        f"Conta: {v['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(dados: dict = Body(default=None)):
    if not isinstance(dados, dict):
        dados = {}
    v = {rotulo: _valor(dados, rotulo) for rotulo in ALIASES}
    docente = _e_docente(dados)
    erros = []

    obrigatorios = [
        rotulo
        for rotulo, alias in ALIASES.items()
        if alias not in OPCIONAIS and not (docente and alias in ("nivel", "tipo_auxilio"))
    ]
    if any(not v[rotulo] for rotulo in obrigatorios):
        erros.append("Preencha todos os campos")

    if v["N. USP"] and not v["N. USP"].isdigit():
        erros.append("N. USP deve conter apenas números")

    if v["NÚMERO DA AGÊNCIA"] and not v["NÚMERO DA AGÊNCIA"].isdigit():
        erros.append("Número da agência deve conter apenas números")

    centavos = None
    if v["VALOR SOLICITADO (R$)"]:
        centavos = _centavos(v["VALOR SOLICITADO (R$)"])
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
            centavos = None

    email = v["E-MAIL"]
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")

    if v["CPF (SEPARADOS POR PONTOS E TRAÇO)"]:
        cpf = v["CPF (SEPARADOS POR PONTOS E TRAÇO)"]
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    if v["CEP"] and not re.fullmatch(r"\d{5}-\d{3}", v["CEP"]):
        erros.append("CEP deve estar no formato 00000-000")

    if v["DATA DE NASCIMENTO"]:
        nascimento = v["DATA DE NASCIMENTO"]
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    if erros:
        return _({"erros": erros})
    return _({"oficio": _oficio(v, docente, centavos)})
