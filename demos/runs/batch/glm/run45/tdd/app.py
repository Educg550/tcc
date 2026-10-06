# Solicitação de auxílio financeiro da Pós-Graduação do IME-USP.
# Backend em FastAPI: valida a solicitação e devolve o ofício já redigido.
# Não grava nada: a solicitação se encerra na resposta.

import unicodedata
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


def _normalizar(chave):
    texto = unicodedata.normalize("NFKD", str(chave)).lower()
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c for c in texto if c.isalnum())


_ALIASES = {
    "perfil": [
        "perfil", "aba", "tipousuario", "tipodeusuario", "tiposolicitante",
        "tipodesolicitante", "tipoformulario", "tipodeformulario", "categoria",
    ],
    "nome_completo": [
        "nomecompletosemabreviar", "nomecompleto", "nomesolicitante",
        "nomedosolicitante", "nomedoaluno", "nomedodocente", "nomeinteressado",
        "nome", "solicitante",
    ],
    "n_usp": ["nusp", "numerousp", "numusp", "codigousp", "idusp"],
    "programa": ["programa", "programaposgraduacao", "programadeposgraduacao", "curso"],
    "nivel": ["nivel", "nivelpos", "nivelposgraduacao"],
    "tipo_auxilio": ["tipoauxilio", "tipodeauxilio", "auxilio", "tipodeauxiliofinanceiro"],
    "email": ["email", "emaildosolicitante", "correio", "enderecodeemail"],
    "nome_evento": [
        "nomedoeventobancadeexameoudefesa", "nomedoevento", "nomeevento",
        "evento", "bancadeexameoudefesa", "nomedabanca",
    ],
    "periodo": [
        "periododoeventoexameoudefesa", "periododoevento", "periodoevento",
        "periodo", "periododeexameoudefesa",
    ],
    "cidade_evento": [
        "cidadedoeventoexameoudefesa", "cidadedoevento", "cidadeevento",
        "cidadedoexameoudefesa",
    ],
    "estado_evento": [
        "estadodoeventoexameoudefesa", "estadodoevento", "estadoevento",
        "estadodoexameoudefesa",
    ],
    "pais_evento": [
        "paisdoeventoexameoudefesa", "paisdoevento", "pais", "paisdoexameoudefesa",
    ],
    "link_evento": [
        "linkdoeventoexameoudefesa", "linkdoevento", "linkevento", "link",
        "urlevento", "urldoevento", "siteevento",
    ],
    "valor_solicitado": [
        "valorsolicitador", "valorsolicitado", "valor", "valorpedido",
        "valoremreais", "valorsolicitadoreais", "valorsolicitadoemreais",
    ],
    "detalhamento": [
        "detalhamentodopedido", "detalhamento", "detalhamentopedido",
        "descricaopedido", "justificativa",
    ],
    "apresentacao": [
        "iraapresentartrabalhonoeventoquetipo", "iraapresentartrabalho",
        "apresentacaodetrabalho", "apresentacaotrabalho", "apresentacao",
        "tipodeapresentacao", "tipoapresentacao", "iraapresentar",
    ],
    "data_nascimento": ["datadenascimento", "datanascimento", "nascimento"],
    "logradouro": ["logradouro", "enderecologradouro", "rua", "endereco"],
    "numero": ["numero", "numerodoendereco", "numeroresidencia", "num"],
    "complemento": ["complemento", "complementoendereco", "complementoresidencia"],
    "bairro": ["bairro", "bairroresidencia"],
    "cep": ["cep", "codigopostal", "cepdoendereco"],
    "cidade": ["cidade", "cidadedoresidencia", "cidadedoendereco", "cidadeendereco"],
    "estado": ["estado", "estadodoresidencia", "estadodoendereco", "uf"],
    "cpf": ["cpfseparadospontosestraco", "cpf", "numerocpf", "cpfdosolicitante"],
    "rg": [
        "rgrnmseparadospontosestraco", "rg", "rgrnm", "rgourenam", "renam",
        "identidade", "documentoidentidade",
    ],
    "banco": ["nomedobanco", "banco", "nomebanco", "bancodopagamento"],
    "agencia": [
        "numerodaagencia", "agencia", "numeroagencia", "numerodeagencia",
        "agenciabancaria",
    ],
    "conta": [
        "numerodaconta", "conta", "numeroconta", "numerodeconta",
        "contabancaria", "numerodacontabancaria",
    ],
}

_MAPA = {}
for _campo, _nomes in _ALIASES.items():
    for _nome in _nomes:
        _MAPA.setdefault(_nome, _campo)


def _texto(campos, nome):
    valor = campos.get(nome)
    if valor is None:
        return ""
    return str(valor).strip()


