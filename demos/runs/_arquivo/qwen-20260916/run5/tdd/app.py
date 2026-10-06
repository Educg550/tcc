from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

BASE = Path(__file__).resolve().parent
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
app.mount("/", StaticFiles(directory=BASE, html=True), name="static")


class Solicitacao(BaseModel):
    aba: str
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


def _validate(s):
    erros = []

    required = [
        s.nome_completo, s.n_usp, s.programa, s.email,
        s.nome_evento, s.periodo_evento, s.cidade_evento,
        s.estado_evento, s.pais_evento, s.valor_solicitado,
        s.detalhamento, s.apresentacao, s.data_nascimento,
        s.logradouro, s.numero, s.bairro, s.cep,
        s.cidade, s.estado, s.cpf, s.rg, s.banco, s.agencia, s.conta,
    ]
    if s.aba == "alunos":
        required.extend([s.nivel, s.tipo_auxilio])

    if any(not v or not v.strip() for v in required):
        erros.append("Preencha todos os campos")

    if s.n_usp and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    if s.valor_solicitado:
        t = s.valor_solicitado.replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            v = float(t)
            if v <= 0 or v != int(v):
                erros.append("Valor solicitado deve ser maior que 0")
        except Exception:
            erros.append("Valor solicitado deve ser maior que 0")

    if s.email and ("@" not in s.email or not s.email.split("@")[-1]):
        erros.append("E-mail inválido")

    if s.cpf:
        import re
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            d = [int(c) for c in s.cpf if c.isdigit()]
            def dv(base):
                p = sum(d[i] * base[i] for i in range(len(base))) % 11
                return 0 if p < 2 else 11 - p
            def check1():
                return dv([10, 9, 8, 7, 6, 5, 4, 3, 2])
            def check2():
                return dv([11, 10, 9, 8, 7, 6, 5, 4, 3, 2])
            if not (check1() == d[9] and check2() == d[10]):
                erros.append("CPF inválido")

    if s.cep:
        import re
        if not re.fullmatch(r"\d{5}-\d{3}", s.cep):
            erros.append("CEP deve estar no formato 00000-000")

    if s.data_nascimento:
        import re
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(x) for x in s.data_nascimento.split("/"))
            dias = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if not (1 <= mes <= 12 and 1 <= dia <= dias[mes - 1]):
                erros.append("Data de nascimento inválida")

    return erros


def _build(s):
    if s.aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        prog = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        prog = f"Programa: {s.programa}"

    lines = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
        prog,
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo_evento}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]

    if s.link_evento.strip():
        lines.append(f"Link do evento: {s.link_evento}")

    lines.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {s.valor_solicitado}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])

    if s.complemento.strip():
        lines.append(f"Complemento: {s.complemento}")

    lines.extend([
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])

    return "\n".join(lines)


@app.post("/solicitacao")
def solicitacao(s: Solicitacao):
    erros = _validate(s)
    if erros:
        return JSONResponse({"erros": erros}, status_code=400)
    return {"oficio": _build(s)}