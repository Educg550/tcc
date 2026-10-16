import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Lock
from unittest.mock import patch

from harness.batch import executar
from harness.models import Batch
from harness.models.harness import Harness


def test_batch_200_runs_sem_avaliacao_e_retomada():
    chamadas = []
    barreira = Barrier(25, timeout=10)
    lock = Lock()
    ativas = pico = 0

    async def simular(harness):
        nonlocal ativas, pico
        with lock:
            ativas += 1
            pico = max(pico, ativas)
        barreira.wait()
        assert not harness.com_cua
        assert isinstance(harness.permissao, Batch)
        assert not harness.projeto.raiz.exists()
        provider = harness.projeto.raiz.parts[-3]
        assert harness.requisito.id == f"01-formulario-docentes-{provider}"
        modelos = {
            "deepseek": "deepseek/deepseek-v4.1-flash",
            "glm": "z-ai/glm-5.3",
        }
        assert harness.requisito.modelos["coder"] == modelos[provider]
        assert harness.requisito.modelos["test_writer"] == modelos[provider]
        chamadas.append(harness.projeto.raiz)
        harness.projeto.preparar()
        (harness.projeto.saida / "RUN.log").write_text("{}")
        await asyncio.sleep(0.01)
        with lock:
            ativas -= 1

    with TemporaryDirectory() as pasta, patch.object(Harness, "executar", simular):
        destino = Path(pasta)
        incompleta = destino / "deepseek" / "run1" / "tdd"
        incompleta.mkdir(parents=True)
        (incompleta / "evidencia.txt").write_text("tentativa anterior")
        executar(destino)
        preservadas = list(incompleta.parent.glob("tdd-interrompida-*/tdd/evidencia.txt"))
        assert len(preservadas) == 1
        assert preservadas[0].read_text() == "tentativa anterior"
        esperado = {
            destino / provider / f"run{numero}" / grupo
            for provider in ("deepseek", "glm")
            for numero in range(1, 51)
            for grupo in ("tdd", "baseline")
        }
        assert len(chamadas) == 200
        assert set(chamadas) == esperado
        assert pico == 25
        executar(destino)
        assert len(chamadas) == 200
