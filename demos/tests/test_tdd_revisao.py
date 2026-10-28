import asyncio
import json
from dataclasses import replace

import pytest

from caronte.tdd_revisao import EtapaTDDRevisao
from harness.models.agentes import Resposta
from harness.models.dominio import Arquivo, Mudanca, Projeto, ResultadoPytest
from harness.models.etapas import CODIGO
from harness.models.politicas import Batch, Orcamento
from harness.models.tracing import Resultado, Trace


def test_revisao_libera_testes_mas_preserva_validacao_e_configuracao(tmp_path):
    escopo = EtapaTDDRevisao.escopo
    texto = "def test_x():\n    assert 1 == 1\n"
    assert escopo.validar(tmp_path, "tests/test_x.py", texto) == tmp_path / "tests/test_x.py"
    with pytest.raises(ValueError):
        CODIGO.validar(tmp_path, "tests/test_x.py", texto)
    with pytest.raises(ValueError, match="não definidos"):
        escopo.validar(tmp_path, "tests/test_x.py", "def test_x():\n    pytest.skip()\n")
    with pytest.raises(SyntaxError):
        escopo.validar(tmp_path, "app.py", "def :")
    for nome in ("pytest.ini", "conftest.py", "_harness/gabarito.py", ".git/config", "../fora.py"):
        with pytest.raises(ValueError):
            escopo.validar(tmp_path, nome, "")


@pytest.mark.parametrize("interrompida", [False, True])
def test_preserva_testes_e_diff_inclusive_ao_interromper_antes_do_gate(tmp_path, interrompida):
    class ProjetoSimulado(Projeto):
        gates = 0

        def rodar_pytest(self):
            self.gates += 1
            return ResultadoPytest.de_saida(
                "1 failed" if self.gates == 1 else "1 passed", self.gates > 1
            )

    class Coder:
        model_id = "simulado"

        def preparar(self, projeto, escopo, *args):
            self.escopo = escopo

        async def propor(self, prompt):
            resposta = Resposta(
                mudanca=Mudanca(arquivos=[Arquivo(caminho="tests/test_x.py", conteudo="assert 2 == 2\n")]),
                custo_usd=0.02, input_tokens=10, output_tokens=5, total_tokens=15,
            )
            return replace(resposta, erro="limite", limite="custo") if interrompida else resposta

    projeto = ProjetoSimulado(tmp_path, None)
    projeto.preparar()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_x.py").write_text("assert 1 == 2\n")
    inicial = projeto.impressao()
    etapa = EtapaTDDRevisao("code", Coder(), Batch(), Orcamento(2, 1, 60),
                           Trace(projeto.saida / "trace.jsonl"))
    parte = asyncio.run(etapa.executar("requisito", projeto))

    pasta = projeto.saida / "revisoes-testes"
    assert json.loads((pasta / "000.json").read_text()) == {"tests/test_x.py": "assert 1 == 2\n"}
    assert json.loads((pasta / "001.json").read_text()) == {"tests/test_x.py": "assert 2 == 2\n"}
    diff = (pasta / "001.diff").read_text()
    assert "-assert 1 == 2" in diff and "+assert 2 == 2" in diff
    assert len(parte["versoes_testes"]) == 2
    assert parte["versoes_testes"][0]["sha256"] == inicial == parte["impressao"]
    assert parte["versoes_testes"][1]["sha256"] == projeto.impressao() != inicial
    assert parte["testes_revisaveis"] and parte["ok"] is not interrompida
    assert projeto.gates == (1 if interrompida else 2)
    assert parte["cost_usd"] == 0.02 and parte["total_tokens"] == 15
    resultado = Resultado(grupo="tdd-revisao", requisito_id="simulado", stages=[parte],
                          impressao_fim=projeto.impressao())
    assert resultado.integridade["intacto"] is False
    eventos = [json.loads(l) for l in etapa.trace.caminho.read_text().splitlines()]
    assert [e["versao"] for e in eventos if e.get("evento") == "versao_testes"] == [0, 1]


def test_variante_troca_apenas_coder_e_etapa_de_codigo(tmp_path):
    from caronte.piloto_v3 import GRUPOS, PROVEDOR, REQUISITO
    from harness.models.dominio import Requisito
    from harness.models.etapas import EtapaTDD, EtapaTestes

    requisito = Requisito(REQUISITO)
    harness = GRUPOS["tdd-revisao"](Projeto(tmp_path, requisito.alvo), requisito, Batch(), com_cua=False)
    coder = harness.agente("coder", requisito.modelos["coder"], EtapaTDD)
    assert coder._agno.model.extra_body["provider"] == PROVEDOR
    assert "REVISOES.md" in coder._agno.instructions
    assert "NÃO altere nada sob" not in coder._agno.instructions
    assert isinstance(harness.etapa("code", coder, EtapaTDD), EtapaTDDRevisao)
    assert type(harness.etapa("tests", coder, EtapaTestes)) is EtapaTestes
    assert harness.orcamento == requisito.orcamento and harness.grupo == "tdd-revisao"
