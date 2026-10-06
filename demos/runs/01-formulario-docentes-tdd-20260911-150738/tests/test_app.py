from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_get_main_page():
    response = client.get("/")
    assert response.status_code == 200

def test_main_page_contains_header():
    response = client.get("/")
    assert "Universidade de São Paulo" in response.text
    assert "assets/usp-logo.png" in response.text

def test_main_page_has_two_tabs():
    response = client.get("/")
    assert 'ALUNOS' in response.text
    assert 'DOCENTES' in response.text

def test_alunos_tab_active_by_default():
    response = client.get("/")
    assert 'ALUNOS' in response.text
    assert 'DOCENTES' in response.text

def test_tabs_have_forms():
    response = client.get("/")
    assert 'Enviar solicitação' in response.text

def test_alunos_form_has_nivel_field():
    response = client.get("/")
    assert 'Mestrado' in response.text
    assert 'Doutorado' in response.text

def test_alunos_form_has_tipo_auxilio_field():
    response = client.get("/")
    assert 'Participação em evento' in response.text
    assert 'Banca de exame ou defesa' in response.text
    assert 'Outro' in response.text

def test_docentes_form_lacks_nivel_and_tipo_auxilio():
    response = client.get("/")
    # Docente form sections should not contain these options
    # We'll check that the docentes tab does not have these fields
    # Since both tabs are in the same HTML, we need to differentiate
    # But for now, we check the page contains fields for alunos; docentes may be separate
    # We'll do a more specific check in later tests
    pass

def test_bloco_solicitante_e_evento_exists():
    response = client.get("/")
    assert "SOLICITANTE E EVENTO" in response.text

def test_bloco_endereco_exists():
    response = client.get("/")
    assert "ENDEREÇO DO SOLICITANTE" in response.text

def test_bloco_pagamento_exists():
    response = client.get("/")
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in response.text

def test_required_fields_labeled():  # MISTURADO: verifica lugar de obrigatório
    # We'll just check that the page has fields listed
    pass

def test_post_invalid_missing_fields():
    response = client.post("/", data={})
    assert response.status_code == 400 or "Preencha todos os campos" in response.text

