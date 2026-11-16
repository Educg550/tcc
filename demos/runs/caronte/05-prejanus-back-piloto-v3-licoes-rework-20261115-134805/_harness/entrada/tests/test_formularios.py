import pytest
from conftest import banco

def secoes(form_id, filtro):
    return [l['id'] for l in banco(f'SELECT id FROM form_section WHERE form_id={form_id} AND {filtro} ORDER BY position, id', 'forms')]

def campos(section_id):
    return [l['name'] for l in banco(f'SELECT name FROM form_field WHERE section_id={section_id} ORDER BY position, id', 'forms')]

@pytest.mark.req('V2-FOR-01')
@pytest.mark.integracao('INT-FORMS-DB')
def test_lista_todos_os_formularios_com_metadados(api):
    r = api.get('forms')
    assert r.status_code == 200
    por_id = {f['id']: f for f in r.json()}
    assert set(por_id) == {1, 2, 3, 4}
    assert por_id[3]['tags'] == {'Ano': '2026', 'Edital': 'doutorado', 'Publico': 'candidatos'}
    assert por_id[1]['title'] == 'Inscrição no Programa de Mestrado em Ciência da Computação (IME-USP 2026)'
    assert por_id[1]['phase'] == 'Registration'

@pytest.mark.req('V2-FOR-01')
@pytest.mark.parametrize('filtros,esperado', [({'notice': 'doutorado'}, {3}), ({'notice': 'mestrado'}, {1, 2, 4}), ({'year': '2026'}, {1, 2, 3, 4}), ({'year': '2025'}, set()), ({'year': '2026', 'notice': 'doutorado'}, {3}), ({'year': '2025', 'notice': 'mestrado'}, set())])
def test_filtra_por_ano_e_edital(api, filtros, esperado):
    assert {f['id'] for f in api.get('forms', params=filtros).json()} == esperado

@pytest.mark.req('V2-FOR-02')
@pytest.mark.parametrize('form_id,versao,filtro', [(1, None, 'is_active'), (1, 1, 'version=1'), (1, 2, 'version=2'), (3, None, 'is_active')])
def test_ids_das_secoes(api, form_id, versao, filtro):
    params = {} if versao is None else {'version': versao}
    assert [s['id'] for s in api.get(f'forms/{form_id}/sections', params=params).json()] == secoes(form_id, filtro)

@pytest.mark.req('V2-FOR-02')
def test_versao_sem_secoes_cai_para_todas_as_secoes(api):
    posicao = {l['id']: l['position'] for l in banco('SELECT id, position FROM form_section WHERE form_id=1', 'forms')}
    for rota in ('forms/1/sections', 'forms/1'):
        ids = [s['id'] for s in api.get(rota, params={'version': 7}).json()]
        assert sorted(ids) == sorted(posicao)
        assert [posicao[i] for i in ids] == sorted((posicao[i] for i in ids))

@pytest.mark.req('V2-FOR-02')
@pytest.mark.parametrize('form_id,section_id', [(1, 2), (1, 102), (2, 10), (3, 13), (4, 18)])
def test_campos_da_secao_com_metadados(api, form_id, section_id):
    r = api.get(f'forms/{form_id}/sessions/{section_id}/fields')
    assert r.status_code == 200
    assert [c['name'] for c in r.json()] == campos(section_id)
    assert all(({'id', 'section_id', 'label', 'type', 'position'} <= set(c) for c in r.json()))
