import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from browser_use import Agent, ChatOpenAI

from .agents import MODEL_CUA, load
from .models import VeredictoCUA

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@contextmanager
def app_rodando(projeto: Path):
    """Sobe `app.py` do projeto num subprocesso e devolve a URL. Sempre derruba."""
    porta = porta_livre()
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(projeto),
        env={**os.environ, "PORT": str(porta)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    url = f"http://localhost:{porta}"
    try:
        for _ in range(50):
            if proc.poll() is not None:
                raise RuntimeError(f"app morreu ao subir: {proc.stderr.read()}")
            try:
                urllib.request.urlopen(url, timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError(f"app não respondeu em {url}")
        yield url
    finally:
        proc.kill()
        proc.wait()


async def avaliar(projeto: Path, requisito: Path, saida: Path) -> dict:
    """Roda o CUA contra os critérios escritos por humano.

    Não sabe quem gerou o projeto: roda igual sobre a saída do harness e do baseline.
    """
    saida.mkdir(parents=True, exist_ok=True)
    criterios = (Path(requisito) / "criterios.md").read_text(encoding="utf-8")

    with app_rodando(Path(projeto)) as url:
        task = load("cua_task").format(base_url=url, criterios=criterios)
        agente = Agent(
            task=task,
            llm=ChatOpenAI(
                model=MODEL_CUA,
                base_url=OPENROUTER_BASE,
                api_key=os.environ["OPENROUTER_API_KEY"],
            ),
            output_model_schema=VeredictoCUA,
            generate_gif=False,
            calculate_cost=True,
        )
        history = await agente.run()

    veredicto = history.structured_output
    usage = history.usage
    resultado = {
        "configured_model": MODEL_CUA,
        "duration_s": round(history.total_duration_seconds() or 0.0, 2),
        "num_steps": history.number_of_steps(),
        "cost_usd": usage.total_cost if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
        "aprovado_geral": veredicto.aprovado_geral if veredicto else False,
        "resumo": veredicto.resumo if veredicto else "",
        "criterios": [c.model_dump() for c in veredicto.criterios] if veredicto else [],
    }
    (saida / "veredito.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resultado