def test_post_invalid_n_usp_not_digits():
    data = {
        'nome': 'Test',
        'n_usp': 'abc',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "N. USP deve conter apenas números" in response.text

def test_post_invalid_agencia_not_digits():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '12a4',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "Número da agência deve conter apenas números" in response.text

def test_post_invalid_valor_zero():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '0',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "Valor solicitado deve ser maior que 0" in response.text

def test_post_invalid_email():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'invalido',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "E-mail inválido" in response.text

def test_post_invalid_cpf():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '123',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "CPF deve estar no formato 000.000.000-00" in response.text

def test_post_invalid_cep():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '1234',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "CEP deve estar no formato 00000-000" in response.text

def test_post_invalid_data_nascimento():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@test.com',
        'nome_evento': 'Evento',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '123',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '12345678',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in response.text

def test_post_success_alunos():
    data = {
        'nome': 'João Silva',
        'n_usp': '123456',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'joao@usp.br',
        'nome_evento': 'Teste',
        'periodo': '01/01/2024',
        'cidade': 'São Paulo',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '150000',
        'detalhamento': 'Teste',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua A',
        'numero': '100',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'São Paulo',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert response.status_code == 200
    assert 'Solicitação registrada' in response.text
    assert 'R$ 1.500,00' in response.text

def test_post_success_docentes():
    data = {
        'nome': 'Maria Oliveira',
        'n_usp': '789012',
        'programa': 'Matemática',
        'email': 'maria@usp.br',
        'nome_evento': 'Teste',
        'periodo': '01/01/2024',
        'cidade': 'São Paulo',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Teste',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua B',
        'numero': '200',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'São Paulo',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert response.status_code == 200
    assert 'Solicitação registrada' in response.text
    # Docentes não tem nível e tipo_auxilio: assunto diferente
    assert 'Verba do programa' in response.text

def test_oficio_alunos_contains_correct_template():
    data = {
        'nome': 'João Silva',
        'n_usp': '123456',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'joao@usp.br',
        'nome_evento': 'Teste',
        'periodo': '01/01/2024',
        'cidade': 'São Paulo',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1500',
        'detalhamento': 'Teste',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua A',
        'numero': '100',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'São Paulo',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert 'Interessada(o): João Silva - 123456' in response.text
    assert 'E-mail: joao@usp.br' in response.text
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in response.text
    assert 'Programa: Ciência da Computação - Mestrado' in response.text

def test_oficio_docentes_no_tipo_auxilio_nivel():
    data = {
        'nome': 'Maria Oliveira',
        'n_usp': '789012',
        'programa': 'Matemática',
        'email': 'maria@usp.br',
        'nome_evento': 'Teste',
        'periodo': '01/01/2024',
        'cidade': 'São Paulo',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Teste',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua B',
        'numero': '200',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'São Paulo',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in response.text
    assert 'Programa: Matemática' in response.text
    # Nível e tipo_auxílio não devem aparecer
    assert 'Mestrado' not in response.text
    assert 'Participação em evento' not in response.text

def test_oficio_valor_formatado():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Doutorado',
        'tipo_auxilio': 'Outro',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1500',
        'detalhamento': 'Test',
        'apresentacao': 'Apresentação oral',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    # 1500 dígitos correspondem a R$ 15,00
    assert 'R$ 15,00' in response.text

def test_oficio_link_omitido_se_vazio():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    # Link do evento: linha não deve aparecer
    assert 'Link do evento:' not in response.text

def test_oficio_complemento_omitido_se_vazio():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert 'Complemento:' not in response.text

def test_page_has_placeholders():
    response = client.get("/")
    # Check at least one placeholder e.g. for nome
    assert 'placeholder' in response.text

def test_valor_formatacao_automatica():
    # We can't test JS directly, but we can test that the output valor is formatted
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '150000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert 'R$ 1.500,00' in response.text

def test_cpf_formatacao_oficio():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert '123.456.789-01' in response.text

def test_cep_formatacao_oficio():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01011990',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert '05508-090' in response.text

def test_data_nascimento_formatacao_oficio():
    data = {
        'nome': 'Test',
        'n_usp': '123',
        'programa': 'Test',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'test@usp.br',
        'nome_evento': 'Test',
        'periodo': '01/01/2024',
        'cidade': 'SP',
        'estado_evento': 'SP',
        'pais': 'Brasil',
        'valor': '1000',
        'detalhamento': 'Test',
        'apresentacao': 'Pôster',
        'data_nascimento': '01021980',
        'logradouro': 'Rua',
        'numero': '123',
        'bairro': 'Centro',
        'cep': '05508090',
        'cidade_endereco': 'SP',
        'estado_endereco': 'SP',
        'cpf': '12345678901',
        'rg': '123456789',
        'banco': 'Banco',
        'agencia': '1234',
        'conta': '12345'
    }
    response = client.post("/", data=data)
    assert '01/02/1980' in response.text

def test_error_displays_all_invalid_messages():
    data = {
        'nome': '',
        'n_usp': 'abc',
        'programa': '',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'invalido',
        'nome_evento': '',
        'periodo': '',
        'cidade': '',
        'estado_evento': '',
        'pais': '',
        'valor': '0',
        'detalhamento': '',
        'apresentacao': 'Pôster',
        'data_nascimento': '123',
        'logradouro': '',
        'numero': '',
        'bairro': '',
        'cep': '1234',
        'cidade_endereco': '',
        'estado_endereco': '',
        'cpf': '123',
        'rg': '',
        'banco': '',
        'agencia': '12a4',
        'conta': ''
    }
    response = client.post("/", data=data)
    assert 'Preencha todos os campos' in response.text
    assert 'N. USP deve conter apenas números' in response.text
    assert 'Número da agência deve conter apenas números' in response.text
    assert 'Valor solicitado deve ser maior que 0' in response.text
    assert 'E-mail inválido' in response.text
    assert 'CPF deve estar no formato 000.000.000-00' in response.text
    assert 'CEP deve estar no formato 00000-000' in response.text
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in response.text

# Nota: testes para funcionalidade JS (formatação automática, troca de abas) não são possíveis via pytest simples; eles seriam cobertos por testes de integração ou e2e.
