"""Métricas dos testes finais e do gabarito. De demos/: python -m caronte.analisar_testes."""

import csv
import json
from importlib.metadata import version
from pathlib import Path

from caronte.analisar_estatica import RAIZ, RUNS, analisar_arquivo, resumir, sha256


def executar():
    projetos = {}
    for nome, pasta in RUNS.items():
        base = RAIZ / "demos/runs/caronte" / pasta
        manifesto = base / "_harness/MANIFESTO_ENTREGA.json"
        arquivos = []
        for rel, info in sorted(json.loads(manifesto.read_text()).items()):
            if info["tipo"] in ("testes_autorais", "testes_fornecidos") and rel.endswith(".py"):
                p = base / rel
                assert sha256(p.read_bytes()) == info["sha256"], p
                arquivos.append(analisar_arquivo(p, base))
        projetos[nome] = {"origem": base.relative_to(RAIZ).as_posix(),
                          "manifesto_sha256": sha256(manifesto.read_bytes()),
                          "resumo": resumir(arquivos), "arquivos": arquivos}
    base = RAIZ / "demos/caronte/piloto-v2"
    fontes = sorted((base / "gabarito").glob("test_*.py"))
    assert fontes, "Gabarito não encontrado"
    fontes += [base / "gabarito/conftest.py", base / "ambiente.py"]
    arquivos = [analisar_arquivo(p, base) for p in fontes]
    projetos["gabarito_completo"] = {"origem": base.relative_to(RAIZ).as_posix(),
                                    "resumo": resumir(arquivos), "arquivos": arquivos}
    saida = RAIZ / "demos/analises/prejanus-back"
    saida.mkdir(parents=True, exist_ok=True)
    resultado = {"ferramentas": {"radon": version("radon")},
                 "coletor_sha256": sha256(Path(__file__).read_bytes()),
                 "projetos": projetos}
    (saida / "testes.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    with (saida / "testes.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(("suite", "arquivos", "sloc", "lloc", "funcoes", "cc_media", "cc_max",
                         "cc_acima_10", "mi_mediana", "mi_min"))
        for nome, projeto in projetos.items():
            r = projeto["resumo"]
            writer.writerow((nome, r["arquivos"], r["radon_raw"]["sloc"], r["radon_raw"]["lloc"],
                             r["radon_cc"]["n"], r["radon_cc"]["media"], r["radon_cc"]["max"],
                             r["radon_cc"]["acima_10"], r["radon_mi"]["mediana"], r["radon_mi"]["min"]))
    return resultado


if __name__ == "__main__":
    executar()
