import re
import struct
import zlib
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")
RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao_trabalho: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg_rnm: str = ""
    nome_banco: str = ""
    agencia: str = ""
    numero_conta: str = ""


OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "numero_conta",
)


def _moeda(texto):
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return "R$ 0,00"
    centavos = int(digitos)
    reais, centavos = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False

    def verificador(parte):
        soma = sum(int(d) * peso for d, peso in zip(parte, range(len(parte) + 1, 1, -1)))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    return (verificador(digitos[:9]) == int(digitos[9])
            and verificador(digitos[:10]) == int(digitos[10]))


def _oficio(s):
    if s.nivel.strip() or s.tipo_auxilio.strip():
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    linhas = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo_evento}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao_trabalho}",
        f"Valor solicitado: {_moeda(s.valor_solicitado)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg_rnm}",
        f"Banco: {s.nome_banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.numero_conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def receber_solicitacao(s: Solicitacao):
    erros = []
    if any(not getattr(s, campo).strip() for campo in OBRIGATORIOS) or (
            bool(s.nivel.strip() or s.tipo_auxilio.strip())
            and not (s.nivel.strip() and s.tipo_auxilio.strip())):
        erros.append("Preencha todos os campos")
    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor_solicitado.strip():
        digitos = re.sub(r"\D", "", s.valor_solicitado)
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if s.email.strip():
        partes = s.email.split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")
    if s.cpf.strip():
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(s.cpf):
            erros.append("CPF inválido")
    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_nascimento.strip():
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento.strip()):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(s.data_nascimento.strip(), "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(s)}


@app.get("/", response_class=HTMLResponse)
def pagina():
    return (RAIZ / "index.html").read_text(encoding="utf-8")


@app.get("/style.css")
def estilo():
    return Response((RAIZ / "style.css").read_text(encoding="utf-8"),
                    media_type="text/css")


@app.get("/app.js")
def script():
    return Response((RAIZ / "app.js").read_text(encoding="utf-8"),
                    media_type="application/javascript")


def _png_minimo():
    def pedaco(tipo, dados):
        return (struct.pack(">I", len(dados)) + tipo + dados
                + struct.pack(">I", zlib.crc32(tipo + dados)))

    cabecalho = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    imagem = zlib.compress(b"\x00\x10\x94\xab")
    return (b"\x89PNG\r\n\x1a\n" + pedaco(b"IHDR", cabecalho)
            + pedaco(b"IDAT", imagem) + pedaco(b"IEND", b""))


@app.get("/assets/usp-logo.png")
def logo():
    arquivo = RAIZ / "assets" / "usp-logo.png"
    dados = arquivo.read_bytes() if arquivo.exists() else _png_minimo()
    return Response(dados, media_type="image/png")
