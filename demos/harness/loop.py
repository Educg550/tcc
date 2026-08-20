import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .models import Mudanca

_CAMPOS = re.compile(r"(\d+)\s+(passed|failed|errors?|error)")


@dataclass
class Pytest:
    passou: bool
    passed: int
    failed: int
    errors: int
    total: int
    saida: str


def escrever(
    mudanca: Mudanca,
    raiz: Path,
    escopo: str | None = None,
    proibido: str | None = None,
) -> list[str]:
    """Escreve os arquivos propostos dentro de `raiz`."""
    raiz = Path(raiz).resolve()
    limite = (raiz / escopo).resolve() if escopo else raiz
    veto = (raiz / proibido).resolve() if proibido else None

    destinos = []
    for arquivo in mudanca.arquivos:
        destino = (raiz / arquivo.caminho).resolve()
        if not destino.is_relative_to(limite):
            raise ValueError(f"caminho fora de {limite}: {arquivo.caminho}")
        if veto and destino.is_relative_to(veto):
            raise ValueError(f"caminho sob {proibido}/, proibido: {arquivo.caminho}")
        destinos.append((destino, arquivo.conteudo))

    escritos = []
    for destino, conteudo in destinos:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo, encoding="utf-8")
        escritos.append(str(destino.relative_to(raiz)))
    return escritos


def contar_pytest(saida: str) -> dict:
    """Contagens da última linha de resumo do pytest. Zeros se não houver resumo."""
    linha = next(
        (
            ln
            for ln in reversed(saida.splitlines())
            if ("passed" in ln or "failed" in ln or "error" in ln)
            and ("=" in ln or " in " in ln)
        ),
        "",
    )
    contagem = {"passed": 0, "failed": 0, "errors": 0}
    for n, palavra in _CAMPOS.findall(linha):
        contagem["errors" if palavra.startswith("error") else palavra] += int(n)
    contagem["total"] = sum(contagem.values())
    return contagem


def rodar_pytest(projeto: Path) -> Pytest:
    """Roda a suíte inteira do projeto."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"],
        cwd=str(projeto),
        capture_output=True,
        text=True,
        check=False,
    )
    saida = proc.stdout + "\n" + proc.stderr
    return Pytest(passou=proc.returncode == 0, saida=saida, **contar_pytest(saida))


@dataclass
class Orcamento:
    """Limites do loop."""

    passos: int = 12
    custo_usd: float = 2.0
    tempo_s: int = 900

    def estourou(self, passos: int, custo: float, inicio: float) -> str | None:
        if passos >= self.passos:
            return "passos"
        if custo >= self.custo_usd:
            return "custo"
        if time.time() - inicio >= self.tempo_s:
            return "tempo"
        return None


def trace(caminho: Path, evento: dict) -> None:
    """Uma linha JSON por passo."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


def como_mudanca(content) -> Mudanca:
    if isinstance(content, Mudanca):
        return content
    if isinstance(content, str):
        return Mudanca.model_validate_json(content)
    return Mudanca.model_validate(content)


async def loop_tdd(
    agent, prompt: str, projeto: Path, orcamento: Orcamento, caminho_trace: Path
) -> dict:
    """Propor -> validar -> escrever -> pytest -> observar

    O modelo nunca executa nada, quem roda o pytest é esta função.
    """
    inicio, passos, custo, tokens, historico = time.time(), 0, 0.0, 0, []
    while True:
        motivo = orcamento.estourou(passos, custo, inicio)
        if motivo:
            return {
                "ok": False,
                "motivo": motivo,
                "passos": passos,
                "cost_usd": custo,
                "total_tokens": tokens,
                "historico": historico,
            }

        resposta = await agent.arun(prompt)
        passos += 1
        metricas = getattr(resposta, "metrics", None)
        custo += getattr(metricas, "cost", None) or 0.0
        tokens += getattr(metricas, "total_tokens", None) or 0
        try:
            escritos = escrever(
                como_mudanca(resposta.content), projeto, proibido="tests"
            )
        except ValueError as erro:
            trace(
                caminho_trace,
                {"passo": passos, "erro": str(erro), "cost_usd": round(custo, 6)},
            )
            prompt += (
                f"\n\n## PROPOSTA REJEITADA (passo {passos})\n{erro}\n"
                "Reenvie a Mudanca com caminhos relativos à raiz do projeto, "
                "nenhum sob `tests/`.\n"
            )
            continue
        resultado = rodar_pytest(projeto)

        historico.append(
            {
                "passed": resultado.passed,
                "failed": resultado.failed,
                "errors": resultado.errors,
            }
        )
        trace(
            caminho_trace,
            {
                "passo": passos,
                "arquivos": escritos,
                "pytest": historico[-1],
                "cost_usd": round(custo, 6),
            },
        )

        if resultado.passou:
            return {
                "ok": True,
                "motivo": "verde",
                "passos": passos,
                "cost_usd": custo,
                "total_tokens": tokens,
                "historico": historico,
            }

        prompt += (
            f"\n\n## PYTEST FALHOU (passo {passos})\n"
            f"```\n{resultado.saida[-4000:]}\n```\n"
            "Corrija o código de produção. Não altere os testes.\n"
        )
