"""Fixtures compartilhadas pelos testes do formulário de auxílio financeiro."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


# Dados válidos para a aba ALUNOS (todos os campos obrigatórios preenchidos).
# Os campos auto-formatados já são enviados no formato final, pois é o backend
# que valida. Valor digitado `1500` (centavos) vira `R$ 15,00` na tela.
DADOS_BASE = {
    "nome": "Maria Silva Souza",
    "num_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso de Computação",
    "periodo": "10 a 12 de maio de 2026",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://exemplo.com/evento",
    "valor": "R$ 15,00",
    "detalhamento": "Necessito de auxílio para inscrição e transporte.",
    "apresentar": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Avenida Professor Luciano Gualberto",
    "numero": "100",
    "complemento": "Apto 10",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

# Campos que pertencem à aba DOCENTES, em relação à base de ALUNOS
# (a aba DOCENTES não tem NÍVEL nem TIPO DE AUXÍLIO).
DOCENTES_SUBSET = [
    "nome", "num_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "link_evento", "valor",
    "detalhamento", "apresentar", "data_nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


def alunos_payload(**over):
    d = dict(DADOS_BASE)
    d.update(over)
    return d


def docentes_payload(**over):
    d = {k: DADOS_BASE[k] for k in DOCENTES_SUBSET}
    d.update(over)
    return d
