import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def _payload_aluno(**overrides):
    data = {
        "aba": "ALUNOS",
        "nome_completo": "Maria Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Simpósio de Computação",
        "periodo_evento": "01/10/2024 a 05/10/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.com",
        "valor_solicitado": "150000",
        "detalhamento": "Passagem e hospedagem",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua Exemplo",
        "numero": "123",
        "complemento": "Apto 45",
        "bairro": "Centro",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "52998224725",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    data.update(overrides)
    return data


def _payload_docente(**overrides):
    data = {
        "aba": "DOCENTES",
        "nome_completo": "João Souza",
        "n_usp": "87654321",
        "programa": "Ciência da Computação",
        "email": "joao@ime.usp.br",
        "nome_evento": "Congresso de Matemática",
        "periodo_evento": "10/11/2024 a 15/11/2024",
        "cidade_evento": "Rio de Janeiro",
        "estado_evento": "RJ",
        "pais_evento": "Brasil",
        "link_evento": "https://congresso.com",
        "valor_solicitado": "250000",
        "detalhamento": "Inscrição",
        "apresentacao_trabalho": "Apresentação oral",
        "data_nascimento": "02031975",
        "logradouro": "Av. Brasil",
        "numero": "456",
        "complemento": "",
        "bairro": "Copacabana",
        "cep": "22040002",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "cpf": "11144477735",
        "rg": "98.765.432-1",
        "banco": "Itaú",
        "agencia": "5678",
        "conta": "12345-6",
    }
    data.update(overrides)
    return data


def test_pagina_inicial_contem_todos_os_rotulos():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    for label in [
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NÍVEL",
        "TIPO DE AUXÍLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
        "Enviar solicitação",
    ]:
        assert label in html, f"Rótulo '{label}' não encontrado"


def test_envio_valido_aluno_gera_oficio():
    r = client.post("/api/solicitar", json=_payload_aluno())
    assert r.status_code == 200
    data = r.json()
    assert data.get("erros") == []
    oficio = data.get("oficio", "")
    assert "Interessada(o): Maria Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação aprovou na data de hoje" in oficio
    assert "Evento: Simpósio de Computação" in oficio
    assert "Período: 01/10/2024 a 05/10/2024" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem e hospedagem" in oficio
    assert "Rua Exemplo, 123" in oficio
    assert "Complemento: Apto 45" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Centro, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 529.982.247-25" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio


def test_envio_valido_docente_gera_oficio_sem_nivel_e_tipo():
    r = client.post("/api/solicitar", json=_payload_docente())
    assert r.status_code == 200
    data = r.json()
    assert data.get("erros") == []
    oficio = data.get("oficio", "")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Programa: Ciência da Computação - " not in oficio
    assert "TIPO DE AUXÍLIO" not in oficio


def test_campo_obrigatorio_vazio_retorna_erro_unico():
    p = _payload_aluno(nome_completo="")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "Preencha todos os campos" in data["erros"]
    assert data["erros"].count("Preencha todos os campos") == 1
    assert data.get("oficio") is None


def test_n_usp_deve_conter_apenas_numeros():
    p = _payload_aluno(n_usp="123a")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "N. USP deve conter apenas números" in data["erros"]
    assert data.get("oficio") is None


def test_numero_agencia_deve_conter_apenas_numeros():
    p = _payload_aluno(agencia="12a4")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "Número da agência deve conter apenas números" in data["erros"]
    assert data.get("oficio") is None


def test_valor_solicitado_deve_ser_maior_que_zero():
    p = _payload_aluno(valor_solicitado="0")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "Valor solicitado deve ser maior que 0" in data["erros"]
    assert data.get("oficio") is None


def test_email_invalido():
    p = _payload_aluno(email="maria")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "E-mail inválido" in data["erros"]
    assert data.get("oficio") is None


def test_cpf_formato_invalido():
    p = _payload_aluno(cpf="123")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "CPF deve estar no formato 000.000.000-00" in data["erros"]
    assert data.get("oficio") is None


def test_cep_formato_invalido():
    p = _payload_aluno(cep="123")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "CEP deve estar no formato 00000-000" in data["erros"]
    assert data.get("oficio") is None


def test_data_nascimento_formato_invalido():
    p = _payload_aluno(data_nascimento="123")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in data["erros"]
    assert data.get("oficio") is None


def test_cpf_digitos_verificadores_invalidos():
    p = _payload_aluno(cpf="12345678900")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "CPF inválido" in data["erros"]
    assert data.get("oficio") is None


def test_data_nascimento_invalida():
    p = _payload_aluno(data_nascimento="31022020")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert "Data de nascimento inválida" in data["erros"]
    assert data.get("oficio") is None


def test_multiplos_erros_listados():
    p = _payload_aluno(n_usp="abc", email="x", cpf="123")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    erros = data["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert data.get("oficio") is None


def test_link_e_complemento_vazios_removem_linhas_do_oficio():
    p = _payload_aluno(link_evento="", complemento="")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert data["erros"] == []
    oficio = data["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_valor_solicitado_formatado_no_oficio():
    p = _payload_aluno(valor_solicitado="1500")
    r = client.post("/api/solicitar", json=p)
    data = r.json()
    assert data["erros"] == []
    assert "Valor solicitado: R$ 15,00" in data["oficio"]
