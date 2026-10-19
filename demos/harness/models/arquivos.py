import os
from pathlib import Path
from typing import TYPE_CHECKING

from .dominio import Arquivo, Mudanca, Projeto

if TYPE_CHECKING:
    from .etapas import Escopo


class Arquivos:
    """Ferramentas nativas do Agno; a etapa grava a mudança após a sessão."""

    def __init__(self, projeto: Projeto, escopo: "Escopo"):
        self.projeto, self.escopo = projeto, escopo
        self.pendentes: dict[str, str] = {}

    def _leitura(self, caminho: str) -> Path:
        destino = (self.projeto.raiz / caminho).resolve()
        relativo = destino.relative_to(self.projeto.raiz)
        if any(p in (".git", "__pycache__") for p in relativo.parts):
            raise ValueError("Arquivo de medição ou interno: leitura proibida.")
        if "_harness" in relativo.parts:
            # O escritor de specs pode ler só a própria subárvore da medição.
            self.escopo.destino(self.projeto.raiz, caminho)
        return destino

    def listar_arquivos(self) -> str:
        """Lista os arquivos disponíveis no projeto, incluindo criações desta sessão."""
        caminhos = set(self.pendentes)
        for pasta, dirs, nomes in os.walk(self.projeto.raiz):
            dirs[:] = [d for d in dirs if d not in
                       ("_harness", ".git", "__pycache__", ".venv", "node_modules")]
            caminhos.update(str((Path(pasta) / n).relative_to(self.projeto.raiz)) for n in nomes)
        visiveis = []
        for caminho in sorted(caminhos):
            try:
                self._leitura(caminho)
            except ValueError:
                continue
            visiveis.append(caminho)
        return "\n".join(visiveis)

    def ler_arquivo(self, caminho: str) -> str:
        """Lê o conteúdo atual de um arquivo relativo à raiz, incluindo edições pendentes."""
        destino = self._leitura(caminho)
        relativo = str(destino.relative_to(self.projeto.raiz))
        if relativo in self.pendentes:
            return self.pendentes[relativo]
        return destino.read_text(encoding="utf-8")

    def _guardar(self, caminho: str, conteudo: str) -> str:
        destino = self.escopo.validar(self.projeto.raiz, caminho, conteudo)
        relativo = str(destino.relative_to(self.projeto.raiz))
        self.pendentes[relativo] = conteudo
        return f"{relativo}: alteração aceita nesta sessão."

    def criar_arquivo(self, caminho: str, conteudo: str) -> str:
        """Cria um arquivo novo. Para alterar um arquivo existente, use substituir_trecho."""
        destino = self.escopo.destino(self.projeto.raiz, caminho)
        relativo = str(destino.relative_to(self.projeto.raiz))
        if destino.exists() or relativo in self.pendentes:
            raise ValueError("O arquivo já existe. Leia-o e use substituir_trecho.")
        return self._guardar(caminho, conteudo)

    def substituir_trecho(self, caminho: str, antigo: str, novo: str) -> str:
        """Substitui uma ocorrência exata de um trecho, preservando o restante do arquivo.

        Args:
            caminho: Caminho relativo à raiz do projeto.
            antigo: Trecho não vazio que aparece exatamente uma vez no conteúdo atual.
            novo: Conteúdo que substituirá o trecho antigo.
        """
        self.escopo.destino(self.projeto.raiz, caminho)
        conteudo = self.ler_arquivo(caminho)
        if not antigo or conteudo.count(antigo) != 1:
            raise ValueError("O trecho antigo deve aparecer exatamente uma vez. Leia o arquivo novamente.")
        return self._guardar(caminho, conteudo.replace(antigo, novo, 1))

    def mudanca(self) -> Mudanca:
        return Mudanca(arquivos=[
            Arquivo(caminho=c, conteudo=t) for c, t in self.pendentes.items()
        ])
