"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Recebe a solicitação enviada, decide se ela é válida e devolve a página que a
tela precisa mostrar. Nada é gravado: a solicitação se encerra na resposta.
"""

import html
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

_RAIZ = Path(__file__).parent

_RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
_RE_CEP = re.compile(r"\d{5}-\d{3}")
_RE_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})")

_CAMPOS = (
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "cidade", "estado", "pais", "link", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "complemento",
    "bairro", "cep", "cidade_endereco", "estado_endereco", "cpf", "rg",
    "banco", "agencia", "conta",
)

_OPCOES = {
    "nivel": {"Mestrado": "sel_nivel_mestrado", "Doutorado": "sel_nivel_doutorado"},
    "tipo_auxilio": {
        "Participação em evento": "sel_auxilio_participacao",
        "Banca de exame ou defesa": "sel_auxilio_banca",
        "Outro": "sel_auxilio_outro",
    },
    "apresentacao": {
        "Pôster": "sel_apresentacao_poster",
        "Apresentação oral": "sel_apresentacao_oral",
        "Outra": "sel_apresentacao_outra",
        "Não irá apresentar trabalho": "sel_apresentacao_nao",
    },
}

_OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
    "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade_endereco", "estado_endereco", "cpf", "rg", "banco", "agencia",
    "conta",
)


def _centavos(valor: str) -> int:
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def _formatar_moeda(centavos: int) -> str:
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(d) for d in cpf if d.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(d * (posicao + 1 - peso) for peso, d in enumerate(digitos[:posicao]))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def _validar(dados: dict, tipo: str) -> list:
    erros = []
    obrigatorios = list(_OBRIGATORIOS)
    if tipo == "ALUNOS":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not dados.get(campo, "").strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados.get("n_usp", "")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("agencia", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("valor", "")
    if valor and _centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "")
    if email and (email.count("@") != 1 or not email.partition("@")[0] or not email.partition("@")[2]):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "")
    if cpf and not _RE_CPF.fullmatch(cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = dados.get("cep", "")
    if cep and not _RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("data_nascimento", "")
    if nascimento:
        partes = _RE_DATA.fullmatch(nascimento)
        if partes is None:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                date(int(partes[3]), int(partes[2]), int(partes[1]))
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def _oficio(dados: dict, tipo: str) -> str:
    e = html.escape
    linhas = [
        f"Interessada(o): {e(dados['nome'])} - {e(dados['n_usp'])}",
        f"E-mail: {e(dados['email'])}",
    ]
    if tipo == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {e(dados['programa'])}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {e(dados['tipo_auxilio'])}")
        linhas.append(f"Programa: {e(dados['programa'])} - {e(dados['nivel'])}")
    linhas += [
        "",
        f"A CCP-{e(dados['programa'])} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {e(dados['evento'])}",
        f"Período: {e(dados['periodo'])}",
        f"Local: {e(dados['cidade'])} - {e(dados['estado'])} - {e(dados['pais'])}",
    ]
    if dados.get("link"):
        linhas.append(f"Link do evento: {e(dados['link'])}")
    linhas += [
        f"Apresentação de trabalho: {e(dados['apresentacao'])}",
        f"Valor solicitado: {_formatar_moeda(_centavos(dados['valor']))}",
        f"Detalhamento: {e(dados['detalhamento'])}",
        "",
        "Endereço da(o) interessada(o)",
        f"{e(dados['logradouro'])}, {e(dados['numero'])}",
    ]
    if dados.get("complemento"):
        linhas.append(f"Complemento: {e(dados['complemento'])}")
    linhas += [
        f"CEP: {e(dados['cep'])}",
        f"{e(dados['bairro'])}, {e(dados['cidade_endereco'])} - {e(dados['estado_endereco'])}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {e(dados['data_nascimento'])}",
        f"CPF: {e(dados['cpf'])}",
        f"RG / RNM: {e(dados['rg'])}",
        f"Banco: {e(dados['banco'])}",
        f"Agência: {e(dados['agencia'])}",
        f"Conta: {e(dados['conta'])}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def _renderizar(dados: dict, tipo: str = "ALUNOS", erros: list | None = None, oficio: str | None = None) -> str:
    if oficio is None:
        secao_formulario, secao_confirmacao = "visivel", "oculto"
    else:
        secao_formulario, secao_confirmacao = "oculto", "visivel"

    trocas = {
        "{{" + campo + "}}": html.escape(dados.get(campo, ""), quote=True)
        for campo in _CAMPOS
    }
    for campo, opcoes in _OPCOES.items():
        valor = dados.get(campo, "")
        for rotulo, marcador in opcoes.items():
            trocas["{{" + marcador + "}}"] = " selected" if valor == rotulo else ""

    bloco = ""
    if erros:
        itens = "".join(f"<li>{html.escape(mensagem)}</li>" for mensagem in erros)
        bloco = f'<ul class="lista-erros">{itens}</ul>'

    alunos_ativo = tipo != "DOCENTES"
    trocas.update(
        {
            "{{classe_tab_alunos}}": "ativa" if alunos_ativo else "inativa",
            "{{classe_tab_docentes}}": "inativa" if alunos_ativo else "ativa",
            "{{aria_tab_alunos}}": "true" if alunos_ativo else "false",
            "{{aria_tab_docentes}}": "false" if alunos_ativo else "true",
            "{{classe_form_alunos}}": "visivel" if alunos_ativo else "oculto",
            "{{classe_form_docentes}}": "oculto" if alunos_ativo else "visivel",
            "{{erros_alunos}}": bloco if alunos_ativo else "",
            "{{erros_docentes}}": "" if alunos_ativo else bloco,
            "{{classe_secao_formulario}}": secao_formulario,
            "{{classe_secao_confirmacao}}": secao_confirmacao,
            "{{titulo_confirmacao}}": "Solicitação registrada" if oficio is not None else "",
            "{{oficio}}": oficio or "",
        }
    )

    pagina = (_RAIZ / "index.html").read_text(encoding="utf-8")
    for marcador, valor in trocas.items():
        pagina = pagina.replace(marcador, valor)
    return pagina


@app.get("/")
def pagina() -> HTMLResponse:
    return HTMLResponse(_renderizar({}, "ALUNOS"))


@app.post("/solicitacao")
async def solicitacao(request: Request) -> HTMLResponse:
    formulario = await request.form()
    dados = {chave: str(valor) for chave, valor in formulario.items()}
    tipo = dados.pop("tipo", "ALUNOS")
    if tipo not in ("ALUNOS", "DOCENTES"):
        tipo = "ALUNOS"
    erros = _validar(dados, tipo)
    if erros:
        return HTMLResponse(_renderizar(dados, tipo, erros))
    return HTMLResponse(_renderizar(dados, tipo, oficio=_oficio(dados, tipo)))


@app.get("/style.css")
def style_css() -> FileResponse:
    return FileResponse(_RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(_RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=_RAIZ / "assets"), name="assets")
