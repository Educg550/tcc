import asyncio

from harness.models.agentes import Resposta
from harness.models.dominio import Alvo, Arquivo, Mudanca, Projeto
from harness.models.etapas import Etapa, EtapaCodigo, EtapaTestes
from harness.models.politicas import (
    Aprovado,
    Batch,
    Decisao,
    FeedbackHumano,
    Orcamento,
    Permissao,
)
from harness.models.tracing import Resultado, Trace

ALVO = Alvo(comando_app="app --port {porta}", comando_teste="pytest -q")
ORCAMENTO = Orcamento(passos=5, custo_usd=1.0, tempo_s=60)


class AgenteRoteirizado:
    """Propõe os caminhos na ordem dada e guarda os prompts que recebeu."""

    model_id = "stub/stub"

    def __init__(self, *caminhos: str):
        self.caminhos = list(caminhos)
        self.prompts: list[str] = []

    async def propor(self, prompt: str) -> Resposta:
        self.prompts.append(prompt)
        arquivo = Arquivo(caminho=self.caminhos.pop(0), conteudo="x = 1\n")
        return Resposta(
            mudanca=Mudanca(arquivos=[arquivo]),
            custo_usd=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
        )


class RejeitaUmaVez(Permissao):
    def __init__(self):
        self.vezes = 0

    def autorizar(self, etapa: str, resumo: str) -> Decisao:
        self.vezes += 1
        return Aprovado() if self.vezes > 1 else FeedbackHumano("faltou o caso vazio")


def rodar(tmp_path, agente, permissao, classe: type[Etapa] = EtapaTestes) -> dict:
    projeto = Projeto(tmp_path, ALVO, "teste")
    projeto.preparar()
    etapa = classe(
        "etapa", agente, permissao, ORCAMENTO, Trace(projeto.saida / "trace.jsonl")
    )
    return asyncio.run(etapa.executar("REQUISITO", projeto))


def test_escopo_violado_volta_ao_modelo_e_nao_encerra_a_etapa(tmp_path):
    agente = AgenteRoteirizado("app.py", "tests/test_x.py")

    parte = rodar(tmp_path, agente, Batch())

    assert parte["ok"] and parte["motivo"] == "verde"
    # A proposta rejeitada não chega ao disco, mas custa um passo e volta no prompt.
    assert parte["arquivos"] == ["tests/test_x.py"]
    assert (parte["passos"], parte["retries"]) == (2, 1)
    assert "PROPOSTA REJEITADA" in agente.prompts[1]
    assert not (tmp_path / "app.py").exists()


def test_feedback_humano_volta_ao_modelo_e_nao_encerra_a_etapa(tmp_path):
    agente = AgenteRoteirizado("tests/test_x.py", "tests/test_y.py")

    parte = rodar(tmp_path, agente, RejeitaUmaVez())

    assert parte["ok"] and (parte["passos"], parte["retries"]) == (2, 1)
    assert "faltou o caso vazio" in agente.prompts[1]


def test_orcamento_estourado_encerra_sem_verde(tmp_path):
    agente = AgenteRoteirizado(*["app.py"] * 5)

    parte = rodar(tmp_path, agente, Batch())

    assert not parte["ok"] and parte["motivo"] == "passos"
    assert parte["passos"] == 5 and parte["arquivos"] == []


def test_etapa_de_codigo_registra_a_impressao_dos_testes(tmp_path):
    parte = rodar(tmp_path, AgenteRoteirizado("app.py"), Batch(), EtapaCodigo)

    # Sem gate de pytest: é a etapa do baseline, e tests_vermelhos não se aplica.
    assert parte["ok"] and parte["impressao"]
    assert parte["tests_vermelhos"] is None


def test_integridade_sai_da_impressao_da_etapa_de_codigo():
    resultado = Resultado(modo="criacao", requisito_id="01")
    resultado.stages = [{"id": "tests"}, {"id": "code", "impressao": "abc"}]

    resultado.impressao_fim = "abc"
    assert resultado.integridade == {"medido_sha256": "abc", "intacto": True}

    resultado.impressao_fim = "outra"
    assert resultado.integridade["intacto"] is False
