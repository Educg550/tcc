import subprocess

import pytest

from caronte.piloto_v2 import REQUISITO, ProjetoV2
from harness.models.dominio import Requisito


def test_gate_tdd_roda_testes_http_contra_o_candidato_no_ambiente_v2(tmp_path):
    ativo = subprocess.run(["docker", "compose", "-p", "caronte-piloto-v2", "ps", "-q", "proxy"],
                           capture_output=True, text=True).stdout.strip()
    if not ativo:
        pytest.skip("requer o ambiente v2 de pé (caronte/piloto-v2/ambiente.py preparar)")
    projeto = ProjetoV2(tmp_path, Requisito(REQUISITO).alvo, "tdd")
    (tmp_path / "app.py").write_text(
        'from fastapi import FastAPI\napp = FastAPI()\n'
        '@app.get("/")\ndef root(): return {"message": "Hello World"}\n'
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_http.py").write_text(
        'import os\nimport httpx\n'
        'def test_api():\n'
        '    assert httpx.get(os.environ["CARONTE_API"]).json() == {"message": "Hello World"}\n'
        '    assert httpx.get(os.environ["CARONTE_API_SEM_ATALHO"]).status_code == 200\n'
    )
    assert projeto.rodar_pytest().passou
    (tmp_path / "app.py").write_text("from routers import auth\n")
    r = projeto.rodar_pytest()
    assert not r.passou and "nenhum teste foi executado" in r.saida
    assert "ModuleNotFoundError: No module named 'routers'" in r.saida
