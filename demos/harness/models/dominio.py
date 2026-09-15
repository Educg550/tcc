from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
import tomllib
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .politicas import Orcamento

# `_harness/` é a medição: fora do contexto que o modelo recebe, sempre. Valia por
# convenção enquanto todo chamador passava uma subárvore; o avaliador passa a raiz.
IGNORADOS = ("__pycache__", "_harness")
DEMOS = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Alvo:
    """Como o harness opera o software gerado: os comandos que sobem o app e rodam os
    testes, e o ambiente dos dois. Tudo declarado pelo caso de uso, nada pelo harness."""

    comando_app: str
    comando_teste: str
    python: str
    pacotes: tuple[str, ...]
    comando_frontend: str = ""

    def comando(self, linha: str) -> list[str]:
        """Ambiente próprio, montado do zero a cada chamada. `--isolated` é o que impede o
        uv de usar o venv do harness como base: sem ele o alvo enxerga dependência que o
        caso de uso não declarou, e o gerado passa a depender de quem o gerou."""
        uv = ["uv", "run", "--isolated", "--no-project", "--python", self.python]
        for pacote in self.pacotes:
            uv += ["--with", pacote]
        return uv + shlex.split(linha)

    @property
    def teste(self) -> list[str]:
        return self.comando(self.comando_teste)

    @property
    def teste_frontend(self) -> list[str]:
        """O Cypress é Node, então não passa pelo uv. Vazio quando o caso de uso não
        declara avaliação de frontend, e aí só o CUA julga."""
        return shlex.split(self.comando_frontend)

    def app(self, porta: int) -> list[str]:
        return self.comando(self.comando_app.format(porta=porta))

    def como_dict(self) -> dict:
        """O que o RUN.log grava do alvo: os comandos e o ambiente exato em que rodaram."""
        return {
            "comando_app": self.comando_app,
            "comando_teste": self.comando_teste,
            "comando_frontend": self.comando_frontend,
            "python": self.python,
            "pacotes": list(self.pacotes),
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
    def deterministicos(self) -> list[Criterio]:
        """O que vira suíte Cypress: verificável sem julgamento."""
        return [c for c in self.criterios if c.tipo == "deterministico"]

    @property
    def subjetivos(self) -> list[Criterio]:
        """O que sobra para o CUA: aparência, proporção, o que só se julga olhando."""
        return [c for c in self.criterios if c.tipo == "subjetivo"]

    @property
    def _declarado(self) -> dict:
        return tomllib.loads((self.diretorio / "alvo.toml").read_text(encoding="utf-8"))

    @property
    def alvo(self) -> Alvo:
        comandos, deps = self._declarado["comandos"], self._declarado["dependencias"]
        return Alvo(
            comando_app=comandos["app"],
            comando_teste=comandos["teste"],
            comando_frontend=comandos.get("teste_frontend", ""),
            python=str(deps["python"]),
            pacotes=tuple(deps["pacotes"]),
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
    na própria ação - não existe ordem implícita entre critérios.

    O `tipo` diz qual instrumento julga o critério, e não tem default: critério sem tipo
    é critério que ninguém mede, e falhar ao carregar é melhor do que sumir da avaliação."""

    identificador: str
    tipo: Literal["deterministico", "subjetivo"]
    acao: str
    resultado_esperado: str


class Arquivo(BaseModel):
    caminho: str
    conteudo: str


class Mudanca(BaseModel):
    """Única ação que o modelo pode propor: escrever estes arquivos."""

    arquivos: list[Arquivo]


MEDIDO = ("tests", "pytest.ini", "conftest.py")

# O mocha embutido no Cypress é o 7, que ignora `--reporter-options output=`: o JSON sai
# no stdout, um blob por spec, no meio da moldura do Cypress.
_BLOB = '{\n  "stats"'

CYPRESS_CONFIG = """module.exports = {
  video: false,
  reporter: "json",
  screenshotsFolder: "_harness/cypress/screenshots",
  videosFolder: "_harness/cypress/videos",
  downloadsFolder: "_harness/cypress/downloads",
  e2e: { supportFile: false, specPattern: "_harness/cypress/e2e/**/*.cy.js" },
};
"""


def blobs_cypress(saida: str) -> list[dict]:
    """Os relatórios do mocha achados no stdout. Vazio quando o Cypress caiu antes de
    rodar spec nenhum - config inválida, baseUrl fora do ar -, e aí o motivo está no
    stdout cru, não aqui."""
    blobs, i = [], 0
    while (i := saida.find(_BLOB, i)) != -1:
        try:
            obj, i = json.JSONDecoder().raw_decode(saida, i)
        except ValueError:
            break
        blobs.append(obj)
    return blobs

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

    @contextmanager
    def rodando(self, sufixo: str = ""):
        """Sobe o app com o comando que o caso de uso declara, numa porta livre."""
        with socket.socket() as s:
            s.bind(("", 0))
            porta = s.getsockname()[1]
        self.saida.mkdir(parents=True, exist_ok=True)
        # Em arquivo, não em pipe: o app loga cada requisição do avaliador e um pipe cheio
        # travaria o processo no meio da avaliação.
        log = self.saida / f"app{sufixo}.log"
        url = f"http://localhost:{porta}"
        with log.open("w", encoding="utf-8") as stderr:
            proc = subprocess.Popen(
                self.alvo.app(porta),
                cwd=str(self.raiz),
                stdout=subprocess.DEVNULL,
                stderr=stderr,
            )
            try:
                # A primeira subida pode pagar a resolução das dependências do caso de uso.
                for _ in range(300):
                    if proc.poll() is not None:
                        raise RuntimeError(f"app morreu ao subir: {log.read_text()}")
                    try:
                        urllib.request.urlopen(url, timeout=1)
                        break
                    except OSError:
                        time.sleep(0.2)
                else:
                    raise RuntimeError(f"app não respondeu em {url}: {log.read_text()}")
                yield url
            finally:
                proc.kill()
                proc.wait()

    def rodar_frontend(self) -> tuple[list[dict], str]:
        """Cypress contra o app subido numa porta livre. Devolve os relatórios do mocha e
        o stdout cru; lista vazia quer dizer que nenhum spec chegou a rodar.

        O binário vem do node_modules de demos/ - um install só, nenhum dentro do projeto
        gerado - e a porta chega por CYPRESS_BASE_URL, que o Cypress normaliza para
        `baseUrl`."""
        # Dentro de `_harness/`, e não na raiz: lá o coder poderia sobrescrever a config
        # da própria medição. Escrita aqui, e não em `preparar()`, para que `avaliar`
        # sobre uma run antiga também a tenha.
        (self.saida / "cypress.config.js").write_text(CYPRESS_CONFIG, encoding="utf-8")
        try:
            with self.rodando("-cypress") as url:
                proc = subprocess.run(
                    self.alvo.teste_frontend,
                    cwd=str(self.raiz),
                    env={
                        **os.environ,
                        "PATH": f"{DEMOS / 'node_modules' / '.bin'}:{os.environ['PATH']}",
                        "CYPRESS_BASE_URL": url,
                        "NO_COLOR": "1",
                    },
                    capture_output=True,
                    text=True,
                    check=False,
                )
        except RuntimeError as erro:
            # App que não sobe é reprovação do app, não queda da avaliação: o baseline
            # tem chance real de gerar algo que não inicia, e o veredito tem que existir.
            return [], str(erro)
        saida = proc.stdout + "\n" + proc.stderr
        return blobs_cypress(saida), saida

    def contexto(self, sub: str, fora: tuple[str, ...] = ()) -> str:
        """Todo arquivo de texto de uma subárvore do projeto. O modelo só recebe o que
        está dentro de `sub`: a medição em `_harness/` fica fora por construção.

        `fora` tira prefixos do que sobrou. Existe para o avaliador poder pedir a
        aplicação sem os testes: `tests/` existe no grupo TDD e não no baseline, e um
        instrumento que enxerga mais de um grupo que do outro deixa de ser régua."""
        base = self.raiz / sub
        partes = []
        for caminho in sorted(base.rglob("*")):
            rel = caminho.relative_to(base)
            if not caminho.is_file() or any(
                p.startswith(".") or p in IGNORADOS for p in rel.parts
            ):
                continue
            if rel.parts[0] in fora:
                continue
            try:
                texto = caminho.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            partes.append(f"### {rel}\n```\n{texto}\n```")
        return "\n\n".join(partes)
