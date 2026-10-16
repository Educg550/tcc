import asyncio
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .agentes import load
from .dominio import Projeto

VERSAO = "1.19.0"
API = "https://openrouter.ai/api/v1"

# Sem isto o opencode lê do ambiente de quem roda: ~/.claude/CLAUDE.md, as skills de
# ~/.claude e ~/.agents e o AGENTS.md da raiz do repositório que contém o projeto.
# HOME próprio é o único corte para ~/.opencode/opencode.json, que ele lê mesmo assim.
ISOLAMENTO = {
    "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
    "OPENCODE_DISABLE_EXTERNAL_SKILLS": "1",
    "OPENCODE_DISABLE_CLAUDE_CODE": "1",
    "OPENCODE_DISABLE_MODELS_FETCH": "1",
    "OPENCODE_DISABLE_AUTOUPDATE": "1",
    "OPENCODE_DISABLE_SHARE": "1",
}


@dataclass(frozen=True)
class Turno:
    """O que uma chamada à sessão custou e usou. O que ela mudou está no disco."""

    custo_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    skills: list[str]
    erro: str | None = None


def relativo_ao_opencode(raiz: Path, regras: dict) -> dict:
    """O opencode casa os padrões de permissão com o caminho relativo ao topo do git que
    contém o projeto, ou a `/` fora de um: `tests/**` só vale com esse prefixo."""
    topo = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=raiz, capture_output=True, text=True
    )
    base = Path(topo.stdout.strip()) if topo.returncode == 0 else Path("/")
    prefixo = "" if raiz == base else f"{raiz.relative_to(base)}/"
    return {k if k == "*" else prefixo + k: v for k, v in regras.items()}


class Sessao:
    """Uma sessão do opencode por etapa. O modelo edita o projeto com as ferramentas que
    o escopo da etapa libera; bash e todo o resto ficam negados, e quem roda o pytest é
    o harness. A primeira chamada abre a sessão, as seguintes a continuam."""

    def __init__(self, papel: str, model_id: str):
        self.papel = papel
        self.model_id = model_id
        self.id: str | None = None
        self.casa = Path(tempfile.mkdtemp(prefix="opencode-"))
        self.chamadas = 0

    def config(self, raiz: Path, escopo_edit: dict, skills: list[Path]) -> dict:
        return {
            "$schema": "https://opencode.ai/config.json",
            "autoupdate": False,
            "share": "disabled",
            "formatter": False,
            "lsp": False,
            "enabled_providers": ["openrouter"],
            # Modelo declarado aqui, e não lido do models.dev: o catálogo muda entre runs.
            "provider": {
                "openrouter": {
                    "options": {"baseURL": API},
                    "models": {self.model_id: {}},
                }
            },
            "model": f"openrouter/{self.model_id}",
            "small_model": f"openrouter/{self.model_id}",
            "skills": {"paths": [str(s) for s in skills]},
            "agent": {
                self.papel: {
                    "mode": "primary",
                    # A diretiva de código mínimo é constante do experimento: idêntica nos dois grupos.
                    "prompt": load(self.papel) + "\n\n" + load("estilo_codigo"),
                    "permission": {
                        "*": "deny",
                        "read": relativo_ao_opencode(raiz, {"*": "allow", "_harness/**": "deny"}),
                        "glob": "allow",
                        "grep": "allow",
                        "list": "allow",
                        "todowrite": "allow",
                        "edit": relativo_ao_opencode(raiz, escopo_edit),
                        "external_directory": {
                            "*": "deny",
                            **{f"{s}/**": "allow" for s in skills},
                        },
                        # Nega também a skill embutida do opencode.
                        "skill": {"*": "deny", **{s.name: "allow" for s in skills}},
                    },
                }
            },
        }

    def ambiente(self) -> dict:
        casa = str(self.casa)
        return {
            "PATH": os.environ["PATH"],
            "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
            "HOME": casa,
            "XDG_CONFIG_HOME": f"{casa}/config",
            "XDG_DATA_HOME": f"{casa}/data",
            "XDG_STATE_HOME": f"{casa}/state",
            "XDG_CACHE_HOME": f"{casa}/cache",
            "OPENCODE_CONFIG": f"{casa}/opencode.json",
            **ISOLAMENTO,
        }

    async def enviar(
        self,
        prompt: str,
        projeto: Projeto,
        escopo_edit: dict,
        skills: list[Path],
        tempo_s: float,
    ) -> Turno:
        if self.id is None:
            versao = subprocess.run(
                ["opencode", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            if versao != VERSAO:
                raise SystemExit(f"opencode {versao}: o harness fixa {VERSAO}")
            (self.casa / "opencode.json").write_text(
                json.dumps(self.config(projeto.raiz, escopo_edit, skills), indent=2), encoding="utf-8"
            )
        cmd = ["opencode", "run", "--format", "json", "--agent", self.papel]
        cmd += ["--title", self.papel, "--dir", str(projeto.raiz)]
        if self.id:
            cmd += ["--session", self.id]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=projeto.raiz,
            env=self.ambiente(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        erro = None
        try:
            # O prompt vai pelo stdin: como argumento, um texto que comece com `-` vira flag.
            saida, stderr = await asyncio.wait_for(
                proc.communicate(prompt.encode()), timeout=max(tempo_s, 1)
            )
        except TimeoutError:
            # O opencode só despeja o JSONL ao sair: kill direto perde tokens, custo e o id.
            proc.terminate()
            try:
                saida, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            except TimeoutError:
                proc.kill()
                saida, stderr = await proc.communicate()
            erro = "tempo da etapa esgotado durante a sessão"
        if proc.returncode and erro is None:
            erro = stderr.decode(errors="replace")[-2000:]

        self.chamadas += 1
        bruto = projeto.saida / "opencode" / f"{self.papel}-{self.chamadas}.jsonl"
        bruto.parent.mkdir(parents=True, exist_ok=True)
        bruto.write_bytes(saida)
        return self._turno(saida.decode(errors="replace"), erro)

    def _turno(self, jsonl: str, erro: str | None) -> Turno:
        tin = tout = total = 0
        # Custo pela tabela de preços do opencode: o uso da chave no OpenRouter chega com
        # minutos de atraso e não separa as etapas.
        custo = 0.0
        skills = []
        for linha in jsonl.splitlines():
            evento = json.loads(linha)
            self.id = self.id or evento.get("sessionID")
            parte = evento.get("part", {})
            if evento["type"] == "step_finish":
                t = parte["tokens"]
                tin += t["input"] + t["cache"]["read"] + t["cache"]["write"]
                tout += t["output"] + t["reasoning"]
                total += t["total"]
                custo += parte["cost"]
            elif evento["type"] == "tool_use" and parte.get("tool") == "skill":
                skills.append(parte["state"]["input"].get("name"))
            elif evento["type"] == "error":
                erro = erro or json.dumps(evento["error"], ensure_ascii=False)[:2000]
        return Turno(custo, tin, tout, total, skills, erro)
