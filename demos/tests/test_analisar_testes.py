import json

import pytest

from caronte import analisar_testes as coletor


def test_selecao_hashes_e_reproducao(tmp_path, monkeypatch):
    monkeypatch.setattr(coletor, "RAIZ", tmp_path)
    monkeypatch.setattr(coletor, "RUNS", {"tdd": "run"})
    run = tmp_path / "demos/runs/caronte/run"
    (run / "_harness").mkdir(parents=True)
    teste = run / "test_x.py"
    teste.write_text("def test_x():\n    assert True\n")
    (run / "app.py").write_text("sintaxe invalida (")
    manifesto = {"test_x.py": {"tipo": "testes_autorais", "sha256": coletor.sha256(teste.read_bytes())},
                 "app.py": {"tipo": "producao", "sha256": "ignorado"}}
    (run / "_harness/MANIFESTO_ENTREGA.json").write_text(json.dumps(manifesto))
    base = tmp_path / "demos/caronte/piloto-v2"
    (base / "gabarito").mkdir(parents=True)
    for rel in ("gabarito/test_x.py", "gabarito/conftest.py", "ambiente.py"):
        (base / rel).write_text("raise RuntimeError('nao executar')\n")
    (base / "gabarito/split.py").write_text("sintaxe invalida (")
    r = coletor.executar()["projetos"]
    assert r["tdd"]["resumo"]["arquivos"] == 1
    assert r["gabarito_completo"]["resumo"]["arquivos"] == 3
    saida = tmp_path / "demos/analises/prejanus-back"
    antes = [(saida / p).read_bytes() for p in ("testes.json", "testes.csv")]
    coletor.executar()
    assert antes == [(saida / p).read_bytes() for p in ("testes.json", "testes.csv")]
    teste.write_text("mudou\n")
    with pytest.raises(AssertionError):
        coletor.executar()
