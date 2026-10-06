import re
import unicodedata
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

# Campo -> rótulo exato. Serve para aceitar tanto a chave curta quanto o rótulo do
# formulário como nome do campo enviado.
ROTULOS = {
    "nome": "NOME COMPLETO - SEM ABREVIAR",
    "n_usp": "N. USP",
    "programa": "PROGRAMA",
    "nivel": "NÍVEL",
    "tipo_auxilio": "TIPO DE AUXÍLIO",
    "email": "E-MAIL",
    "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "pais_evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "link_evento": "LINK DO EVENTO, EXAME OU DEFESA",
    "valor": "VALOR SOLICITADO (R$)",
    "detalhamento": "DETALHAMENTO DO PEDIDO",
    "apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "data_nascimento": "DATA DE NASCIMENTO",
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
}

OBRIGATORIOS = [
    "nome",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]

SOMENTE_ALUNOS = ["nivel", "tipo_auxilio"]


def _chave(texto):
    """Reduz um nome de campo a letras, dígitos e sublinhados."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


APELIDOS = {}
for _campo, _rotulo in ROTULOS.items():
    APELIDOS[_campo] = _campo
    APELIDOS[_chave(_rotulo)] = _campo
APELIDOS["aba"] = "aba"
APELIDOS["formulario"] = "aba"


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def _data_valida(texto):
    dia, mes, ano = texto.split("/")
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def _valor_em_reais(texto):
    """Aceita 'R$ 1.500,00' (moeda) ou só dígitos, que valem como centavos."""
    texto = texto.strip()
    if texto.startswith("R$"):
        numero = texto[2:].strip().replace(".", "").replace(",", ".")
        try:
            return float(numero)
        except ValueError:
            return None
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return None
    return int(digitos) / 100


def _moeda(valor):
    centavos = int(round(valor * 100))
    inteiros, resto = divmod(centavos, 100)
    return "R$ " + f"{inteiros:,}".replace(",", ".") + f",{resto:02d}"


def _validar(aba, dados):
    obrigatorios = list(OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += SOMENTE_ALUNOS

    n_usp = dados.get("n_usp", "")
    agencia = dados.get("agencia", "")
    valor_texto = dados.get("valor", "")
    email = dados.get("email", "")
    cpf = dados.get("cpf", "")
    cep = dados.get("cep", "")
    nascimento = dados.get("data_nascimento", "")

    valor = _valor_em_reais(valor_texto) if valor_texto else None
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    nascimento_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))

    erros = []
    if any(not dados.get(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if n_usp and not re.fullmatch(r"\d+", n_usp):
        erros.append("N. USP deve conter apenas números")
    if agencia and not re.fullmatch(r"\d+", agencia):
        erros.append("Número da agência deve conter apenas números")
    if valor_texto and (valor is None or valor <= 0 or valor != int(valor)):
        erros.append("Valor solicitado deve ser maior que 0")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf and cpf_no_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")
    if nascimento and nascimento_no_formato and not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def _oficio(aba, dados):
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")

    linhas += [
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio "
        "financeiro para a interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados.get("link_evento"):
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {_moeda(_valor_em_reais(dados['valor']))}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados.get("complemento"):
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def _corpo(request):
    if "json" in request.headers.get("content-type", ""):
        try:
            return await request.json()
        except ValueError:
            return {}
    return dict(await request.form())


@app.post("/api/solicitar")
async def solicitar(request: Request):
    corpo = await _corpo(request)
    dados = {}
    for bruto, enviado in corpo.items():
        campo = APELIDOS.get(_chave(str(bruto)))
        if campo:
            dados[campo] = "" if enviado is None else str(enviado).strip()

    aba = "docentes" if "doc" in dados.get("aba", "").lower() else "alunos"
    erros = _validar(aba, dados)
    if erros:
        return {"valido": False, "erros": erros, "oficio": ""}
    return {"valido": True, "erros": [], "oficio": _oficio(aba, dados)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="estaticos")
