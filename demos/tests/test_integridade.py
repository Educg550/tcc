import pytest

from harness.models.dominio import Alvo, Arquivo, Mudanca, Projeto
from harness.models.etapas import CODIGO
from harness.models.propostas import PropostaRejeitada

ALVO = Alvo(comando_app="app --port {porta}", comando_teste="pytest -q")


def escrever(projeto, caminho, conteudo=""):
    return CODIGO.aplicar(
        Mudanca(arquivos=[Arquivo(caminho=caminho, conteudo=conteudo)]), projeto
    )


@pytest.fixture
def projeto(tmp_path):
    p = Projeto(tmp_path, ALVO, "teste")
    p.preparar()
    (p.raiz / "tests").mkdir()
    (p.raiz / "tests" / "test_x.py").write_text("def test_x():\n    assert True\n")
    return p


@pytest.mark.parametrize(
    "caminho",
    [
        "tests/test_x.py",
        "pytest.ini",
        "conftest.py",
        "_harness/RUN.log",
        ".git/hooks/pre-commit",
    ],
)
def test_coder_nao_escreve_superficie_medida(projeto, caminho):
    assert isinstance(escrever(projeto, caminho), PropostaRejeitada)


def test_contexto_nao_devolve_a_medicao(projeto):
    escrever(projeto, "app.py", "x = 1")
    (projeto.saida / "RUN.log").write_text('{"total_cost_usd": 0.42}', encoding="utf-8")

    contexto = projeto.contexto()

    assert "app.py" in contexto
    assert "RUN.log" not in contexto
    assert "total_cost_usd" not in contexto


def test_impressao_denuncia_adulteracao(projeto):
    antes = projeto.impressao()
    escrever(projeto, "app.py", "x = 1")
    assert projeto.impressao() == antes

    (projeto.raiz / "pytest.ini").write_text("[pytest]\naddopts = --ignore=tests\n")
    assert projeto.impressao() != antes
