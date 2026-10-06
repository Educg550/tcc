import re
import unicodedata
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

ALIASES = {
    "nome": ("nome", "nomecompleto", "nome_completo", "nome_completo_sem_abreviar", "nome_do_solicitante"),
    "n_usp": ("n_usp", "nusp", "numero_usp", "num_usp", "cod_usp"),
    "programa": ("programa", "nome_do_programa"),
    "nivel": ("nivel", "nivel_do_aluno"),
    "tipo_auxilio": ("tipo_auxilio", "tipo_de_auxilio", "tipodeauxilio", "auxilio"),
    "email": ("email", "e_mail"),
    "evento": ("evento", "nome_do_evento", "nome_evento", "nome_do_evento_banca_de_exame_ou_defesa"),
    "periodo": ("periodo", "periodo_do_evento", "periodo_do_evento_exame_ou_defesa"),
    "cidade_evento": ("cidade_do_evento", "cidade_evento", "cidade_do_evento_exame_ou_defesa"),
    "estado_evento": ("estado_do_evento", "estado_evento", "estado_do_evento_exame_ou_defesa"),
    "pais_evento": ("pais_do_evento", "pais_evento", "pais_do_evento_exame_ou_defesa", "pais"),
    "link": ("link", "link_do_evento", "link_evento", "link_do_evento_exame_ou_defesa"),
    "valor": ("valor", "valor_solicitado", "valorsolicitado", "valor_solicitado_r", "valor_solicitado_rs"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido", "detalhes"),
    "apresentacao": ("apresentacao", "ira_apresentar_trabalho_no_evento_que_tipo", "apresentacao_de_trabalho", "ira_apresentar_trabalho"),
    "data_nascimento": ("data_de_nascimento", "data_nascimento", "datadenascimento"),
    "logradouro": ("logradouro",),
    "numero": ("numero", "num"),
    "complemento": ("complemento",),
    "bairro": ("bairro",),
    "cep": ("cep",),
    "cidade": ("cidade", "cidade_endereco", "cidade_do_solicitante"),
    "estado": ("estado", "estado_endereco", "estado_do_solicitante", "uf"),
    "cpf": ("cpf", "cpf_separados_por_pontos_e_traco"),
    "rg": ("rg", "rg_rnm", "rg_rnm_separados_por_pontos_e_traco"),
    "banco": ("banco", "nome_do_banco"),
    "agencia": ("agencia", "numero_da_agencia", "n_agencia"),
    "conta": ("conta", "numero_da_conta", "n_conta"),
}

OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
)

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_CPF = re.compile(r"^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$")
RE_CEP = re.compile(r"^[0-9]{5}-[0-9]{3}$")
RE_DATA = re.compile(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$")
RE_SO_DIGITOS = re.compile(r"^[0-9]+$")


def _chave(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^0-9A-Za-z]+", "_", texto).strip("_").lower()


def _so_digitos(texto):
    return re.sub(r"[^0-9]", "", str(texto))


def _cpf_valido(cpf):
    d = _so_digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * ((i + 1) - j) for j in range(i))
        resto = soma % 11
        if (0 if resto < 2 else 11 - resto) != int(d[i]):
            return False
    return True


def _data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _moeda(valor):
    total = int(_so_digitos(valor) or "0")
    reais, centavos = divmod(total, 100)
    return "R$ {},{:02d}".format("{:,}".format(reais).replace(",", "."), centavos)


def _coletar(dados):
    mapa = {}
    for chave, valor in dados.items():
        mapa[_chave(chave)] = "" if valor is None else str(valor).strip()
    campos = {}
    for campo, nomes in ALIASES.items():
        achado = ""
        for nome in nomes:
            if nome in mapa:
                achado = mapa[nome]
                if achado:
                    break
        campos[campo] = achado
    return campos, mapa


def _aba(mapa, campos):
    for nome in ("aba", "tipo", "tipo_solicitante", "solicitante", "perfil", "categoria"):
        if mapa.get(nome):
            return "docentes" if "doc" in mapa[nome].lower() else "alunos"
    return "alunos" if (campos["nivel"] or campos["tipo_auxilio"]) else "docentes"


def _erros(campos, aba):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not campos[c] for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if campos["n_usp"] and not RE_SO_DIGITOS.fullmatch(campos["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if campos["agencia"] and not RE_SO_DIGITOS.fullmatch(campos["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if campos["valor"] and int(_so_digitos(campos["valor"]) or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if campos["email"] and not RE_EMAIL.fullmatch(campos["email"]):
        erros.append("E-mail inválido")
    if campos["cpf"] and not RE_CPF.fullmatch(campos["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif campos["cpf"] and not _cpf_valido(campos["cpf"]):
        erros.append("CPF inválido")
    if campos["cep"] and not RE_CEP.fullmatch(campos["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if campos["data_nascimento"] and not RE_DATA.fullmatch(campos["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif campos["data_nascimento"] and not _data_valida(campos["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros


def _oficio(campos, aba):
    linhas = [
        "Interessada(o): {} - {}".format(campos["nome"], campos["n_usp"]),
        "E-mail: {}".format(campos["email"]),
    ]
    if aba == "docentes":
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            "Programa: {}".format(campos["programa"]),
        ]
    else:
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(campos["tipo_auxilio"]),
            "Programa: {} - {}".format(campos["programa"], campos["nivel"]),
        ]
    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(campos["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(campos["evento"]),
        "Período: {}".format(campos["periodo"]),
        "Local: {} - {} - {}".format(campos["cidade_evento"], campos["estado_evento"], campos["pais_evento"]),
    ]
    if campos["link"]:
        linhas.append("Link do evento: {}".format(campos["link"]))
    linhas += [
        "Apresentação de trabalho: {}".format(campos["apresentacao"]),
        "Valor solicitado: {}".format(_moeda(campos["valor"])),
        "Detalhamento: {}".format(campos["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(campos["logradouro"], campos["numero"]),
    ]
    if campos["complemento"]:
        linhas.append("Complemento: {}".format(campos["complemento"]))
    linhas += [
        "CEP: {}".format(campos["cep"]),
        "{}, {} - {}".format(campos["bairro"], campos["cidade"], campos["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(campos["data_nascimento"]),
        "CPF: {}".format(campos["cpf"]),
        "RG / RNM: {}".format(campos["rg"]),
        "Banco: {}".format(campos["banco"]),
        "Agência: {}".format(campos["agencia"]),
        "Conta: {}".format(campos["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def _processar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        try:
            dados = dict(await request.form())
        except Exception:
            dados = {}
    if not isinstance(dados, dict):
        dados = {}
    campos, mapa = _coletar(dados)
    aba = _aba(mapa, campos)
    erros = _erros(campos, aba)
    return {
        "ok": not erros,
        "aba": aba,
        "erros": erros,
        "mensagens": erros,
        "oficio": "" if erros else _oficio(campos, aba),
    }


@app.post("/")
@app.post("/solicitacao")
@app.post("/api/solicitacao")
@app.post("/enviar")
@app.post("/api/enviar")
@app.post("/submit")
async def solicitar_auxilio(request: Request):
    return await _processar(request)


app.mount("/", StaticFiles(directory=RAIZ, html=True), name="estaticos")