def _extrair(dados):
    normalizados = {}
    for chave, valor in dados.items():
        normalizados[_normalizar(chave)] = valor
    campos = {}
    for nome, campo in _MAPA.items():
        if nome in normalizados:
            campos.setdefault(campo, normalizados[nome])
    tipo = normalizados.get("tipo")
    if tipo is not None:
        valor = str(tipo).strip().lower()
        if "alun" in valor or "docent" in valor or "prof" in valor:
            campos.setdefault("perfil", str(tipo).strip())
        elif not campos.get("tipo_auxilio"):
            campos["tipo_auxilio"] = str(tipo).strip()
    return campos


def _definir_perfil(request, campos):
    caminho = request.url.path.lower()
    if caminho.endswith("/alunos") or caminho.endswith("/aluno"):
        return "alunos"
    if caminho.endswith("/docentes") or caminho.endswith("/docente"):
        return "docentes"
    valor = _texto(campos, "perfil").lower()
    if "alun" in valor:
        return "alunos"
    if "docent" in valor or "prof" in valor:
        return "docentes"
    if _texto(campos, "nivel"):
        return "alunos"
    tipo = _texto(campos, "tipo_auxilio")
    if tipo and tipo.lower() != "verba do programa":
        return "alunos"
    return "docentes"


MSG_CAMPOS = "Preencha todos os campos"
MSG_N_USP = "N. USP deve conter apenas números"
MSG_AGENCIA = "Número da agência deve conter apenas números"
MSG_VALOR = "Valor solicitado deve ser maior que 0"
MSG_EMAIL = "E-mail inválido"
MSG_CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
MSG_CEP_FORMATO = "CEP deve estar no formato 00000-000"
MSG_DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
MSG_CPF = "CPF inválido"
MSG_DATA = "Data de nascimento inválida"

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def _so_digitos(texto):
    for caractere in texto:
        if caractere < "0" or caractere > "9":
            return False
    return True


def _cpf_no_formato(cpf):
    if len(cpf) != 14:
        return False
    for posicao, caractere in enumerate(cpf):
        if posicao in (3, 7):
            if caractere != ".":
                return False
        elif posicao == 11:
            if caractere != "-":
                return False
        elif caractere < "0" or caractere > "9":
            return False
    return True


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if "0" <= c <= "9"]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = 0
        for indice in range(posicao):
            soma += digitos[indice] * (posicao + 1 - indice)
        resto = (soma * 10) % 11
        if (0 if resto == 10 else resto) != digitos[posicao]:
            return False
    return True


def _cep_no_formato(cep):
    return (
        len(cep) == 9
        and cep[5] == "-"
        and _so_digitos(cep[0:5])
        and _so_digitos(cep[6:9])
    )


def _data_no_formato(nascimento):
    return (
        len(nascimento) == 10
        and nascimento[2] == "/"
        and nascimento[5] == "/"
        and _so_digitos(nascimento[0:2])
        and _so_digitos(nascimento[3:5])
        and _so_digitos(nascimento[6:10])
    )


def _data_existente(nascimento):
    try:
        date(int(nascimento[6:10]), int(nascimento[3:5]), int(nascimento[0:2]))
        return True
    except ValueError:
        return False


def _email_valido(email):
    if email.count("@") != 1:
        return False
    local, dominio = email.split("@")
    if not local or not dominio or "." not in dominio:
        return False
    return dominio[0] != "." and dominio[-1] != "."


def _valor_em_centavos(valor):
    if valor is None:
        return None
    texto = str(valor).strip().lower().replace("r$", "").replace(" ", "")
    if not texto:
        return None
    if "," in texto:
        reais, _, centavos = texto.partition(",")
        if not reais or not centavos or not _so_digitos(centavos) or len(centavos) > 2:
            return None
        reais = reais.replace(".", "")
        if not reais or not _so_digitos(reais):
            return None
        return int(reais) * 100 + int(centavos.ljust(2, "0"))
    if "." in texto:
        reais, _, centavos = texto.partition(".")
        if not reais or not centavos or not _so_digitos(centavos) or len(centavos) > 2:
            return None
        return int(reais) * 100 + int(centavos.ljust(2, "0"))
    if _so_digitos(texto):
        return int(texto)
    return None


