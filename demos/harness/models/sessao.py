import asyncio
import json
import os
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass, replace
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


def uso_da_chave() -> float:
    """Gasto acumulado da chave no OpenRouter: o custo real, não a tabela do opencode."""
    pedido = urllib.request.Request(
        f"{API}/key",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as r:
        return json.load(r)["data"]["usage"]


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

    def config(self, escopo_edit: dict, skills: list[Path]) -> dict:
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
                        "read": {"*": "allow", "_harness/**": "deny"},
                        "glob": "allow",
                        "grep": "allow",
                        "list": "allow",
                        "todowrite": "allow",
                        "edit": escopo_edit,
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
                json.dumps(self.config(escopo_edit, skills), indent=2), encoding="utf-8"
            )
        cmd = ["opencode", "run", "--format", "json", "--agent", self.papel]
        cmd += ["--title", self.papel, "--dir", str(projeto.raiz)]
        if self.id:
            cmd += ["--session", self.id]

        antes = uso_da_chave()
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
            proc.kill()
            saida, stderr = await proc.communicate()
            erro = "tempo da etapa esgotado durante a sessão"
        if proc.returncode and erro is None:
            erro = stderr.decode(errors="replace")[-2000:]

        self.chamadas += 1
        bruto = projeto.saida / "opencode" / f"{self.papel}-{self.chamadas}.jsonl"
        bruto.parent.mkdir(parents=True, exist_ok=True)
        bruto.write_bytes(saida)
        turno = self._turno(saida.decode(errors="replace"), erro)
        # shortcut: lê o uso da chave logo depois da sessão; se o OpenRouter contabilizar
        # com atraso, o custo do passo vaza para o seguinte. Conferir na run paga.
        return replace(turno, custo_usd=uso_da_chave() - antes)

    def _turno(self, jsonl: str, erro: str | None) -> Turno:
        tin = tout = total = 0
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
            elif evento["type"] == "tool_use" and parte.get("tool") == "skill":
                skills.append(parte["state"]["input"].get("name"))
            elif evento["type"] == "error":
                erro = erro or json.dumps(evento["error"], ensure_ascii=False)[:2000]
        return Turno(0.0, tin, tout, total, skills, erro)
