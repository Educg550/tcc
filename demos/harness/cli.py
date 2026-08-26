import argparse
import asyncio
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


def main() -> None:
    ap = argparse.ArgumentParser(prog="harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="gera ou mantém o projeto até o pytest passar")
    run.add_argument("projeto")
    run.add_argument("requisito")
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
    requisito = Requisito(Path(args.requisito))
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
