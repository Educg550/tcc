import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

app = FastAPI()


class Solicitacao(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    aba: str = "alunos"

    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
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


def _cpf_valido(cpf: str) -> bool:
    nums = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(nums) != 11:
        return False
    for i in (9, 10):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != nums[i]:
            return False
    return True


def _data_valida(s: str) -> bool:
    try:
        d, m, a = (int(x) for x in s.split("/"))
        date(a, m, d)
    except (ValueError, TypeError):
        return False
    return True


def _valor_centavos(s: str) -> int:
    digitos = re.sub(r"\D", "", s)
    return int(digitos) if digitos else 0


def _formata_moeda(centavos: int) -> str:
    reais, cent = divmod(centavos, 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{cent:02d}"


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    alunos = s.aba == "alunos"

    obrigatorios = [
        "nome", "n_usp", "programa", "email", "nome_evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta",
    ]
    if alunos:
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not str(getattr(s, campo)).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not re.fullmatch(r"\d+", s.n_usp.strip()):
        erros.append("N. USP deve conter apenas números")

    if s.agencia.strip() and not re.fullmatch(r"\d+", s.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    if s.valor.strip() and _valor_centavos(s.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s.email.strip()):
        erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    dn = s.data_nascimento.strip()
    if dn:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dn):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(dn):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(s: Solicitacao) -> str:
    alunos = s.aba == "alunos"
    valor_fmt = _formata_moeda(_valor_centavos(s.valor))

    if alunos:
        assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa_linha = f"{s.programa} - {s.nivel}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = s.programa

    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
        f"Programa: {programa_linha}",
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
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
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(s)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
