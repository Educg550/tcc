import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PASTA = Path(__file__).resolve().parent
STATIC = PASTA / "static"

SO_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]
OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str
    campos: dict


def texto(campos, chave):
    valor = campos.get(chave, "")
    return "" if valor is None else str(valor).strip()


def apenas_digitos(valor):
    return re.sub(r"\D", "", valor)


def cpf_valido(digitos):
    if digitos == digitos[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        if soma * 10 % 11 % 10 != int(digitos[posicao]):
            return False
    return True


def valida_data(valor):
    casou = re.fullmatch(r"(\d{2})(\d{2})(\d{4})", valor)
    if not casou:
        return "Data de nascimento deve estar no formato dd/mm/aaaa"
    dia, mes, ano = (int(parte) for parte in casou.groups())
    try:
        date(ano, mes, dia)
    except ValueError:
        return "Data de nascimento inválida"
    return None


def validar(tipo, campos):
    erros = []
    obrigatorios = OBRIGATORIOS + (SO_ALUNOS if tipo == "alunos" else [])
    if any(not texto(campos, chave) for chave in obrigatorios):
        erros.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", texto(campos, "N. USP")):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", texto(campos, "NÚMERO DA AGÊNCIA")):
        erros.append("Número da agência deve conter apenas números")
    centavos = apenas_digitos(texto(campos, "VALOR SOLICITADO (R$)"))
    if not centavos or int(centavos) == 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", texto(campos, "E-MAIL")):
        erros.append("E-mail inválido")
    cpf = apenas_digitos(texto(campos, "CPF (SEPARADOS POR PONTOS E TRAÇO)"))
    if len(cpf) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(cpf):
        erros.append("CPF inválido")
    if len(apenas_digitos(texto(campos, "CEP"))) != 8:
        erros.append("CEP deve estar no formato 00000-000")
    erro_data = valida_data(texto(campos, "DATA DE NASCIMENTO"))
    if erro_data:
        erros.append(erro_data)
    return erros


def moeda(centavos):
    return f"R$ {centavos // 100:,}".replace(",", ".") + f",{centavos % 100:02d}"


def gerar_oficio(tipo, campos):
    def v(chave):
        return texto(campos, chave)

    centavos = int(apenas_digitos(v("VALOR SOLICITADO (R$)")))
    cpf = apenas_digitos(v("CPF (SEPARADOS POR PONTOS E TRAÇO)"))
    cep = apenas_digitos(v("CEP"))
    nascimento = apenas_digitos(v("DATA DE NASCIMENTO"))
    assunto = v("TIPO DE AUXÍLIO") if tipo == "alunos" else "Verba do programa"
    nivel = f" - {v('NÍVEL')}" if tipo == "alunos" else ""
    linhas = [
        f"Interessada(o): {v('NOME COMPLETO - SEM ABREVIAR')} - {v('N. USP')}",
        f"E-mail: {v('E-MAIL')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {v('PROGRAMA')}{nivel}",
        "",
        f"A CCP-{v('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {v('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {v('CIDADE DO EVENTO, EXAME OU DEFESA')} - {v('ESTADO DO EVENTO, EXAME OU DEFESA')} - {v('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    if v("LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append(f"Link do evento: {v('LINK DO EVENTO, EXAME OU DEFESA')}")
    linhas += [
        f"Apresentação de trabalho: {v('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {moeda(centavos)}",
        f"Detalhamento: {v('DETALHAMENTO DO PEDIDO')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v('LOGRADOURO')}, {v('NÚMERO')}",
    ]
    if v("COMPLEMENTO"):
        linhas.append(f"Complemento: {v('COMPLEMENTO')}")
    linhas += [
        f"CEP: {cep[:5]}-{cep[5:]}",
        f"{v('BAIRRO')}, {v('CIDADE')} - {v('ESTADO')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {nascimento[:2]}/{nascimento[2:4]}/{nascimento[4:]}",
        f"CPF: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}",
        f"RG / RNM: {v('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {v('NOME DO BANCO')}",
        f"Agência: {v('NÚMERO DA AGÊNCIA')}",
        f"Conta: {v('NÚMERO DA CONTA')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(solicitacao: Solicitacao):
    erros = validar(solicitacao.tipo, solicitacao.campos)
    return {
        "erros": erros,
        "oficio": "" if erros else gerar_oficio(solicitacao.tipo, solicitacao.campos),
    }


@app.get("/")
def pagina_inicial():
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount("/assets", StaticFiles(directory=PASTA / "assets"), name="assets")
