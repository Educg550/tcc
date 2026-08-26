import argparse
import asyncio
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from .models import (
    Avaliador,
    Batch,
    HarnessDireto,
    HarnessTDD,
    Interativa,
    Orcamento,
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


def main() -> None:
    ap = argparse.ArgumentParser(prog="harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="gera ou mantém o projeto até o pytest passar")
    run.add_argument("projeto")
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
        "--passos", type=int, default=Orcamento.passos, help="propostas por etapa"
    )
    run.add_argument(
        "--custo", type=float, default=Orcamento.custo_usd, help="USD por etapa"
    )
    run.add_argument(
        "--tempo", type=int, default=Orcamento.tempo_s, help="segundos por etapa"
    )

    ava = sub.add_parser("avaliar", help="roda o CUA contra criterios.md")
    ava.add_argument("projeto")
    ava.add_argument("requisito")

    args = ap.parse_args()
    caminho = Path(args.requisito) if args.requisito else novo_caso(REQUISITOS)
    requisito = Requisito(caminho)
    projeto = Projeto(Path(args.projeto), requisito.alvo)

    if args.cmd == "run":
        classe = HarnessDireto if args.direto else HarnessTDD
        permissao = Batch() if args.yes else Interativa()
        orcamento = Orcamento(args.passos, args.custo, args.tempo)
        harness = classe(projeto, requisito, permissao, orcamento)
        log = asyncio.run(harness.executar())
        print(
            f"\npytest final: {log['pytest_final']}  loop: {log['loop']['motivo']}"
            f"  testes intactos: {log['integridade']['intacto']}"
        )
        print(f"RUN.log: {projeto.saida / 'RUN.log'}")
    else:
        cua = Avaliador(projeto.alvo.modelos["cua"])
        r = asyncio.run(cua.avaliar(projeto, requisito))
        print(f"\naprovado_geral: {r['aprovado_geral']}\n{r['resumo']}")


if __name__ == "__main__":
    main()
