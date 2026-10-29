import pytest

from harness.models.arquivos import Arquivos
from harness.models.avaliacao import SPECS
from harness.models.dominio import Arquivo, Mudanca, Projeto
from harness.models.etapas import CODIGO, SO_TESTES
from harness.models.propostas import PropostaRejeitada


@pytest.fixture
def arquivos(tmp_path):
    projeto = Projeto(tmp_path, None)
    projeto.preparar()
    return Arquivos(projeto, CODIGO)


def test_edicao_preserva_resto_e_recusa_sintaxe_antes_de_gravar(arquivos):
    arquivos.criar_arquivo("app.py", "x = 1\ny = 2\n")
    assert arquivos.ler_arquivo("./app.py") == "x = 1\ny = 2\n"
    arquivos.substituir_trecho("app.py", "x = 1", "x = 3")
    with pytest.raises(SyntaxError):
        arquivos.substituir_trecho("app.py", "x = 3", "x = (")
    assert arquivos.ler_arquivo("app.py") == "x = 3\ny = 2\n"
    assert not (arquivos.projeto.raiz / "app.py").exists()
    CODIGO.aplicar(arquivos.mudanca(), arquivos.projeto)
    assert (arquivos.projeto.raiz / "app.py").read_text() == "x = 3\ny = 2\n"
    with pytest.raises(ValueError, match="já existe"):
        arquivos.criar_arquivo("./app.py", "x = 0\n")


@pytest.mark.parametrize("antigo", ["", "ausente", "x"])
def test_substituicao_ambigua_ou_ausente_nao_altera_arquivo(arquivos, antigo):
    arquivos.criar_arquivo("app.py", "x = 'x'\n")
    with pytest.raises(ValueError, match="exatamente uma vez"):
        arquivos.substituir_trecho("app.py", antigo, "novo")
    assert arquivos.ler_arquivo("app.py") == "x = 'x'\n"


@pytest.mark.parametrize("caminho", ["tests/test_x.py", "pytest.ini", "conftest.py",
                                    "_harness/trace.jsonl", ".git/config", "../fora.py"])
def test_coder_nao_edita_fora_do_escopo(arquivos, caminho):
    with pytest.raises(ValueError):
        arquivos.criar_arquivo(caminho, "x = 1\n")
    with pytest.raises(ValueError):
        arquivos.substituir_trecho(caminho, "x", "y")
    assert not arquivos.pendentes


def test_leitura_permite_testes_e_anexos_mas_esconde_medicao_e_escapes(arquivos, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_x.py").write_text("assert False\n")
    (tmp_path / "_harness/gabarito.py").write_text("reservado\n")
    (tmp_path / "atalho.py").symlink_to(tmp_path / "_harness/gabarito.py")
    (tmp_path / "externo.py").symlink_to(tmp_path.parent / "fora.py")
    assert arquivos.ler_arquivo("tests/test_x.py") == "assert False\n"
    assert arquivos.listar_arquivos().splitlines() == ["pytest.ini", "tests/test_x.py"]
    for caminho in ("_harness/gabarito.py", "atalho.py", "externo.py", "../fora.py"):
        with pytest.raises(ValueError):
            arquivos.ler_arquivo(caminho)
        with pytest.raises(ValueError):
            arquivos.criar_arquivo(caminho, "x = 1\n")


def test_test_writer_so_cria_testes_e_specs_so_editam_a_propria_subarvore(arquivos):
    testes = Arquivos(arquivos.projeto, SO_TESTES)
    with pytest.raises(ValueError):
        testes.criar_arquivo("app.py", "x = 1")
    testes.criar_arquivo("tests/test_x.py", "assert False\n")
    assert "tests/test_x.py" in testes.listar_arquivos()

    specs = Arquivos(arquivos.projeto, SPECS)
    caminho = "_harness/cypress/e2e/c1.cy.js"
    specs.criar_arquivo(caminho, "describe('C1', () => {});")
    assert specs.ler_arquivo(caminho).startswith("describe")
    assert caminho in specs.listar_arquivos()
    with pytest.raises(ValueError):
        specs.ler_arquivo("_harness/trace.jsonl")


def test_test_writer_nao_grava_teste_com_nome_indefinido(arquivos):
    testes = Arquivos(arquivos.projeto, SO_TESTES)
    corpo = "def test_x(cliente):\n    if not cliente:\n        pytest.skip('sem cliente')\n"
    with pytest.raises(ValueError, match="pytest"):
        testes.criar_arquivo("tests/test_x.py", corpo)
    testes.criar_arquivo("tests/test_x.py", "import pytest\n\n" + corpo)
    # O coder não é checado: nome indefinido no código aparece no pytest, como na baseline.
    arquivos.criar_arquivo("app.py", "x = y\n")


def test_proposta_com_sintaxe_invalida_nao_grava_nenhum_arquivo(arquivos):
    mudanca = Mudanca(arquivos=[
        Arquivo(caminho="valido.py", conteudo="x = 1\n"),
        Arquivo(caminho="invalido.py", conteudo="x = (\n"),
    ])
    assert isinstance(CODIGO.aplicar(mudanca, arquivos.projeto), PropostaRejeitada)
    assert not (arquivos.projeto.raiz / "valido.py").exists()


def test_prefixo_permitido_nao_pode_ser_link_para_fora_da_raiz(arquivos, tmp_path):
    (tmp_path / "tests").symlink_to(tmp_path.parent, target_is_directory=True)
    testes = Arquivos(arquivos.projeto, SO_TESTES)
    with pytest.raises(ValueError):
        testes.criar_arquivo("tests/fora.py", "assert False\n")
