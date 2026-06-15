import json
import os
from pathlib import Path

from browser_use import Agent, BrowserProfile, ChatOpenAI

from .models import Criterios, VeredictoCUA
from .prompts import load

MODEL_CUA = "google/gemini-2.5-flash"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _llm() -> ChatOpenAI:
    # browser-use 0.13 não tem ChatOpenRouter; OpenRouter é OpenAI-compatível.
    return ChatOpenAI(
        model=MODEL_CUA,
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


async def run_cua(base_url: str, criterios: Criterios, artifacts_dir: Path) -> dict:
    """Roda o CUA uma vez contra base_url. Grava artefatos e retorna o dict da
    seção `cua` do RUN.log."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    video_dir = artifacts_dir / "video"
    video_dir.mkdir(exist_ok=True)

    task = load("cua_task").format(
        base_url=base_url,
        criterios=criterios.model_dump_json(indent=2),
    )

    agent = Agent(
        task=task,
        llm=_llm(),
        output_model_schema=VeredictoCUA,
        browser_profile=BrowserProfile(record_video_dir=str(video_dir)),
    )
    history = await agent.run()

    veredicto: VeredictoCUA | None = history.structured_output

    trace = {
        "urls": history.urls(),
        "actions": history.action_names(),
        "thoughts": [str(t) for t in history.model_thoughts()],
        "errors": [e for e in history.errors() if e],
        "duration_s": history.total_duration_seconds(),
        "num_steps": history.number_of_steps(),
    }
    (artifacts_dir / "trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if veredicto is not None:
        (artifacts_dir / "veredito.json").write_text(
            veredicto.model_dump_json(indent=2), encoding="utf-8"
        )

    return {
        "configured_model": MODEL_CUA,
        "duration_s": round(trace["duration_s"] or 0.0, 2),
        "num_steps": trace["num_steps"],
        "aprovado_geral": veredicto.aprovado_geral if veredicto else False,
        "criterios": [c.model_dump() for c in veredicto.criterios] if veredicto else [],
        "artefatos": {
            "video": str(video_dir),
            "screenshots": history.screenshot_paths(),
            "trace": str(artifacts_dir / "trace.json"),
        },
    }
