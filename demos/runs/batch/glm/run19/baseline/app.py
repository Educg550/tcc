"""API de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def formulario() -> FileResponse:
    return FileResponse("index.html")


def _cpf_valido(cpf: str) -> bool:
    """Valida CPF conforme algoritmo oficial (nove dígitos + dois verificadores)."""
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11 or all(igual == digitos[0] for igual in digitos):
        return False
    for posicao in (9, 10):
        soma = sum(d * (posicao + 1 - i) for i, d in enumerate(digitos[:posicao]))
        resto = soma * 10 % 11
        if resto == 10:
            resto = 0
        if resto != digitos[posicao]:
            return False
    return True


def _dia_mes_ano(data: str) -> tuple[int, int, int] | None:
    """Separa e valida 'dd/mm/aaaa': retorna (dia, mês, ano) ou None se inválida."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data.strip())
    if not m:
        return None
    dia, mes, ano = (int(p) for p in m.groups())
    try:
        date(ano, mes, dia)
    except ValueError:
        return None
    return dia, mes, ano


def _valor_em_centavos(valor: str) -> int:
    return int(re.sub(r"\D", "", valor))


def _validar(dados: dict) -> list[str]:
    erros: list[str] = []
    docentes = dados.get("destino") == "docentes"
    obrigatorios = ["nome", "nusp", "programa", "email", "evento", "periodo",
                    "cidadeEvento", "estadoEvento", "paisEvento", "valor",
                    "detalhamento", "apresentacao", "logradouro", "numero", "bairro",
                    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
                    "conta", "nascimento"]
    if not docentes:
        obrigatorios += ["nivel", "tipo"]
    if any(not str(dados.get(campo, "")).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", dados.get("nusp", "")):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", dados.get("agencia", "")):
        erros.append("Número da agência deve conter apenas números")
    if _valor_em_centavos(dados.get("valor", "")) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados.get("email", "")):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados.get("cpf", "")):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", dados.get("cep", "")):
        erros.append("CEP deve estar no formato 00000-000")
    if not _dia_mes_ano(dados.get("nascimento", "")):
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados.get("nascimento", "")):
            erros.append("Data de nascimento inválida")
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    return erros


def _formatar_moeda(valor: str) -> str:
    digitos = str(_valor_em_centavos(valor)).zfill(3)
    return "R$ " + f"{int(digitos[:-2]):,}".replace(",", ".") + "," + digitos[-2:]


def _gerar_oficio(d: dict, hoje: str) -> str:
    linhas = [
        f"Interessada(o): {d['nome']} - {d['nusp']}",
        f"E-mail: {d['email']}",
        ("Assunto: Solicitação de Auxílio Financeiro - Verba do programa" if d.get("destino") == "docentes"
         else f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo']}"),
    ]
    if d.get("destino") == "docentes":
        linhas.append(f"Programa: {d['programa']}")
    else:
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    linhas += [
        "",
        f"A CCP-{d['programa']} aprovou na data de hoje, {hoje}, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['evento']}",
        f"Período: {d['periodo']}",
        f"Local: {d['cidadeEvento']} - {d['estadoEvento']} - {d['paisEvento']}",
    ]
    if d.get("link"):
        linhas.append(f"Link do evento: {d['link']}")
    linhas += [
        f"Apresentação de trabalho: {d['apresentacao']}",
        f"Valor solicitado: {_formatar_moeda(d['valor'])}",
        f"Detalhamento: {d['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d['logradouro']}, {d['numero']}",
    ]
    if d.get("complemento"):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas += [
        f"CEP: {d['cep']}",
        f"{d['bairro']}, {d['cidade']} - {d['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d['nascimento']}",
        f"CPF: {d['cpf']}",
        f"RG / RNM: {d['rg']}",
        f"Banco: {d['banco']}",
        f"Agência: {d['agencia']}",
        f"Conta: {d['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(dados: dict) -> dict:
    erros = _validar(dados)
    if erros:
        return {"erros": erros}
    hoje = date.today().strftime("%d/%m/%Y")
    return {"oficio": _gerar_oficio(dados, hoje)}
