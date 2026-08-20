from __future__ import annotations

import os
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

EXTENSOES = (".py", ".html", ".css", ".js")


@dataclass(frozen=True)
class Requisito:
    diretorio: Path

    @property
    def id(self) -> str:
        return self.diretorio.name

    @property
    def texto(self) -> str:
        return (self.diretorio / "requisito.md").read_text(encoding="utf-8")

    @property
    def criterios(self) -> str:
        return (self.diretorio / "criterios.md").read_text(encoding="utf-8")


class Arquivo(BaseModel):
    caminho: str
    conteudo: str


class Mudanca(BaseModel):
    """Única ação que o modelo pode propor: escrever estes arquivos."""

    arquivos: list[Arquivo]


class EscopoViolado(ValueError):
    pass


@dataclass(frozen=True)
class Escopo:
    """Onde uma etapa pode escrever: um prefixo permitido e prefixos negados."""

    dentro: str | None = None
    fora: tuple[str, ...] = ()

    def destino(self, raiz: Path, caminho: str) -> Path:
        alvo = (raiz / caminho).resolve()
        limite = (raiz / self.dentro).resolve() if self.dentro else raiz
        if not alvo.is_relative_to(limite):
            raise EscopoViolado(f"{caminho}: fora de {self.dentro or '.'}/")
        for negado in self.fora:
            if alvo.is_relative_to((raiz / negado).resolve()):
                raise EscopoViolado(f"{caminho}: {negado} é proibido")
        return alvo

    @property
    def regra(self) -> str:
        if self.dentro:
            return f"todo caminho começa com `{self.dentro}/`"
        return "nenhum caminho em " + ", ".join(f"`{f}`" for f in self.fora)


SO_TESTES = Escopo(dentro="tests")
# O coder escreve código de produção. A negação inclui a config do pytest e o próprio
# registro da execução: sem isso ele pode desligar o teste que o mede.
CODIGO = Escopo(fora=("tests", "_harness", ".git", "pytest.ini", "conftest.py"))

_CAMPOS = re.compile(r"(\d+)\s+(passed|failed|errors?|error)")


@dataclass(frozen=True)
class ResultadoPytest:
    passou: bool
    passed: int
    failed: int
    errors: int
    saida: str = ""

    @classmethod
    def de_saida(cls, saida: str, passou: bool) -> ResultadoPytest:
        """Contagens da última linha de resumo. Zeros se não houver resumo."""
        linha = next(
            (
                ln
                for ln in reversed(saida.splitlines())
                if ("passed" in ln or "failed" in ln or "error" in ln)
                and ("=" in ln or " in " in ln)
            ),
            "",
        )
        c = {"passed": 0, "failed": 0, "errors": 0}
        for n, palavra in _CAMPOS.findall(linha):
            c["errors" if palavra.startswith("error") else palavra] += int(n)
        return cls(passou=passou, saida=saida, **c)

    @property
    def contagem(self) -> dict:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "total": self.passed + self.failed + self.errors,
        }


@dataclass
class Projeto:
    """O mundo em que o modelo age: o único lugar que escreve em disco e roda o pytest."""

    raiz: Path

    def __post_init__(self) -> None:
        self.raiz = Path(self.raiz).resolve()

    @property
    def saida(self) -> Path:
        return self.raiz / "_harness"

    def preparar(self) -> None:
        self.saida.mkdir(parents=True, exist_ok=True)
        # Sem isso o pytest do projeto gerado herda o pyproject.toml de demos/ como rootdir.
        (self.raiz / "pytest.ini").write_text(
            "[pytest]\npythonpath = .\n", encoding="utf-8"
        )

    def aplicar(self, mudanca: Mudanca, escopo: Escopo) -> list[str]:
        """Valida todos os caminhos antes de escrever qualquer um: proposta inválida
        não deixa mudança pela metade para o pytest medir."""
        destinos = [
            (escopo.destino(self.raiz, a.caminho), a.conteudo) for a in mudanca.arquivos
        ]
        escritos = []
        for destino, conteudo in destinos:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(conteudo, encoding="utf-8")
            escritos.append(str(destino.relative_to(self.raiz)))
        return escritos

    def rodar_pytest(self) -> ResultadoPytest:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=short"],
            cwd=str(self.raiz),
            # Sem isto o pytest importa .pyc velho quando o modelo reescreve um arquivo
            # com o mesmo tamanho no mesmo segundo, e o harness mede falso vermelho.
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            check=False,
        )
        return ResultadoPytest.de_saida(
            proc.stdout + "\n" + proc.stderr, proc.returncode == 0
        )

    def contexto(self, sub: str = "") -> str:
        base = self.raiz / sub
        partes = []
        for caminho in sorted(base.rglob("*")):
            if not caminho.is_file() or caminho.suffix not in EXTENSOES:
                continue
            rel = caminho.relative_to(base)
            if any(parte.startswith(".") for parte in rel.parts):
                continue
            partes.append(f"### {rel}\n```\n{caminho.read_text(encoding='utf-8')}\n```")
        return "\n\n".join(partes)

    def commitar(self, requisito_id: str) -> None:
        """Um commit por requisito no projeto gerado: dá diff, tamanho e rollback."""
        if not (self.raiz / ".git").exists():
            subprocess.run(["git", "init", "-q"], cwd=self.raiz, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.raiz, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", requisito_id], cwd=self.raiz, check=False
        )


class Modo(ABC):
    """Não existe flag de modo: quem decide é o estado do diretório."""

    nome: str

    @staticmethod
    def detectar(projeto: Projeto) -> Modo:
        vazio = not projeto.raiz.exists() or not any(projeto.raiz.iterdir())
        return Criacao() if vazio else Manutencao()

    @abstractmethod
    def contexto(self, projeto: Projeto) -> str: ...

    @abstractmethod
    def baseline(self, projeto: Projeto) -> ResultadoPytest | None: ...


class Criacao(Modo):
    nome = "criacao"

    def contexto(self, projeto: Projeto) -> str:
        return ""

    def baseline(self, projeto: Projeto) -> None:
        return None


class Manutencao(Modo):
    nome = "manutencao"

    def contexto(self, projeto: Projeto) -> str:
        return "\n\n## PROJETO ATUAL\n\n" + projeto.contexto()

    def baseline(self, projeto: Projeto) -> ResultadoPytest:
        return projeto.rodar_pytest()
