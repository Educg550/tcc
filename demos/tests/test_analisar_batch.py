from pathlib import Path
from tempfile import TemporaryDirectory

from analisar_batch import executar


def test_separacao_sintaxe_e_repetibilidade():
    with TemporaryDirectory() as pasta:
        batch = Path(pasta)
        for grupo in ("baseline", "tdd"):
            raiz = batch / "modelo" / "run1" / grupo
            raiz.mkdir(parents=True)
            (raiz / "app.py").write_text("raise RuntimeError('nao executar')\ndef f(x):\n    return 1 if x else 0\n")
        tdd = batch / "modelo/run1/tdd"
        (tdd / "tests").mkdir()
        (tdd / "tests/test_app.py").write_text("def test_f():\n    assert True\n")
        (tdd / "_harness").mkdir()
        (tdd / "_harness/invalido.py").write_text("def (")
        (tdd / ".venv").mkdir()
        (tdd / ".venv/invalido.py").write_text("def (")
        arquivo = batch / "modelo/run1/tdd-interrompida-123/tdd"
        arquivo.mkdir(parents=True)
        (arquivo / "app.py").write_text("def (")

        runs = executar(batch)["runs"]
        assert len(runs) == 2
        assert runs[0]["implementacao"] == runs[1]["implementacao"]
        assert runs[0]["implementacao"]["metricas"]["cc_max"] == 2
        assert runs[0]["testes"]["status"] == "ausente"
        assert runs[0]["testes"]["metricas"] is None
        assert runs[1]["testes"]["status"] == "ok"
        antes = [(batch / nome).read_bytes() for nome in ("radon.json", "radon.csv")]
        executar(batch)
        assert antes == [(batch / nome).read_bytes() for nome in ("radon.json", "radon.csv")]

        (tdd / "test_extra.py").write_text("return 1\n")
        run = executar(batch)["runs"][1]
        assert run["testes"]["status"] == "erro_sintaxe"
        assert run["testes"]["metricas"] is None
        assert run["implementacao"] == runs[1]["implementacao"]
        (tdd / "app.py").write_text("def (")
        assert executar(batch)["runs"][1]["implementacao"]["metricas"] is None


def test_esqueleto_sai_do_ranking():
    """Placeholder e esqueleto de backend nao podem ser ranqueados: saem pela
    estrutura (sem funcao, sem ponto de decisao), nao por MI ou contagem de linhas."""
    with TemporaryDirectory() as pasta:
        batch = Path(pasta)
        codigo = {
            "run1": "...\n",
            "run2": "from x import y\n\napp = y()\napp.mount('/s', y(), name='s')\n",
            "run3": "def index():\n    return open('i.html')\n",
            "run4": "def valida(v):\n    if not v:\n        return ['erro']\n    return []\n",
        }
        for nome, fonte in codigo.items():
            for grupo in ("baseline", "tdd"):
                raiz = batch / "modelo" / nome / grupo
                (raiz / "_harness").mkdir(parents=True)
                (raiz / "app.py").write_text(fonte)
                (raiz / "_harness/RUN.log").write_text(
                    '{"stages": [{"ok": true}], "alvo": {"modelos": {"coder": "m"}}}')
                (raiz / "index.html").write_text("<form></form>")

        motivos = {r["run"]: r["inelegivel"] for r in executar(batch)["runs"]}
        assert motivos["modelo/run1/baseline"] == "sem_funcao"
        assert motivos["modelo/run2/baseline"] == "sem_funcao"
        assert motivos["modelo/run3/baseline"] == "sem_decisao"
        assert motivos["modelo/run4/baseline"] is None

        # o MI dos tres excluidos e 100, o maximo: o ranking os premiaria primeiro
        runs = {r["run"]: r for r in executar(batch)["runs"]}
        assert runs["modelo/run1/baseline"]["implementacao"]["metricas"]["mi_min"] == 100
        assert runs["modelo/run4/baseline"]["posicao"] == 1

        # pagina so conta fora de _harness e de pasta oculta
        (batch / "modelo/run4/tdd/index.html").unlink()
        (batch / "modelo/run4/tdd/_harness/index.html").write_text("<form></form>")
        assert {r["run"]: r["inelegivel"] for r in executar(batch)["runs"]}["modelo/run4/tdd"] == "sem_pagina"
        (batch / "modelo/run4/tdd/publico").mkdir()
        (batch / "modelo/run4/tdd/publico/index.html").write_text("<form></form>")
        assert {r["run"]: r["inelegivel"] for r in executar(batch)["runs"]}["modelo/run4/tdd"] is None

        # etapa sem sucesso e sintaxe invalida tambem tem motivo proprio
        (batch / "modelo/run4/tdd/_harness/RUN.log").write_text('{"stages": [{"ok": false}]}')
        (batch / "modelo/run3/tdd/app.py").write_text("def (")
        motivos = {r["run"]: r["inelegivel"] for r in executar(batch)["runs"]}
        assert motivos["modelo/run4/tdd"] == "etapas_sem_sucesso"
        assert motivos["modelo/run3/tdd"] == "erro_sintaxe"
