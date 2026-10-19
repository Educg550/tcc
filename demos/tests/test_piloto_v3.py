import ast
import json

from caronte.piloto_v2 import REQUISITO as ANTERIOR
from caronte.piloto_v2 import SPLIT, V2
from caronte.piloto_v3 import (ENTRADA_REWORK, GRUPOS, PROVEDOR, REQUISITO, BaselineV3, manifesto,
                               preparar_rework_v3)
from harness.models import Batch, Projeto, Requisito
from harness.models.etapas import EtapaCodigo, EtapaTDD, EtapaTestes


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


def test_todos_os_agentes_dos_grupos_fixam_o_provedor(tmp_path):
    requisito = Requisito(REQUISITO)
    for grupo in ("tdd", "rework"):
        harness = GRUPOS[grupo](Projeto(tmp_path / grupo, requisito.alvo), requisito, Batch(), com_cua=False)
        assert harness.grupo == grupo
        for papel, classe in (("test_writer", EtapaTestes), ("coder", EtapaTDD)):
            modelo = harness.agente(papel, requisito.modelos[papel], classe)._agno.model
            assert modelo.extra_body["provider"] == PROVEDOR and modelo.max_retries == 0
            assert modelo.extra_body["reasoning"] == {"max_tokens": 32000}


def test_entrada_rework_v3_so_tem_testes_visiveis_e_diretiva_modular():
    entrada = Requisito(preparar_rework_v3())
    assert entrada.diretorio == ENTRADA_REWORK
    assert [p.name for p in entrada.anexos] == ["infra", "tests"]
    assert entrada.skills and all(p.is_dir() for ps in entrada.skills.values() for p in ps)
    assert entrada.orcamento == Requisito(REQUISITO).orcamento
    texto = entrada.texto
    assert "testes em `tests/`" in texto and "Organização obrigatória" in texto
    assert "V2-" not in texto
    funcoes, fonte = set(), ""
    for arquivo in sorted((ENTRADA_REWORK / "tests").glob("test_*.py")):
        fonte += arquivo.read_text()
        funcoes |= {f"{arquivo.name}::{n.name}" for n in ast.parse(arquivo.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    assert funcoes == {i.split("[")[0] for i in SPLIT["visiveis"]}
    assert len(funcoes) == 94 and not (ENTRADA_REWORK / "tests/test_rastreio.py").exists()
    for sobra in ("ADMINISTRATIVAS", "BIDDINGS", "TODAS", "def respostas", "def convite_pendente"):
        assert sobra not in fonte
    for reservado in {i.split("[")[0].split("::")[1] for i in SPLIT["reservados"]}:
        assert reservado not in fonte
    assert "divergencias" not in json.dumps(sorted(p.name for p in (ENTRADA_REWORK / "tests").iterdir()))
    assert (V2 / "oraculo/conftest.py").read_bytes() == (ENTRADA_REWORK / "tests/conftest.py").read_bytes()


def test_manifesto_separa_producao_testes_e_semeado(tmp_path):
    origem = tmp_path / "entrada"
    (origem / "infra").mkdir(parents=True)
    (origem / "alvo.toml").write_text("")
    (origem / "infra/a.sql").write_text("x\n")
    raiz = tmp_path / "run"
    for nome, texto in {"app.py": "a\nb\n", "rotas/x.py": "c\n", "tests/test_x.py": "t\n",
                        "infra/a.sql": "mudou\n", "pytest.ini": "", "_harness/RUN.log": "",
                        "__pycache__/app.pyc": ""}.items():
        (raiz / nome).parent.mkdir(parents=True, exist_ok=True)
        (raiz / nome).write_text(texto)
    tdd = manifesto(raiz, Requisito(origem), "tdd")
    assert {n: a["tipo"] for n, a in tdd.items()} == {
        "app.py": "producao", "rotas/x.py": "producao", "tests/test_x.py": "testes_autorais",
        "infra/a.sql": "infra_semeada", "pytest.ini": "harness"}
    assert tdd["app.py"]["linhas"] == 2 and tdd["infra/a.sql"]["semeado_alterado"]
    assert manifesto(raiz, Requisito(origem), "rework")["tests/test_x.py"]["tipo"] == "testes_fornecidos"
