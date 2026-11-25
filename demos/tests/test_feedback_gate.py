"""Regressão da rodada com lições, TDD com revisão: as três verificações deram 15/58 porque
o coder nunca viu a causa (coluna do ORM divergente do esquema). Ela só estava nos logs do
app, que não iam ao prompt com o app de pé; o pouco que ia era o fim da saída do pytest.
E a mensagem de falha proibia mexer nos testes, contra o prompt da própria variante."""

import asyncio
import subprocess
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

import caronte.piloto_v2 as piloto_v2
from caronte.piloto_v2 import ProjetoV2, resumir_logs
from caronte.tdd_revisao import EtapaTDDRevisao
from harness.models.agentes import Resposta
from harness.models.dominio import Alvo, Arquivo, Mudanca, Projeto, ResultadoPytest
from harness.models.etapas import EtapaTDD
from harness.models.observacoes import LIMITE_SAIDA, PytestFalhou
from harness.models.politicas import Batch, Orcamento
from harness.models.tracing import Trace

GATE = Path(__file__).parent / "fixtures/gate-revisao"
SAIDA = (GATE / "pytest.txt").read_text()
LOGS = {p.name: p.read_text() for p in sorted(GATE.glob("app-*.log"))}
CAUSA = "coluna submission.recommender_form_ids não existe"
PROIBE = "Não altere os testes"


# Ponto 1: a mensagem de falha segue a regra da variante sobre os testes.

def test_falha_proibe_alterar_testes_por_padrao():
    assert PROIBE in PytestFalhou("1 failed").como_prompt()


def test_falha_na_revisao_permite_revisar_testes_com_registro():
    prompt = PytestFalhou("1 failed", instrucao=EtapaTDDRevisao.instrucao_falha).como_prompt()
    assert PROIBE not in prompt
    assert "tests/REVISOES.md" in prompt


@pytest.mark.parametrize("grupo", ["tdd", "rework", "tdd-revisao"])
def test_mensagem_de_falha_concorda_com_o_prompt_do_coder(tmp_path, grupo):
    """A contradição da rodada: o prompt da revisão liberava `tests/`, a falha proibia."""
    from caronte.piloto_v3 import GRUPOS, REQUISITO
    from harness.models.dominio import Requisito

    requisito = Requisito(REQUISITO)
    harness = GRUPOS[grupo](Projeto(tmp_path, requisito.alvo), requisito, Batch(), com_cua=False)
    coder = harness.agente("coder", requisito.modelos["coder"], EtapaTDD)
    etapa = harness.etapa("code", coder, EtapaTDD)
    revisa = "REVISOES.md" in coder._agno.instructions
    assert revisa is (grupo == "tdd-revisao")
    prompt = PytestFalhou("1 failed", instrucao=etapa.instrucao_falha).como_prompt()
    assert (PROIBE in prompt) is not revisa
    assert ("REVISOES.md" in prompt) is revisa


# Ponto 2: o recorte da saída do pytest guarda o começo e o fim.

def test_saida_curta_vai_inteira():
    saida = "F\nE   assert 1 == 2\n1 failed in 0.01s\n"
    prompt = PytestFalhou(saida).como_prompt()
    assert saida in prompt and "omitidos" not in prompt


def test_saida_longa_preserva_a_causa_no_comeco_e_a_contagem_no_fim():
    saida = "E   KeyError: 'causa_no_comeco'\n" + "ruído\n" * 80_000 \
        + "FAILED tests/test_x.py::test_x\n3 failed, 1 passed in 9.99s\n"
    prompt = PytestFalhou(saida).como_prompt()
    assert "causa_no_comeco" in prompt
    assert "3 failed, 1 passed in 9.99s" in prompt
    assert "omitidos" in prompt
    assert len(prompt) < LIMITE_SAIDA + 1000


def test_saida_real_do_gate_leva_primeiro_traceback_e_resumo():
    prompt = PytestFalhou(SAIDA).como_prompt()
    assert "ERROR at setup of test_comentario_criacao_e_consulta" in prompt
    assert "tests/helpers.py:28: in source_edict" in prompt
    assert "27 failed, 15 passed, 16 errors in 2.56s" in prompt
    assert len(prompt) < LIMITE_SAIDA + 1000


# Ponto 2: os logs do app chegam ao coder.

def test_regressao_a_causa_nao_estava_na_saida_do_pytest():
    """Nenhum recorte da saída resolve: é preciso anexar os logs."""
    assert CAUSA not in SAIDA
    assert any(CAUSA in t for t in LOGS.values())


def test_resumo_dos_logs_traz_a_causa_e_corta_o_ruido():
    resumo = resumir_logs(LOGS.values())
    assert CAUSA in resumo
    assert 'Talvez você queira fazer referência à coluna "submission.recommenders_form_ids"' in resumo
    # Linhas de acesso e o prefixo do compose são ruído.
    assert "HTTP/1.1" not in resumo and "INFO:" not in resumo and "local-1  |" not in resumo
    # O mesmo erro em quatro backends aparece uma vez por log, não quatro vezes inteiro.
    assert resumo.count(CAUSA) <= 4
    assert len(resumo) <= piloto_v2.LIMITE_LOGS


def test_resumo_dos_logs_deduplica_backends_iguais():
    erro = "ERROR:    Exception in ASGI application\nTraceback (most recent call last):\n" \
           "  File \"/workspace/app.py\", line 3, in f\nValueError: boom\n"
    logs = ["".join(f"{nome}-1  | {linha}\n" for linha in erro.splitlines())
            for nome in ("local", "local-admin", "local-estudante")]
    resumo = resumir_logs(logs)
    assert resumo.count("ValueError: boom") == 1


