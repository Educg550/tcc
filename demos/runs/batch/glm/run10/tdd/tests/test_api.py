import pytest


SOLICITACAO_ALUNO = {
    "aba": "alunos",
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Matemática Aplicada",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "Congresso Nacional de Matemática",
    "periodo": "10 a 12 de julho de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Inscrição no evento",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua Alice",
    "numero": "100",
    "complemento": "Apto 2",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "529.982.247-25",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def solicitacao_docente(**alteracoes):
    dados = dict(SOLICITACAO_ALUNO)
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["aba"] = "docentes"
    dados.update(alteracoes)
    return dados


def test_solicitacao_valida_aluno_gera_oficio(client):
    r = client.post("/api/solicitacao", json=SOLICITACAO_ALUNO)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    )
    assert "Programa: Matemática Aplicada - Mestrado" in oficio
    assert "A CCP-Matemática Aplicada aprovou na data de hoje" in oficio
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de julho de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição no evento" in oficio
    assert "Rua Alice, 100" in oficio
    assert "Complemento: Apto 2" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 529.982.247-25" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_linha_opcional_vazia_sai_do_oficio(client):
    dados = dict(SOLICITACAO_ALUNO)
    dados["link_evento"] = ""
    dados["complemento"] = ""
    oficio = client.post("/api/solicitacao", json=dados).json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_solicitacao_valida_docente(client):
    r = client.post(
        "/api/solicitacao", json=solicitacao_docente()
    )
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    )
    assert "Programa: Matemática Aplicada" in oficio
    assert " - Mestrado" not in oficio


def test_campo_obrigatorio_vazio(client):
    dados = solicitacao_docente()
    dados["nome_completo"] = ""
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "Preencha todos os campos" in r.json()["errors"]


def test_n_usp_com_letras(client):
    dados = solicitacao_docente(n_usp="12a456")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "N. USP deve conter apenas números" in r.json()["errors"]


def test_agencia_com_letras(client):
    dados = solicitacao_docente(agencia="12a4")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "Número da agência deve conter apenas números" in r.json()["errors"]


def test_valor_zero_ou_negativo(client):
    for valor in ["R$ 0,00", "R$ -10,00", "0"]:
        dados = solicitacao_docente(valor_solicitado=valor)
        r = client.post("/api/solicitacao", json=dados)
        assert r.status_code == 400
        assert "Valor solicitado deve ser maior que 0" in r.json()["errors"]


def test_email_invalido(client):
    for email in ["mariausp.br", "maria@", "@usp.br"]:
        dados = solicitacao_docente(email=email)
        r = client.post("/api/solicitacao", json=dados)
        assert r.status_code == 400
        assert "E-mail inválido" in r.json()["errors"]


def test_cpf_formato_errado(client):
    dados = solicitacao_docente(cpf="52998224725")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["errors"]


def test_cpf_digitos_verificadores_errados(client):
    dados = solicitacao_docente(cpf="529.982.247-24")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "CPF inválido" in r.json()["errors"]


def test_cep_formato_errado(client):
    dados = solicitacao_docente(cep="05508090")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "CEP deve estar no formato 00000-000" in r.json()["errors"]


def test_data_formato_errado(client):
    dados = solicitacao_docente(data_nascimento="1980-02-01")
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["errors"]


def test_data_inexistente(client):
    for data in ["31/02/1980", "01/13/1980", "00/02/1980"]:
        dados = solicitacao_docente(data_nascimento=data)
        r = client.post("/api/solicitacao", json=dados)
        assert r.status_code == 400
        assert "Data de nascimento inválida" in r.json()["errors"]


def test_todos_os_erros_de_uma_vez(client):
    dados = solicitacao_docente()
    dados.update(
        n_usp="12a456",
        agencia="12a4",
        valor_solicitado="0",
        email="maria",
        cpf="52998224725",
        cep="05508090",
        data_nascimento="1980-02-01",
    )
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    esperados = [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]
    for mensagem in esperados:
        assert mensagem in r.json()["errors"]


def test_com_erro_nao_gera_oficio(client):
    dados = solicitacao_docente()
    dados["email"] = "maria"
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 400
    assert "oficio" not in r.json()
