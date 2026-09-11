import argparse
import asyncio
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .models import (
    Avaliador,
    Batch,
    HarnessDireto,
    HarnessTDD,
    Interativa,
    Projeto,
    Requisito,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REQUISITOS = Path("requisitos")
MODELO = "00-exemplo-caso-de-uso"


def novo_caso(base: Path) -> Path:
    """Copia o modelo e abre cada arquivo no editor: o input multilinha é do $EDITOR."""
    while not (nome := input("nome do caso de uso (ex: 02-listagem): ").strip()):
        pass
    destino = base / nome
    if any(destino.glob("*")):
        raise SystemExit(f"{destino} já tem arquivos")
    shutil.copytree(base / MODELO, destino, dirs_exist_ok=True)
    editor = os.environ.get("EDITOR", "nano")
    for arquivo in sorted(destino.iterdir()):
        subprocess.run([editor, str(arquivo)], check=True)
    return destino


def nome_do_projeto(requisito_id: str, grupo: str) -> str:
    """Quem nomeia o projeto é o harness: toda run parte de um diretório novo, e o nome
    diz de que caso de uso, de que grupo e de quando ela é. Requisito na frente para as
    runs do mesmo caso de uso ficarem juntas; data no fim para ordenarem entre si."""
    return f"{requisito_id}-{grupo}-{datetime.now():%Y%m%d-%H%M%S}"


def main() -> None:
    ap = argparse.ArgumentParser(prog="harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="gera um projeto novo até o pytest passar")
    run.add_argument("destino", help="pasta-mãe; o harness cria o projeto dentro dela")
    run.add_argument(
        "requisito",
        nargs="?",
        help="caso de uso; vazio cria um novo a partir do modelo",
    )
    run.add_argument("--yes", action="store_true", help="modo batch, sem gate humano")
    run.add_argument(
        "--direto", action="store_true", help="grupo baseline: uma etapa, sem TDD"
    )
    run.add_argument(
        "--sem-cua",
        action="store_true",
        help="para o pipeline no pytest; `avaliar` roda o CUA sobre a run depois",
    )

    ava = sub.add_parser(
        "avaliar", help="re-roda so o CUA e regrava o CUA.log de um projeto ja gerado"
    )
    ava.add_argument("projeto", help="o diretorio que o `run` criou")
    ava.add_argument("requisito")

    args = ap.parse_args()
    caminho = Path(args.requisito) if args.requisito else novo_caso(REQUISITOS)
    requisito = Requisito(caminho)

    if args.cmd == "run":
        classe = HarnessDireto if args.direto else HarnessTDD
        raiz = Path(args.destino) / nome_do_projeto(requisito.id, classe.grupo)
        projeto = Projeto(raiz, requisito.alvo)
        permissao = Batch() if args.yes else Interativa()
        harness = classe(projeto, requisito, permissao, not args.sem_cua)
        log = asyncio.run(harness.executar())
        print(
            f"\npytest final: {log['pytest_final']}"
            f"  code: {log['stages'][-1]['motivo']}"
            f"  testes intactos: {log['integridade']['intacto']}"
        )
        print(f"logs: {projeto.saida}")
    else:
        projeto = Projeto(Path(args.projeto), requisito.alvo)
        cua = Avaliador(requisito.modelos["cua"])
        r = asyncio.run(cua.avaliar(projeto, requisito))
        print(f"\naprovado_geral: {r['aprovado_geral']}\n{r['resumo']}")
        print(f"CUA.log: {projeto.saida / 'CUA.log'}")


if __name__ == "__main__":
    main()
