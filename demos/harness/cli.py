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
    Modo,
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


def nova_run(raiz: Path, requisito_id: str, direto: bool) -> str:
    """O nome carrega quando a run rodou e o que ela é: sem isso duas execuções do mesmo
    caso de uso se sobrescrevem e o RUN.log deixa de dizer de qual delas veio."""
    grupo = "baseline" if direto else Modo.detectar(raiz).nome
    return f"{datetime.now():%Y%m%d-%H%M%S}-{grupo}-{requisito_id}"


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
        "avaliar", help="re-roda so o CUA e regrava o CUA.log da ultima run"
    )
    ava.add_argument("projeto")
    ava.add_argument("requisito")

    args = ap.parse_args()
    caminho = Path(args.requisito) if args.requisito else novo_caso(REQUISITOS)
    requisito = Requisito(caminho)
    raiz = Path(args.projeto)

    if args.cmd == "run":
        nome = nova_run(raiz, requisito.id, args.direto)
        projeto = Projeto(raiz, requisito.alvo, nome)
        classe = HarnessDireto if args.direto else HarnessTDD
        permissao = Batch() if args.yes else Interativa()
        log = asyncio.run(classe(projeto, requisito, permissao).executar())
        print(
            f"\npytest final: {log['pytest_final']}"
            f"  code: {log['stages'][-1]['motivo']}"
            f"  testes intactos: {log['integridade']['intacto']}"
        )
        print(f"logs: {projeto.saida}")
    else:
        projeto = Projeto(raiz, requisito.alvo, ultima_run(raiz))
        cua = Avaliador(requisito.modelos["cua"])
        r = asyncio.run(cua.avaliar(projeto, requisito))
        print(f"\naprovado_geral: {r['aprovado_geral']}\n{r['resumo']}")
        print(f"CUA.log: {projeto.saida / 'CUA.log'}")


if __name__ == "__main__":
    main()
