import json
from pathlib import Path
from tempfile import TemporaryDirectory

from avaliar_batch import ranquear


def test_extra_desempata_antes_do_custo():
    with TemporaryDirectory() as pasta:
        batch = Path(pasta)
        placar = {"barata": (12, 8, 0.01), "cara": (12, 10, 0.05), "quebrada": (3, None, 0.001)}
        for run, (passou, _, custo) in placar.items():
            (batch / run / "_harness").mkdir(parents=True)
            (batch / run / "_harness/RUN.log").write_text(json.dumps({"total_cost_usd": custo}))
        (batch / "cypress.json").write_text(json.dumps(
            [{"run": r, "grupo": "tdd", "passou": p} for r, (p, _, _) in placar.items()]))
        (batch / "cypress-extra.json").write_text(json.dumps(
            [{"run": r, "passou": e} for r, (_, e, _) in placar.items() if e is not None]))

        assert [a["run"] for a in ranquear(batch, "tdd")] == ["cara", "barata", "quebrada"]
