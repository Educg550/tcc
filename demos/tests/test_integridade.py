import asyncio
from pathlib import Path

import pytest

from harness.models.dominio import Alvo, Arquivo, Mudanca, Projeto, Requisito
from harness.models.etapas import CODIGO
from harness.models.harness import HarnessTDD
from harness.models.politicas import Batch
from harness.models.propostas import PropostaRejeitada

ALVO = Alvo(
    comando_app="app --port {porta}",
    comando_teste="pytest -q",
    python="3.11",
    pacotes=("pytest",),
)
MODELO = Path(__file__).parent.parent / "requisitos" / "00-exemplo-caso-de-uso"


def escrever(projeto, caminho, conteudo=""):
    return CODIGO.aplicar(
        Mudanca(arquivos=[Arquivo(caminho=caminho, conteudo=conteudo)]), projeto
    )


@pytest.fixture
def projeto(tmp_path):
    p = Projeto(tmp_path, ALVO)
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


def test_impressao_denuncia_adulteracao(projeto):
    antes = projeto.impressao()
    escrever(projeto, "app.py", "x = 1")
    assert projeto.impressao() == antes

    (projeto.raiz / "pytest.ini").write_text("[pytest]\naddopts = --ignore=tests\n")
    assert projeto.impressao() != antes


def test_run_nao_reaproveita_projeto(tmp_path):
    (tmp_path / "app.py").write_text("x = 1", encoding="utf-8")
    harness = HarnessTDD(Projeto(tmp_path, ALVO), Requisito(MODELO), Batch())

    # Projeto com arquivo dentro mediria manutenção, não a geração que se compara.
    with pytest.raises(SystemExit):
        asyncio.run(harness.executar())
