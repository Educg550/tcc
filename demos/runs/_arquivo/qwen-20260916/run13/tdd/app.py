"""Backend do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import re
import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS = [
    ("nome_completo", "Nome Completo - Sem Abreviar"),
    ("n_usp", "N. USP"),
    ("programa", "Programa"),
    ("nivel", "Nível"),
    ("tipo_auxilio", "Tipo de Auxílio"),
    ("email", "E-mail"),
    ("nome_evento", "Nome do Evento / Banca de Exame ou Defesa"),
    ("periodo_evento", "Período do Evento, Exame ou Defesa"),
    ("cidade_evento", "Cidade do Evento, Exame ou Defesa"),
    ("estado_evento", "Estado do Evento, Exame ou Defesa"),
    ("pais_evento", "País do Evento, Exame ou Defesa"),
    ("link_evento", "Link do Evento, Exame ou Defesa"),
    ("valor_solicitado", "Valor Solicitado (R$)"),
    ("detalhamento", "Detalhamento do Pedido"),
    ("apresentacao", "Irá Apresentar Trabalho no Evento? Que Tipo?"),
    ("data_nascimento", "Data de Nascimento"),
    ("logradouro", "Logradouro"),
    ("numero", "Número"),
    ("complemento", "Complemento"),
    ("bairro", "Bairro"),
    ("cep", "CEP"),
    ("cidade", "Cidade"),
    ("estado", "Estado"),
    ("cpf", "CPF (Separados por Pontos e Traço)"),
    ("rg_rnm", "RG / RNM (Separados por Pontos e Traço)"),
    ("nome_banco", "Nome do Banco"),
    ("numero_agencia", "Número da Agência"),
    ("numero_conta", "Número da Conta"),
]

ROTULOS = dict(CAMPOS)

OPCIONAIS = {"link_evento", "complemento"}

SO_ALUNOS = {"nivel", "tipo_auxilio"}


def _digitos(texto):
    return re.sub(r"\D", "", texto or "")


def _cpf_valido(cpf):
    for i in range(11):
        if cpf.count(cpf[i]) == 11:
            return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9)) % 11
    dig1 = 0 if soma < 2 else 11 - soma
    if dig1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10)) % 11
    dig2 = 0 if soma < 2 else 11 - soma
    return dig2 == int(cpf[10])


def _email_valido(email):
    if "@" not in email:
        return False
    _, _, dominio = email.rpartition("@")
    return "." in dominio.strip(".")


def _moeda(centavos):
    inteiro = int(centavos) // 100
    resto = int(centavos) % 100
    com_ponto = ""
    s = str(inteiro)
    while s:
        com_ponto = s[-3:] + com_ponto
        s = s[:-3]
        if s:
            com_ponto = "." + com_ponto
    return "R$ {0},{1:02d}".format(com_ponto, resto)


def validar(tipo, dados):
    erros = []
    aplicaveis = [chave for chave, _ in CAMPOS if not (tipo == "docentes" and chave in SO_ALUNOS)]
    if any(not (dados.get(chave) or "").strip() for chave in aplicaveis if chave not in OPCIONAIS):
        erros.append("Preencha todos os campos")
    if not (dados.get("n_usp") or "").isdigit():
        erros.append("N. USP deve conter apenas números")
    if not (dados.get("numero_agencia") or "").isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = _digitos(dados.get("valor_solicitado"))
    if not valor or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not _email_valido(dados.get("email") or ""):
        erros.append("E-mail inválido")
    cpf = dados.get("cpf") or ""
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(_digitos(cpf)):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", dados.get("cep") or ""):
        erros.append("CEP deve estar no formato 00000-000")
    data = dados.get("data_nascimento") or ""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = (int(p) for p in data.split("/"))
        try:
            datetime.date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(tipo, dados):
    linha = lambda rotulo, valor: "{} {}".format(rotulo, valor) if valor.strip() else None
    linhas = []
    linhas.append("Interessada(o): {} - {}".format(dados["nome_completo"], dados["n_usp"]))
    linhas.append("E-mail: {}".format(dados["email"]))
    if tipo == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(dados["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(dados["programa"], dados["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(dados["programa"]))
    linhas.append("")
    linhas.append("A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(dados["programa"]))
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: {}".format(dados["nome_evento"]))
    linhas.append("Período: {}".format(dados["periodo_evento"]))
    linhas.append("Local: {} - {} - {}".format(dados["cidade_evento"], dados["estado_evento"], dados["pais_evento"]))
    opt = linha("Link do evento:", dados["link_evento"])
    if opt:
        linhas.append(opt)
    linhas.append("Apresentação de trabalho: {}".format(dados["apresentacao"]))
    linhas.append("Valor solicitado: {}".format(_moeda(dados["valor_solicitado"])))
    linhas.append("Detalhamento: {}".format(dados["detalhamento"]))
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("{}, {}".format(dados["logradouro"], dados["numero"]))
    opt = linha("Complemento:", dados["complemento"])
    if opt:
        linhas.append(opt)
    linhas.append("CEP: {}".format(dados["cep"]))
    linhas.append("{}, {} - {}".format(dados["bairro"], dados["cidade"], dados["estado"]))
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: {}".format(dados["data_nascimento"]))
    linhas.append("CPF: {}".format(dados["cpf"]))
    linhas.append("RG / RNM: {}".format(dados["rg_rnm"]))
    linhas.append("Banco: {}".format(dados["nome_banco"]))
    linhas.append("Agência: {}".format(dados["numero_agencia"]))
    linhas.append("Conta: {}".format(dados["numero_conta"]))
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    tipo = dados.get("tipo") or "alunos"
    erros = validar(tipo, dados)
    return {"erros": erros, "oficio": "" if erros else gerar_oficio(tipo, dados)}


@app.get("/", response_class=HTMLResponse)
async def pagina_principal():
    with open("index.html", encoding="utf-8") as pagina:
        return pagina.read()


app.mount("/", StaticFiles(directory="."), name="estaticos")
