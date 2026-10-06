"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import html as html_lib
import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount(
    "/assets",
    StaticFiles(directory=str(BASE / "assets"), check_dir=False),
    name="assets",
)

CAMPOS = (
    "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor_solicitado", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
)
OPCIONAIS = ("link_evento", "complemento")
EXCLUSIVOS_ALUNOS = ("nivel", "tipo_auxilio")
OBRIGATORIOS = tuple(
    c for c in CAMPOS if c not in OPCIONAIS and c not in EXCLUSIVOS_ALUNOS
)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def _valor_numerico(valor: str):
    limpo = valor.replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _formatar_moeda(valor: float) -> str:
    reais, centavos = divmod(int(round(valor * 100)), 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{centavos:02d}"


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in _somente_digitos(cpf)]
    if len(numeros) != 11:
        return False
    for tamanho in (9, 10):
        soma = sum(n * (tamanho + 1 - i) for i, n in enumerate(numeros[:tamanho]))
        resto = (soma * 10) % 11
        digito = 0 if resto >= 10 else resto
        if digito != numeros[tamanho]:
            return False
    return True


def _eh_alunos(aba: str, dados: dict) -> bool:
    marcador = aba.strip().lower()
    if marcador == "docentes":
        return False
    if marcador == "alunos":
        return True
    return bool(dados["nivel"].strip() or dados["tipo_auxilio"].strip())


def _validar(dados: dict, alunos: bool) -> list:
    erros = []

    obrigatorios = list(OBRIGATORIOS)
    if alunos:
        obrigatorios += list(EXCLUSIVOS_ALUNOS)
    if any(not dados[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados["n_usp"].strip()
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = dados["agencia"].strip()
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = dados["valor_solicitado"].strip()
    if valor:
        numero = _valor_numerico(valor)
        if numero is None or numero <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados["email"].strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = dados["cpf"].strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados["cep"].strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados["data_nascimento"].strip()
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _montar_oficio(dados: dict, alunos: bool) -> str:
    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
    ]
    if alunos:
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        )
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")

    linhas += [
        "",
        "A CCP-" + dados["programa"]
        + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link_evento"].strip():
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {_formatar_moeda(_valor_numerico(dados['valor_solicitado']))}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"].strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def _cabecalho() -> str:
    return (
        '<header class="cabecalho">'
        '<span class="logo-caixa">'
        '<img class="logo" src="assets/usp-logo.png" '
        'alt="Logotipo da Universidade de São Paulo">'
        "</span>"
        '<div class="titulos">'
        '<span class="universidade">Universidade de São Paulo</span>'
        '<span class="programa">Pós-Graduação &ndash; Instituto de Matemática e Estatística</span>'
        "</div>"
        "</header>"
    )


def _pagina_confirmacao(oficio: str) -> str:
    return (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Solicitação registrada</title>\n"
        '<link rel="stylesheet" href="style.css">\n'
        "</head>\n<body class=\"pagina-confirmacao\">\n"
        + _cabecalho()
        + "\n<main>\n<h1>Solicitação registrada</h1>\n"
        + '<pre class="oficio">'
        + html_lib.escape(oficio)
        + "</pre>\n</main>\n</body>\n</html>\n"
    )


def _pagina_com_erros(dados: dict, alunos: bool, erros: list) -> HTMLResponse:
    pagina = (BASE / "index.html").read_text(encoding="utf-8")
    payload = json.dumps(
        {
            "aba": "alunos" if alunos else "docentes",
            "erros": erros,
            "valores": dados,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    script = f"<script>window.__resposta = {payload};</script>"
    return HTMLResponse(pagina.replace("</body>", script + "\n</body>"))


@app.post("/solicitacao")
def solicitar(
    nome_completo: str = Form(""),
    n_usp: str = Form(""),
    programa: str = Form(""),
    nivel: str = Form(""),
    tipo_auxilio: str = Form(""),
    email: str = Form(""),
    nome_evento: str = Form(""),
    periodo: str = Form(""),
    cidade_evento: str = Form(""),
    estado_evento: str = Form(""),
    pais_evento: str = Form(""),
    link_evento: str = Form(""),
    valor_solicitado: str = Form(""),
    detalhamento: str = Form(""),
    apresentacao: str = Form(""),
    data_nascimento: str = Form(""),
    logradouro: str = Form(""),
    numero: str = Form(""),
    complemento: str = Form(""),
    bairro: str = Form(""),
    cep: str = Form(""),
    cidade: str = Form(""),
    estado: str = Form(""),
    cpf: str = Form(""),
    rg: str = Form(""),
    banco: str = Form(""),
    agencia: str = Form(""),
    conta: str = Form(""),
    aba: str = Form(""),
) -> HTMLResponse:
    dados = {
        "nome_completo": nome_completo,
        "n_usp": n_usp,
        "programa": programa,
        "nivel": nivel,
        "tipo_auxilio": tipo_auxilio,
        "email": email,
        "nome_evento": nome_evento,
        "periodo": periodo,
        "cidade_evento": cidade_evento,
        "estado_evento": estado_evento,
        "pais_evento": pais_evento,
        "link_evento": link_evento,
        "valor_solicitado": valor_solicitado,
        "detalhamento": detalhamento,
        "apresentacao": apresentacao,
        "data_nascimento": data_nascimento,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cep": cep,
        "cidade": cidade,
        "estado": estado,
        "cpf": cpf,
        "rg": rg,
        "banco": banco,
        "agencia": agencia,
        "conta": conta,
    }

    alunos = _eh_alunos(aba, dados)
    erros = _validar(dados, alunos)
    if erros:
        return _pagina_com_erros(dados, alunos, erros)
    return HTMLResponse(_pagina_confirmacao(_montar_oficio(dados, alunos)))
