"""Testes para o backend de validação e geração do ofício."""

import pytest
from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


@pytest.fixture(scope="module")
def student_data():
    return {
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria.silva@usp.br",
        "nome_do_evento": "Congresso Nacional de Matemática",
        "periodo_do_evento": "10 a 15 de agosto de 2025",
        "cidade_do_evento": "São Paulo",
        "estado_do_evento": "SP",
        "pais_do_evento": "Brasil",
        "link_do_evento": "https://exemplo.com.br",
        "valor_solicitado": "150000",
        "detalhamento_do_pedido": "Inscrição no evento",
        "apresentar_trabalho": "Pôster",
        "data_de_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "567890-1",
    }
