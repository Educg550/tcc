import os
import re
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402

ARQUIVOS_ESTATICOS = {
    "/",
    "/index.html",
    "/style.css",
    "/app.js",
    "/favicon.ico",
    "/assets/usp-logo.png",
}

_VALORES = ["R$ 1.500,00", "150000", "1.500,00", "1500,00", "1500"]

_MARCADORES = {
    "alunos": [
        {},
        {"aba": "alunos"},
        {"aba": "ALUNOS"},
        {"tipo": "alunos"},
        {"tipo": "ALUNOS"},
        {"tipo": "aluno"},
        {"formulario": "alunos"},
        {"formulario": "ALUNOS"},
        {"tipo_solicitante": "alunos"},
        {"tipo_solicitante": "ALUNOS"},
        {"categoria": "alunos"},
        {"categoria": "ALUNOS"},
        {"origem": "alunos"},
        {"origem": "ALUNOS"},
        {"perfil": "alunos"},
        {"perfil": "ALUNOS"},
        {"solicitante": "alunos"},
        {"solicitante": "ALUNOS"},
    ],
    "docentes": [
        {},
        {"aba": "docentes"},
        {"aba": "DOCENTES"},
        {"tipo": "docentes"},
        {"tipo": "DOCENTES"},
        {"tipo": "docente"},
        {"formulario": "docentes"},
        {"formulario": "DOCENTES"},
        {"tipo_solicitante": "docentes"},
        {"tipo_solicitante": "DOCENTES"},
        {"categoria": "docentes"},
        {"categoria": "DOCENTES"},
        {"origem": "docentes"},
        {"origem": "DOCENTES"},
        {"perfil": "docentes"},
        {"perfil": "DOCENTES"},
        {"solicitante": "docentes"},
        {"solicitante": "DOCENTES"},
    ],
}

_NOMES_COMUNS = [
    "/solicitar",
    "/solicitacao",
    "/auxilio",
    "/api/solicitar",
    "/api/solicitacao",
    "/api/auxilio",
    "/submit",
    "/api/submit",
    "/enviar",
    "/api/enviar",
    "/solicitacoes",
    "/api/solicitacoes",
]

_ALIASES = {
    "NOME COMPLETO - SEM ABREVIAR": "nome_completo",
    "N. USP": "numero_usp",
    "PROGRAMA": "programa",
    "NÍVEL": "nivel",
    "TIPO DE AUXÍLIO": "tipo_auxilio",
    "E-MAIL": "email",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "nome_evento",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "periodo_evento",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "cidade_evento",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "estado_evento",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "pais_evento",
    "LINK DO EVENTO, EXAME OU DEFESA": "link_evento",
    "VALOR SOLICITADO (R$)": "valor_solicitado",
    "DETALHAMENTO DO PEDIDO": "detalhamento",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "apresentacao_trabalho",
    "DATA DE NASCIMENTO": "data_nascimento",
    "LOGRADOURO": "logradouro",
    "NÚMERO": "numero",
    "COMPLEMENTO": "complemento",
    "BAIRRO": "bairro",
    "CEP": "cep",
    "CIDADE": "cidade",
    "ESTADO": "estado",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "cpf",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "rg_rnm",
    "NOME DO BANCO": "nome_banco",
    "NÚMERO DA AGÊNCIA": "numero_agencia",
    "NÚMERO DA CONTA": "numero_conta",
}

_combinacoes = {}


def _com_alias(dados):
    for rotulo, valor in list(dados.items()):
        alias = _ALIASES.get(rotulo)
        if alias:
            dados[alias] = valor
    return dados


