import html
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


NOME = "Maria de Souza"
NUSP = "8765432"
PROGRAMA = "Ciência da Computação"
EMAIL = "maria.souza@usp.br"
EVENTO = "SBES 2025"
PERIODO = "20 a 24 de outubro de 2025"
CIDADE_EVENTO = "Salvador"
ESTADO_EVENTO = "BA"
PAIS_EVENTO = "Brasil"
LINK = "https://sbes2025.example.br"
VALOR = "R$ 1.500,00"
DETALHAMENTO = "Inscrição e passagens para o evento."
APRESENTACAO = "Pôster"
NASCIMENTO = "01/02/1990"
LOGRADOURO = "Rua do Anfiteatro"
NUMERO = "181"
COMPLEMENTO = "Sala 5"
BAIRRO = "Butantã"
CEP = "05508-090"
CIDADE = "São Paulo"
ESTADO = "SP"
CPF = "111.444.777-35"
RG = "12.345.678-9"
BANCO = "Banco do Brasil"
AGENCIA = "1234"
CONTA = "98765-4"

IDENTIFICADORES = (
    "aba",
    "perfil",
    "categoria",
    "tipo",
    "tipo_solicitante",
    "tipoSolicitante",
    "formulario",
)

GRUPOS = {
    "nome": {
        "NOME COMPLETO - SEM ABREVIAR": NOME,
        "nome completo - sem abreviar": NOME,
        "nome_completo": NOME,
        "nomeCompleto": NOME,
        "nome": NOME,
    },
    "nusp": {
        "N. USP": NUSP,
        "n. usp": NUSP,
        "n_usp": NUSP,
        "numero_usp": NUSP,
        "numeroUSP": NUSP,
        "nUSP": NUSP,
    },
    "programa": {"PROGRAMA": PROGRAMA, "programa": PROGRAMA},
    "nivel": {"NÍVEL": "Mestrado", "nivel": "Mestrado"},
    "tipo_auxilio": {
        "TIPO DE AUXÍLIO": "Participação em evento",
        "tipo de auxílio": "Participação em evento",
        "tipo_auxilio": "Participação em evento",
        "tipoAuxilio": "Participação em evento",
        "auxilio": "Participação em evento",
    },
    "email": {"E-MAIL": EMAIL, "e-mail": EMAIL, "email": EMAIL},
    "evento": {
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": EVENTO,
        "nome do evento / banca de exame ou defesa": EVENTO,
        "nome_evento": EVENTO,
        "nomeEvento": EVENTO,
        "evento": EVENTO,
    },
    "periodo": {
        "PERÍODO DO EVENTO, EXAME OU DEFESA": PERIODO,
        "periodo do evento, exame ou defesa": PERIODO,
        "periodo_evento": PERIODO,
        "periodoEvento": PERIODO,
        "periodo": PERIODO,
    },
    "cidade_evento": {
        "CIDADE DO EVENTO, EXAME OU DEFESA": CIDADE_EVENTO,
        "cidade do evento, exame ou defesa": CIDADE_EVENTO,
        "cidade_evento": CIDADE_EVENTO,
        "cidadeEvento": CIDADE_EVENTO,
    },
    "estado_evento": {
        "ESTADO DO EVENTO, EXAME OU DEFESA": ESTADO_EVENTO,
        "estado do evento, exame ou defesa": ESTADO_EVENTO,
        "estado_evento": ESTADO_EVENTO,
        "estadoEvento": ESTADO_EVENTO,
    },
    "pais_evento": {
        "PAÍS DO EVENTO, EXAME OU DEFESA": PAIS_EVENTO,
        "pais do evento, exame ou defesa": PAIS_EVENTO,
        "pais_evento": PAIS_EVENTO,
        "paisEvento": PAIS_EVENTO,
        "pais": PAIS_EVENTO,
    },
    "link": {
        "LINK DO EVENTO, EXAME OU DEFESA": LINK,
        "link do evento, exame ou defesa": LINK,
        "link_evento": LINK,
        "linkEvento": LINK,
        "link": LINK,
    },
    "valor": {
        "VALOR SOLICITADO (R$)": VALOR,
        "valor solicitado (r$)": VALOR,
        "valor_solicitado": VALOR,
        "valorSolicitado": VALOR,
        "valor": VALOR,
    },
    "detalhamento": {
        "DETALHAMENTO DO PEDIDO": DETALHAMENTO,
        "detalhamento do pedido": DETALHAMENTO,
        "detalhamento_pedido": DETALHAMENTO,
        "detalhamentoPedido": DETALHAMENTO,
        "detalhamento": DETALHAMENTO,
    },
    "apresentacao": {
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": APRESENTACAO,
        "irá apresentar trabalho no evento? que tipo?": APRESENTACAO,
        "apresentacao_trabalho": APRESENTACAO,
        "apresentacaoTrabalho": APRESENTACAO,
        "apresentacao": APRESENTACAO,
    },
    "nascimento": {
        "DATA DE NASCIMENTO": NASCIMENTO,
        "data de nascimento": NASCIMENTO,
        "data_nascimento": NASCIMENTO,
        "dataNascimento": NASCIMENTO,
        "data_de_nascimento": NASCIMENTO,
        "nascimento": NASCIMENTO,
    },
    "logradouro": {
        "LOGRADOURO": LOGRADOURO,
        "logradouro": LOGRADOURO,
        "endereco": LOGRADOURO,
        "endereço": LOGRADOURO,
    },
    "numero_endereco": {
        "NÚMERO": NUMERO,
        "número": NUMERO,
        "numero": NUMERO,
        "numero_endereco": NUMERO,
        "numero_logradouro": NUMERO,
    },
    "complemento": {"COMPLEMENTO": COMPLEMENTO, "complemento": COMPLEMENTO},
    "bairro": {"BAIRRO": BAIRRO, "bairro": BAIRRO},
    "cep": {"CEP": CEP, "cep": CEP},
    "cidade": {"CIDADE": CIDADE, "cidade": CIDADE},
    "estado": {"ESTADO": ESTADO, "estado": ESTADO},
    "cpf": {
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": CPF,
        "cpf (separados por pontos e traço)": CPF,
        "cpf": CPF,
    },
    "rg": {
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": RG,
        "rg / rnm (separados por pontos e traço)": RG,
        "rg_rnm": RG,
        "rgRnm": RG,
        "rg": RG,
        "rnm": RG,
    },
    "banco": {
        "NOME DO BANCO": BANCO,
        "nome do banco": BANCO,
        "nome_banco": BANCO,
        "nomeBanco": BANCO,
        "banco": BANCO,
    },
    "agencia": {
        "NÚMERO DA AGÊNCIA": AGENCIA,
        "número da agência": AGENCIA,
        "numero_agencia": AGENCIA,
        "numeroAgencia": AGENCIA,
        "agencia": AGENCIA,
    },
    "conta": {
        "NÚMERO DA CONTA": CONTA,
        "número da conta": CONTA,
        "numero_conta": CONTA,
        "numeroConta": CONTA,
        "conta": CONTA,
    },
}

