"""Regressão da rodada com lições: sessão interrompida por custo ou tempo gravou código
que nem importava, sem passar pelo gate, e TDD e rework entregaram app fora do ar."""

import asyncio
import json
import subprocess
import sys

import pytest

from caronte.tdd_revisao import EtapaTDDRevisao
from harness.models.agentes import Resposta
from harness.models.dominio import Alvo, Arquivo, Mudanca, Projeto, ResultadoPytest
from harness.models.etapas import EtapaTDD
from harness.models.politicas import Batch, Orcamento
from harness.models.tracing import Trace

TESTES = """from app import dobro, triplo, metade, nome


def test_dobro():
    assert dobro(2) == 4


def test_triplo():
    assert triplo(2) == 6


def test_metade():
    assert metade(4) == 2


def test_nome():
    assert nome() == "x"
"""
# Dois de quatro testes passam.
PARCIAL = 'def dobro(n):\n    return 2 * n\n\ndef triplo(n):\n    return 3 * n\n\ndef metade(n):\n    return 0\n\ndef nome():\n    return ""\n'
# Três de quatro.
MELHOR = PARCIAL.replace("return 0", "return n // 2")
# O defeito da rodada: nome indefinido no import derruba a coleta inteira.
QUEBRADO = "from util import formatar\n" + MELHOR + "\nPADRAO = Indefinido()\n"


class ProjetoLocal(Projeto):
    """pytest de verdade, no python do harness: sem o uv isolado, o teste não depende de rede."""

    def rodar_pytest(self):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                           cwd=self.raiz, capture_output=True, text=True,
                           env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": ""})
        return ResultadoPytest.de_saida(r.stdout + r.stderr, r.returncode == 0)


class Roteiro:
    """Cada sessão é (arquivos, limite); limite diferente de False encerra por interrupção."""

    model_id = "roteiro"

    def __init__(self, *sessoes):
        self.sessoes = list(sessoes)

    def preparar(self, *args):
        pass

    async def propor(self, prompt):
        arquivos, limite = self.sessoes.pop(0)
        resposta = dict(custo_usd=0.5, input_tokens=10, output_tokens=5, total_tokens=15)
        if limite is False:
            return Resposta(mudanca=Mudanca(arquivos=[Arquivo(caminho=c, conteudo=t) for c, t in arquivos.items()]),
                            **resposta)
        mudanca = Mudanca(arquivos=[Arquivo(caminho=c, conteudo=t) for c, t in arquivos.items()]) if arquivos else None
        return Resposta(mudanca=mudanca, erro="Orçamento esgotado", limite=limite, **resposta)


def rodar(tmp_path, *sessoes, classe=EtapaTDD, passos=10):
    projeto = ProjetoLocal(tmp_path, Alvo("", "", "3.11", ()))
    projeto.preparar()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_app.py").write_text(TESTES)
    etapa = classe("code", Roteiro(*sessoes), Batch(), Orcamento(passos, 100, 600),
                   Trace(projeto.saida / "trace.jsonl"))
    return projeto, asyncio.run(etapa.executar("requisito", projeto))


def eventos(projeto):
    return [json.loads(l) for l in (projeto.saida / "trace.jsonl").read_text().splitlines()]


@pytest.mark.parametrize("limite,motivo", [("custo", "custo"), ("tempo", "tempo"), (None, "erro_modelo")])
def test_interrompida_que_nao_sobe_volta_a_ultima_verificada(tmp_path, limite, motivo):
    projeto, parte = rodar(tmp_path, ({"app.py": PARCIAL}, False),
                           ({"app.py": QUEBRADO, "util.py": "def formatar(): ...\n"}, limite))

    assert not parte["ok"] and parte["motivo"] == motivo
    assert parte["interrompida"] == "descartada"
    # O gate rodou na proposta interrompida e mediu o app quebrado.
    assert [h["passed"] for h in parte["historico"]] == [2, 0]
    # O que fica em disco, e é o que o gabarito mede, é a versão verificada.
    assert (tmp_path / "app.py").read_text() == PARCIAL
    assert not (tmp_path / "util.py").exists()
    assert parte["arquivos"] == ["app.py"]
    assert projeto.rodar_pytest().contagem["passed"] == 2
    # A sessão descartada continua paga e contada.
    assert parte["passos"] == 2 and parte["cost_usd"] == 1.0 and parte["total_tokens"] == 30
    assert eventos(projeto)[-1]["interrompida"] == "descartada"


def test_interrompida_que_melhora_fica(tmp_path):
    projeto, parte = rodar(tmp_path, ({"app.py": PARCIAL}, False), ({"app.py": MELHOR}, "tempo"))

    assert parte["interrompida"] == "mantida"
    assert [h["passed"] for h in parte["historico"]] == [2, 3]
    assert projeto.rodar_pytest().contagem["passed"] == 3


def test_interrompida_que_empata_fica(tmp_path):
    empate = PARCIAL.replace("return 3 * n", "return 0").replace('return ""', 'return "x"')
    projeto, parte = rodar(tmp_path, ({"app.py": PARCIAL}, False), ({"app.py": empate}, "custo"))

    assert parte["interrompida"] == "mantida"
    assert (tmp_path / "app.py").read_text() == empate


def test_interrompida_compara_com_a_anterior_e_nao_com_a_melhor(tmp_path):
    """Só a proposta anterior está em disco: é para ela que a reversão volta."""
    projeto, parte = rodar(tmp_path, ({"app.py": MELHOR}, False), ({"app.py": PARCIAL}, False),
                           ({"app.py": PARCIAL.replace("dobro", "dobro_")}, "tempo"))

    assert [h["passed"] for h in parte["historico"]] == [3, 2, 0]
    assert (tmp_path / "app.py").read_text() == PARCIAL


def test_primeira_sessao_interrompida_fica_por_falta_de_versao_verificada(tmp_path):
    projeto, parte = rodar(tmp_path, ({"app.py": QUEBRADO}, "custo"))

    assert parte["interrompida"] == "mantida" and parte["historico"][0]["passed"] == 0
    assert (tmp_path / "app.py").exists()


def test_interrompida_sem_edicao_nao_roda_gate_nem_mexe_no_disco(tmp_path):
    projeto, parte = rodar(tmp_path, ({"app.py": PARCIAL}, False), ({}, "tempo"), passos=2)

    assert [h["passed"] for h in parte["historico"]] == [2]
    assert (tmp_path / "app.py").read_text() == PARCIAL
    assert "interrompida" not in parte


def test_tdd_revisao_reverte_testes_e_codigo_juntos(tmp_path):
    testes_ruins = TESTES.replace('== "x"', '== "y"')
    projeto, parte = rodar(tmp_path, ({"app.py": PARCIAL}, False),
                           ({"app.py": QUEBRADO, "tests/test_app.py": testes_ruins}, "tempo"),
                           classe=EtapaTDDRevisao)

    assert parte["interrompida"] == "descartada"
    assert (tmp_path / "tests/test_app.py").read_text() == TESTES
    assert (tmp_path / "app.py").read_text() == PARCIAL
    # As versões registradas mostram a revisão interrompida e o retorno ao original.
    versoes = [json.loads((projeto.saida / "revisoes-testes" / f"{v['versao']:03}.json").read_text())
               for v in parte["versoes_testes"]]
    assert [v["tests/test_app.py"] for v in versoes] == [TESTES, testes_ruins, TESTES]
    assert parte["versoes_testes"][-1]["sha256"] == parte["impressao"] == projeto.impressao()
