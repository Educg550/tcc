import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

valid_alunos = {
    "aba": "ALUNOS",
    "nome_completo": "João da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "joao@usp.br",
    "nome_evento": "Simpósio Brasileiro de Computação",
    "periodo_evento": "10 a 15 de outubro de 2023",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "http://evento.com",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Participação no evento.",
    "apresentar_trabalho": "Apresentação oral",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua das Flores",
    "numero": "123",
    "complemento": "Apto 45",
    "bairro": "Jardim Paulista",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6"
}

valid_docentes = {
    "aba": "DOCENTES",
    "nome_completo": "Maria Souza",
    "n_usp": "87654321",
    "programa": "Matemática Aplicada",
    "email": "maria@usp.br",
    "nome_evento": "Congresso de Matemática",
    "periodo_evento": "20 a 22 de novembro de 2023",
    "cidade_evento": "Rio de Janeiro",
    "estado_evento": "RJ",
    "pais_evento": "Brasil",
    "link_evento": "http://congresso.com",
    "valor_solicitado": "R$ 2.000,00",
    "detalhamento": "Participação no congresso.",
    "apresentar_trabalho": "Pôster",
    "data_nascimento": "15/05/1975",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "complemento": "Sala 10",
    "bairro": "Bela Vista",
    "cep": "01310-100",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "98.765.432-1",
    "banco": "Itaú",
    "agencia": "5678",
    "conta": "98765-4"
}