CANDIDATOS = (
    "/api/solicitacao",
    "/solicitacao",
    "/api/solicitar",
    "/solicitar",
    "/api/enviar",
    "/enviar",
    "/api/submit",
    "/submit",
    "/api/solicitacoes",
    "/api/auxilio",
    "/auxilio",
    "/solicitar-auxilio",
    "/api/solicitar-auxilio",
    "/api/enviar-solicitacao",
    "/enviar-solicitacao",
    "/api/gerar-oficio",
    "/gerar-oficio",
    "/api/oficio",
    "/oficio",
    "/api/form",
    "/form",
    "/api",
    "/",
)

_estado = {}


def normalizar(texto):
    texto = html.unescape(texto)
    texto = texto.replace("\u00a0", " ")
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"[\u2010-\u2015\u2212]", "-", texto)
    return re.sub(r"\s+", " ", texto).casefold()


def contem(oficio, fragmento):
    if not oficio:
        return False
    return normalizar(fragmento) in normalizar(oficio)


def montar(aba, estilo="formatado", sem=(), trocas=None):
    trocas = dict(trocas or {})
    dados = {chave: aba for chave in IDENTIFICADORES}
    for grupo, variantes in GRUPOS.items():
        if aba == "DOCENTES" and grupo in ("nivel", "tipo_auxilio"):
            continue
        if grupo in sem:
            continue
        for chave, padrao in variantes.items():
            dados[chave] = padrao
    if estilo == "numerico" and "valor" not in sem:
        for chave in GRUPOS["valor"]:
            dados[chave] = 150000
    for grupo, valor in trocas.items():
        if grupo in GRUPOS:
            for chave in GRUPOS[grupo]:
                dados[chave] = valor
    return dados


