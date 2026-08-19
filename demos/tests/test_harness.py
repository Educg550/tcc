from pathlib import Path

import pytest

from harness.loop import escrever
from harness.models import Arquivo, Mudanca


def _m(*pares):
    return Mudanca(arquivos=[Arquivo(caminho=c, conteudo=t) for c, t in pares])


def test_escrever_grava_dentro_da_raiz(tmp_path):
    escritos = escrever(_m(("app.py", "x = 1"), ("templates/i.html", "<b>")), tmp_path)
    assert escritos == ["app.py", "templates/i.html"]
    assert (tmp_path / "app.py").read_text() == "x = 1"
    assert (tmp_path / "templates/i.html").read_text() == "<b>"


def test_escrever_rejeita_caminho_relativo_para_fora(tmp_path):
    with pytest.raises(ValueError):
        escrever(_m(("../fora.py", "mal")), tmp_path)
    assert not (tmp_path.parent / "fora.py").exists()


def test_escrever_rejeita_caminho_absoluto(tmp_path):
    alvo = tmp_path.parent / "absoluto.py"
    with pytest.raises(ValueError):
        escrever(_m((str(alvo), "mal")), tmp_path)
    assert not alvo.exists()


def test_escopo_restringe_a_um_subdiretorio(tmp_path):
    assert escrever(_m(("tests/test_a.py", "def test_a(): pass")), tmp_path, escopo="tests")
    with pytest.raises(ValueError):
        escrever(_m(("app.py", "codigo de producao")), tmp_path, escopo="tests")
    assert not (tmp_path / "app.py").exists()
