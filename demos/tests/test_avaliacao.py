import asyncio
import json
from types import SimpleNamespace

from harness.models.avaliacao import Avaliador, _veredito
from harness.models.dominio import Criterio


CRITERIO = Criterio(
    identificador="C1",
    tipo="deterministico",
    acao="Abrir a página",
    resultado_esperado="Título visível",
)


def test_sem_comando_frontend_reprova_criterio_e_avaliacao(tmp_path):
    projeto = SimpleNamespace(alvo=SimpleNamespace(comando_frontend=""), saida=tmp_path)
    requisito = SimpleNamespace(deterministicos=[CRITERIO], subjetivos=[])

    resultado = asyncio.run(Avaliador("cua", "specs").avaliar(projeto, requisito))

    assert not resultado["aprovado_geral"]
    assert not resultado["cypress"]["aprovado"]
    veredito = resultado["cypress"]["criterios"][0]
    assert veredito["identificador"] == "C1" and not veredito["passou"]
    assert "teste_frontend" in veredito["evidencia"]
    assert json.loads((tmp_path / "AVALIACAO.log").read_text()) == resultado
    requisito.deterministicos = []
    assert asyncio.run(Avaliador("cua", "specs")._cypress(projeto, requisito)) == {}


def test_veredito_exige_todos_os_testes_aprovados():
    passou = {"fullTitle": "C1 mostra título", "err": {}}
    ignorado = {"fullTitle": "C1 mostra campo", "err": {}}
    falhou = {"fullTitle": "C1 mostra mensagem", "err": {"message": "mensagem ausente"}}
    blob = {"tests": [passou], "passes": [passou], "pending": [], "failures": []}
    assert _veredito(CRITERIO, [blob])["passou"]
    evidencia_aprovado = _veredito(CRITERIO, [blob])["evidencia"]
    assert not _veredito(CRITERIO, [])["passou"]
    blob["tests"].append(ignorado)
    blob["pending"].append(ignorado)
    assert not _veredito(CRITERIO, [blob])["passou"]
    assert "não passaram" in _veredito(CRITERIO, [blob])["evidencia"]
    blob["tests"] = [ignorado]
    blob["passes"] = []
    assert not _veredito(CRITERIO, [blob])["passou"]
    blob["tests"] = [falhou]
    blob["pending"] = []
    blob["failures"] = [falhou]
    assert not _veredito(CRITERIO, [blob])["passou"]
    assert _veredito(CRITERIO, [blob])["evidencia"] == "mensagem ausente"
    assert evidencia_aprovado == "testes aprovados: 1"
