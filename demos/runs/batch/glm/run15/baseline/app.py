"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Recebe a solicitação enviada, decide se ela é válida e devolve ao frontend
os erros ou o ofício já redigido. Não grava nada.
"""
from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Campo(str):
    """String que lembra se veio vazia do frontend."""

    vazio: bool = False


class Solicitacao(BaseModel):
    perfil: str
    solicitante: dict[str, Campo]
    endereco: dict[str, Campo]
    pagamento: dict[str, Campo]


CAMPOS_OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}

ERRO_OBRIGATORIO = "Preencha todos os campos"

FORMATOS = {
    "N. USP": ("N. USP deve conter apenas números", str.isdigit),
    "NÚMERO DA AGÊNCIA": (
        "Número da agência deve conter apenas números",
        str.isdigit,
    ),
    "E-MAIL": ("E-mail inválido", email_valido),
    "VALOR SOLICITADO (R$)": ("Valor solicitado deve ser maior que 0", valor_positivo),
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": (
        "CPF deve estar no formato 000.000.000-00",
        padrao_cpf,
    ),
    "CEP": ("CEP deve estar no formato 00000-000", padrao_cep),
    "DATA DE NASCIMENTO": (
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        padrao_data,
    ),
}

DADOS_EVENTO = [
    ("Evento: ", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    ("Período: ", "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    ("Local: ", "CIDADE DO EVENTO, EXAME OU DEFESA"),
]

MASCARA_EVENTO = (
    "CEP: {}",
    "Data de nascimento: {}",
    "CPF: {}",
    "Agência: {}",
)


def valor_em_centavos(texto: str) -> int:
    """`R$ 1.234,56` -> 123456; -1 se não der para converter."""
    digitos = "".join(c for c in texto if c.isdigit())
    return int(digitos) if digitos else -1


def cpf_valido(cpf: str) -> bool:
    digitos = "".join(c for c in cpf if c.isdigit())
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    pesos = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    calculados = []
    for deslocamento in (0, 1):
        soma = sum(
            int(d) * p for d, p in zip(digitos[0 + deslocamento : 9 + deslocamento], pesos)
        )
        resto = soma * 10 % 11
        calculados.append("0" if resto == 10 else str(resto))
    return cpf.endswith("".join(calculados))


def data_valida(texto: str) -> bool:
    try:
        dia, mes, ano = (int(p) for p in texto.split("/"))
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


@app.post("/api/solicitacao")
def registrar(solicitacao: Solicitacao) -> dict[str, object]:
    blocos = (
        solicitacao.solicitante,
        solicitacao.endereco,
        solicitacao.pagamento,
    )

    faltando = [
        nome
        for bloco in blocos
        for nome, campo in bloco.items()
        if campo.vazio and nome not in CAMPOS_OPCIONAIS
    ]
    erros = [ERRO_OBRIGATORIO] if faltando else []

    for bloco in blocos:
        for nome, campo in bloco.items():
            if campo.vazio:
                continue
            mensagem, valido = FORMATOS.get(nome, (None, None))
            if valido and not valido(campo):
                erros.append(mensagem)

    cpf = solicitacao.pagamento.get("CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf and not cpf.vazio and padrao_cpf(cpf) and not cpf_valido(cpf):
        erros.append("CPF inválido")

    nascimento = solicitacao.endereco.get("DATA DE NASCIMENTO")
    if nascimento and not nascimento.vazio and padrao_data(nascimento) and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    return {"ok": True, "oficio": redigir(solicitacao, blocos)}


def linha_se_preenchido(rotulo: str, nome: str, blocos) -> str:
    campo = next(b[nome] for b in blocos if nome in b)
    return "{}: {}".format(rotulo, campo) if not campo.vazio else ""


def campo(nome: str, blocos) -> str:
    return str(next(b[nome] for b in blocos if nome in b))


def redigir(solicitacao: Solicitacao, blocos) -> str:
    perfil = solicitacao.perfil
    get = lambda nome: campo(nome, blocos)

    if perfil == "ALUNOS":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - {}".format(get("TIPO DE AUXÍLIO"))
        programa = "Programa: {} - {}".format(get("PROGRAMA"), get("NÍVEL"))
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: {}".format(get("PROGRAMA"))

    p = solicitacao.pagamento
    s = solicitacao.solicitante
    e = solicitacao.endereco

    linhas = [
        "Interessada(o): {} - {}".format(get("NOME COMPLETO - SEM ABREVIAR"), get("N. USP")),
        "E-mail: {}".format(get("E-MAIL")),
        assunto,
        programa,
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(get("PROGRAMA")),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
    ]
    linhas += ["{}{}".format(rotulo, get(nome)) for rotulo, nome in DADOS_EVENTO]
    linhas += [
        "Link do evento: {}".format(get("LINK DO EVENTO, EXAME OU DEFESA")) if not s["LINK DO EVENTO, EXAME OU DEFESA"].vazio else "",
    ]
    linhas += [
        "Apresentação de trabalho: {}".format(get("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?")),
        "Valor solicitado: {}".format(get("VALOR SOLICITADO (R$)")),
        "Detalhamento: {}".format(get("DETALHAMENTO DO PEDIDO")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(get("LOGRADOURO"), get("NÚMERO")),
        "Complemento: {}".format(get("COMPLEMENTO")) if not e["COMPLEMENTO"].vazio else "",
        "CEP: {}".format(get("CEP")),
        "{}, {} - {}".format(get("BAIRRO"), get("CIDADE"), get("ESTADO")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(get("DATA DE NASCIMENTO")),
        "CPF: {}".format(get("CPF (SEPARADOS POR PONTOS E TRAÇO)")),
        "RG / RNM: {}".format(get("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)")),
        "Banco: {}".format(get("NOME DO BANCO")),
        "Agência: {}".format(get("NÚMERO DA AGÊNCIA")),
        "Conta: {}".format(get("NÚMERO DA CONTA")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linha for linha in linhas if linha != "")


app.mount("/", StaticFiles(directory="static", html=True), name="static")
