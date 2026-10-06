import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def enviar(client):
    caminhos = [
        rota.path
        for rota in app.routes
        if "POST" in (getattr(rota, "methods", None) or set())
    ]
    assert caminhos, "o backend não define nenhuma rota POST"

    def _enviar(payload):
        resposta = None
        for caminho in caminhos:
            tentativa = client.post(caminho, =payload)
            if tentativa.status_code not in (404, 405):
                resposta = tentativa
                break
        assert resposta is not None, "nenhuma rota POST aceitou a solicitação"
        return resposta

    return _enviar


def textos_da_resposta(resposta):
    def coletar(obj):
        if isinstance(obj, str):
            return [obj]
        if isinstance(obj, dict):
            return [pedaco for valor in obj.values() for pedaco in coletar(valor)]
        if isinstance(obj, (list, tuple)):
            return [pedaco for valor in obj for pedaco in coletar(valor)]
        return []

    try:
        dados = resposta.()
    except ValueError:
        dados = resposta.text
    return coletar(dados)


def texto_normalizado(resposta):
    return " ".join("\n".join(textos_da_resposta(resposta)).split())


def assert_erro(resposta, mensagens, ausentes=()):
    texto = texto_normalizado(resposta)
    for mensagem in mensagens:
        assert mensagem in texto, f"esperava a mensagem {mensagem!r}; resposta: {texto!r}"
    for ausente in ausentes:
        assert ausente not in texto, f"não esperava {ausente!r}; resposta: {texto!r}"
    assert "Interessada(o):" not in texto, "ofício gerado mesmo com erro"
    return texto


def assert_oficio(resposta, trechos):
    assert resposta.status_code < 400, f"status inesperado: {resposta.status_code}"
    texto = texto_normalizado(resposta)
    for trecho in trechos:
        assert trecho in texto, f"esperava no ofício {trecho!r}; resposta: {texto!r}"
    assert "Preencha todos os campos" not in texto
    return texto


ALUNOS_VALIDOS = {
    "aba": "ALUNOS",
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.silva@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Computação",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/09/2025 a 15/09/2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Rio de Janeiro",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "RJ",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.exemplo.org/2025",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Passagens aéreas e inscrição no evento.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "181",
    "COMPLEMENTO": "Biomédicas 4",
    "BAIRRO": "Cidade Universitária",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "98765-4",
}

DOCENTES_VALIDOS = {
    chave: valor
    for chave, valor in ALUNOS_VALIDOS.items()
    if chave not in ("aba", "NÍVEL", "TIPO DE AUXÍLIO")
}
DOCENTES_VALIDOS["aba"] = "DOCENTES"
