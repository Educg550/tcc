import json
import pytest
from ambiente import RAIZ, dc, esperar, pdf
from conftest import BASE, banco, sql
OPENAPI = json.loads((RAIZ / 'demos/requisitos/03-caronte-prejanus-completo/infra/openapi-original.json').read_text())
CHAVES = set(OPENAPI['components']['schemas']['SubmissionSchema']['required'])
NOMES = {1: 'Ana Piloto Caronte', 2: 'Bruno Piloto V2', 3: 'Carla Doutorado V2', 4: 'Diego Poscomp V2'}
RESPOSTA = {1: 1, 2: 2, 3: 3, 4: 7}
ACESSO = {1: 'candidata.piloto@example.com', 2: 'bruno.piloto@example.com', 3: 'carla.piloto@example.com'}

def anexos(response_id):
    return banco(f"SELECT r.response_id, f.name, r.value FROM responses r JOIN form_field f ON f.id=r.field_id WHERE f.type='File' AND r.response_id={response_id} ORDER BY f.name", 'forms')

def listar(c, edict_id, **params):
    r = c.get(f'edicts/{edict_id}/submissions', params=params)
    assert r.status_code == 200, r.text
    return {s['id']: s for s in r.json()['submissions']}

def nova_candidatura(response_id, nome, submetida=True):
    sql(f"""INSERT INTO form_response(id,form_id,shared_id,email,token,current_section,submitted_at,metadata,form_version)\n        VALUES({response_id},1,1,'nova{response_id}@example.com','c0a5e1f0-0000-4000-8000-0000000001{response_id:02d}',8,\n        {("'2026-10-18 09:00:00'" if submetida else 'NULL')},'{{}}',2);\n        INSERT INTO responses(response_id,field_id,value) SELECT {response_id},field_id,\n        CASE WHEN field_id=1002 THEN '{nome}' ELSE value END FROM responses WHERE response_id=2;""", 'forms')

@pytest.mark.req('V2-INS-01')
@pytest.mark.integracao('INT-FORMS-DB')
@pytest.mark.parametrize('edict_id,esperado', [(1, {1, 2, 4}), (2, {3})])
def test_lista_candidaturas_do_edital(api, edict_id, esperado):
    lista = listar(api, edict_id)
    assert set(lista) == esperado
    assert {i: s['name'] for i, s in lista.items()} == {i: NOMES[i] for i in esperado}
    assert all((CHAVES <= set(s) for s in lista.values()))

@pytest.mark.req('V2-INS-01')
def test_listagem_traz_dados_mapeados(api):
    ana = listar(api, 1)[1]
    assert (ana['phone_number'], ana['birth_date'], ana['nationality']) == ('+55 11 99999-0001', '1998-03-14', 'Brasileira')
    assert ana['graduation']['course'] == 'Ciência da Computação'
    assert ana['research']['field']['primary'] == 'Engenharia de software e bancos de dados.'
    assert (ana['stats'], ana['is_favorite'], ana['labels'], ana['disabilities']) == ('underreview', False, [], True)
    assert ana['accept']['sent'] == 'not_sent'
    carla = listar(api, 2)[3]
    assert (carla['birth_date'], carla['phone_number']) == ('1997-06-20', '+55 11 99999-0003')

@pytest.mark.req('V2-INS-01')
def test_filtra_por_situacao(admin):
    sql("UPDATE submission SET stats='refused' WHERE id=2")
    assert set(listar(admin, 1, stats='refused')) == {2}
    assert set(listar(admin, 1, stats='underreview')) == {1, 4}

@pytest.mark.req('V2-INS-01', 'V2-BD-01')
@pytest.mark.integracao('INT-FORMS-DB', 'INT-PREJANUS-DB')
def test_associa_recomendacoes_sem_misturar_candidatos(api):
    listar(api, 1)
    ids = {l['id']: sorted(l['recs'] or []) for l in banco('SELECT id, recommenders_form_ids AS recs FROM submission WHERE edict_id=1')}
    assert ids == {1: [4, 5], 2: [6], 4: []}

@pytest.mark.req('V2-INS-01', 'V2-BD-01')
def test_leituras_repetidas_nao_duplicam_nem_apagam_decisoes(admin):
    assert admin.post('submissions/2/select', json={'stats': 'approved', 'user_ids': [3]}).status_code == 200
    admin.post('submissions/2/entry-semester', json={'semester': 'segundo'})
    antes = banco('SELECT id, candidate_form_id, stats, advisor_id, entry_semester FROM submission ORDER BY id')
    for _ in range(3):
        listar(admin, 1)
    assert banco('SELECT id, candidate_form_id, stats, advisor_id, entry_semester FROM submission ORDER BY id') == antes
    orientador = listar(admin, 1)[2]['advisor']
    assert (orientador['name'], orientador['email']) == ('Outra Docente', 'outra.piloto@example.com')

@pytest.mark.req('V2-INS-01', 'V2-BD-01')
@pytest.mark.integracao('INT-FORMS-DB', 'INT-PREJANUS-DB')
def test_candidatura_recem_finalizada_entra_na_listagem(api):
    nova_candidatura(20, 'Elisa Nova V2')
    nomes = {s['name'] for s in listar(api, 1).values()}
    assert 'Elisa Nova V2' in nomes
    assert len(banco('SELECT id FROM submission WHERE edict_id=1 AND candidate_form_id=20')) == 1
    listar(api, 1)
    assert len(banco('SELECT id FROM submission WHERE edict_id=1 AND candidate_form_id=20')) == 1

