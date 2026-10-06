import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import app as aplicacao
from helpers import post_solicitacao, texto_resposta


@pytest.fixture(scope='session')
def client():
    with TestClient(aplicacao.app, raise_server_exceptions=False) as cliente:
        yield cliente


@pytest.fixture(scope='session')
def solicitar(client):
    def enviar(dados, marcador):
        resposta = post_solicitacao(client, dados, marcador)
        assert resposta is not None, 'a aplicação não expõe nenhuma rota POST'
        return texto_resposta(resposta)

    return enviar
