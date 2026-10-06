"""Backend do formulário de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE / "templates"))

BLOCOS = [
    (
        "SOLICITANTE E EVENTO",
        [
            {"n": "nome", "l": "NOME COMPLETO - SEM ABREVIAR", "t": "text", "p": "ex.: Maria da Silva", "w": "largo"},
            {"n": "n_usp", "l": "N. USP", "t": "text", "p": "ex.: 12345678"},
            {"n": "programa", "l": "PROGRAMA", "t": "text", "p": "ex.: Matemática"},
            {"n": "nivel", "l": "NÍVEL", "t": "select", "opts": ["Mestrado", "Doutorado"], "so": "alunos"},
            {"n": "tipo_auxilio", "l": "TIPO DE AUXÍLIO", "t": "select", "opts": ["Participação em evento", "Banca de exame ou defesa", "Outro"], "so": "alunos", "w": "largo"},
            {"n": "email", "l": "E-MAIL", "t": "email", "p": "ex.: maria@ime.usp.br"},
            {"n": "evento", "l": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "t": "text", "p": "ex.: Congresso Nacional de Matemática", "w": "largo"},
            {"n": "periodo", "l": "PERÍODO DO EVENTO, EXAME OU DEFESA", "t": "text", "p": "ex.: 10 a 12 de agosto de 2025"},
            {"n": "cidade", "l": "CIDADE DO EVENTO, EXAME OU DEFESA", "t": "text", "p": "ex.: São Paulo"},
            {"n": "estado", "l": "ESTADO DO EVENTO, EXAME OU DEFESA", "t": "text", "p": "ex.: SP"},
            {"n": "pais", "l": "PAÍS DO EVENTO, EXAME OU DEFESA", "t": "text", "p": "ex.: Brasil"},
            {"n": "link", "l": "LINK DO EVENTO, EXAME OU DEFESA", "t": "text", "p": "https://exemplo.com/congresso (opcional)", "opcional": True},
            {"n": "valor", "l": "VALOR SOLICITADO (R$)", "t": "text", "p": "ex.: 150000 (digitar só centavos)"},
            {"n": "detalhamento", "l": "DETALHAMENTO DO PEDIDO", "t": "textarea", "p": "ex.: Inscrição e hospedagem.", "w": "largo"},
            {"n": "apresentacao", "l": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "t": "select", "opts": ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"], "w": "largo"},
        ],
    ),
    (
        "ENDEREÇO DO SOLICITANTE",
        [
            {"n": "data_nascimento", "l": "DATA DE NASCIMENTO", "t": "text", "p": "ex.: 01021980"},
            {"n": "logradouro", "l": "LOGRADOURO", "t": "text", "p": "ex.: Rua do Matão", "w": "largo"},
            {"n": "numero", "l": "NÚMERO", "t": "text", "p": "ex.: 1010"},
            {"n": "complemento", "l": "COMPLEMENTO", "t": "text", "p": "ex.: Apto 12 (opcional)", "opcional": True},
            {"n": "bairro", "l": "BAIRRO", "t": "text", "p": "ex.: Butantã"},
            {"n": "cep", "l": "CEP", "t": "text", "p": "ex.: 05508090"},
            {"n": "endereco_cidade", "l": "CIDADE", "t": "text", "p": "ex.: São Paulo"},
            {"n": "endereco_estado", "l": "ESTADO", "t": "text", "p": "ex.: SP"},
        ],
    ),
    (
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        [
            {"n": "cpf", "l": "CPF (SEPARADOS POR PONTOS E TRAÇO)", "t": "text", "p": "ex.: 12345678909", "w": "largo"},
            {"n": "rg", "l": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "t": "text", "p": "ex.: 12.345.678-9", "w": "largo"},
            {"n": "banco", "l": "NOME DO BANCO", "t": "text", "p": "ex.: Banco do Brasil"},
            {"n": "agencia", "l": "NÚMERO DA AGÊNCIA", "t": "text", "p": "ex.: 1234"},
            {"n": "conta", "l": "NÚMERO DA CONTA", "t": "text", "p": "ex.: 98765-4"},
        ],
    ),
]
TODOS = [c for _, campos in BLOCOS for c in campos]


def _blocos_da_aba(aba):
    return [
        (titulo, [c for c in campos if not c.get("so") or c.get("so") == aba])
        for titulo, campos in BLOCOS
    ]


def _milhar(s):
    partes = []
    while len(s) > 3:
        partes.insert(0, s[-3:])
        s = s[:-3]
    partes.insert(0, s)
    return ".".join(partes)


def _moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return f"R$ {_milhar(str(reais))},{cent:02d}"


def _centavos(valor):
    v = str(valor).strip()
    if re.fullmatch(r"\d+", v):
        return int(v)
    m = re.fullmatch(r"R\$ ?(\d{1,3}(?:\.\d{3})*|\d+),(\d{2})", v)
    if m:
        return int(m.group(1).replace(".", "")) * 100 + int(m.group(2))
    return None


def _cpf_valido(d):
    if d == d[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10 % 11) % 10 != int(d[n]):
            return False
    return True


def _dias_do_mes(mes, ano):
    if not 1 <= mes <= 12:
        return None
    if mes == 2:
        return 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28
    return 30 if mes in (4, 6, 9, 11) else 31


def _validar_data(valor):
    v = str(valor).strip()
    if re.fullmatch(r"\d{8}", v):
        d = v
    elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", v):
        d = v.replace("/", "")
        if int(d[:2]) > 31 or not 1 <= int(d[2:4]) <= 12:
            return "formato"
    else:
        return "formato"
    dia, mes, ano = int(d[:2]), int(d[2:4]), int(d[4:])
    dias = _dias_do_mes(mes, ano)
    if dias is None or not 1 <= dia <= dias:
        return "invalida"
    return None


def _validar(v, obrigatorios):
    erros = []
    if any(not str(v.get(f, "")).strip() for f in obrigatorios):
        erros.append("Preencha todos os campos")
    if not str(v.get("n_usp", "")).strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    centavos = _centavos(v.get("valor", ""))
    if centavos is None or centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(v.get("email", ""))):
        erros.append("E-mail inválido")
    dc = re.sub(r"\D", "", str(v.get("cpf", "")))
    if len(dc) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(dc):
        erros.append("CPF inválido")
    if len(re.sub(r"\D", "", str(v.get("cep", "")))) != 8:
        erros.append("CEP deve estar no formato 00000-000")
    erro_data = _validar_data(v.get("data_nascimento", ""))
    if erro_data == "formato":
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif erro_data == "invalida":
        erros.append("Data de nascimento inválida")
    if not str(v.get("agencia", "")).strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    return erros


def _oficio(aba, v):
    def d(nome):
        return re.sub(r"\D", "", str(v[nome]))

    linhas = [
        f"Interessada(o): {v['nome']} - {v['n_usp']}",
        f"E-mail: {v['email']}",
    ]
    if aba == "alunos":
        linhas += [
            f"Assunto: Solicitação de Auxílio Financeiro - {v['tipo_auxilio']}",
            f"Programa: {v['programa']} - {v['nivel']}",
        ]
    else:
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {v['programa']}",
        ]
    linhas += [
        "",
        f"A CCP-{v['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['evento']}",
        f"Período: {v['periodo']}",
        f"Local: {v['cidade']} - {v['estado']} - {v['pais']}",
    ]
    if str(v.get("link", "")).strip():
        linhas.append(f"Link do evento: {v['link']}")
    linhas += [
        f"Apresentação de trabalho: {v['apresentacao']}",
        f"Valor solicitado: {_moeda(_centavos(v['valor']))}",
        f"Detalhamento: {v['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['logradouro']}, {v['numero']}",
    ]
    if str(v.get("complemento", "")).strip():
        linhas.append(f"Complemento: {v['complemento']}")
    dcep = d("cep")
    dcpf = d("cpf")
    dnasc = d("data_nascimento")
    linhas += [
        f"CEP: {dcep[:5]}-{dcep[5:]}",
        f"{v['bairro']}, {v['endereco_cidade']} - {v['endereco_estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dnasc[:2]}/{dnasc[2:4]}/{dnasc[4:]}",
        f"CPF: {dcpf[:3]}.{dcpf[3:6]}.{dcpf[6:9]}-{dcpf[9:]}",
        f"RG / RNM: {v['rg']}",
        f"Banco: {v['banco']}",
        f"Agência: {v['agencia']}",
        f"Conta: {v['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def style():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


@app.get("/assets/{nome}")
def asset(nome: str):
    return FileResponse(BASE / "assets" / nome)


@app.post("/solicitar")
async def solicitar(request: Request):
    form = await request.form()
    aba = "docentes" if form.get("aba") == "docentes" else "alunos"
    valores = {c["n"]: str(form.get(c["n"], "")) for c in TODOS}
    obrigatorios = [c["n"] for c in TODOS if not c.get("opcional") and not c.get("so")]
    if aba == "alunos":
        obrigatorios += [c["n"] for c in TODOS if c.get("so") == "alunos"]
    erros = _validar(valores, obrigatorios)
    if erros:
        return templates.TemplateResponse(
            request,
            "resposta.html",
            {"aba": aba, "erros": erros, "valores": valores, "blocos": _blocos_da_aba(aba)},
        )
    return templates.TemplateResponse(
        request, "resposta.html", {"aba": aba, "oficio": _oficio(aba, valores)}
    )
