"""Testes da validação do backend."""
from test_solicitacao import SOLICITACAO_DOCENTE_VALIDA, SOLICITACAO_VALIDA


def test_solicitacao_valida_nao_gera_erro(client):
    resposta = post(client, SOLICITACAO_VALIDA)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []


def test_campo_obrigatorio_vazio(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["nome"] = ""
    resposta = post(client, dados)
    assert "Preencha todos os campos" in resposta.json()["erros"]


def test_link_opcional_nao_gera_erro(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["link"] = ""
    resposta = post(client, dados)
    assert resposta.json()["erros"] == []


def test_complemento_opcional_nao_gera_erro(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["complemento"] = ""
    resposta = post(client, dados)
    assert resposta.json()["erros"] == []


def test_nusp_com_letras(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["nusp"] = "123456a"
    resposta = post(client, dados)
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_com_letras(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["agencia"] = "1234-a"
    resposta = post(client, dados)
    assert "Número da agência deve conter apenas números" in resposta.json()["erros"]


def test_valor_zero(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["valor"] = "R$ 0,00"
    resposta = post(client, dados)
    assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_sem_dominio(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["email"] = "joao@"
    resposta = post(client, dados)
    assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_fora_do_formato(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["cpf"] = "12345678909"
    resposta = post(client, dados)
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cpf_com_digitos_verificadores_errados(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["cpf"] = "123.456.789-00"
    resposta = post(client, dados)
    assert "CPF inválido" in resposta.json()["erros"]


def test_cep_fora_do_formato(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["cep"] = "05508090"
    resposta = post(client, dados)
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_fora_do_formato(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["nascimento"] = "01021980"
    resposta = post(client, dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]


def test_data_inexistente(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["nascimento"] = "31/02/1980"
    resposta = post(client, dados)
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_data_com_mes_fora_do_intervalo(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["nascimento"] = "01/13/1980"
    resposta = post(client, dados)
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_erros_multiplos_aparecem_todos(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["email"] = "joao@"
    dados["cep"] = "05508090"
    dados["cpf"] = "12345678909"
    dados["nascimento"] = "01021980"
    resposta = post(client, dados)
    erros = resposta.json()["erros"]
    assert "E-mail inválido" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_oficio_nao_gerado_quando_ha_erro(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["email"] = "joao@"
    resposta = post(client, dados)
    assert resposta.json()["oficio"] == ""


def test_solicitacao_docente_valida(client):
    resposta = post(client, SOLICITACAO_DOCENTE_VALIDA)
    assert resposta.status_code == 200
    assert resposta.json()["erros"] == []
