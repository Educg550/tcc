from pathlib import Path

from harness.models.agentes import load, resumir
from harness.models.dominio import Requisito

REQUISITOS = Path(__file__).parent.parent / "requisitos"
MODELO = REQUISITOS / "00-exemplo-caso-de-uso"

TOML = """
comando_app = "uvicorn app:app --port {porta}"
comando_teste = "pytest -q"

[modelos]
coder = "provedor/modelo"
"""


def caso(tmp_path, requirements: bool):
    (tmp_path / "alvo.toml").write_text(TOML, encoding="utf-8")
    if requirements:
        (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    return Requisito(tmp_path)


def test_sem_requirements_nao_passa_a_flag(tmp_path):
    assert caso(tmp_path, requirements=False).alvo.teste == [
        "uv",
        "run",
        "--no-project",
        "pytest",
        "-q",
    ]


def test_com_requirements_e_porta_substituida(tmp_path):
    requisito = caso(tmp_path, requirements=True)
    assert requisito.alvo.app(41537) == [
        "uv",
        "run",
        "--no-project",
        "--with-requirements",
        str((tmp_path / "requirements.txt").resolve()),
        "uvicorn",
        "app:app",
        "--port",
        "41537",
    ]
    assert requisito.modelos["coder"] == "provedor/modelo"


def test_modelo_de_caso_de_uso_e_input_valido():
    requisito = Requisito(MODELO)
    alvo = requisito.alvo

    assert alvo.teste[:3] == ["uv", "run", "--no-project"]
    assert "{porta}" in alvo.comando_app
    assert set(requisito.modelos) == {"test_writer", "coder", "cua"}
    assert requisito.orcamento.passos > 0
    assert "#" not in " ".join(alvo.dependencias)
    # Relativo aqui vira inexistente lá: o comando roda com cwd na raiz do projeto.
    assert alvo.requirements.is_absolute()


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
