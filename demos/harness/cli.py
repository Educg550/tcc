import argparse
import asyncio
from pathlib import Path

from .cua import avaliar
from .run import executar


def main() -> None:
    ap = argparse.ArgumentParser(prog="harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="gera ou mantém o projeto até o pytest passar")
    run.add_argument("projeto")
    run.add_argument("requisito")
    run.add_argument("--yes", action="store_true", help="modo batch, sem gate humano")

    ava = sub.add_parser("avaliar", help="roda o CUA contra criterios.md")
    ava.add_argument("projeto")
    ava.add_argument("requisito")

    args = ap.parse_args()
    if args.cmd == "run":
        log = asyncio.run(executar(Path(args.projeto), Path(args.requisito), args.yes))
        print(f"\npytest final: {log['pytest_final']}  loop: {log['loop']['motivo']}")
        print(f"RUN.log: {Path(args.projeto) / '_harness' / 'RUN.log'}")
    else:
        r = asyncio.run(
            avaliar(
                Path(args.projeto),
                Path(args.requisito),
                Path(args.projeto) / "_harness",
            )
        )
        print(f"\naprovado_geral: {r['aprovado_geral']}\n{r['resumo']}")


if __name__ == "__main__":
    main()
