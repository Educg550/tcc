import re
import subprocess
import sys
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


def escrever(mudanca: Mudanca, raiz: Path, escopo: str | None = None) -> list[str]:
    """Escreve os arquivos propostos dentro de `raiz`.

    Fronteira de confiança do harness: o conteúdo vem do modelo, o destino não.
    Caminho que escape de `raiz` (ou de `raiz/escopo`, quando dado) levanta ValueError
    antes de qualquer escrita acontecer.
    """
    raiz = Path(raiz).resolve()
    limite = (raiz / escopo).resolve() if escopo else raiz

    destinos = []
    for arquivo in mudanca.arquivos:
        destino = (raiz / arquivo.caminho).resolve()
        if not destino.is_relative_to(limite):
            raise ValueError(f"caminho fora de {limite}: {arquivo.caminho}")
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
    """Roda a suíte inteira do projeto. Nunca levanta: falha é observação, não erro."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"],
        cwd=str(projeto),
        capture_output=True,
        text=True,
        check=False,
    )
    saida = proc.stdout + "\n" + proc.stderr
    return Pytest(passou=proc.returncode == 0, saida=saida, **contar_pytest(saida))
