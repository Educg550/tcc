import subprocess

import pytest

from caronte.piloto import ProjetoPiloto, REQUISITO, RUNTIME
from harness.models.dominio import Requisito


@pytest.mark.parametrize("grupo", ["tdd", "rework"])
def test_gate_http_roda_testes_sem_exigir_servidor_do_agente(tmp_path, grupo):
    if subprocess.run(["docker", "image", "inspect", RUNTIME], capture_output=True).returncode:
        pytest.skip("requer a imagem congelada do piloto")
    projeto = ProjetoPiloto(tmp_path, Requisito(REQUISITO).alvo, grupo)
    projeto.preparar()
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
    (tmp_path / "app.py").unlink()
    assert not projeto.rodar_pytest().passou
