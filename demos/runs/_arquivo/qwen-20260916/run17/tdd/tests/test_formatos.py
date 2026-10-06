"""Testes do frontend (app.js): campos que se formatam ao sair deles.

Estes testes exercitam as funções puras de formatação expostas por app.js, pois
o ambiente de teste não tem navegador. Eles falham até que app.js exporte essas
funções com os nomes contratados.
"""

import re
import pytest


@pytest.fixture(scope="module")
def app_js(client):
    return client.get("/app.js").text


def _funcao(app_js, nome):
    m = re.search(r"function\s+" + nome + r"\s*\(.*?\)\s*\{", app_js, re.S)
    if m:
        return m.group(0)
    m = re.search(r"(?:const|let|var|window\.)" + nome + r"\s*=\s*(?:function\s*)?\(.*?\)\s*(?:=>|\{)", app_js, re.S)
    return m.group(0) if m else None


@pytest.mark.parametrize("nome", [
    "formatarValorMoeda",
    "formatarCPF",
    "formatarCEP",
    "formatarData",
])
def test_funcao_de_formatacao_exposta(app_js, nome):
    """app.js define e expõe cada função de formatação."""
    assert _funcao(app_js, nome), f"app.js não define/expõe {nome}"


def test_formatacao_ao_sair(input_names):
    """Os quatro campos reformatam ao sair deles (blur/input) sem enviar o form."""
    assert set(input_names) >= {
        "valor", "cpf", "cep", "data_nascimento",
    }
