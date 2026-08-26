from pathlib import Path

from harness.models.dominio import Alvo

MODELO = Path(__file__).parent.parent / "requisitos" / "00-exemplo-caso-de-uso"

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
    return Alvo.de(tmp_path)


def test_sem_requirements_nao_passa_a_flag(tmp_path):
    assert caso(tmp_path, requirements=False).teste == [
        "uv",
        "run",
        "--no-project",
        "pytest",
        "-q",
    ]


def test_com_requirements_e_porta_substituida(tmp_path):
    alvo = caso(tmp_path, requirements=True)
    assert alvo.app(41537) == [
        "uv",
        "run",
        "--no-project",
        "--with-requirements",
        str(tmp_path / "requirements.txt"),
        "uvicorn",
        "app:app",
        "--port",
        "41537",
    ]
    assert alvo.modelos["coder"] == "provedor/modelo"


def test_modelo_de_caso_de_uso_e_input_valido():
    alvo = Alvo.de(MODELO)

    assert alvo.teste[:3] == ["uv", "run", "--no-project"]
    assert "{porta}" in alvo.comando_app
    assert set(alvo.modelos) == {"test_writer", "coder", "cua"}
    assert "#" not in " ".join(alvo.dependencias)
