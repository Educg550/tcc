"""Cobertura de linhas vivas do prejanus-back: relatório JSON do coverage.py menos as faixas de codigo-morto.json.

uso (de demos/): uv run python caronte/cobertura.py <cobertura.json>
"""

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def linhas_vivas(relatorio, morto):
    mortas = {}
    for i in morto["itens"]:
        mortas.setdefault(i["arquivo"], set()).update(range(i["inicio"], i["fim"] + 1))
    total = cobertas = 0
    for arquivo, dados in relatorio["files"].items():
        excluir = mortas.get(f"prejanus-back/{arquivo}", set())
        executadas = set(dados["executed_lines"]) - excluir
        total += len(executadas) + len(set(dados["missing_lines"]) - excluir)
        cobertas += len(executadas)
    return cobertas, total


def test_desconta_codigo_morto():
    relatorio = {"files": {"src/a.py": {"executed_lines": [1, 2, 5], "missing_lines": [3, 4, 6]}}}
    morto = {"itens": [{"arquivo": "prejanus-back/src/a.py", "inicio": 4, "fim": 5}]}
    assert linhas_vivas(relatorio, morto) == (2, 4)


if __name__ == "__main__":
    cobertas, total = linhas_vivas(json.loads(Path(sys.argv[1]).read_text()),
                                   json.loads((AQUI / "codigo-morto.json").read_text()))
    print(f"linhas vivas cobertas: {cobertas}/{total} ({100 * cobertas / total:.1f}%)")
