import argparse
import asyncio
import json
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


def ultima_run(raiz: Path) -> str:
    """Reavaliar não abre run nova: o veredito pertence à execução que gerou o código."""
    runs = sorted(p.name for p in (raiz / "_harness").iterdir() if p.is_dir())
    if not runs:
        raise SystemExit(f"{raiz}/_harness não tem run para reavaliar")
    return runs[-1]


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

    ava = sub.add_parser(
        "avaliar", help="re-roda so o CUA e regrava o campo `cua` da ultima run"
    )
    ava.add_argument("projeto")
    ava.add_argument("requisito")

    args = ap.parse_args()
    caminho = Path(args.requisito) if args.requisito else novo_caso(REQUISITOS)
    requisito = Requisito(caminho)
    raiz = Path(args.projeto)

    if args.cmd == "run":
        nome = f"{datetime.now():%Y%m%d-%H%M%S}-{requisito.id}"
        projeto = Projeto(raiz, requisito.alvo, nome)
        classe = HarnessDireto if args.direto else HarnessTDD
        permissao = Batch() if args.yes else Interativa()
        log = asyncio.run(classe(projeto, requisito, permissao).executar())
        print(
            f"\npytest final: {log['pytest_final']}"
            f"  code: {log['stages'][-1]['motivo']}"
            f"  testes intactos: {log['integridade']['intacto']}"
            f"  cua: {log['cua']['aprovado_geral']}"
        )
        print(f"RUN.log: {projeto.saida / 'RUN.log'}")
    else:
        projeto = Projeto(raiz, requisito.alvo, ultima_run(raiz))
        cua = Avaliador(projeto.alvo.modelos["cua"])
        r = asyncio.run(cua.avaliar(projeto, requisito))
        destino = projeto.saida / "RUN.log"
        log = json.loads(destino.read_text(encoding="utf-8"))
        log["cua"] = r
        destino.write_text(
            json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\naprovado_geral: {r['aprovado_geral']}\n{r['resumo']}")
        print(f"RUN.log: {destino}")


if __name__ == "__main__":
    main()
