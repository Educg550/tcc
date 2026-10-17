import ast

from caronte.piloto import materializar_visiveis


def test_visiveis_nao_entregam_parametrizacoes_reservadas():
    fonte = materializar_visiveis()
    funcoes = [n for n in ast.parse(fonte).body if isinstance(n, ast.FunctionDef)]
    assert len(funcoes) == 20
    assert "parametrize" not in fonte
    assert "def test_encontra_a_inscricao_pelo_nome" not in fonte
    secoes = [n.value.value for f in funcoes for n in f.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "secao"]
    assert sorted(secoes) == [0, 2, 4, 5, 6, 7]
    assert "00000000000000000000000000000002_disabilities-file.pdf" not in fonte
    assert "00000000000000000000000000000003_ethnicity-race-file.pdf" not in fonte