def test_resumo_dos_logs_guarda_o_fim_de_log_enorme():
    log = "".join(f"local-1  | INFO:     1.2.3.4:5 - \"GET /x HTTP/1.1\" 500 Internal Server Error\n"
                  f"local-1  | linha {i} de traceback\n" for i in range(50_000))
    log += "local-1  | RuntimeError: a última\n"
    resumo = resumir_logs([log])
    assert resumo.rstrip().endswith("RuntimeError: a última")
    assert len(resumo) <= piloto_v2.LIMITE_LOGS


def test_resumo_dos_logs_so_com_acesso_fica_vazio():
    log = "prejanus-back-1  | INFO:     Started server process [1]\n" \
          "prejanus-back-1  | INFO:     192.168.96.18:33844 - \"POST /auth HTTP/1.1\" 200 OK\n"
    assert resumir_logs([log, ""]) == ""


def test_prompt_com_logs_traz_saida_logs_e_instrucao():
    prompt = PytestFalhou(SAIDA, logs=resumir_logs(LOGS.values())).como_prompt()
    assert CAUSA in prompt
    assert "27 failed, 15 passed, 16 errors" in prompt
    assert "## LOGS DO APP" in prompt
    assert prompt.rstrip().endswith(f"{PROIBE}.")


def test_prompt_sem_logs_nao_anuncia_secao_vazia():
    assert "LOGS DO APP" not in PytestFalhou("1 failed").como_prompt()


# A fiação no gate do piloto: rodar_pytest preenche os logs também com o app de pé.

@pytest.fixture
def gate(tmp_path, monkeypatch):
    """O gate sem Docker: o candidato grava os logs do fixture e o pytest devolve o roteiro."""
    estado = {"subiu": True, "saida": SAIDA, "rc": 1}

    @contextmanager
    def candidato(raiz, saida):
        saida.mkdir(parents=True, exist_ok=True)
        yield estado["subiu"]
        for nome, texto in LOGS.items():
            (saida / nome).write_text(texto)

    def rodar(*args, **kwargs):
        return subprocess.CompletedProcess([], estado["rc"], estado["saida"], "")

    monkeypatch.setattr(piloto_v2, "candidato", candidato)
    monkeypatch.setattr(piloto_v2.subprocess, "run", rodar)
    monkeypatch.setattr(piloto_v2, "pytest_gabarito", rodar)
    return estado


@pytest.mark.parametrize("grupo", ["tdd", "tdd-revisao", "rework"])
def test_gate_com_app_de_pe_e_falha_anexa_os_logs(tmp_path, gate, grupo):
    r = ProjetoV2(tmp_path, None, grupo).rodar_pytest()
    assert (r.passed, r.failed, r.errors) == (15, 27, 16)
    assert r.saida.strip() == SAIDA.strip()
    assert CAUSA in r.logs
    # O arquivo de evidência do gate continua como antes.
    assert CAUSA in (tmp_path / "_harness/pytest-1.txt").read_text()


def test_gate_verde_nao_anexa_logs(tmp_path, gate):
    gate.update(saida="58 passed in 3.00s\n", rc=0)
    r = ProjetoV2(tmp_path, None, "tdd").rodar_pytest()
    assert r.passou and r.logs == ""


def test_gate_com_app_fora_do_ar_leva_o_log_de_subida(tmp_path, gate, monkeypatch):
    gate["subiu"] = False
    monkeypatch.setitem(LOGS, "app-local.log", "local-1  | Traceback (most recent call last):\n"
                        "local-1  |   File \"/workspace/app.py\", line 1, in <module>\n"
                        "local-1  | ModuleNotFoundError: No module named 'routers'\n")
    r = ProjetoV2(tmp_path, None, "tdd").rodar_pytest()
    assert not r.passou and "nenhum teste foi executado" in r.saida
    assert "ModuleNotFoundError: No module named 'routers'" in r.logs


# De ponta a ponta na etapa: o prompt seguinte à falha leva a causa e a instrução certa.

class Roteiro:
    model_id = "roteiro"

    def __init__(self):
        self.prompts = []

    def preparar(self, *args):
        pass

    async def propor(self, prompt):
        self.prompts.append(prompt)
        return Resposta(mudanca=Mudanca(arquivos=[Arquivo(caminho="app.py", conteudo="x = 1\n")]),
                        custo_usd=0.0, input_tokens=0, output_tokens=0, total_tokens=0)


class ProjetoFalhando(Projeto):
    def rodar_pytest(self):
        return replace(ResultadoPytest.de_saida(SAIDA, False), logs=resumir_logs(LOGS.values()))


@pytest.mark.parametrize("classe,proibe", [(EtapaTDD, True), (EtapaTDDRevisao, False)])
def test_etapa_devolve_causa_e_instrucao_da_variante(tmp_path, classe, proibe):
    projeto = ProjetoFalhando(tmp_path, Alvo("", "", "3.11", ()))
    projeto.preparar()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_x.py").write_text("def test_x():\n    assert False\n")
    agente = Roteiro()
    etapa = classe("code", agente, Batch(), Orcamento(2, 100, 600), Trace(projeto.saida / "trace.jsonl"))
    asyncio.run(etapa.executar("requisito", projeto))

    feedback = agente.prompts[1]
    assert CAUSA in feedback
    assert "27 failed, 15 passed, 16 errors" in feedback
    assert (PROIBE in feedback) is proibe
