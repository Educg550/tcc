from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_form_page_returns_200():
    response = client.get('/')
    assert response.status_code == 200

def test_form_page_contains_expected_labels_and_placeholders():
    response = client.get('/')
    html = response.text
    # Check all required field labels
    assert 'NOME COMPLETO - SEM ABREVIAR' in html
    assert 'N. USP' in html
    assert 'PROGRAMA' in html
    assert 'NOME DO EVENTO' in html
    assert 'PERÍODO DO EVENTO' in html
    assert 'CIDADE DO EVENTO' in html
    assert 'VALOR SOLICITADO' in html
    # Check submit button
    assert 'Enviar solicitação' in html
    # Check placeholders (exact attribute values)
    assert 'placeholder="NOME COMPLETO - SEM ABREVIAR"' in html
    assert 'placeholder="N. USP"' in html
    assert 'placeholder="PROGRAMA"' in html
    assert 'placeholder="NOME DO EVENTO"' in html
    assert 'placeholder="PERÍODO DO EVENTO"' in html
    assert 'placeholder="CIDADE DO EVENTO"' in html
    assert 'placeholder="VALOR SOLICITADO"' in html

def test_submit_empty_fields_shows_error():
    response = client.post('/', data={})
    assert response.status_code == 200
    assert 'Preencha todos os campos' in response.text

def test_submit_missing_some_field_shows_error():
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': '123456',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        # missing VALOR SOLICITADO
    }
    response = client.post('/', data=data)
    assert 'Preencha todos os campos' in response.text

def test_submit_non_digit_n_usp_shows_error():
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': 'abc123',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        'VALOR SOLICITADO': '5000'
    }
    response = client.post('/', data=data)
    assert 'N. USP deve conter apenas números' in response.text

def test_submit_negative_or_zero_valor_shows_error():
    # zero value
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': '123456',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        'VALOR SOLICITADO': '0'
    }
    response = client.post('/', data=data)
    assert 'Valor solicitado deve ser maior que 0' in response.text

def test_submit_negative_valor_shows_error():
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': '123456',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        'VALOR SOLICITADO': '-100'
    }
    response = client.post('/', data=data)
    assert 'Valor solicitado deve ser maior que 0' in response.text

def test_submit_non_numeric_valor_shows_error():
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': '123456',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        'VALOR SOLICITADO': 'cem reais'
    }
    response = client.post('/', data=data)
    assert 'Valor solicitado deve ser maior que 0' in response.text

def test_successful_submission_shows_confirmation():
    data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
        'N. USP': '123456',
        'PROGRAMA': 'Mestrado',
        'NOME DO EVENTO': 'Conferência de Tecnologia',
        'PERÍODO DO EVENTO': '2025-07-01 a 2025-07-05',
        'CIDADE DO EVENTO': 'São Paulo',
        'VALOR SOLICITADO': '150000'  # 150000 centavos = R$ 1.500,00
    }
    response = client.post('/', data=data)
    assert response.status_code == 200
    html = response.text
    assert 'Solicitação registrada' in html
    expected_oficio = (
        'Interessada(o): Maria Silva - 123456\n'
        'Assunto: Solicitação de Auxílio Financeiro\n'
        'Programa: Mestrado\n'
        'Evento: Conferência de Tecnologia\n'
        'Período: 2025-07-01 a 2025-07-05\n'
        'Local: São Paulo\n'
        'Valor solicitado: R$ 1.500,00'
    )
    assert expected_oficio in html

def test_valor_conversion_to_brazilian_currency():
    # Test different examples from requirement
    test_cases = [
        ('1500', 'R$ 15,00'),  # 1500 centavos = R$15,00
        ('150000', 'R$ 1.500,00'),
        ('150000000', 'R$ 1.500.000,00'),
    ]
    base_data = {
        'NOME COMPLETO - SEM ABREVIAR': 'Test',
        'N. USP': '999999',
        'PROGRAMA': 'X',
        'NOME DO EVENTO': 'Y',
        'PERÍODO DO EVENTO': 'Z',
        'CIDADE DO EVENTO': 'W'
    }
    for raw_val, expected_str in test_cases:
        data = {**base_data, 'VALOR SOLICITADO': raw_val}
        response = client.post('/', data=data)
        assert response.status_code == 200
        assert expected_str in response.text, f'For input {raw_val}, expected {expected_str} in response'
