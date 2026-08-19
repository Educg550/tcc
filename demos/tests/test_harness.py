from pathlib import Path

import pytest

from harness.loop import escrever
from harness.models import Arquivo, Mudanca


def _m(*pares):
    return Mudanca(arquivos=[Arquivo(caminho=c, conteudo=t) for c, t in pares])


def test_escrever_grava_dentro_da_raiz(tmp_path):
    escritos = escrever(_m(("app.py", "x = 1"), ("templates/i.html", "<b>")), tmp_path)
    assert escritos == ["app.py", "templates/i.html"]
    assert (tmp_path / "app.py").read_text() == "x = 1"
    assert (tmp_path / "templates/i.html").read_text() == "<b>"


def test_escrever_rejeita_caminho_relativo_para_fora(tmp_path):
    with pytest.raises(ValueError):
        escrever(_m(("../fora.py", "mal")), tmp_path)
    assert not (tmp_path.parent / "fora.py").exists()


def test_escrever_rejeita_caminho_absoluto(tmp_path):
    alvo = tmp_path.parent / "absoluto.py"
    with pytest.raises(ValueError):
        escrever(_m((str(alvo), "mal")), tmp_path)
    assert not alvo.exists()


def test_escopo_restringe_a_um_subdiretorio(tmp_path):
    assert escrever(_m(("tests/test_a.py", "def test_a(): pass")), tmp_path, escopo="tests")
    with pytest.raises(ValueError):
        escrever(_m(("app.py", "codigo de producao")), tmp_path, escopo="tests")
    assert not (tmp_path / "app.py").exists()


from harness.loop import contar_pytest, rodar_pytest


def test_contar_linha_verde():
    c = contar_pytest("=========== 27 passed in 1.24s ============")
    assert (c["passed"], c["failed"], c["errors"], c["total"]) == (27, 0, 0, 27)


def test_contar_linha_com_falhas_e_erros():
    c = contar_pytest("====== 5 failed, 2 errors in 0.4s =======")
    assert (c["passed"], c["failed"], c["errors"], c["total"]) == (0, 5, 2, 7)


def test_contar_sem_linha_de_resumo():
    c = contar_pytest("ERRO de importacao, nada coletado")
    assert c == {"passed": 0, "failed": 0, "errors": 0, "total": 0}


def test_rodar_pytest_num_projeto_de_verdade(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok(): assert True")
    (tmp_path / "tests" / "test_nao.py").write_text("def test_nao(): assert False")
    r = rodar_pytest(tmp_path)
    assert r.passou is False
    assert (r.passed, r.failed) == (1, 1)
    assert "test_nao" in r.saida


import json
import time

from harness.loop import Orcamento, trace


def test_orcamento_sem_estouro():
    assert Orcamento().estourou(passos=1, custo=0.01, inicio=time.time()) is None


def test_orcamento_estoura_por_passos():
    assert Orcamento(passos=3).estourou(3, 0.0, time.time()) == "passos"


def test_orcamento_estoura_por_custo():
    assert Orcamento(custo_usd=1.0).estourou(0, 1.0, time.time()) == "custo"


def test_orcamento_estoura_por_tempo():
    assert Orcamento(tempo_s=10).estourou(0, 0.0, time.time() - 11) == "tempo"


def test_trace_acumula_uma_linha_json_por_evento(tmp_path):
    alvo = tmp_path / "trace.jsonl"
    trace(alvo, {"passo": 1})
    trace(alvo, {"passo": 2})
    linhas = [json.loads(ln) for ln in alvo.read_text().splitlines()]
    assert [ln["passo"] for ln in linhas] == [1, 2]
