from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from .politicas import Orcamento

IGNORADOS = ("__pycache__",)


@dataclass(frozen=True)
class Alvo:
    """Como o harness opera o software gerado: o comando que sobe o app, o que roda os
    testes e o ambiente dos dois. Tudo declarado pelo caso de uso, nada pelo harness."""

    comando_app: str
    comando_teste: str
    requirements: Path | None = None

    def comando(self, linha: str) -> list[str]:
        """Roda no ambiente que o caso de uso declara, isolado do venv do harness."""
        uv = ["uv", "run", "--no-project"]
        if self.requirements:
            uv += ["--with-requirements", str(self.requirements)]
        return uv + shlex.split(linha)

    @property
    def teste(self) -> list[str]:
        return self.comando(self.comando_teste)

    def app(self, porta: int) -> list[str]:
        return self.comando(self.comando_app.format(porta=porta))

    @property
    def dependencias(self) -> list[str]:
        if not self.requirements:
            return []
        linhas = self.requirements.read_text(encoding="utf-8").splitlines()
        return [ln.strip() for ln in linhas if ln.strip() and not ln.startswith("#")]

    def como_dict(self) -> dict:
        """O que o RUN.log grava do alvo. As dependências vão por conteúdo, não por
        caminho: o caminho não diz em que ambiente a execução rodou."""
        return {
            "comando_app": self.comando_app,
            "comando_teste": self.comando_teste,
            "dependencias": self.dependencias,
        }


@dataclass(frozen=True)
class Requisito:
    """O caso de uso em disco: o texto, os critérios de aceitação, e o que o alvo.toml
    declara - como rodar o gerado, com que modelos e sob que teto."""

    diretorio: Path

    @property
    def id(self) -> str:
        return self.diretorio.name

    @property
    def texto(self) -> str:
        return (self.diretorio / "requisito.md").read_text(encoding="utf-8")

    @property
    def criterios(self) -> list[Criterio]:
        texto = (self.diretorio / "criterios.toml").read_text(encoding="utf-8")
        dados = tomllib.loads(texto)
        return [
            Criterio(**{k: v.strip() for k, v in c.items()}) for c in dados["criterios"]
        ]

    @property
    def _declarado(self) -> dict:
        return tomllib.loads((self.diretorio / "alvo.toml").read_text(encoding="utf-8"))

    @property
    def alvo(self) -> Alvo:
        # Absoluto: o comando roda com cwd na raiz do projeto gerado, não aqui.
        requirements = (self.diretorio / "requirements.txt").resolve()
        return Alvo(
            comando_app=self._declarado["comando_app"],
            comando_teste=self._declarado["comando_teste"],
            requirements=requirements if requirements.exists() else None,
        )

    @property
    def anexos(self) -> list[Path]:
        """Pastas do caso de uso que o projeto gerado recebe como estão - imagem, fonte,
        dado de exemplo. O prefixo `_` marca a pasta que é material de pesquisa e não
        entra no projeto."""
        return [
            d
            for d in sorted(self.diretorio.iterdir())
            if d.is_dir() and not d.name.startswith(("_", "."))
        ]

    @property
    def modelos(self) -> dict[str, str]:
        return self._declarado["modelos"]

    @property
    def orcamento(self) -> Orcamento:
        return Orcamento(**self._declarado["orcamento"])


class Criterio(BaseModel):
    """Critério de aceitação: autocontido. Se depende de um passo anterior, o passo está
    na própria ação - não existe ordem implícita entre critérios."""

    identificador: str
    acao: str
    resultado_esperado: str


class Arquivo(BaseModel):
    caminho: str
    conteudo: str


class Mudanca(BaseModel):
    """Única ação que o modelo pode propor: escrever estes arquivos."""

    arquivos: list[Arquivo]


MEDIDO = ("tests", "pytest.ini", "conftest.py")

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
    alvo: Alvo

    def __post_init__(self) -> None:
        self.raiz = Path(self.raiz).resolve()

    @property
    def saida(self) -> Path:
        """Uma run por projeto, e a medição dela fora do código medido: `_harness/` não
        entra no contexto que o modelo recebe."""
        return self.raiz / "_harness"

    def preparar(self) -> None:
        self.saida.mkdir(parents=True, exist_ok=True)
        # Sem isso o pytest do projeto gerado herda o pyproject.toml de demos/ como rootdir.
        (self.raiz / "pytest.ini").write_text(
            "[pytest]\npythonpath = .\n", encoding="utf-8"
        )

    def semear(self, anexos: list[Path]) -> None:
        """Conteúdo que o modelo não escreve, só usa: o harness põe em disco antes da
        primeira etapa."""
        for origem in anexos:
            shutil.copytree(origem, self.raiz / origem.name, dirs_exist_ok=True)

    def escrever(self, destinos: list[tuple[Path, str]]) -> list[str]:
        escritos = []
        for destino, conteudo in destinos:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(conteudo, encoding="utf-8")
            escritos.append(str(destino.relative_to(self.raiz)))
        return escritos

    def impressao(self) -> str:
        h = hashlib.sha256()
        for alvo in MEDIDO:
            base = self.raiz / alvo
            for arq in sorted(base.rglob("*") if base.is_dir() else [base]):
                if arq.is_file() and "__pycache__" not in arq.parts:
                    h.update(str(arq.relative_to(self.raiz)).encode())
                    h.update(arq.read_bytes())
        return h.hexdigest()

    def rodar_pytest(self) -> ResultadoPytest:
        proc = subprocess.run(
            self.alvo.teste,
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

    def contexto(self, sub: str) -> str:
        """Todo arquivo de texto de uma subárvore do projeto. O modelo só recebe o que
        está dentro de `sub`: a medição em `_harness/` fica fora por construção."""
        base = self.raiz / sub
        partes = []
        for caminho in sorted(base.rglob("*")):
            rel = caminho.relative_to(base)
            if not caminho.is_file() or any(
                p.startswith(".") or p in IGNORADOS for p in rel.parts
            ):
                continue
            try:
                texto = caminho.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            partes.append(f"### {rel}\n```\n{texto}\n```")
        return "\n\n".join(partes)
