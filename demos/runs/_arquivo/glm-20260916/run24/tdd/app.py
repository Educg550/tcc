import re
from datetime import datetime
from html import escape
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

IDENTIFICADOR = ("aba", "perfil", "tipo_solicitante")

CAMPOS = {
    "nome": ("nome_completo", "nome", "nomeCompleto", "NOME COMPLETO - SEM ABREVIAR"),
    "n_usp": ("n_usp", "numero_usp", "nUSP", "numeroUSP", "N. USP"),
    "programa": ("programa", "PROGRAMA"),
    "nivel": ("nivel", "NÍVEL"),
    "tipo_auxilio": ("tipo_de_auxilio", "tipo_auxilio", "tipoDeAuxilio", "TIPO DE AUXÍLIO"),
    "email": ("email", "e_mail", "E-MAIL"),
    "evento": ("nome_do_evento", "evento", "nomeDoEvento", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    "periodo": ("periodo", "periodo_do_evento", "periodoDoEvento", "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    "cidade_evento": ("cidade_do_evento", "cidade_evento", "cidadeDoEvento", "CIDADE DO EVENTO, EXAME OU DEFESA"),
    "estado_evento": ("estado_do_evento", "estado_evento", "estadoDoEvento", "ESTADO DO EVENTO, EXAME OU DEFESA"),
    "pais_evento": ("pais_do_evento", "pais_evento", "paisDoEvento", "PAÍS DO EVENTO, EXAME OU DEFESA"),
    "link_evento": ("link_do_evento", "link", "linkDoEvento", "LINK DO EVENTO, EXAME OU DEFESA"),
    "valor": ("valor_solicitado", "valor", "valorSolicitado", "VALOR SOLICITADO (R$)"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido", "detalhamentoDoPedido", "DETALHAMENTO DO PEDIDO"),
    "apresentacao": ("apresentacao_trabalho", "ira_apresentar_trabalho", "apresentacaoTrabalho", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
    "nascimento": ("data_de_nascimento", "data_nascimento", "dataDeNascimento", "DATA DE NASCIMENTO"),
    "logradouro": ("logradouro", "LOGRADOURO"),
    "numero_endereco": ("numero", "numero_endereco", "NÚMERO"),
    "complemento": ("complemento", "COMPLEMENTO"),
    "bairro": ("bairro", "BAIRRO"),
    "cep": ("cep", "CEP"),
    "cidade": ("cidade", "CIDADE"),
    "estado": ("estado", "ESTADO"),
    "cpf": ("cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
    "rg": ("rg", "rg_rnm", "rgRnm", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
    "banco": ("nome_do_banco", "banco", "nomeDoBanco", "NOME DO BANCO"),
    "agencia": ("agencia", "numero_da_agencia", "numeroDaAgencia", "NÚMERO DA AGÊNCIA"),
    "conta": ("numero_da_conta", "conta", "numeroDaConta", "NÚMERO DA CONTA"),
}

OPCIONAIS = {"link_evento", "complemento"}
SO_ALUNOS = {"nivel", "tipo_auxilio"}

app = FastAPI(title="Auxílio Financeiro — Pós-Graduação IME-USP")


def extrair(dados: dict, chaves) -> str:
    for chave in chaves:
        valor = dados.get(chave)
        if valor is None:
            continue
        texto = str(valor).strip()
        if texto:
            return texto
    return ""


def centavos(texto: str) -> int:
    return int(re.sub(r"\D", "", texto) or "0")


def formatar_moeda(texto: str) -> str:
    total = centavos(texto)
    return f"R$ {total // 100:,}".replace(",", ".") + f",{total % 100:02d}"


def email_valido(email: str) -> bool:
    local, separador, dominio = email.partition("@")
    if not separador or not local:
        return False
    rotulos = dominio.split(".")
    return len(rotulos) > 1 and all(rotulos)


def cpf_valido(cpf: str) -> bool:
    digitos = [int(d) for d in cpf if d.isdigit()]
    if len(digitos) != 11:
        return False
    base = digitos[:9]
    soma = sum(digito * peso for digito, peso in zip(base, range(10, 1, -1)))
    if (soma * 10) % 11 % 10 != digitos[9]:
        return False
    base.append(digitos[9])
    soma = sum(digito * peso for digito, peso in zip(base, range(11, 1, -1)))
    return (soma * 10) % 11 % 10 == digitos[10]


def validar(campos: dict, e_aluno: bool) -> list:
    erros = []
    obrigatorios = [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS and (e_aluno or campo not in SO_ALUNOS)
    ]
    if any(not campos[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if campos["n_usp"] and not campos["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if campos["agencia"] and not campos["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    if campos["valor"] and centavos(campos["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if campos["email"] and not email_valido(campos["email"]):
        erros.append("E-mail inválido")
    if campos["cpf"]:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", campos["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(campos["cpf"]):
            erros.append("CPF inválido")
    if campos["cep"] and not re.fullmatch(r"\d{5}-\d{3}", campos["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if campos["nascimento"]:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", campos["nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(campos["nascimento"], "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def montar_oficio(c: dict, e_aluno: bool) -> str:
    if e_aluno:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}"
        programa = f"Programa: {c['programa']} - {c['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c['programa']}"
    linhas = [
        f"Interessada(o): {c['nome']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link_evento"]:
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {formatar_moeda(c['valor'])}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero_endereco']}",
    ]
    if c["complemento"]:
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def ler_corpo(request: Request) -> dict:
    tipo = request.headers.get("content-type", "")
    try:
        if "" in tipo:
            dados = await request.()
        else:
            dados = dict(await request.form())
    except Exception:
        return {}
    return dados if isinstance(dados, dict) else {}


@app.get("/", response_class=HTMLResponse)
def pagina_inicial():
    return (RAIZ / "index.html").read_text(encoding="utf-8")


@app.get("/style.css")
def folha_de_estilo():
    return Response(
        (RAIZ / "style.css").read_text(encoding="utf-8"), media_type="text/css"
    )


@app.get("/app.js")
def roteiro():
    return Response(
        (RAIZ / "app.js").read_text(encoding="utf-8"), media_type="text/javascript"
    )


@app.post("/solicitar")
async def solicitar(request: Request):
    dados = await ler_corpo(request)
    e_aluno = extrair(dados, IDENTIFICADOR) != "docentes"
    campos = {campo: extrair(dados, chaves) for campo, chaves in CAMPOS.items()}
    erros = validar(campos, e_aluno)
    if erros:
        itens = "".join(f"<p>{escape(erro)}</p>" for erro in erros)
        return HTMLResponse(f'<div class="erros">{itens}</div>', status_code=422)
    oficio = montar_oficio(campos, e_aluno)
    return HTMLResponse(
        f'<h1>Solicitação registrada</h1>\n<pre class="oficio">{escape(oficio)}</pre>'
    )


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