@pytest.mark.req('V2-INS-01')
def test_listagem_com_ppi_mapeado(api):
    lista = listar(api, 3)
    assert {s['name'] for s in lista.values()} == {NOMES[1], NOMES[2], NOMES[4]}
    assert all((s['ethnicity_race'] is True for s in lista.values()))

@pytest.mark.req('V2-INS-02')
@pytest.mark.parametrize('submission_id', [1, 2, 3])
def test_resumo_identifica_a_candidatura(api, submission_id):
    r = api.get(f'submissions/{submission_id}')
    assert r.status_code == 200
    resumo = r.json()['summary']
    assert (resumo['id'], resumo['name'], resumo['email']) == (submission_id, NOMES[submission_id], ACESSO[submission_id])
    assert (resumo['stats'], resumo['letter_sent'], resumo['private_note']) == ('underreview', False, '')

@pytest.mark.req('V2-INS-02')
def test_resumo_traz_formacao_pesquisa_e_semestre(api):
    resumo = api.get('submissions/1').json()['summary']
    assert resumo['graduation']['institution'] == 'Universidade Presbiteriana Mackenzie (Mackenzie)'
    assert resumo['research']['field']['secondary'] == 'Inteligência artificial e métodos formais.'
    assert resumo['entry_semester'] == 'Primeiro semestre.'

@pytest.mark.req('V2-INS-02')
def test_resumo_com_nota_do_poscomp(api):
    r = api.get('submissions/4')
    assert r.status_code == 200
    assert str(r.json()['summary']['poscomp']['score']) == '650'
    assert str(r.json()['summary']['poscomp']['year']) == '2025'

@pytest.mark.req('V2-INS-02', 'V2-INS-01')
@pytest.mark.integracao('INT-FORMS-DB')
def test_resumo_traz_recomendacoes_e_convites_pendentes(api):
    listar(api, 1)
    recs = {r['fullname']: r for r in api.get('submissions/1').json()['summary']['recommenders']}
    assert set(recs) == {'Paula Recomendadora Um', 'Pedro Recomendador Dois'}
    assert recs['Paula Recomendadora Um']['rating'] == 'Paula recomenda a Ana.'
    assert recs['Pedro Recomendador Dois']['affiliation'] == 'UFABC'
    bruno = api.get('submissions/2').json()['summary']['recommenders']
    assert [r['rating'] for r in bruno if r.get('sent')] == ['Rui recomenda o Bruno.']
    assert 'Pedro recomenda a Ana.' not in json.dumps(bruno, ensure_ascii=False)

@pytest.mark.req('V2-INS-02')
def test_detalhe_inexistente_responde_404_sem_criar_inscricao(api):
    antes = banco('SELECT count(*) AS n FROM submission')
    assert api.get('submissions/999').status_code == 404
    assert banco('SELECT count(*) AS n FROM submission') == antes

@pytest.mark.req('V2-INS-03')
@pytest.mark.integracao('INT-UPLOADS')
@pytest.mark.parametrize('submission_id', [1, 2, 3])
def test_baixa_todos_os_anexos_da_candidatura(api, submission_id):
    lista = anexos(RESPOSTA[submission_id])
    assert len(lista) == (9 if submission_id == 3 else 8)
    for a in lista:
        r = api.get(f"submissions/{submission_id}/files/{a['name']}/{a['value']}")
        assert r.status_code == 200, a
        assert r.headers['content-type'] == 'application/pdf'
        assert r.headers['content-disposition'].startswith('attachment')
        assert r.content == pdf(f"Piloto v2 - resposta {a['response_id']} - {a['name']}")

@pytest.mark.req('V2-INS-03')
@pytest.mark.integracao('INT-UPLOADS')
@pytest.mark.parametrize('caminho', ['submissions/1/files/lattes-cv-file/00000000000000000000000000000005_studies-transcripts.pdf', 'submissions/2/files/lattes-cv-file/00000000000000000000000000000004_lattes-cv-file.pdf', 'submissions/1/files/lattes-cv-file/..%2F..%2Fetc%2Fpasswd', 'submissions/999/files/lattes-cv-file/00000000000000000000000000000004_lattes-cv-file.pdf'])
def test_nao_entrega_arquivo_de_outro_campo_ou_candidatura(api, caminho):
    r = api.get(caminho)
    assert r.status_code >= 400
    assert not r.content.startswith(b'%PDF') and b'root:' not in r.content

@pytest.mark.req('V2-BD-01')
@pytest.mark.integracao('INT-PREJANUS-DB')
def test_estado_sobrevive_ao_reinicio_do_backend(api):
    api.post('submissions/1/comments', json={'comment': 'Persistente'})
    api.post('submissions/1/private_notes', json={'note': 'Nota persistente'})
    dc('restart', 'prejanus-back')
    esperar(BASE + '/backend/')
    resumo = api.get('submissions/1').json()['summary']
    assert resumo['private_note'] == 'Nota persistente'
    assert 'Persistente' in json.dumps(api.get('submissions/1/comments').json(), ensure_ascii=False)
