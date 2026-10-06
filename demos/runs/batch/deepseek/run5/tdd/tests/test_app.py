import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def _base_aluno(**over):
    dados = {
        'nome_completo': 'Fulano de Souza',
        'n_usp': '12345678',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'fulano@ime.usp.br',
        'nome_evento': 'SBC 2024',
        'periodo': '01/07/2024 a 05/07/2024',
        'cidade_evento': 'São Paulo',
        'estado_evento': 'SP',
        'pais_evento': 'Brasil',
        'link_evento': 'http://sbc.org',
        'valor_solicitado': '150000',
        'detalhamento': 'Passagem aérea',
        'apresentacao': 'Pôster',
        'data_nascimento': '01021980',
        'logradouro': 'Av. Paulista',
        'numero': '100',
        'complemento': 'Apto 1',
        'bairro': 'Bela Vista',
        'cep': '01310100',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cpf': '12345678909',
        'rg': '12.345.678-9',
        'banco': 'Banco do Brasil',
        'agencia': '1234',
        'conta': '12345-6',
    }
    dados.update(over)
    return dados


def test_formulario_get_exibe_abas_e_blocos():
    r = client.get('/')
    assert r.status_code == 200
    html = r.text
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert 'NOME COMPLETO - SEM ABREVIAR' in html
    assert 'N. USP' in html
    assert 'PROGRAMA' in html
    assert 'NÍVEL' in html
    assert 'TIPO DE AUXÍLIO' in html
    assert 'E-MAIL' in html
    assert 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA' in html
    assert 'PERÍODO DO EVENTO, EXAME OU DEFESA' in html
    assert 'CIDADE DO EVENTO, EXAME OU DEFESA' in html
    assert 'ESTADO DO EVENTO, EXAME OU DEFESA' in html
    assert 'PAÍS DO EVENTO, EXAME OU DEFESA' in html
    assert 'LINK DO EVENTO, EXAME OU DEFESA' in html
    assert 'VALOR SOLICITADO (R$)' in html
    assert 'DETALHAMENTO DO PEDIDO' in html
    assert 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?' in html
    assert 'DATA DE NASCIMENTO' in html
    assert 'LOGRADOURO' in html
    assert 'NÚMERO' in html
    assert 'COMPLEMENTO' in html
    assert 'BAIRRO' in html
    assert 'CEP' in html
    assert 'CIDADE' in html
    assert 'ESTADO' in html
    assert 'CPF (SEPARADOS POR PONTOS E TRAÇO)' in html
    assert 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)' in html
    assert 'NOME DO BANCO' in html
    assert 'NÚMERO DA AGÊNCIA' in html
    assert 'NÚMERO DA CONTA' in html
    assert 'SOLICITANTE E EVENTO' in html
    assert 'ENDEREÇO DO SOLICITANTE' in html
    assert 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO' in html
    assert 'Enviar solicitação' in html
    assert 'Universidade de São Paulo' in html


def test_aluno_valido_gera_oficio():
    r = client.post('/solicitar', json=_base_aluno())
    assert r.status_code == 200
    oficio = r.text if isinstance(r.text, str) else r.json()
    if isinstance(oficio, dict):
        oficio = str(oficio)
    assert 'Solicitação registrada' in oficio or 'oficio' in oficio.lower()
    assert 'Interessada(o): Fulano de Souza - 12345678' in oficio
    assert 'E-mail: fulano@ime.usp.br' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in oficio
    assert 'Programa: Ciência da Computação - Mestrado' in oficio
    assert 'Evento: SBC 2024' in oficio
    assert 'Valor solicitado: R$ 1.500,00' in oficio
    assert 'CPF: 123.456.789-09' in oficio
    assert 'Data de nascimento: 01/02/1980' in oficio


def test_docente_sem_nivel_nem_tipo_auxilio():
    dados = _base_aluno()
    dados.pop('nivel', None)
    dados.pop('tipo_auxilio', None)
    dados['programa'] = 'Física'
    r = client.post('/solicitar', json=dados)
    assert r.status_code == 200
    oficio = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Física' in oficio
    assert '<<NÍVEL>>' not in oficio


def test_campos_obrigatorios_vazios():
    dados = _base_aluno(nome_completo='')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert r.status_code != 200 or 'Preencha todos os campos' in body


def test_n_usp_nao_numerico():
    dados = _base_aluno(n_usp='12a34')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'N. USP deve conter apenas números' in body


def test_agencia_nao_numerica():
    dados = _base_aluno(agencia='12a4')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Número da agência deve conter apenas números' in body


def test_valor_zero_ou_invalido():
    dados = _base_aluno(valor_solicitado='0')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Valor solicitado deve ser maior que 0' in body


def test_email_invalido():
    dados = _base_aluno(email='fulano-ime.usp.br')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'E-mail inválido' in body


def test_cpf_formato_invalido():
    dados = _base_aluno(cpf='12345678')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'CPF deve estar no formato 000.000.000-00' in body


def test_cep_formato_invalido():
    dados = _base_aluno(cep='0550809')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'CEP deve estar no formato 00000-000' in body


def test_data_formato_invalido():
    dados = _base_aluno(data_nascimento='0102198')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in body


def test_cpf_verificador_invalido():
    dados = _base_aluno(cpf='12345678900')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'CPF inválido' in body


def test_data_inexistente():
    dados = _base_aluno(data_nascimento='32021980')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Data de nascimento inválida' in body


def test_multiplos_erros_aparecem_todos():
    dados = _base_aluno(email='invalido', n_usp='12a34')
    r = client.post('/solicitar', json=dados)
    body = r.text if isinstance(r.text, str) else str(r.json())
    assert 'E-mail inválido' in body
    assert 'N. USP deve conter apenas números' in body


def test_link_e_complemento_vazios_somem_do_oficio():
    dados = _base_aluno(link_evento='', complemento='')
    r = client.post('/solicitar', json=dados)
    oficio = r.text if isinstance(r.text, str) else str(r.json())
    assert 'Link do evento' not in oficio
    assert 'Complemento:' not in oficio
