import calendar
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()



def _txt(dados, campo):
    return str(dados.get(campo) or "").strip()



def _valor_valido(valor):
    v = valor.replace("R$", "").strip()
    v = re.sub(r"[^0-9,.]", "", v)
    if not v:
        return False
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(".", "")
    try:
        return float(v) > 0
    except ValueError:
        return False



def _formatar_valor(valor):
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return valor
    reais, centavos = divmod(int(digitos), 100)
    inteiros = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiros},{centavos:02d}"



def _cpf_valido(cpf):
    n = [int(c) for c in cpf if c.isdigit()]
    if len(n) != 11:
        return False
    for tam in (9, 10):
        soma = sum(n[i] * (tam + 1 - i) for i in range(tam))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != n[tam]:
            return False
    return True



def _data_valida(data):
    dia = int(data[0:2])
    mes = int(data[3:5])
    ano = int(data[6:10])
    if not 1 <= mes <= 12 or dia < 1:
        return False
    return dia <= calendar.monthrange(ano, mes)[1]



def _validar(dados):
    alunos = dados.get("aba") == "alunos"
    erros = []

    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email",
        "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
        "valor", "detalhamento", "apresentacao",
        "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade_endereco", "estado_endereco",
        "cpf", "rg", "banco", "agencia", "conta",
    ]
    if alunos:
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not _txt(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _txt(dados, "n_usp")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = _txt(dados, "agencia")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = _txt(dados, "valor")
    if valor and not _valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _txt(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = _txt(dados, "cpf")
    cpf_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf))
    if cpf and not cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = _txt(dados, "cep")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _txt(dados, "data_nascimento")
    nascimento_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento))
    if nascimento and not nascimento_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato and not _cpf_valido(cpf):
        erros.append("CPF inv\u00e1lido")

    if nascimento_formato and not _data_valida(nascimento):
        erros.append("Data de nascimento inv\u00e1lida")

    return erros



def _gerar_oficio(dados):
    alunos = dados.get("aba") == "alunos"
    programa = _txt(dados, "programa")

    linhas = [
        f"Interessada(o): {_txt(dados, 'nome_completo')} - {_txt(dados, 'n_usp')}",
        f"E-mail: {_txt(dados, 'email')}",
    ]
    if alunos:
        linhas.append(
            f"Assunto: Solicitac\u0327a\u0303o de Aux\u00edlio Financeiro - {_txt(dados, 'tipo_auxilio')}"
        )
        linhas.append(f"Programa: {programa} - {_txt(dados, 'nivel')}")
    else:
        linhas.append("Assunto: Solicitac\u0327a\u0303o de Aux\u00edlio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")

    linhas += [
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitac\u0327a\u0303o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_txt(dados, 'nome_evento')}",
        f"Per\u00edodo: {_txt(dados, 'periodo')}",
        f"Local: {_txt(dados, 'cidade_evento')} - {_txt(dados, 'estado_evento')} - {_txt(dados, 'pais_evento')}",
    ]

    link = _txt(dados, "link_evento")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentac\u0327a\u0303o de trabalho: {_txt(dados, 'apresentacao')}",
        f"Valor solicitado: {_formatar_valor(_txt(dados, 'valor'))}",
        f"Detalhamento: {_txt(dados, 'detalhamento')}",
        "",
        "Enderec\u0327o da(o) interessada(o)",
        f"{_txt(dados, 'logradouro')}, {_txt(dados, 'numero')}",
    ]

    complemento = _txt(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {_txt(dados, 'cep')}",
        f"{_txt(dados, 'bairro')}, {_txt(dados, 'cidade_endereco')} - {_txt(dados, 'estado_endereco')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_txt(dados, 'data_nascimento')}",
        f"CPF: {_txt(dados, 'cpf')}",
        f"RG / RNM: {_txt(dados, 'rg')}",
        f"Banco: {_txt(dados, 'banco')}",
        f"Ag\u00eancia: {_txt(dados, 'agencia')}",
        f"Conta: {_txt(dados, 'conta')}",
        "",
        "Encaminhe-se ao Servic\u0327o Financeiro para provid\u00eancias.",
    ]

    return "\n".join(linhas)



@app.post("/api/solicitacao")
async def solicitar(requisicao: Request):
    dados = await requisicao.json()
    erros = _validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _gerar_oficio(dados)}



@app.get("/")
async def raiz():
    return FileResponse(BASE / "index.html")



@app.get("/style.css")
async def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")



@app.get("/app.js")
async def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")



app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
