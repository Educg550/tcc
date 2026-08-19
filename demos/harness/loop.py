from pathlib import Path

from .models import Mudanca


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
