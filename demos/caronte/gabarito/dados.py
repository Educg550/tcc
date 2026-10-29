import json
import re
from pathlib import Path

CARONTE = Path(__file__).parent.parent


def respostas_da_fixture():
    sql = (CARONTE / "fixture-consulta-forms.sql").read_text()
    return dict(re.findall(r"^    \('([a-z0-9-]+)', '([^']*)'\),?$", sql, re.M))


def secoes_do_formulario():
    form = json.loads((CARONTE / "formulario-mestrado.json").read_text())
    return [[f["name"] for f in s["fields"]] for s in form["sections"]]


ANEXOS = sorted(p.name for p in (CARONTE / "uploads-consulta").glob("*.pdf"))
