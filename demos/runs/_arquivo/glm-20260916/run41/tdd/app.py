"""Backend do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Serve o frontend estático e processa a solicitação enviada: valida os dados e
devolve os erros ou o ofício redigido. Nada é gravado.
"""

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def javascript():
    return FileResponse(RAIZ / "app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


# Cada campo pode chegar com qualquer um destes nomes; o frontend usa o primeiro.
ALIASES = {
    "nome": ("nome_completo", "nome_completo_sem_abreviar", "nome",
             "NOME COMPLETO - SEM ABREVIAR"),
    "n_usp": ("n_usp", "num_usp", "numero_usp", "nusp", "N. USP"),
    "programa": ("programa", "PROGRAMA"),
    "nivel": ("nivel", "grau", "NÍVEL"),
    "tipo_auxilio": ("tipo_auxilio", "tipo_de_auxilio", "TIPO DE AUXÍLIO"),
    "email": ("email", "e_mail", "E-MAIL"),
    "nome_evento": ("nome_evento", "nome_do_evento", "evento",
                    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    "periodo": ("periodo_evento", "periodo_do_evento", "periodo",
                "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    "cidade_evento": ("cidade_evento", "cidade_do_evento",
                      "CIDADE DO EVENTO, EXAME OU DEFESA"),
    "estado_evento": ("estado_evento", "estado_do_evento",
                      "ESTADO DO EVENTO, EXAME OU DEFESA"),
    "pais_evento": ("pais_evento", "pais_do_evento",
                    "PAÍS DO EVENTO, EXAME OU DEFESA"),
    "link_evento": ("link_evento", "link_do_evento", "link", "url_evento",
                    "LINK DO EVENTO, EXAME OU DEFESA"),
    "valor": ("valor_solicitado", "valor", "VALOR SOLICITADO (R$)"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido",
                     "DETALHAMENTO DO PEDIDO"),
    "apresentacao": ("apresentacao", "apresentacao_trabalho", "tipo_apresentacao",
                     "ira_apresentar_trabalho",
                     "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
    "data_nascimento": ("data_nascimento", "data_de_nascimento",
                        "DATA DE NASCIMENTO"),
    "logradouro": ("logradouro", "endereco", "LOGRADOURO"),
    "numero": ("numero", "numero_endereco", "NUMERO"),
    "complemento": ("complemento", "COMPLEMENTO"),
    "bairro": ("bairro", "BAIRRO"),
    "cep": ("cep", "CEP"),
    "cidade": ("cidade", "CIDADE"),
    "estado": ("estado", "uf", "ESTADO"),
    "cpf": ("cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
    "rg": ("rg_rnm", "rg", "rnm", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
    "banco": ("nome_do_banco", "nome_banco", "banco", "NOME DO BANCO"),
    "agencia": ("numero_da_agencia", "numero_agencia", "agencia",
                "NÚMERO DA AGÊNCIA"),
    "conta": ("numero_da_conta", "numero_conta", "conta", "NÚMERO DA CONTA"),
}

OBRIGATORIOS = ("nome", "n_usp", "programa", "email", "nome_evento", "periodo",
                "cidade_evento", "estado_evento", "pais_evento", "valor",
                "detalhamento", "apresentacao", "data_nascimento", "logradouro",
                "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
                "banco", "agencia", "conta")


def _campo(dados, campo):
    for chave in ALIASES[campo]:
        valor = dados.get(chave)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def _parse_valor(texto):
    """Valor em centavos: dígitos puros são centavos; senão, número decimal."""
    t = texto.replace("R$", "").replace(" ", "")
    if not t:
        return None
    if t.isdigit():
        return int(t)
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    else:
        inteiro, _, decimal = t.rpartition(".")
        t = inteiro.replace(".", "") + "." + decimal if len(decimal) == 2 else t.replace(".", "")
    try:
        return round(float(t) * 100)
    except ValueError:
        return None


def _formata_valor(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _cpf_valido(digitos):
    def digito(base, peso):
        resto = sum(int(d) * (peso - i) for i, d in enumerate(base)) % 11
        return "0" if resto < 2 else str(11 - resto)

    nove = digitos[:9]
    primeiro = digito(nove, 10)
    return digitos[9] == primeiro and digitos[10] == digito(nove + primeiro, 11)


def _oficio(c, valor, cpf, cep, data, aluno):
    assunto = "Solicitação de Auxílio Financeiro - " + (
        c["tipo_auxilio"] if aluno else "Verba do programa")
    linhas = [
        f"Interessada(o): {c['nome']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        f"Assunto: {assunto}",
        "Programa: " + c["programa"] + (f" - {c['nivel']}" if aluno else ""),
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['nome_evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link_evento"]:
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c["complemento"]:
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {cep}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data}",
        f"CPF: {cpf}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def _validar_e_redigir(dados):
    c = {campo: _campo(dados, campo) for campo in ALIASES}
    aluno = bool(c["nivel"] or c["tipo_auxilio"])
    erros = []

    obrigatorios = OBRIGATORIOS + (("nivel", "tipo_auxilio") if aluno else ())
    if any(not c[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if c["n_usp"] and not c["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")

    if c["agencia"] and not c["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = None
    if c["valor"]:
        centavos = _parse_valor(c["valor"])
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
        else:
            valor = _formata_valor(centavos)

    if c["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", c["email"]):
        erros.append("E-mail inválido")

    cpf = None
    if c["cpf"]:
        if re.fullmatch(r"\d{11}", c["cpf"]):
            digitos = c["cpf"]
            cpf = f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
        elif re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", c["cpf"]):
            digitos = re.sub(r"\D", "", c["cpf"])
            cpf = c["cpf"]
        else:
            digitos = None
            erros.append("CPF deve estar no formato 000.000.000-00")
        if digitos and not _cpf_valido(digitos):
            erros.append("CPF inválido")

    cep = None
    if c["cep"]:
        if re.fullmatch(r"\d{8}", c["cep"]):
            cep = f"{c['cep'][:5]}-{c['cep'][5:]}"
        elif re.fullmatch(r"\d{5}-\d{3}", c["cep"]):
            cep = c["cep"]
        else:
            erros.append("CEP deve estar no formato 00000-000")

    data = None
    if c["data_nascimento"]:
        if re.fullmatch(r"\d{8}", c["data_nascimento"]):
            candidata = (f"{c['data_nascimento'][:2]}/{c['data_nascimento'][2:4]}"
                         f"/{c['data_nascimento'][4:]}")
        elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", c["data_nascimento"]):
            candidata = c["data_nascimento"]
        else:
            candidata = None
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        if candidata:
            try:
                datetime.strptime(candidata, "%d/%m/%Y")
                data = candidata
            except ValueError:
                erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(c, valor, cpf, cep, data, aluno)}


@app.post("/solicitacao")
async def solicitar(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    return JSONResponse(_validar_e_redigir(dados))
