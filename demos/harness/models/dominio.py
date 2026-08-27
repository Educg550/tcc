from __future__ import annotations

import hashlib
import os
import re
import shlex
import subprocess
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from .politicas import Orcamento
from .propostas import Proposta, PropostaAceita, PropostaRejeitada

# Fora do contexto que o modelo recebe: `_harness/` é a medição, e RUN.log dentro do
# prompt é vazamento da métrica para dentro do que ela mede.
IGNORADOS = ("_harness", "__pycache__")


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
    declara — como rodar o gerado, com que modelos e sob que teto."""

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
            Criterio(**{k: v.strip() for k, v in c.items()})
            for c in dados["criterios"]
        ]

    @property
    def _declarado(self) -> dict:
        return tomllib.loads(
            (self.diretorio / "alvo.toml").read_text(encoding="utf-8")
        )

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
    def modelos(self) -> dict[str, str]:
        return self._declarado["modelos"]

    @property
    def orcamento(self) -> Orcamento:
        return Orcamento(**self._declarado["orcamento"])


class Criterio(BaseModel):
    """Critério de aceitação: autocontido. Se depende de um passo anterior, o passo está
    na própria ação — não existe ordem implícita entre critérios."""

    identificador: str
    acao: str
    resultado_esperado: str


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


MEDIDO = ("tests", "pytest.ini", "conftest.py")

SO_TESTES = Escopo(dentro="tests")
CODIGO = Escopo(fora=MEDIDO + ("_harness", ".git"))

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
    run: str

    def __post_init__(self) -> None:
        self.raiz = Path(self.raiz).resolve()

    @property
    def saida(self) -> Path:
        """Uma pasta por execução: RUN.log, trace e telas de runs diferentes do mesmo
        projeto não se sobrescrevem."""
        return self.raiz / "_harness" / self.run

    def preparar(self) -> None:
        self.saida.mkdir(parents=True, exist_ok=True)
        # Sem isso o pytest do projeto gerado herda o pyproject.toml de demos/ como rootdir.
        (self.raiz / "pytest.ini").write_text(
            "[pytest]\npythonpath = .\n", encoding="utf-8"
        )

    def aplicar(self, mudanca: Mudanca, escopo: Escopo) -> Proposta:
        """Valida todos os caminhos antes de escrever qualquer um: proposta inválida
        não deixa mudança pela metade para o pytest medir."""
        try:
            destinos = [
                (escopo.destino(self.raiz, a.caminho), a.conteudo)
                for a in mudanca.arquivos
            ]
        except EscopoViolado as erro:
            return PropostaRejeitada(str(erro), escopo.regra)
        escritos = []
        for destino, conteudo in destinos:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(conteudo, encoding="utf-8")
            escritos.append(str(destino.relative_to(self.raiz)))
        return PropostaAceita(escritos)

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

    def contexto(self, sub: str = "") -> str:
        """Todo arquivo de texto do projeto. Que arquivo entra não é escolha de extensão:
        é o que o modelo pode ver sem receber a própria medição de volta."""
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
        return "## PROJETO ATUAL\n\n" + projeto.contexto()

    def baseline(self, projeto: Projeto) -> ResultadoPytest:
        return projeto.rodar_pytest()
