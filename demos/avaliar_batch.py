"""Suite unica de Cypress contra cada run elegivel: a regua nao muda de run para run."""

import argparse
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

from harness.models.avaliacao import _veredito
from harness.models.dominio import Projeto, Requisito

SUITE = Path(__file__).parent / "avaliacao"
EXTRA = SUITE / "extra"


def avaliar(raiz: Path, requisito: Requisito, extra: bool = False) -> dict:
    destino = raiz / "_harness" / "cypress" / "e2e"
    shutil.rmtree(destino, ignore_errors=True)
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copy(SUITE / "campos.js", destino)
    for spec in (EXTRA if extra else SUITE).glob("*.cy.js"):
        shutil.copy(spec, destino)
    projeto = Projeto(raiz=raiz, alvo=requisito.alvo)
    projeto.preparar()
    inicio = time.time()
    blobs, saida = projeto.rodar_frontend()
    alvos = (
        [SimpleNamespace(identificador=f"E{i}") for i in range(1, 11)]
        if extra
        else requisito.deterministicos
    )
    criterios = [_veredito(c, blobs) for c in alvos]
    return {
        "criterios": criterios,
        "passou": sum(c["passou"] for c in criterios),
        "duration_s": round(time.time() - inicio, 2),
        # Sem blob nenhum o motivo esta no stdout: app que nao sobe, config invalida.
        "saida": "" if blobs else saida[-2000:],
    }


def executar(batch: Path, requisito: Requisito, extra: bool = False) -> list[dict]:
    if extra:
        # Desempate: so as que passaram em tudo. As demais ja estao ordenadas.
        anterior = json.loads((batch / "cypress.json").read_text())
        teto = max(a["passou"] for a in anterior)
        runs = [a for a in anterior if a["passou"] == teto]
    else:
        runs = [r for r in json.loads((batch / "radon.json").read_text())["runs"]
                if not r["inelegivel"]]
    destino = batch / ("cypress-extra.json" if extra else "cypress.json")
    feitos = {r["run"]: r for r in json.loads(destino.read_text())} if destino.is_file() else {}
    for i, run in enumerate(runs, 1):
        if run["run"] in feitos:
            continue
        resultado = avaliar(batch / run["run"], requisito, extra)
        feitos[run["run"]] = {"run": run["run"], "grupo": run["grupo"],
                              "modelo": run["modelo"], **resultado}
        print(f'{i:>4}/{len(runs)}  {run["run"]:<26} {resultado["passou"]:>2}/'
              f'{len(resultado["criterios"])}  {resultado["duration_s"]:>6.1f}s', flush=True)
        destino.write_text(json.dumps(list(feitos.values()), ensure_ascii=False, indent=2) + "\n")
    return list(feitos.values())


def custo(batch: Path, run: str) -> float:
    log = json.loads((batch / run / "_harness" / "RUN.log").read_text())
    return log.get("total_cost_usd") or float("inf")


def ranquear(batch: Path, grupo: str | None = None) -> list[dict]:
    """Comportamento decide. Entre runs que passam nos mesmos criterios o instrumento
    deterministico nao tem mais o que dizer sobre a aplicacao, entao desempata pelo custo
    de gerar - medido, de ordem total, e o que o TCC pergunta. Nao e nota de qualidade, e
    enviesa para o baseline, que gera menos: por isso o recorte por grupo importa."""
    avaliacoes = json.loads((batch / "cypress.json").read_text())
    if grupo:
        avaliacoes = [a for a in avaliacoes if a["grupo"] == grupo]
    return sorted(avaliacoes, key=lambda a: (-a["passou"], custo(batch, a["run"]), a["run"]))


def motivo_zero(avaliacao: dict) -> str:
    """App que nao sobe e app que sobe sem servir `/` reprovam igual, mas nao sao a mesma
    falha, e og5.1 precisa da diferenca para decidir o que reexecutar."""
    saida = avaliacao["saida"]
    if not saida:
        return ""
    return "nao serve /" if "Application startup complete" in saida else "nao subiu"


def confronto_radon(batch: Path) -> list[tuple[str, int]]:
    """O que o Radon escolheu contra o que a regua comportamental diz das mesmas runs.
    Reproduzivel a partir de radon.json e cypress.json, sem script solto."""
    elegiveis = [r for r in json.loads((batch / "radon.json").read_text())["runs"]
                 if not r["inelegivel"]]
    ordem = sorted(elegiveis, key=lambda r: (-r["implementacao"]["metricas"]["mi_min"],
                                             r["implementacao"]["metricas"]["cc_max"], r["run"]))
    placar = {a["run"]: a["passou"] for a in json.loads((batch / "cypress.json").read_text())}
    return [(r["run"], placar.get(r["run"], -1)) for r in ordem[:5]]


def relatar(batch: Path) -> None:
    for titulo, grupo in (("global", None), ("baseline", "baseline"), ("tdd", "tdd")):
        ranking = ranquear(batch, grupo)
        teto = ranking[0]["passou"] if ranking else 0
        empate = sum(a["passou"] == teto for a in ranking)
        print(f"\n── top 5 {titulo} ({len(ranking)} runs, {empate} empatadas em {teto}/12) ──")
        for posicao, a in enumerate(ranking[:5], 1):
            print(f'{posicao}  {a["run"]:<26} {a["modelo"].split("/")[1]:<20} '
                  f'{a["passou"]:>2}/12  US$ {custo(batch, a["run"]):.4f}')
    print("\n── top 5 do Radon (MI minimo desc) contra o Cypress ──")
    for posicao, (nome, placar) in enumerate(confronto_radon(batch), 1):
        print(f'{posicao}  {nome:<26} {"nao avaliada" if placar < 0 else f"{placar:>2}/12"}')
    zerados = [a for a in json.loads((batch / "cypress.json").read_text()) if a["passou"] == 0]
    if zerados:
        print(f"\n── {len(zerados)} runs com 0/12 ──")
        for a in zerados:
            print(f'   {a["run"]:<26} {motivo_zero(a) or "specs rodaram e falharam"}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", nargs="?", type=Path, default=Path(__file__).parent / "runs" / "batch")
    parser.add_argument("--requisito", type=Path,
                        default=Path(__file__).parent / "requisitos" / "01-formulario-docentes-glm")
    parser.add_argument("--so-relatar", action="store_true")
    parser.add_argument("--extra", action="store_true",
                        help="roda os criterios de desempate so nas runs empatadas no teto")
    args = parser.parse_args()
    if not args.so_relatar:
        executar(args.batch, Requisito(args.requisito), args.extra)
    relatar(args.batch)
