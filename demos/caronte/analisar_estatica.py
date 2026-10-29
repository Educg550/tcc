"""Análise estática das entregas válidas. De demos/: python -m caronte.analisar_estatica."""

import argparse
import csv
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from statistics import mean, median

from radon.complexity import add_inner_blocks, cc_rank, cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze

RAIZ = Path(__file__).resolve().parents[2]
RUNS = {
    "baseline": "05-prejanus-back-piloto-v3-baseline-20261023-221756",
    "tdd": "05-prejanus-back-piloto-v3-tdd-20261023-223904",
    "rework": "05-prejanus-back-piloto-v3-rework-20261024-000419",
    "tdd_revisao_exploratorio": "05-prejanus-back-piloto-v3-tdd-revisao-20261027-161847",
}


def sha256(dados):
    return hashlib.sha256(dados).hexdigest()


def sem_mortas(texto, faixas):
    linhas = texto.splitlines(keepends=True)
    for inicio, fim in faixas:
        assert 1 <= inicio <= fim <= len(linhas)
        linhas[inicio - 1:fim] = ["\n"] * (fim - inicio + 1)
    return "".join(linhas)


def analisar_arquivo(caminho, base, faixas=()):
    dados = caminho.read_bytes()
    nome = caminho.relative_to(base).as_posix()
    codigo = sem_mortas(dados.decode("utf-8"), faixas)
    compile(codigo, nome, "exec")
    return {
        "arquivo": nome, "sha256": sha256(dados),
        "analisado_sha256": sha256(codigo.encode()), "faixas_excluidas": faixas,
        "radon": {
            "raw": analyze(codigo)._asdict(),
            "funcoes": [{"nome": b.fullname, "inicio": b.lineno, "fim": b.endline,
                         "cc": b.complexity, "rank": cc_rank(b.complexity)}
                        for b in sorted(add_inner_blocks(cc_visit(codigo)), key=lambda b: (b.lineno, b.fullname))
                        if b.letter in ("F", "M")],
            "mi": mi_visit(codigo, multi=False), "halstead": h_visit(codigo).total._asdict(),
        },
    }


def distribuicao(valores):
    return {"n": len(valores), "media": mean(valores) if valores else None,
            "mediana": median(valores) if valores else None,
            "max": max(valores) if valores else None,
            "acima_10": sum(v > 10 for v in valores)}


def resumir(arquivos):
    rf = [f for a in arquivos for f in a["radon"]["funcoes"]]
    mi = [a["radon"]["mi"] for a in arquivos if a["radon"]["raw"]["sloc"]]
    return {
        "arquivos": len(arquivos),
        "radon_raw": {k: sum(a["radon"]["raw"][k] for a in arquivos)
                      for k in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments")},
        "radon_cc": distribuicao([f["cc"] for f in rf]),
        "radon_mi": {"arquivos_com_sloc": len(mi), "mediana": median(mi) if mi else None,
                     "min": min(mi) if mi else None},
    }


def executar(saida):
    morto = RAIZ / "demos/caronte/codigo-morto.json"
    faixas = {}
    for i in json.loads(morto.read_text())["itens"]:
        if i["arquivo"].startswith("prejanus-back/"):
            faixas.setdefault(i["arquivo"].removeprefix("prejanus-back/"), []).append((i["inicio"], i["fim"]))
    original = RAIZ / "caronte-core/prejanus-back"
    fontes = [p for p in sorted(original.rglob("*.py"))
              if not any(parte.startswith(".") or parte in ("tests", "test", "migrations", "__pycache__")
                         for parte in p.relative_to(original).parts[:-1])
              and p.name != "conftest.py" and not p.name.startswith("test_") and not p.name.endswith("_test.py")]
    projetos = {}
    for nome, excluir in (("original_bruto", {}), ("original_vivo", faixas)):
        arquivos = [analisar_arquivo(p, original, excluir.get(p.relative_to(original).as_posix(), ())) for p in fontes]
        projetos[nome] = {"origem": original.relative_to(RAIZ).as_posix(),
                          "resumo": resumir(arquivos), "arquivos": arquivos}
    for nome, pasta in RUNS.items():
        base = RAIZ / "demos/runs/caronte" / pasta
        manifesto = base / "_harness/MANIFESTO_ENTREGA.json"
        fontes = json.loads(manifesto.read_text())
        arquivos = []
        for rel, info in sorted(fontes.items()):
            if info["tipo"] == "producao" and rel.endswith(".py"):
                p = base / rel
                assert sha256(p.read_bytes()) == info["sha256"], p
                arquivos.append(analisar_arquivo(p, base))
        projetos[nome] = {"origem": base.relative_to(RAIZ).as_posix(),
                          "manifesto_sha256": sha256(manifesto.read_bytes()),
                          "resumo": resumir(arquivos), "arquivos": arquivos}
    resultado = {"ferramentas": {"radon": version("radon")},
                 "coletor_sha256": sha256(Path(__file__).read_bytes()),
                 "codigo_morto_sha256": sha256(morto.read_bytes()), "projetos": projetos}
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "estatica.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    with (saida / "estatica.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(("projeto", "arquivos", "radon_sloc", "radon_lloc", "radon_funcoes",
                         "radon_cc_media", "radon_cc_max", "radon_cc_acima_10", "radon_mi_mediana", "radon_mi_min"))
        for nome, p in projetos.items():
            r = p["resumo"]
            writer.writerow((nome, r["arquivos"],
                             r["radon_raw"]["sloc"], r["radon_raw"]["lloc"], r["radon_cc"]["n"],
                             r["radon_cc"]["media"], r["radon_cc"]["max"], r["radon_cc"]["acima_10"],
                             r["radon_mi"]["mediana"], r["radon_mi"]["min"]))
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=RAIZ / "demos/analises/prejanus-back")
    resultado = executar(parser.parse_args().saida)
    for nome, projeto in resultado["projetos"].items():
        print(nome, json.dumps(projeto["resumo"], ensure_ascii=False))