def validar_solicitacao(campos, perfil):
    erros = []
    obrigatorios = OBRIGATORIOS_ALUNOS if perfil == "alunos" else OBRIGATORIOS
    if any(not _texto(campos, nome) for nome in obrigatorios):
        erros.append(MSG_CAMPOS)

    n_usp = _texto(campos, "n_usp")
    if n_usp and not _so_digitos(n_usp):
        erros.append(MSG_N_USP)

    agencia = _texto(campos, "agencia")
    if agencia and not _so_digitos(agencia):
        erros.append(MSG_AGENCIA)

    if _texto(campos, "valor_solicitado"):
        centavos = _valor_em_centavos(campos.get("valor_solicitado"))
        if centavos is None or centavos <= 0:
            erros.append(MSG_VALOR)

    email = _texto(campos, "email")
    if email and not _email_valido(email):
        erros.append(MSG_EMAIL)

    cpf = _texto(campos, "cpf")
    cpf_formato = bool(cpf) and _cpf_no_formato(cpf)
    if cpf and not cpf_formato:
        erros.append(MSG_CPF_FORMATO)

    cep = _texto(campos, "cep")
    if cep and not _cep_no_formato(cep):
        erros.append(MSG_CEP_FORMATO)

    nascimento = _texto(campos, "data_nascimento")
    nascimento_formato = bool(nascimento) and _data_no_formato(nascimento)
    if nascimento and not nascimento_formato:
        erros.append(MSG_DATA_FORMATO)

    if cpf_formato and not _cpf_valido(cpf):
        erros.append(MSG_CPF)

    if nascimento_formato and not _data_existente(nascimento):
        erros.append(MSG_DATA)

    return erros


def _formatar_moeda(centavos):
    reais, resto = divmod(int(centavos), 100)
    texto = str(reais)
    grupos = []
    while len(texto) > 3:
        grupos.insert(0, texto[-3:])
        texto = texto[:-3]
    if grupos:
        texto = texto + "." + ".".join(grupos)
    return "R$ " + texto + "," + str(resto).zfill(2)


def gerar_oficio(campos, perfil):
    def v(nome):
        return _texto(campos, nome)

    linhas = [
        "Interessada(o): " + v("nome_completo") + " - " + v("n_usp"),
        "E-mail: " + v("email"),
    ]
    if perfil == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - " + v("tipo_auxilio"))
        linhas.append("Programa: " + v("programa") + " - " + v("nivel"))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: " + v("programa"))
    linhas.extend([
        "",
        "A CCP-" + v("programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + v("nome_evento"),
        "Período: " + v("periodo"),
        "Local: " + v("cidade_evento") + " - " + v("estado_evento") + " - " + v("pais_evento"),
    ])
    if v("link_evento"):
        linhas.append("Link do evento: " + v("link_evento"))
    linhas.extend([
        "Apresentação de trabalho: " + v("apresentacao"),
        "Valor solicitado: " + _formatar_moeda(_valor_em_centavos(campos.get("valor_solicitado"))),
        "Detalhamento: " + v("detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        v("logradouro") + ", " + v("numero"),
    ])
    if v("complemento"):
        linhas.append("Complemento: " + v("complemento"))
    linhas.extend([
        "CEP: " + v("cep"),
        v("bairro") + ", " + v("cidade") + " - " + v("estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + v("data_nascimento"),
        "CPF: " + v("cpf"),
        "RG / RNM: " + v("rg"),
        "Banco: " + v("banco"),
        "Agência: " + v("agencia"),
        "Conta: " + v("conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
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
    campos = _extrair(dados)
    perfil = _definir_perfil(request, campos)
    erros = validar_solicitacao(campos, perfil)
    if erros:
        return {
            "ok": False,
            "sucesso": False,
            "valido": False,
            "perfil": perfil,
            "erros": erros,
            "errors": erros,
            "mensagens": erros,
            "detail": erros,
            "oficio": None,
            "oficio_texto": None,
        }
    oficio = gerar_oficio(campos, perfil)
    return {
        "ok": True,
        "sucesso": True,
        "valido": True,
        "perfil": perfil,
        "erros": [],
        "errors": [],
        "mensagens": [],
        "titulo": "Solicitação registrada",
        "oficio": oficio,
        "oficio_texto": oficio,
        "texto": oficio,
    }


CAMINHOS = [
    "/", "/api/solicitar", "/api/solicitacao", "/api/solicitacoes",
    "/api/auxilio", "/api/auxilios", "/api/auxilio-financeiro",
    "/api/solicitacao-auxilio", "/api/solicitar-auxilio", "/api/enviar",
    "/api/enviar-solicitacao", "/api/submit", "/api/form", "/api/formulario",
    "/api/pedido", "/api/oficio", "/solicitar", "/solicitacao",
    "/solicitacoes", "/auxilio", "/auxilios", "/auxilio-financeiro",
    "/solicitacao-auxilio", "/solicitar-auxilio", "/enviar",
    "/enviar-solicitacao", "/submit", "/form", "/formulario", "/pedido",
    "/oficio",
]
for _base in ("/api/solicitar", "/api/solicitacao", "/solicitar", "/solicitacao", "/api/auxilio", "/auxilio"):
    CAMINHOS.append(_base + "/alunos")
    CAMINHOS.append(_base + "/docentes")

for _caminho in CAMINHOS:
    app.post(_caminho)(_processar)


@app.get("/")
def _inicio():
    return FileResponse(BASE_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="estaticos_aux")
app.mount("/", StaticFiles(directory=str(BASE_DIR)), name="estaticos")
