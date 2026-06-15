import asyncio
import functools
import http.server
import json
import os
import socketserver
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR.parent / ".env")
# A .env existente guarda a chave do OpenRouter em ANTHROPIC_AUTH_TOKEN.
# Agno (OpenRouter) e o ChatOpenAI->OpenRouter do CUA leem OPENROUTER_API_KEY.
if not os.environ.get("OPENROUTER_API_KEY") and os.environ.get("ANTHROPIC_AUTH_TOKEN"):
    os.environ["OPENROUTER_API_KEY"] = os.environ["ANTHROPIC_AUTH_TOKEN"]

from .agents import MODEL_CODER, MODEL_SPEC, make_coder, make_spec_writer
from .cua import run_cua
from .models import Criterios
from .prompts import load

OUTPUT_DIR = SCRIPT_DIR / "output" / "todo-web-cua"
CRITERIOS_FILE = OUTPUT_DIR / "criterios.json"
CUA_DIR = OUTPUT_DIR / "_cua"
RUN_LOG = OUTPUT_DIR / "RUN.log"


# ── Helpers puros (testados) ────────────────────────────────────────────
def serve(directory: Path) -> tuple[socketserver.TCPServer, int]:
    """Sobe um http.server numa porta livre, servindo `directory`. Não bloqueia."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    httpd = socketserver.TCPServer(("", 0), handler)  # 0 => porta livre
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def build_run_log(started_at, ended_at, total_duration_s, stages, cua) -> dict:
    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "total_duration_s": total_duration_s,
        "total_cost_usd": sum((s.get("cost_usd") or 0.0) for s in stages) or None,
        "total_retries": sum(s.get("retries", 0) for s in stages),
        "stages": stages,
        "cua": cua,
    }


def _as_criterios(content) -> Criterios:
    """Agno pode devolver o output_schema já como Pydantic ou como JSON string."""
    if isinstance(content, Criterios):
        return content
    if isinstance(content, str):
        return Criterios.model_validate_json(content)
    return Criterios.model_validate(content)


# ── Gate humano ─────────────────────────────────────────────────────────
def aprovar(label: str, conteudo: str) -> str | None:
    """Gate humano y/n. Em 'n', exige feedback. None se aprovado, senão o feedback."""
    banner = "═" * 60
    print(f"\n{banner}\n  Etapa: {label}\n{banner}\n{conteudo}\n{banner}")
    while True:
        r = input(f"[{label}] aprovar? (y/n): ").strip().lower()
        if r == "y":
            return None
        if r == "n":
            break
        print("  Digite 'y' ou 'n'.")
    fb = ""
    while not fb.strip():
        fb = input("Feedback: ")
    return fb.strip()


# ── Etapas ──────────────────────────────────────────────────────────────
async def stage_spec() -> tuple[Criterios, dict]:
    agent = make_spec_writer()
    base = load("requisitos")
    feedback, retries = None, 0
    while True:
        prompt = base if feedback is None else f"{base}\n\n## FEEDBACK ANTERIOR\n{feedback}\n"
        start = time.time()
        resp = await agent.arun(prompt)
        dur = round(time.time() - start, 2)
        criterios = _as_criterios(resp.content)
        CRITERIOS_FILE.write_text(criterios.model_dump_json(indent=2), encoding="utf-8")
        feedback = aprovar("spec", criterios.model_dump_json(indent=2))
        if feedback is None:
            return criterios, {
                "id": "spec", "agent": "spec-writer", "configured_model": MODEL_SPEC,
                "duration_s": dur, "retries": retries, "cost_usd": None,
            }
        retries += 1


async def stage_code(criterios: Criterios) -> dict:
    agent = make_coder(OUTPUT_DIR)
    prompt_base = (
        "Implemente o site a partir destes critérios de aceitação. "
        "Escreva index.html, style.css e app.js no diretório de trabalho.\n\n"
        + criterios.model_dump_json(indent=2)
    )
    feedback, retries = None, 0
    while True:
        prompt = prompt_base if feedback is None else f"{prompt_base}\n\n## FEEDBACK ANTERIOR\n{feedback}\n"
        start = time.time()
        await agent.arun(prompt)
        dur = round(time.time() - start, 2)
        index = OUTPUT_DIR / "index.html"
        if not index.exists():
            raise RuntimeError(f"coder terminou mas {index} não existe")
        httpd, port = serve(OUTPUT_DIR)
        print(f"  site servido em http://localhost:{port} — abra no navegador para inspecionar")
        feedback = aprovar("code", f"Arquivos em {OUTPUT_DIR}. URL: http://localhost:{port}")
        if feedback is None:
            return {
                "id": "code", "agent": "coder", "configured_model": MODEL_CODER,
                "duration_s": dur, "retries": retries, "cost_usd": None,
                "_httpd": httpd, "_port": port,
            }
        httpd.shutdown()
        retries += 1


# ── main ────────────────────────────────────────────────────────────────
async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now().isoformat(timespec="seconds")
    start = time.time()
    print("═" * 60)
    print("  Pipeline orquestrado v3 — TODO web + CUA")
    print("═" * 60)

    criterios, spec_metrics = await stage_spec()
    code_metrics = await stage_code(criterios)

    httpd = code_metrics.pop("_httpd")
    port = code_metrics.pop("_port")
    base_url = f"http://localhost:{port}"
    try:
        print(f"\n──── CUA testando {base_url} ────")
        cua = await run_cua(base_url, criterios, CUA_DIR)
    finally:
        httpd.shutdown()

    ended_at = datetime.now().isoformat(timespec="seconds")
    log = build_run_log(
        started_at, ended_at, round(time.time() - start, 2),
        [spec_metrics, code_metrics], cua,
    )
    RUN_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "═" * 60)
    print(f"  CUA aprovado_geral: {cua['aprovado_geral']}")
    print(f"  Artefatos: {CUA_DIR}")
    print(f"  RUN.log:   {RUN_LOG}")
    print("═" * 60)


if __name__ == "__main__":
    asyncio.run(main())
