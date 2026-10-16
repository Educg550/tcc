import asyncio

from harness.models.dominio import Alvo, Projeto
from harness.models.etapas import Etapa, EtapaCodigo, EtapaTestes
from harness.models.politicas import (
    Aprovado,
    Batch,
    Decisao,
    FeedbackHumano,
    Orcamento,
    Permissao,
)
from harness.models.sessao import Turno
from harness.models.tracing import Resultado, Trace

ALVO = Alvo(
    comando_app="app --port {porta}",
    comando_teste="pytest -q",
    python="3.11",
    pacotes=("pytest",),
)
ORCAMENTO = Orcamento(passos=5, custo_usd=1.0, tempo_s=60)


class SessaoRoteirizada:
    """Escreve os caminhos na ordem dada, como a sessão do opencode faria, e guarda os
    prompts que recebeu. `None` simula uma chamada que terminou com erro."""

    model_id = "stub/stub"
    id = "ses_stub"

    def __init__(self, *caminhos: str | None):
        self.caminhos = list(caminhos)
        self.prompts: list[str] = []
        self.chamadas: list[tuple[dict, list]] = []

    async def enviar(self, prompt, projeto, escopo_edit, skills, tempo_s) -> Turno:
        self.prompts.append(prompt)
        self.chamadas.append((escopo_edit, skills))
        caminho = self.caminhos.pop(0)
        if caminho is None:
            return Turno(0.01, 10, 2, 12, [], erro="APIError 502")
        destino = projeto.raiz / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(f"x = {len(self.prompts)}\n")
        return Turno(0.01, 10, 2, 12, ["ponytail"])


class RejeitaUmaVez(Permissao):
    def __init__(self):
        self.vezes = 0

    def autorizar(self, etapa: str, resumo: str) -> Decisao:
        self.vezes += 1
        return Aprovado() if self.vezes > 1 else FeedbackHumano("faltou o caso vazio")


def rodar(tmp_path, sessao, permissao, classe: type[Etapa] = EtapaTestes) -> dict:
    projeto = Projeto(tmp_path, ALVO)
    projeto.preparar()
    etapa = classe(
        "etapa", sessao, permissao, ORCAMENTO, Trace(projeto.saida / "trace.jsonl")
    )
    return asyncio.run(etapa.executar("REQUISITO", projeto))


def test_escrita_fora_do_escopo_encerra_a_etapa(tmp_path):
    sessao = SessaoRoteirizada("app.py")

    parte = rodar(tmp_path, sessao, Batch())

    # O opencode já nega a escrita; se ela passar, a medição foi adulterada.
    assert not parte["ok"] and parte["motivo"] == "escopo"
    assert parte["arquivos"] == ["app.py"]
    assert sessao.chamadas[0][0] == {"*": "deny", "tests/**": "allow"}


def test_sessao_com_erro_volta_ao_modelo_e_nao_derruba_a_etapa(tmp_path):
    sessao = SessaoRoteirizada(None, "tests/test_x.py")

    parte = rodar(tmp_path, sessao, Batch())

    assert parte["ok"] and parte["motivo"] == "verde"
    assert (parte["passos"], parte["retries"]) == (2, 1)
    assert "SESSÃO INTERROMPIDA" in sessao.prompts[1]
    assert parte["cost_usd"] == 0.02 and parte["total_tokens"] == 24


def test_feedback_humano_volta_ao_modelo_e_nao_encerra_a_etapa(tmp_path):
    sessao = SessaoRoteirizada("tests/test_x.py", "tests/test_y.py")

    parte = rodar(tmp_path, sessao, RejeitaUmaVez())

    assert parte["ok"] and (parte["passos"], parte["retries"]) == (2, 1)
    assert "faltou o caso vazio" in sessao.prompts[1]
    # A sessão já tem o requisito no histórico: o passo seguinte leva só a observação.
    assert "REQUISITO" not in sessao.prompts[1]
    assert parte["arquivos"] == ["tests/test_x.py", "tests/test_y.py"]
    assert parte["skills"] == ["ponytail", "ponytail"]


def test_orcamento_estourado_encerra_sem_verde(tmp_path):
    sessao = SessaoRoteirizada(*[None] * 5)

    parte = rodar(tmp_path, sessao, Batch())

    assert not parte["ok"] and parte["motivo"] == "passos"
    assert parte["passos"] == 5 and parte["arquivos"] == []


def test_etapa_de_codigo_registra_a_impressao_dos_testes(tmp_path):
    parte = rodar(tmp_path, SessaoRoteirizada("app.py"), Batch(), EtapaCodigo)

    # Sem gate de pytest: é a etapa do baseline, e tests_vermelhos não se aplica.
    assert parte["ok"] and parte["impressao"]
    assert parte["tests_vermelhos"] is None


def test_integridade_sai_da_impressao_da_etapa_de_codigo():
    resultado = Resultado(grupo="tdd", requisito_id="01")
    resultado.stages = [{"id": "tests"}, {"id": "code", "impressao": "abc"}]

    resultado.impressao_fim = "abc"
    assert resultado.integridade == {"medido_sha256": "abc", "intacto": True}

    resultado.impressao_fim = "outra"
    assert resultado.integridade["intacto"] is False
