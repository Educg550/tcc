"""Sintaxe e Radon do Python gerado, sem importar ou executar os aplicativos."""

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import tokenize
from importlib.metadata import version
from pathlib import Path
from statistics import mean

from radon.complexity import add_inner_blocks, cc_rank, cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze

IGNORADOS = ("_harness", "__pycache__", "node_modules", "venv")


def analisar_arquivo(caminho: Path, raiz: Path) -> dict:
    dados = caminho.read_bytes()
    registro = {
        "arquivo": caminho.relative_to(raiz).as_posix(),
        "sha256": hashlib.sha256(dados).hexdigest(),
    }
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(dados).readline)
        codigo = dados.decode(encoding)
        compile(codigo, registro["arquivo"], "exec", dont_inherit=True, optimize=0)
    except (SyntaxError, UnicodeError, LookupError) as erro:
        return {**registro, "erro": {
            "tipo": type(erro).__name__,
            "mensagem": str(erro),
            "linha": getattr(erro, "lineno", None),
        }}
    return {
        **registro,
        "raw": analyze(codigo)._asdict(),
        "cc": [
            {"nome": b.fullname, "linha": b.lineno, "cc": b.complexity,
             "rank": cc_rank(b.complexity)}
            for b in sorted(add_inner_blocks(cc_visit(codigo)), key=lambda b: b.lineno)
            if b.letter in ("F", "M")
        ],
        "mi": mi_visit(codigo, multi=False),
        "halstead": h_visit(codigo).total._asdict(),
    }


def analisar_run(raiz: Path) -> dict:
    partes = {"implementacao": [], "testes": []}
    for pasta, diretorios, arquivos in os.walk(raiz):
        diretorios[:] = sorted(d for d in diretorios if not d.startswith(".")
                               and d not in IGNORADOS)
        for nome in sorted(arquivos):
            if not nome.endswith(".py"):
                continue
            caminho = Path(pasta) / nome
            relativo = caminho.relative_to(raiz)
            teste = ("tests" in relativo.parts or "test" in relativo.parts
                     or nome == "conftest.py" or nome.startswith("test_")
                     or nome.endswith("_test.py"))
            partes["testes" if teste else "implementacao"].append(analisar_arquivo(caminho, raiz))
    resultado = {}
    for parte, arquivos in partes.items():
        erros = sum("erro" in a for a in arquivos)
        status = "ausente" if not arquivos else "erro_sintaxe" if erros else "ok"
        cc = [b["cc"] for a in arquivos for b in a.get("cc", [])]
        metricas = None
        if status == "ok":
            metricas = {
                "sloc": sum(a["raw"]["sloc"] for a in arquivos),
                "lloc": sum(a["raw"]["lloc"] for a in arquivos),
                "funcoes": len(cc),
                "cc_media": mean(cc) if cc else None,
                "cc_max": max(cc) if cc else None,
                "cc_acima_10_pct": 100 * sum(c > 10 for c in cc) / len(cc) if cc else None,
                "mi_min": min(a["mi"] for a in arquivos),
            }
        resultado[parte] = {"status": status, "erros": erros, "metricas": metricas,
                            "arquivos": arquivos}
    return resultado


def tem_pagina(raiz: Path) -> bool:
    """O requisito e um formulario web: sem pagina servida nao ha aplicacao a avaliar."""
    return any(not any(parte.startswith(".") or parte in IGNORADOS
                       for parte in arquivo.relative_to(raiz).parts[:-1])
               for arquivo in raiz.rglob("index.html"))


def inelegivel(run: dict) -> str | None:
    """Motivo para ficar de fora do ranking, ou None. Esqueleto e placeholder saem
    pela estrutura do codigo: sem funcao definida ou sem nenhum ponto de decisao."""
    implementacao = run["implementacao"]
    if implementacao["status"] != "ok":
        return implementacao["status"]
    if not run["etapas_ok"]:
        return "etapas_sem_sucesso"
    metricas = implementacao["metricas"]
    if not metricas["funcoes"]:
        return "sem_funcao"
    if metricas["cc_max"] < 2:
        return "sem_decisao"
    if not run["pagina"]:
        return "sem_pagina"
    return None


def ordem(run: dict) -> tuple:
    metricas = run["implementacao"]["metricas"]
    return -metricas["mi_min"], metricas["cc_max"], run["run"]


def executar(batch: Path) -> dict:
    pastas = sorted((p for p in batch.glob("*/run[0-9]*")
                     if p.is_dir() and p.name[3:].isdigit()),
                    key=lambda p: (p.parent.name, int(p.name[3:])))
    if not pastas:
        raise SystemExit(f"Nenhuma run encontrada em {batch}")
    runs = []
    for pasta in pastas:
        for grupo in ("baseline", "tdd"):
            raiz = pasta / grupo
            log = raiz / "_harness" / "RUN.log"
            dados = json.loads(log.read_text()) if log.is_file() else {}
            run = {"run": raiz.relative_to(batch).as_posix(), "grupo": grupo,
                   "modelo": dados.get("alvo", {}).get("modelos", {}).get("coder"),
                   "etapas_ok": all(s["ok"] for s in dados["stages"]) if dados.get("stages") else None,
                   "pytest_final": dados.get("pytest_final"), "pagina": tem_pagina(raiz),
                   **analisar_run(raiz)}
            run["inelegivel"] = inelegivel(run)
            run["posicao"] = None
            runs.append(run)
    ranking = sorted((r for r in runs if not r["inelegivel"]), key=ordem)
    for posicao, run in enumerate(ranking, 1):
        run["posicao"] = posicao
    linhas = [{"run": run["run"], "modelo": run["modelo"], "grupo": run["grupo"], "parte": parte,
               "etapas_ok": run["etapas_ok"], "inelegivel": run["inelegivel"],
               "posicao": run["posicao"], "status": run[parte]["status"],
               "arquivos": len(run[parte]["arquivos"]), "erros": run[parte]["erros"],
               **(run[parte]["metricas"] or {})}
              for run in runs for parte in ("implementacao", "testes")]
    relatorio = {"python": platform.python_version(), "radon": version("radon"), "runs": runs}
    (batch / "radon.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    colunas = list(dict.fromkeys(k for linha in linhas for k in linha))
    with (batch / "radon.csv").open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(linhas)
    print(f"{len(runs)} runs, {len(ranking)} elegiveis: "
          f"{batch / 'radon.json'} e {batch / 'radon.csv'}")
    for run in ranking[:5]:
        metricas = run["implementacao"]["metricas"]
        print(f'{run["posicao"]:>3}  {run["run"]:<26} '
              f'mi_min={metricas["mi_min"]:6.2f}  cc_max={metricas["cc_max"]:>3}  '
              f'funcoes={metricas["funcoes"]:>3}  sloc={metricas["sloc"]:>4}')
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", nargs="?", type=Path, default=Path(__file__).parent / "runs" / "batch")
    executar(parser.parse_args().batch)