def _linhas_de_erro(texto):
    if "interessada(o):" in normalizar(texto):
        return None
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    return linhas or None


def _listas_de_strings(dados):
    if isinstance(dados, list):
        if dados and all(isinstance(item, str) for item in dados):
            yield dados
        for item in dados:
            yield from _listas_de_strings(item)
    elif isinstance(dados, dict):
        for valor in dados.values():
            yield from _listas_de_strings(valor)


def achar_oficio(dados):
    if isinstance(dados, str):
        return dados if "interessada(o):" in normalizar(dados) else None
    if isinstance(dados, dict):
        for valor in dados.values():
            achado = achar_oficio(valor)
            if achado:
                return achado
    elif isinstance(dados, list):
        for item in dados:
            achado = achar_oficio(item)
            if achado:
                return achado
    return None


def achar_erros(dados):
    for lista in _listas_de_strings(dados):
        if lista:
            return [item.strip() for item in lista]
    if isinstance(dados, str):
        return _linhas_de_erro(dados)
    if isinstance(dados, dict):
        for valor in dados.values():
            if isinstance(valor, str):
                linhas = _linhas_de_erro(valor)
                if linhas:
                    return linhas
    return None


def _descobrir(client):
    if _estado:
        return _estado["caminho"], _estado["estilo"]
    for estilo in ("formatado", "numerico"):
        for caminho in CANDIDATOS:
            try:
                resposta = client.post(caminho, =montar("ALUNOS", estilo))
            except Exception:
                continue
            if resposta.status_code in (404, 405, 422):
                continue
            try:
                dados = resposta.()
            except ValueError:
                dados = resposta.text
            if achar_oficio(dados) is None and achar_erros(dados) is None:
                continue
            _estado["caminho"] = caminho
            _estado["estilo"] = estilo
            return caminho, estilo
    pytest.fail("Não encontrei o endpoint que recebe a solicitação")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    import app as backend

    return TestClient(backend.app)


@pytest.fixture(scope="session")
def codigo(client):
    partes = []
    for caminho in ("/", "/style.css", "/app.js"):
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            partes.append(resposta.text)
    return partes


@pytest.fixture
def solicitar(client):
    def _solicitar(aba="ALUNOS", sem=(), trocas=None):
        caminho, estilo = _descobrir(client)
        resposta = client.post(caminho, =montar(aba, estilo, sem, trocas))
        if resposta.status_code in (404, 405, 422):
            pytest.fail(f"POST {caminho} respondeu {resposta.status_code} para a aba {aba}")
        try:
            dados = resposta.()
        except ValueError:
            dados = resposta.text
        return achar_oficio(dados), achar_erros(dados)

    return _solicitar


@pytest.fixture
def estilo_solicitacao(client):
    def _estilo():
        _, estilo = _descobrir(client)
        return estilo

    return _estilo


@pytest.fixture
def normalizar():
    return normalizar


@pytest.fixture
def contem():
    return contem
