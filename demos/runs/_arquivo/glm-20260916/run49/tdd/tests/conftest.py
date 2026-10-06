import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def client():
    from app import app

    return TestClient(app)


@pytest.fixture
def dados_alunos():
    return {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "1234567",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@usp.br",
        "nome_evento": "Simpósio Brasileiro de Computação",
        "periodo_evento": "1 a 5 de julho de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.example.br",
        "valor_solicitado": "150000",
        "detalhamento": "Inscrição e passagens aéreas.",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Anfiteatro",
        "numero": "181",
        "complemento": "Sala 5",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "529.982.247-25",
        "rg_rnm": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "98765-4",
    }


@pytest.fixture
def dados_docentes():
    return {
        "aba": "docentes",
        "nome_completo": "João Pereira",
        "n_usp": "7654321",
        "programa": "Estatística",
        "email": "joao@ime.usp.br",
        "nome_evento": "Banca de defesa de mestrado",
        "periodo_evento": "10 de agosto de 2025",
        "cidade_evento": "Campinas",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor_solicitado": "30000",
        "detalhamento": "Reembolso de transporte.",
        "apresentacao_trabalho": "Não irá apresentar trabalho",
        "data_nascimento": "15/03/1975",
        "logradouro": "Av. Professor Lineu Prestes",
        "numero": "338",
        "complemento": "",
        "bairro": "Cidade Universitária",
        "cep": "05508-000",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "529.982.247-25",
        "rg_rnm": "98.765.432-1",
        "nome_banco": "Itaú",
        "numero_agencia": "0912",
        "numero_conta": "45678-9",
    }
