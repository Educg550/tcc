from caronte.analisar_estatica import analisar_arquivo, resumir, sem_mortas


def test_remove_so_faixa_congelada_preserva_linhas_e_nao_executa(tmp_path):
    codigo = ('raise RuntimeError("nao executar")\n'
              'def morta(x):\n    if x:\n        return 1\n    return 0\n'
              'class Viva:\n    def metodo(self, x):\n        return 1 if x else 0\n')
    arquivo = tmp_path / 'app.py'
    arquivo.write_text(codigo)
    bruto = analisar_arquivo(arquivo, tmp_path)
    vivo = analisar_arquivo(arquivo, tmp_path, [(2, 5)])
    assert arquivo.read_text() == codigo
    assert sem_mortas(codigo, [(2, 5)]).splitlines()[5] == 'class Viva:'
    assert len(bruto['radon']['funcoes']) == 2
    assert len(vivo['radon']['funcoes']) == 1
    assert vivo['radon']['funcoes'][0]['inicio'] == 7
    assert vivo['radon']['funcoes'][0]['cc'] == 2
    assert vivo['sha256'] == bruto['sha256']
    assert vivo['analisado_sha256'] != bruto['analisado_sha256']
    r = resumir([vivo])
    assert r['radon_cc']['media'] == 2
    assert r['radon_raw']['sloc'] < resumir([bruto])['radon_raw']['sloc']


def test_media_por_funcao_e_mi_exclui_arquivo_vazio(tmp_path):
    (tmp_path / 'vazio.py').write_text('')
    (tmp_path / 'funcoes.py').write_text('def f(x):\n    return 1 if x else 0\ndef g():\n    return 0\n')
    r = resumir([analisar_arquivo(p, tmp_path) for p in sorted(tmp_path.glob('*.py'))])
    assert r['arquivos'] == 2
    assert r['radon_cc']['n'] == 2
    assert r['radon_cc']['media'] == 1.5
    assert r['radon_mi']['arquivos_com_sloc'] == 1


def test_coleta_so_producao_confere_manifesto_e_repete_sem_mudar_saida(tmp_path, monkeypatch):
    import json
    import pytest
    from caronte import analisar_estatica as coletor

    monkeypatch.setattr(coletor, 'RAIZ', tmp_path)
    monkeypatch.setattr(coletor, 'RUNS', {'baseline': 'run'})
    original = tmp_path / 'caronte-core/prejanus-back'
    original.mkdir(parents=True)
    (original / 'app.py').write_text('def f():\n    return 0\n')
    (original / 'tests').mkdir()
    (original / 'tests/test_x.py').write_text('sintaxe invalida (')
    morto = tmp_path / 'demos/caronte/codigo-morto.json'
    morto.parent.mkdir(parents=True)
    morto.write_text('{"itens": []}')
    run = tmp_path / 'demos/runs/caronte/run'
    (run / '_harness').mkdir(parents=True)
    app = run / 'app.py'
    app.write_text('raise RuntimeError("nao executar")\n')
    (run / 'test_x.py').write_text('sintaxe invalida (')
    manifesto = {'app.py': {'tipo': 'producao', 'sha256': coletor.sha256(app.read_bytes())},
                 'test_x.py': {'tipo': 'testes_autorais', 'sha256': 'ignorado'}}
    (run / '_harness/MANIFESTO_ENTREGA.json').write_text(json.dumps(manifesto))
    saida = tmp_path / 'saida'
    r = coletor.executar(saida)
    assert r['projetos']['baseline']['resumo']['arquivos'] == 1
    assert r['projetos']['original_vivo']['resumo']['arquivos'] == 1
    antes = [(saida / p).read_bytes() for p in ('estatica.json', 'estatica.csv')]
    coletor.executar(saida)
    assert antes == [(saida / p).read_bytes() for p in ('estatica.json', 'estatica.csv')]
    app.write_text('mudou\n')
    with pytest.raises(AssertionError):
        coletor.executar(saida)