def payload_alunos(valor):
    return _com_alias({
        "NOME COMPLETO - SEM ABREVIAR": "Maria de Souza",
        "N. USP": "1234567",
        "PROGRAMA": "Ciência da Computação",
        "NÍVEL": "Mestrado",
        "TIPO DE AUXÍLIO": "Participação em evento",
        "E-MAIL": "maria@usp.br",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Computação",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/03/2025 a 14/03/2025",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "Gramado",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "RS",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://congresso.org.br",
        "VALOR SOLICITADO (R$)": valor,
        "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição no evento",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "DATA DE NASCIMENTO": "01/02/1980",
        "LOGRADOURO": "Rua do Anfiteatro",
        "NÚMERO": "181",
        "COMPLEMENTO": "Sala 10",
        "BAIRRO": "Butantã",
        "CEP": "05508-090",
        "CIDADE": "São Paulo",
        "ESTADO": "SP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "NOME DO BANCO": "Banco do Brasil",
        "NÚMERO DA AGÊNCIA": "1234",
        "NÚMERO DA CONTA": "98765-4",
    })


def payload_docentes(valor):
    dados = payload_alunos(valor)
    del dados["NÍVEL"]
    del dados["nivel"]
    del dados["TIPO DE AUXÍLIO"]
    del dados["tipo_auxilio"]
    return dados


def com(dados, mudancas):
    return _com_alias({**dados, **mudancas})


def enviar(client, endpoint, dados):
    resposta = client.post(endpoint, =dados)
    if resposta.status_code == 422:
        alternativa = client.post(endpoint, data=dados)
        if alternativa.status_code != 422:
            return alternativa
    return resposta


def _texto_js(client):
    html = client.get("/").text
    caminho = "/app.js"
    for referencia in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', html):
        if referencia.endswith("app.js"):
            caminho = referencia
            break
    return client.get(caminho).text


def _caminhos_candidatos(client):
    codigo = _texto_js(client) + "\n" + client.get("/").text
    padroes = [
        r'fetch\(\s*[`\'"]([^`\'"$]+)',
        r'\.open\(\s*[\'"][A-Z]+[\'"]\s*,\s*[`\'"]([^`\'"]+)',
        r'action\s*=\s*[\'"]([^\'"]+)',
        r'(?i)url\s*[:=]\s*[`\'"]([^`\'"]+)',
    ]
    candidatos = []
    for padrao in padroes:
        for achado in re.findall(padrao, codigo):
            achado = achado.split("${")[0].split("?")[0].strip()
            if not achado or achado.startswith(("http://", "https://", "#", "data:")):
                continue
            if not achado.startswith("/"):
                achado = "/" + achado
            if achado not in ARQUIVOS_ESTATICOS and achado not in candidatos:
                candidatos.append(achado)
    return candidatos


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def endpoint(client):
    reserva = None
    for caminho in _caminhos_candidatos(client) + _NOMES_COMUNS:
        resposta = client.post(caminho, ={})
        if resposta.status_code == 404:
            continue
        if "Preencha todos os campos" in resposta.text:
            return caminho
        if reserva is None:
            reserva = caminho
    if reserva is not None:
        return reserva
    pytest.fail("Não encontrei o endpoint que recebe a solicitação do formulário")


def _procurar_combinacao(client, endpoint, montar, aba):
    sinal = "Verba do programa" if aba == "docentes" else "Interessada(o):"
    for marcador in _MARCADORES[aba]:
        for valor in _VALORES:
            dados = {**montar(valor), **marcador}
            if sinal in enviar(client, endpoint, dados).text:
                return dados
    return {**montar(_VALORES[0]), **_MARCADORES[aba][0]}


@pytest.fixture(scope="session")
def base_alunos(client, endpoint):
    if "alunos" not in _combinacoes:
        _combinacoes["alunos"] = _procurar_combinacao(client, endpoint, payload_alunos, "alunos")
    return _combinacoes["alunos"]


@pytest.fixture(scope="session")
def base_docentes(client, endpoint):
    if "docentes" not in _combinacoes:
        _combinacoes["docentes"] = _procurar_combinacao(client, endpoint, payload_docentes, "docentes")
    return _combinacoes["docentes"]
