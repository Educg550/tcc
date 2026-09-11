from pathlib import Path

from harness.models.agentes import load, resumir
from harness.models.dominio import Requisito

REQUISITOS = Path(__file__).parent.parent / "requisitos"
MODELO = REQUISITOS / "00-exemplo-caso-de-uso"

TOML = """
[comandos]
app = "uvicorn app:app --port {porta}"
teste = "pytest -q"

[dependencias]
python = "3.11"
pacotes = ["pytest", "fastapi[standard]"]

[modelos]
coder = "provedor/modelo"
"""


def caso(tmp_path):
    (tmp_path / "alvo.toml").write_text(TOML, encoding="utf-8")
    return Requisito(tmp_path)


def test_alvo_roda_isolado_do_venv_do_harness(tmp_path):
    assert caso(tmp_path).alvo.teste == [
        "uv",
        "run",
        # Sem `--isolated` o uv usa o venv do harness como base, e o alvo enxerga
        # dependência que o caso de uso não declarou.
        "--isolated",
        "--no-project",
        "--python",
        "3.11",
        "--with",
        "pytest",
        "--with",
        "fastapi[standard]",
        "pytest",
        "-q",
    ]


def test_porta_substituida_no_comando_do_app(tmp_path):
    requisito = caso(tmp_path)

    assert requisito.alvo.app(41537)[-4:] == ["uvicorn", "app:app", "--port", "41537"]
    assert requisito.modelos["coder"] == "provedor/modelo"


def test_modelo_de_caso_de_uso_e_input_valido():
    requisito = Requisito(MODELO)
    alvo = requisito.alvo

    assert alvo.teste[:4] == ["uv", "run", "--isolated", "--no-project"]
    assert "{porta}" in alvo.comando_app
    assert set(requisito.modelos) == {"test_writer", "coder", "cua"}
    assert requisito.orcamento.passos > 0
    assert alvo.python and alvo.pacotes


def test_criterios_do_modelo_e_do_caso_01():
    for diretorio in (MODELO, REQUISITOS / "01-formulario-docentes"):
        criterios = Requisito(diretorio).criterios

        assert criterios, diretorio
        for c in criterios:
            assert c.identificador.startswith("C")
            assert c.acao == c.acao.strip() and c.acao
            assert c.resultado_esperado == c.resultado_esperado.strip()
            # Autocontido: a sessão começa em branco, sem a tela do critério anterior.
            assert "Abrir a página inicial" in c.acao


def test_prompt_da_sessao_nao_deixa_placeholder():
    criterio = Requisito(REQUISITOS / "01-formulario-docentes").criterios[0]

    prompt = load("cua_task").format(
        base_url="http://localhost:1234",
        acao=criterio.acao,
        resultado_esperado=criterio.resultado_esperado,
    )

    assert "{" not in prompt and "}" not in prompt
    assert criterio.resultado_esperado in prompt


def test_resumo_mostra_a_evidencia_de_quem_falhou():
    resumo = resumir(
        [
            {"identificador": "C1", "passou": True, "evidencia": "os sete campos"},
            {"identificador": "C2", "passou": False, "evidencia": "campo ficou 1500"},
        ]
    )

    assert resumo == "C1 passou\nC2 FALHOU: campo ficou 1500"
