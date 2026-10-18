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
IMAGEM = "ghcr.io/anomalyco/opencode@sha256:543fe6b18470c9e4787e9be9813c4d340fba5738085b833ea76fb330ddff514a"
API = "https://openrouter.ai/api/v1"
AMOSTRAGEM = {"temperature": 0.1, "top_p": 0.9}

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
    # Teto próprio do opencode (32k), aplicado mesmo com o limite do modelo declarado.
    "OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX": "131072",
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


def no_container(regras: dict) -> dict:
    """Sem git na imagem, a base do opencode é `/`; só `/workspace` é editável."""
    return {"*": "deny", **{
        "workspace/**" if k == "*" else f"workspace/{k}": v
        for k, v in regras.items()
    }}


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
        skills = [Path("/skills") / s.name for s in skills]
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
                    # O raciocínio do GLM 5.3 esgotou 32k num passo só nas runs baseline v2.
                    "models": {self.model_id: {"limit": {"context": 1048576, "output": 131072}}},
                }
            },
            "model": f"openrouter/{self.model_id}",
            "small_model": f"openrouter/{self.model_id}",
            "skills": {"paths": [str(s) for s in skills]},
            "agent": {
                self.papel: {
                    "mode": "primary",
                    **AMOSTRAGEM,
                    # A diretiva de código mínimo é constante do experimento: idêntica nos dois grupos.
                    "prompt": load(self.papel) + "\n\n" + load("estilo_codigo"),
                    "permission": {
                        "*": "deny",
                        "read": {**no_container({"*": "allow", "_harness": "deny", "_harness/**": "deny"}),
                                 "skills/**": "allow"},
                        "glob": "allow",
                        "grep": "allow",
                        "list": "allow",
                        "todowrite": "allow",
                        "edit": no_container(escopo_edit),
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
        casa = "/estado"
        return {
            "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
            "HOME": casa,
            "XDG_CONFIG_HOME": f"{casa}/config",
            "XDG_DATA_HOME": f"{casa}/data",
            "XDG_STATE_HOME": f"{casa}/state",
            "XDG_CACHE_HOME": f"{casa}/cache",
            "OPENCODE_CONFIG": f"{casa}/opencode.json",
            **ISOLAMENTO,
        }

    def container(self, projeto: Projeto, skills: list[Path]) -> list[str]:
        cmd = ["docker", "run", "--rm", "-i", "--init", "--name", self.casa.name,
               "--user", f"{os.getuid()}:{os.getgid()}", "--read-only", "--tmpfs", "/tmp",
               "--cap-drop=ALL", "--security-opt=no-new-privileges", "--workdir", "/workspace",
               "--mount", f"type=bind,src={projeto.raiz},dst=/workspace",
               "--mount", f"type=bind,src={self.casa},dst=/estado",
               "--mount", "type=tmpfs,dst=/workspace/_harness"]
        for skill in skills:
            cmd += ["--mount", f"type=bind,src={skill},dst=/skills/{skill.name},readonly"]
        for nome, valor in self.ambiente().items():
            cmd += ["--env", nome if nome == "OPENROUTER_API_KEY" else f"{nome}={valor}"]
        return cmd + [IMAGEM]

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
                self.container(projeto, skills) + ["--version"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            if versao != VERSAO:
                raise SystemExit(f"opencode {versao}: o harness fixa {VERSAO}")
            (self.casa / "opencode.json").write_text(
                json.dumps(self.config(escopo_edit, skills), indent=2), encoding="utf-8"
            )
        cmd = self.container(projeto, skills) + ["run", "--format", "json", "--agent", self.papel]
        cmd += ["--title", self.papel, "--dir", "/workspace"]
        if self.id:
            cmd += ["--session", self.id]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=projeto.raiz,
            env=os.environ.copy(),
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
            subprocess.run(["docker", "rm", "-f", self.casa.name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            erro = "tempo da etapa esgotado durante a sessão"
        if proc.returncode and erro is None:
            erro = stderr.decode(errors="replace")[-2000:] or f"opencode retornou {proc.returncode}"

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
