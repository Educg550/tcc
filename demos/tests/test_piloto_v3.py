from caronte.piloto_v2 import REQUISITO as ANTERIOR
from caronte.piloto_v3 import PROVEDOR, REQUISITO, BaselineV3
from harness.models import Batch, Projeto, Requisito
from harness.models.etapas import EtapaCodigo


def test_v3_preserva_contratos_e_orcamento_sem_entregar_oraculo(tmp_path):
    requisito = Requisito(REQUISITO)
    anterior = Requisito(ANTERIOR)
    assert requisito.alvo == anterior.alvo
    assert requisito.orcamento == anterior.orcamento
    assert requisito.modelos == anterior.modelos
    assert [p.name for p in requisito.anexos] == ["infra"]
    for arquivo in (ANTERIOR / "infra").iterdir():
        if arquivo.suffix in (".sql", ".json"):
            assert arquivo.read_bytes() == (REQUISITO / "infra" / arquivo.name).read_bytes()
    harness = BaselineV3(Projeto(tmp_path, requisito.alvo), requisito, Batch(), com_cua=False)
    agente = harness.agente("direto", requisito.modelos["coder"], EtapaCodigo)
    assert agente._agno.model.extra_body["provider"] == PROVEDOR
    assert agente._agno.model.max_retries == 0
    assert "Organização obrigatória" in harness.prompt()
    assert not harness.com_cua
