import httpx
import pytest
from conftest import IDS, OAUTH, banco, cliente, entrar
PROTEGIDAS = [('GET', 'auth/login'), ('GET', 'edicts'), ('GET', 'edicts/1'), ('GET', 'edicts/1/submissions'), ('GET', 'forms'), ('GET', 'submissions/1'), ('GET', 'submissions/1/comments'), ('POST', 'submissions/1/view'), ('POST', 'edicts')]

@pytest.mark.req('V2-AMB-01')
@pytest.mark.parametrize('caminho', ['docs', 'openapi.json'])
def test_documentacao_exposta(anonimo, caminho):
    assert anonimo.get(caminho).status_code == 200

@pytest.mark.req('V2-AMB-01')
def test_openapi_declara_as_operacoes(anonimo):
    caminhos = anonimo.get('openapi.json').json()['paths']
    assert {'/edicts/{edict_id}/submissions', '/submissions/{submission_id}/reesend_submission', '/forms/{form_id}/sessions/{section_id}/fields'} <= set(caminhos)

@pytest.mark.req('V2-AMB-01')
@pytest.mark.integracao('INT-FRONT')
def test_cors_com_credenciais_para_a_origem_configurada(anonimo):
    r = anonimo.options('edicts', headers={'Origin': 'https://localhost:8543', 'Access-Control-Request-Method': 'GET'})
    assert r.headers['access-control-allow-origin'] == 'https://localhost:8543'
    assert r.headers['access-control-allow-credentials'] == 'true'

@pytest.mark.req('V2-AMB-01')
def test_cors_recusa_origem_desconhecida(anonimo):
    r = anonimo.options('edicts', headers={'Origin': 'https://intruso.example', 'Access-Control-Request-Method': 'GET'})
    assert r.headers.get('access-control-allow-origin') != 'https://intruso.example'

@pytest.mark.req('V2-AUT-01')
def test_atalho_local_usa_o_usuario_configurado(local):
    r = local.get('auth/login')
    assert r.status_code == 200
    assert r.json() == {'id': 2, 'name': 'Docente Piloto', 'email': 'docente.piloto@example.com', 'nusp': '900002', 'role': 'teacher'}

@pytest.mark.req('V2-AUT-01')
@pytest.mark.parametrize('metodo,caminho', PROTEGIDAS)
def test_sem_sessao_responde_401(anonimo, metodo, caminho):
    assert anonimo.request(metodo, caminho).status_code == 401

@pytest.mark.req('V2-AUT-02')
@pytest.mark.integracao('INT-OAUTH')
def test_login_reconhece_usuario_existente_e_preserva_o_papel(anonimo):
    r = entrar(anonimo, 'secretaria')
    assert r.status_code == 200
    assert {k: r.json()[k] for k in ('id', 'email', 'role')} == {'id': 4, 'email': 'secretaria.piloto@example.com', 'role': 'secretary'}
    assert anonimo.get('auth/login').json()['id'] == 4
    assert httpx.get(OAUTH + '/eventos').json()[-1]['assinatura_valida']

@pytest.mark.req('V2-AUT-02')
@pytest.mark.integracao('INT-OAUTH')
def test_cookie_de_sessao_seguro_lax_de_oito_horas(anonimo):
    r = entrar(anonimo, 'docente')
    cookie = r.headers['set-cookie'].lower()
    assert 'secure' in cookie and 'samesite=lax' in cookie and ('max-age=28800' in cookie)

@pytest.mark.req('V2-AUT-02', 'V2-BD-01')
@pytest.mark.integracao('INT-OAUTH', 'INT-PREJANUS-DB')
def test_novo_usuario_autorizado_vira_docente(anonimo):
    r = entrar(anonimo, 'novo')
    assert r.status_code == 200
    assert anonimo.get('auth/login').json()['role'] == 'teacher'
    assert banco('SELECT name, email, nusp, role FROM "user" WHERE email=\'novo.piloto@example.com\'') == [{'name': 'Novo Docente', 'email': 'novo.piloto@example.com', 'nusp': '900007', 'role': 'teacher'}]

@pytest.mark.req('V2-AUT-02')
@pytest.mark.integracao('INT-OAUTH')
def test_nusp_fora_da_whitelist_nao_entra(anonimo):
    assert entrar(anonimo, 'negado').status_code >= 400
    assert anonimo.get('auth/login').status_code == 401
    assert banco('SELECT id FROM "user" WHERE email=\'negado.piloto@example.com\'') == []

@pytest.mark.req('V2-AUT-02')
@pytest.mark.integracao('INT-OAUTH')
def test_verifier_invalido_responde_500(anonimo):
    inicio = anonimo.post('auth/login/senhaunica').json()['redirect_to']
    token = inicio.split('oauth_token=')[1].split('&')[0]
    r = anonimo.post('auth/login/senhaunica', params={'oauth_token': token, 'oauth_verifier': 'errado'})
    assert r.status_code == 500

@pytest.mark.req('V2-AUT-03')
@pytest.mark.parametrize('perfil', ['admin', 'secretaria', 'coordenador'])
def test_papeis_administrativos_alteram_editais(clientes, perfil):
    r = clientes(perfil).post('edicts/1/edit-date', json={'closed_date': '2031-01-01'})
    assert r.status_code == 200
    assert banco('SELECT closed_date::text FROM edict WHERE id=1') == [{'closed_date': '2031-01-01'}]

@pytest.mark.req('V2-AUT-03')
def test_download_de_relatorio_e_publico(anonimo):
    assert anonimo.get('edicts/download_pdf/inexistente').status_code == 404

@pytest.mark.req('V2-AUT-03')
def test_ids_dos_perfis_do_ensaio(clientes):
    for perfil, id in IDS.items():
        assert clientes(perfil).get('auth/login').json()['id'] == id