def build_oficio_alunos(data):
    lines = []
    lines.append(f"Interessada(o): {data['nome_completo']} - {data['n_usp']}")
    lines.append(f"E-mail: {data['email']}")
    lines.append(f"Assunto: Solicitação de Auxílio Financeiro - {data['tipo_auxilio']}")
    lines.append(f"Programa: {data['programa']} - {data['nivel']}")
    lines.append("")
    lines.append(f"A CCP-{data['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {data['nome_evento']}")
    lines.append(f"Período: {data['periodo_evento']}")
    lines.append(f"Local: {data['cidade_evento']} - {data['estado_evento']} - {data['pais_evento']}")
    if data.get('link_evento'):
        lines.append(f"Link do evento: {data['link_evento']}")
    lines.append(f"Apresentação de trabalho: {data['apresentar_trabalho']}")
    lines.append(f"Valor solicitado: {data['valor_solicitado']}")
    lines.append(f"Detalhamento: {data['detalhamento']}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{data['logradouro']}, {data['numero']}")
    if data.get('complemento'):
        lines.append(f"Complemento: {data['complemento']}")
    lines.append(f"CEP: {data['cep']}")
    lines.append(f"{data['bairro']}, {data['cidade']} - {data['estado']}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data['data_nascimento']}")
    lines.append(f"CPF: {data['cpf']}")
    lines.append(f"RG / RNM: {data['rg']}")
    lines.append(f"Banco: {data['banco']}")
    lines.append(f"Agência: {data['agencia']}")
    lines.append(f"Conta: {data['conta']}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(lines) + "\n"

def build_oficio_docentes(data):
    lines = []
    lines.append(f"Interessada(o): {data['nome_completo']} - {data['n_usp']}")
    lines.append(f"E-mail: {data['email']}")
    lines.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
    lines.append(f"Programa: {data['programa']}")
    lines.append("")
    lines.append(f"A CCP-{data['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {data['nome_evento']}")
    lines.append(f"Período: {data['periodo_evento']}")
    lines.append(f"Local: {data['cidade_evento']} - {data['estado_evento']} - {data['pais_evento']}")
    if data.get('link_evento'):
        lines.append(f"Link do evento: {data['link_evento']}")
    lines.append(f"Apresentação de trabalho: {data['apresentar_trabalho']}")
    lines.append(f"Valor solicitado: {data['valor_solicitado']}")
    lines.append(f"Detalhamento: {data['detalhamento']}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{data['logradouro']}, {data['numero']}")
    if data.get('complemento'):
        lines.append(f"Complemento: {data['complemento']}")
    lines.append(f"CEP: {data['cep']}")
    lines.append(f"{data['bairro']}, {data['cidade']} - {data['estado']}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data['data_nascimento']}")
    lines.append(f"CPF: {data['cpf']}")
    lines.append(f"RG / RNM: {data['rg']}")
    lines.append(f"Banco: {data['banco']}")
    lines.append(f"Agência: {data['agencia']}")
    lines.append(f"Conta: {data['conta']}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(lines) + "\n"

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert "ALUNOS" in text
    assert "DOCENTES" in text
    assert "NOME COMPLETO - SEM ABREVIAR" in text
    assert "N. USP" in text
    assert "PROGRAMA" in text
    assert "NÍVEL" in text
    assert "TIPO DE AUXÍLIO" in text
    assert "E-MAIL" in text
    assert "NOME DO EVENTO / BANCA DE EXAME OU DEFESA" in text
    assert "PERÍODO DO EVENTO, EXAME OU DEFESA" in text
    assert "CIDADE DO EVENTO, EXAME OU DEFESA" in text
    assert "ESTADO DO EVENTO, EXAME OU DEFESA" in text
    assert "PAÍS DO EVENTO, EXAME OU DEFESA" in text
    assert "LINK DO EVENTO, EXAME OU DEFESA" in text
    assert "VALOR SOLICITADO (R$)" in text
    assert "DETALHAMENTO DO PEDIDO" in text
    assert "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?" in text
    assert "DATA DE NASCIMENTO" in text
    assert "LOGRADOURO" in text
    assert "NÚMERO" in text
    assert "COMPLEMENTO" in text
    assert "BAIRRO" in text
    assert "CEP" in text
    assert "CIDADE" in text
    assert "ESTADO" in text
    assert "CPF (SEPARADOS POR PONTOS E TRAÇO)" in text
    assert "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)" in text
    assert "NOME DO BANCO" in text
    assert "NÚMERO DA AGÊNCIA" in text
    assert "NÚMERO DA CONTA" in text
    assert "Enviar solicitação" in text

def test_static_files():
    response = client.get("/style.css")
    assert response.status_code == 200
    assert "#1094ab" in response.text
    assert "#64c4d2" in response.text
    assert "#fcb421" in response.text

    response = client.get("/app.js")
    assert response.status_code == 200
    assert "R$ " in response.text
    assert "replace" in response.text

    response = client.get("/assets/usp-logo.png")
    assert response.status_code == 200

def test_submit_valid_alunos():
    response = client.post("/submit", json=valid_alunos)
    assert response.status_code == 200
    data = response.json()
    assert "oficio" in data
    expected = build_oficio_alunos(valid_alunos)
    assert data["oficio"] == expected

def test_submit_valid_docentes():
    response = client.post("/submit", json=valid_docentes)
    assert response.status_code == 200
    data = response.json()
    assert "oficio" in data
    expected = build_oficio_docentes(valid_docentes)
    assert data["oficio"] == expected

def test_submit_alunos_without_link():
    data = valid_alunos.copy()
    data["link_evento"] = ""
    response = client.post("/submit", json=data)
    assert response.status_code == 200
    expected = build_oficio_alunos(data)
    assert response.json()["oficio"] == expected

def test_submit_alunos_without_complemento():
    data = valid_alunos.copy()
    data["complemento"] = ""
    response = client.post("/submit", json=data)
    assert response.status_code == 200
    expected = build_oficio_alunos(data)
    assert response.json()["oficio"] == expected

def test_submit_missing_required_field():
    data = valid_alunos.copy()
    data["nome_completo"] = ""
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "Preencha todos os campos" in errors

def test_submit_invalid_n_usp():
    data = valid_alunos.copy()
    data["n_usp"] = "123a456"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "N. USP deve conter apenas números" in errors

def test_submit_invalid_agencia():
    data = valid_alunos.copy()
    data["agencia"] = "12a4"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "Número da agência deve conter apenas números" in errors

def test_submit_invalid_valor():
    data = valid_alunos.copy()
    data["valor_solicitado"] = "R$ 0,00"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "Valor solicitado deve ser maior que 0" in errors

def test_submit_invalid_email():
    data = valid_alunos.copy()
    data["email"] = "joao"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "E-mail inválido" in errors

def test_submit_invalid_cpf_format():
    data = valid_alunos.copy()
    data["cpf"] = "12345678909"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "CPF deve estar no formato 000.000.000-00" in errors

def test_submit_invalid_cep_format():
    data = valid_alunos.copy()
    data["cep"] = "05508090"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "CEP deve estar no formato 00000-000" in errors

def test_submit_invalid_data_nascimento_format():
    data = valid_alunos.copy()
    data["data_nascimento"] = "01021980"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in errors

def test_submit_invalid_cpf_check_digits():
    data = valid_alunos.copy()
    data["cpf"] = "123.456.789-00"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "CPF inválido" in errors

def test_submit_invalid_data_nascimento():
    data = valid_alunos.copy()
    data["data_nascimento"] = "31/02/1980"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "Data de nascimento inválida" in errors

def test_submit_multiple_errors():
    data = valid_alunos.copy()
    data["n_usp"] = "abc"
    data["email"] = "joao"
    response = client.post("/submit", json=data)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert "N. USP deve conter apenas números" in errors
    assert "E-mail inválido" in errors
