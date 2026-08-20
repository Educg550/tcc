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


def test_proibido_veta_um_subdiretorio(tmp_path):
    with pytest.raises(ValueError):
        escrever(_m(("tests/test_x.py", "trapaca")), tmp_path, proibido="tests")
    assert not (tmp_path / "tests").exists()
    assert escrever(_m(("app.py", "x = 1")), tmp_path, proibido="tests")


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


def test_pytest_ini_isola_o_projeto_da_config_do_pai(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-k nome_que_nao_existe"\n'
    )
    projeto = tmp_path / "projeto"
    (projeto / "tests").mkdir(parents=True)
    (projeto / "app.py").write_text("valor = 42")
    (projeto / "tests" / "test_app.py").write_text(
        "from app import valor\n\n\ndef test_valor():\n    assert valor == 42\n"
    )
    assert rodar_pytest(projeto).passed == 0
    (projeto / "pytest.ini").write_text("[pytest]\npythonpath = .\n")
    assert rodar_pytest(projeto).passed == 1


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


import asyncio
from types import SimpleNamespace

from harness.loop import loop_tdd


class AgenteFake:
    """Devolve respostas enroladas, uma por chamada, como a Agno devolve."""

    def __init__(self, *mudancas):
        self.mudancas = list(mudancas)
        self.prompts = []

    async def arun(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(
            content=self.mudancas.pop(0),
            metrics=SimpleNamespace(cost=0.01, total_tokens=100),
        )


TESTE = Mudanca(
    arquivos=[
        Arquivo(
            caminho="tests/test_soma.py",
            conteudo="from calc import soma\n\n\ndef test_soma():\n    assert soma(1, 2) == 3\n",
        )
    ]
)
ERRADO = Mudanca(arquivos=[Arquivo(caminho="calc.py", conteudo="def soma(a, b):\n    return 0\n")])
CERTO = Mudanca(arquivos=[Arquivo(caminho="calc.py", conteudo="def soma(a, b):\n    return a + b\n")])


def test_loop_para_quando_o_pytest_fica_verde(tmp_path):
    asyncio.run(_loop_verde(tmp_path))


async def _loop_verde(tmp_path):
    escrever(TESTE, tmp_path)
    agente = AgenteFake(ERRADO, CERTO)
    r = await loop_tdd(agente, "implemente", tmp_path, Orcamento(), tmp_path / "trace.jsonl")
    assert r["ok"] is True
    assert r["motivo"] == "verde"
    assert r["passos"] == 2
    assert [h["failed"] for h in r["historico"]] == [1, 0]
    assert r["total_tokens"] == 200


def test_saida_do_pytest_volta_para_o_modelo(tmp_path):
    asyncio.run(_saida_volta(tmp_path))


async def _saida_volta(tmp_path):
    escrever(TESTE, tmp_path)
    agente = AgenteFake(ERRADO, CERTO)
    await loop_tdd(agente, "implemente", tmp_path, Orcamento(), tmp_path / "trace.jsonl")
    assert "test_soma" in agente.prompts[1]
    assert agente.prompts[1].startswith("implemente")


TRAPACA = Mudanca(
    arquivos=[Arquivo(caminho="tests/test_soma.py", conteudo="def test_soma(): pass")]
)


def test_loop_rejeita_escrita_em_tests_e_segue(tmp_path):
    asyncio.run(_loop_rejeita(tmp_path))


async def _loop_rejeita(tmp_path):
    escrever(TESTE, tmp_path)
    agente = AgenteFake(TRAPACA, CERTO)
    r = await loop_tdd(agente, "implemente", tmp_path, Orcamento(), tmp_path / "trace.jsonl")
    assert r["motivo"] == "verde"
    assert r["passos"] == 2
    assert len(r["historico"]) == 1
    assert "PROPOSTA REJEITADA" in agente.prompts[1]
    assert (tmp_path / "tests" / "test_soma.py").read_text() == TESTE.arquivos[0].conteudo
    linhas = [json.loads(ln) for ln in (tmp_path / "trace.jsonl").read_text().splitlines()]
    assert "erro" in linhas[0] and "pytest" in linhas[1]


def test_loop_para_no_orcamento_de_passos(tmp_path):
    asyncio.run(_loop_estoura(tmp_path))


async def _loop_estoura(tmp_path):
    escrever(TESTE, tmp_path)
    agente = AgenteFake(ERRADO, ERRADO)
    r = await loop_tdd(agente, "implemente", tmp_path, Orcamento(passos=2), tmp_path / "trace.jsonl")
    assert r["ok"] is False
    assert r["motivo"] == "passos"
    assert len((tmp_path / "trace.jsonl").read_text().splitlines()) == 2


from harness.agents import load


def test_load_le_prompt_do_disco():
    assert "mínimo" in load("diretiva_codigo_minimo")


def test_load_prompt_inexistente_estoura():
    with pytest.raises(FileNotFoundError):
        load("nao_existe")


from harness.run import build_run_log, contexto, modo


def test_modo_criacao_em_diretorio_ausente(tmp_path):
    assert modo(tmp_path / "novo") == "criacao"


def test_modo_criacao_em_diretorio_vazio(tmp_path):
    assert modo(tmp_path) == "criacao"


def test_modo_manutencao_com_codigo(tmp_path):
    (tmp_path / "app.py").write_text("x = 1")
    assert modo(tmp_path) == "manutencao"


def test_contexto_traz_codigo_e_ignora_git(tmp_path):
    (tmp_path / "app.py").write_text("codigo")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.py").write_text("segredo")
    saida = contexto(tmp_path)
    assert "app.py" in saida and "codigo" in saida
    assert "segredo" not in saida


def test_run_log_soma_custo_e_tokens():
    log = build_run_log(
        started_at="a",
        ended_at="b",
        total_duration_s=1.0,
        modo="criacao",
        requisito_id="01-x",
        stages=[{"cost_usd": 0.1, "total_tokens": 10}],
        loop={"cost_usd": 0.2, "total_tokens": 5, "retries": 1},
        pytest_final={"passed": 3},
        regressao=None,
        cua=None,
    )
    assert round(log["total_cost_usd"], 2) == 0.3
    assert log["total_tokens"] == 15
    assert log["total_retries"] == 1
    assert log["modo"] == "criacao"


import urllib.request

from harness.cua import app_rodando, porta_livre

APP_FAKE = """
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"vivo")

    def log_message(self, *a):
        pass


HTTPServer(("", int(os.environ["PORT"])), H).serve_forever()
"""


def test_porta_livre_devolve_porta_usavel():
    assert 1024 < porta_livre() < 65536


def test_app_rodando_sobe_e_derruba(tmp_path):
    (tmp_path / "app.py").write_text(APP_FAKE)
    with app_rodando(tmp_path) as url:
        assert urllib.request.urlopen(url, timeout=2).read() == b"vivo"
    with pytest.raises(Exception):
        urllib.request.urlopen(url, timeout=2)


def test_app_que_nao_sobe_estoura(tmp_path):
    (tmp_path / "app.py").write_text("raise SystemExit(1)")
    with pytest.raises(RuntimeError):
        with app_rodando(tmp_path):
            pass
