import pytest
from dados import CARONTE, respostas_da_fixture, secoes_do_formulario
CANDIDATA = "Ana Piloto Caronte"
EMAIL = "candidata.piloto@example.com"


@pytest.mark.req('PIL-AMB-01')
def test_api_responde_visivel_00(api):
    assert api.get('/').status_code == 200

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_01(api):
    arquivo = '00000000000000000000000000000001_official-document-file.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_02(api):
    arquivo = '00000000000000000000000000000004_lattes-cv-file.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_03(api):
    arquivo = '00000000000000000000000000000005_studies-transcripts.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_04(api):
    arquivo = '00000000000000000000000000000006_poscomp-file.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_05(api):
    arquivo = '00000000000000000000000000000007_graduate-courses-file.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-03', 'PIL-AMB-01')
def test_baixa_o_anexo_visivel_06(api):
    arquivo = '00000000000000000000000000000008_motivation-letter.pdf'
    campo = arquivo.split('_', 1)[1].removesuffix('.pdf')
    r = api.get(f'/submissions/1/files/{campo}/{arquivo}')
    assert r.status_code == 200
    assert r.headers['content-disposition'].startswith('attachment')
    assert r.content == (CARONTE / 'uploads-consulta' / arquivo).read_bytes()
    assert f'(Piloto Caronte - {campo})'.encode() in r.content

@pytest.mark.req('PIL-DOC-01')
def test_consulta_o_edital_visivel_07(api):
    r = api.get('/edicts/1')
    assert r.status_code == 200
    e = r.json()
    assert (e['id'], e['title'], e['candidate_form_id']) == (1, 'Piloto TCC - Mestrado 2026', '1')

@pytest.mark.req('PIL-DOC-01')
def test_consultas_repetidas_nao_duplicam_visivel_08(api):
    for _ in range(3):
        assert [s['id'] for s in api.get('/edicts/1/submissions').json()['submissions']] == [1]

@pytest.mark.req('PIL-DOC-02')
def test_detalhe_identifica_a_candidata_visivel_09(api):
    r = api.get('/submissions/1')
    assert r.status_code == 200
    resumo = r.json()['summary']
    assert (resumo['name'], resumo['email']) == (CANDIDATA, EMAIL)

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_10(api):
    secao = 0
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_11(api):
    secao = 2
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_12(api):
    secao = 4
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_13(api):
    secao = 5
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_14(api):
    secao = 6
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-02', 'PIL-BD-01')
def test_detalhe_traz_as_respostas_da_secao_visivel_15(api):
    secao = 7
    esperado = respostas_da_fixture()
    nomes = secoes_do_formulario()[secao]
    campos = {f['name']: f for s in api.get('/submissions/1').json()['submission_form'] for f in s['fields']}
    assert {n: str(campos[n]['value'] or '') for n in nomes} == {n: esperado[n] for n in nomes}

@pytest.mark.req('PIL-DOC-01')
def test_lista_o_edital_visivel_16(api):
    r = api.get('/edicts')
    assert r.status_code == 200
    assert [(e['id'], e['title']) for e in r.json()] == [(1, 'Piloto TCC - Mestrado 2026')]

@pytest.mark.req('PIL-AUT-01')
def test_login_local_reconhece_o_docente_visivel_17(api):
    r = api.get('/auth/login')
    assert r.status_code == 200
    assert r.json() == {'id': 2, 'name': 'Docente', 'email': 'docente@example.com', 'nusp': '0000001', 'role': 'teacher'}

@pytest.mark.req('PIL-AUT-01')
def test_sem_atalho_e_sem_sessao_responde_401_visivel_18(api_sem_atalho):
    rota = '/edicts/1/submissions'
    assert api_sem_atalho.get(rota).status_code == 401

@pytest.mark.req('PIL-AUT-01')
def test_sem_atalho_e_sem_sessao_responde_401_visivel_19(api_sem_atalho):
    rota = '/edicts'
    assert api_sem_atalho.get(rota).status_code == 401
