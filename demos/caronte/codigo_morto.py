"""Gera codigo-morto.json: código morto do caronte-core congelado, em faixas de linhas.

uso (de demos/): uv run python caronte/codigo_morto.py
"""

import json
import os
import re
import subprocess
from pathlib import Path

import vulture

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1] / "caronte-core"
KNIP = "knip@5.88.1"
# o webpack.config.js usa como `insert` do style-loader, e o knip não segue esse caminho
FALSO_POSITIVO_KNIP = {"static-assets/insert-function.js"}


def python():
    os.chdir(RAIZ)
    # função decorada é rota, hook ou fixture registrada pelo framework; Config é lida pelo Pydantic
    v = vulture.Vulture(ignore_names=["Config"], ignore_decorators=["@*"])
    v.scavenge(["forms/app", "prejanus-back/src"],
               exclude=["*/tests/*", "*/test/*", "conftest.py", "test_*.py", "*/migrations/*"])
    for i in v.get_unused_code():
        if i.typ in ("function", "class", "method", "property", "unreachable_code"):
            arquivo = os.path.relpath(i.filename, RAIZ)
            if i.typ != "unreachable_code":
                assert i.name in linhas(arquivo)[i.first_lineno - 1], (arquivo, i.name)
            yield item(arquivo, i.first_lineno, i.last_lineno, i.typ, i.name, "vulture")


def js(projeto):
    subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=RAIZ / projeto, check=True)
    saida = subprocess.run(
        ["npx", "-y", KNIP, "--no-progress", "--reporter", "json", "--include", "files,exports",
         "-c", str(AQUI / "knip.json")],
        cwd=RAIZ / projeto, capture_output=True, text=True).stdout
    relatorio = json.loads(saida)
    for f in relatorio["files"]:
        arquivo = f"{projeto}/{f}"
        if arquivo not in FALSO_POSITIVO_KNIP:
            yield item(arquivo, 1, len(linhas(arquivo)), "file", None, "knip")
    for issue in relatorio["issues"]:
        arquivo = f"{projeto}/{issue['file']}"
        for e in issue["exports"]:
            # export que não é função executa ao carregar o módulo, então nunca vira linha morta
            if re.search(r"\bfunction\b|=>", linhas(arquivo)[e["line"] - 1]):
                yield item(arquivo, e["line"], fim_por_chaves(arquivo, e["line"]), "function", e["name"], "knip")


def fim_por_chaves(arquivo, inicio):
    texto = linhas(arquivo)
    profundidade = 0
    for n in range(inicio, len(texto) + 1):
        profundidade += texto[n - 1].count("{") - texto[n - 1].count("}")
        if profundidade == 0 and "{" in "".join(texto[inicio - 1:n]):
            assert texto[n - 1].rstrip().endswith("}"), (arquivo, inicio, n)
            return n
    raise AssertionError((arquivo, inicio))


def linhas(arquivo):
    return (RAIZ / arquivo).read_text().splitlines()


def item(arquivo, inicio, fim, tipo, nome, ferramenta):
    return {"arquivo": arquivo, "inicio": inicio, "fim": fim, "tipo": tipo, "nome": nome, "ferramenta": ferramenta}


if __name__ == "__main__":
    itens = [*python(), *js("prejanus-front"), *js("static-assets")]
    (AQUI / "codigo-morto.json").write_text(json.dumps({
        "commit": "46b89c1",
        "comando": "uv run python caronte/codigo_morto.py (de demos/)",
        "ferramentas": {"vulture": vulture.__version__, "knip": KNIP.split("@")[1]},
        "itens": sorted(itens, key=lambda i: (i["arquivo"], i["inicio"])),
    }, indent=2, ensure_ascii=False) + "\n")
