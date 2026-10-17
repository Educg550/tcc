"""Uso: demos/.venv/bin/python <este script> <raiz do TCC> <pasta da run>."""

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

import lizard


def sem_mortas(texto, faixas):
    linhas = texto.splitlines(keepends=True)
    for inicio, fim in faixas:
        for i in range(inicio - 1, fim):
            linhas[i] = "\n"
    return "".join(linhas)


def analisar(base, mortas):
    arquivos = []
    for p in sorted(base.rglob("*.py")):
        rel = p.relative_to(base)
        if any(parte.startswith((".", "_")) or parte in ("tests", "test", "migrations") for parte in rel.parts[:-1]):
            continue
        if p.name == "conftest.py" or p.name.startswith("test_") or p.name.endswith("_test.py"):
            continue
        texto = p.read_text()
        compile(texto, str(p), "exec")
        filtrado = sem_mortas(texto, mortas.get(str(rel), []))
        r = lizard.analyze_file.analyze_source_code(str(rel), filtrado)
        arquivos.append({
            "arquivo": str(rel), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "nloc": r.nloc,
            "funcoes": [{"nome": f.long_name, "inicio": f.start_line, "fim": f.end_line,
                         "nloc": f.nloc, "cc": f.cyclomatic_complexity} for f in r.function_list],
        })
    funcoes = [f for a in arquivos for f in a["funcoes"]]
    return {"arquivos": arquivos, "nloc": sum(a["nloc"] for a in arquivos),
            "funcoes": len(funcoes), "cc_medio": sum(f["cc"] for f in funcoes) / len(funcoes) if funcoes else None,
            "cc_maximo": max((f["cc"] for f in funcoes), default=None)}


if __name__ == "__main__":
    exemplo = "def f(x):\n    if x:\n        return 1\n    return 0\n"
    assert lizard.analyze_file.analyze_source_code("a.py", sem_mortas(exemplo, [(2, 3)])).function_list[0].cyclomatic_complexity == 1
    raiz, run = map(Path, sys.argv[1:])
    morto = raiz / "demos/caronte/codigo-morto.json"
    faixas = {}
    for item in json.loads(morto.read_text())["itens"]:
        if item["arquivo"].startswith("prejanus-back/"):
            faixas.setdefault(item["arquivo"].removeprefix("prejanus-back/"), []).append((item["inicio"], item["fim"]))
    resultado = {
        "lizard": importlib.metadata.version("lizard"),
        "codigo_morto_sha256": hashlib.sha256(morto.read_bytes()).hexdigest(),
        "limite": "Original: todo src do prejanus-back, exceto testes e migracoes, com faixas mortas removidas. Reconstrucao: apenas a consulta do piloto. Tamanhos e medias nao representam comparacao de escopos equivalentes.",
        "original": analisar(raiz / "caronte-core/prejanus-back", faixas),
        "baseline": analisar(run, {}),
    }
    (run / "_harness/LIZARD.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    for grupo in ("original", "baseline"):
        print(grupo, {k: v for k, v in resultado[grupo].items() if k != "arquivos"})
