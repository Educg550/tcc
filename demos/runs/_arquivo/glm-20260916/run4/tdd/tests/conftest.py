import copy
import 
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app  # noqa: E402

DADOS_ALUNO = {
    "ABA": "ALUNOS",
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBBD 2025",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "1 a 4 de outubro de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbbd.org.br",
    "VALOR SOLICITADO (R$)": "150000",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição no evento.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "181",
    "COMPLEMENTO": "Sala 214",
    "BAIRRO": "Cidade Universitária",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-04",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "98765-4",
}


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def post_path(client):
    esquema = client.get("/openapi.").()
    rotas = [c for c, metodos in esquema["paths"].items() if "post" in metodos]
    assert rotas, "o backend deve expor um endpoint POST para receber a solicitação"
    return rotas[0]


@pytest.fixture
def enviar(client, post_path):
    def _enviar(dados):
        return client.post(post_path, =dados)

    return _enviar


@pytest.fixture
def texto():
    def _texto(resposta):
        try:
            return .dumps(resposta.(), ensure_ascii=False)
        except ValueError:
            return resposta.text

    return _texto


@pytest.fixture
def dados_aluno():
    return copy.deepcopy(DADOS_ALUNO)


@pytest.fixture
def dados_docente(dados_aluno):
    dados = dados_aluno
    dados["ABA"] = "DOCENTES"
    del dados["NÍVEL"]
    del dados["TIPO DE AUXÍLIO"]
    return dados


@pytest.fixture(scope="session")
def html(client):
    return client.get("/").text


@pytest.fixture(scope="session")
def css(client):
    return client.get("/style.css").text


@pytest.fixture(scope="session")
def js(client):
    return client.get("/app.js").text
