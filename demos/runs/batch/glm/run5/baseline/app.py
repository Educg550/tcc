import calendar
import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Form(BaseModel):
    aba: str
    nome: str
    nusp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link: str
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


LABELS = {
    "aluno": {
        "nome": "NOME COMPLETO - SEM ABREVIAR",
        "nusp": "N. USP",
        "programa": "PROGRAMA",
        "nivel": "NÍVEL",
        "tipo_auxilio": "TIPO DE AUXÍLIO",
        "email": "E-MAIL",
        "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
        "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
        "pais_evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
        "link": "LINK DO EVENTO, EXAME OU DEFESA",
        "valor": "VALOR SOLICITADO (R$)",
        "detalhamento": "DETALHAMENTO DO PEDIDO",
        "apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "nascimento": "DATA DE NASCIMENTO",
        "logradouro": "LOGRADOURO",
        "numero": "NÚMERO",
        "complemento": "COMPLEMENTO",
        "bairro": "BAIRRO",
        "cep": "CEP",
        "cidade": "CIDADE",
        "estado": "ESTADO",
        "cpf": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "rg": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "banco": "NOME DO BANCO",
        "agencia": "NÚMERO DA AGÊNCIA",
        "conta": "NÚMERO DA CONTA",
    },
    "docente": {
        "nome": "NOME COMPLETO - SEM ABREVIAR",
        "nusp": "N. USP",
        "programa": "PROGRAMA",
        "nivel": "",
        "tipo_auxilio": "",
        "email": "E-MAIL",
        "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
        "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
        "pais_evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
        "link": "LINK DO EVENTO, EXAME OU DEFESA",
        "valor": "VALOR SOLICITADO (R$)",
        "detalhamento": "DETALHAMENTO DO PEDIDO",
        "apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "nascimento": "DATA DE NASCIMENTO",
        "logradouro": "LOGRADOURO",
        "numero": "NÚMERO",
        "complemento": "COMPLEMENTO",
        "bairro": "BAIRRO",
        "cep": "CEP",
        "cidade": "CIDADE",
        "estado": "ESTADO",
        "cpf": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "rg": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "banco": "NOME DO BANCO",
        "agencia": "NÚMERO DA AGÊNCIA",
        "conta": "NÚMERO DA CONTA",
    },
}

OBRIGATORIOS = [
    "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
    "conta",
]

OBRIGATORIOS_DOCENTE = [
    f for f in OBRIGATORIOS if f not in ("nivel", "tipo_auxilio")
]


def valida_cpf(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    soma1 = sum(d * w for d, w in zip(digitos[:9], range(10, 1, -1)))
    dv1 = (soma1 * 10) % 11
    if dv1 == 10:
        dv1 = 0
    if dv1 != digitos[9]:
        return False
    soma2 = sum(d * w for d, w in zip(digitos[:10], range(11, 1, -1)))
    dv2 = (soma2 * 10) % 11
    if dv2 == 10:
        dv2 = 0
    return dv2 == digitos[10]


def data_valida(texto: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto):
        return False
    dia, mes, ano = (int(p) for p in texto.split("/"))
    if mes < 1 or mes > 12:
        return False
    return 1 <= dia <= calendar.monthrange(ano, mes)[1]


def valor_maior_que_zero(valor: str) -> bool:
    digitos = "".join(c for c in valor if c.isdigit())
    if not digitos:
        return False
    return int(digitos) > 0


def email_valido(email: str) -> bool:
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def gera_oficio(data: Form) -> str:
    labels = LABELS[data.aba]
    valor = data.valor
    linhas = []
    linhas.append(
        f"Interessada(o): {data.nome} - {data.nusp}"
    )
    linhas.append(f"E-mail: {data.email}")
    if data.aba == "aluno":
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {data.tipo_auxilio}"
        )
        linhas.append(f"Programa: {data.programa} - {data.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {data.programa}")
    linhas.append("")
    linhas.append(
        "A CCP-" + data.programa
        + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {data.evento}")
    linhas.append(f"Período: {data.periodo}")
    linhas.append(
        f"Local: {data.cidade_evento} - {data.estado_evento} - {data.pais_evento}"
    )
    if data.link:
        linhas.append(f"Link do evento: {data.link}")
    linhas.append(f"Apresentação de trabalho: {data.apresentacao}")
    linhas.append(f"Valor solicitado: {valor}")
    linhas.append(f"Detalhamento: {data.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{data.logradouro}, {data.numero}")
    if data.complemento:
        linhas.append(f"Complemento: {data.complemento}")
    linhas.append(f"CEP: {data.cep}")
    linhas.append(f"{data.bairro}, {data.cidade} - {data.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {data.nascimento}")
    linhas.append(f"CPF: {data.cpf}")
    linhas.append(f"RG / RNM: {data.rg}")
    linhas.append(f"Banco: {data.banco}")
    linhas.append(f"Agência: {data.agencia}")
    linhas.append(f"Conta: {data.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def submeter(data: Form):
    obrig = OBRIGATORIOS_DOCENTE if data.aba == "docente" else OBRIGATORIOS
    erros = []
    faltando = [
        LABELS[data.aba][campo] for campo in obrig if not data.dict()[campo].strip()
    ]
    if faltando:
        erros.append("Preencha todos os campos")
    if not data.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not data.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not valor_maior_que_zero(data.valor):
        erros.append("Valor solicitado deve ser maior que 0")
    if not email_valido(data.email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", data.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    if not re.fullmatch(r"\d{5}-\d{3}", data.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if (
        re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", data.cpf)
        and not valida_cpf(data.cpf)
    ):
        erros.append("CPF inválido")
    if (
        re.fullmatch(r"\d{2}/\d{2}/\d{4}", data.nascimento)
        and not data_valida(data.nascimento)
    ):
        erros.append("Data de nascimento inválida")
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gera_oficio(data)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
