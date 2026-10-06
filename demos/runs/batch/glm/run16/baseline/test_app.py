from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_validos():
    return {
        "tipo": "alunos",
        "nome": "Maria da Silva Santos",
        "numero_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "12 a 16 de agosto de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://exemplo.com.br",
        "valor_solicitado": "150000",
        "detalhamento": "Passagem aérea e hospedagem",
        "apresentacao": "Pôster",
        "endereco": {
            "data_nascimento": "01/02/1980",
            "logradouro": "Rua do Matão",
            "numero": "1010",
            "complemento": "",
            "bairro": "Butantã",
            "cep": "05508090",
            "cidade": "São Paulo",
            "estado": "SP"
        },
        "pagamento": {
            "data_nascimento": "01/02/1980",
            "cpf": "12345678909",
            "rg_rnm": "12.345.678-9",
            "banco": "Banco do Brasil",
            "agencia": "1234",
            "conta": "12345-6"
        }
    }


def test_solicitacao_valida_gera_oficio():
    resposta = client.post("/solicitacao", json=dados_validos())
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["ok"] is True
    oficio = dados["oficio"]
    assert "Interessada(o): Maria da Silva Santos - 12345678" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "A CCP-Matemática aprovou" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_linhas_opcionais_somem_quando_vazias():
    dados = dados_validos()
    dados["link_evento"] = ""
    dados["endereco"]["complemento"] = ""
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio


def test_linhas_opcionais_aparecem_quando_preenchidas():
    dados = dados_validos()
    dados["endereco"]["complemento"] = "Bloco A"
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Complemento: Bloco A" in oficio


def test_docentes_sem_nivel_e_tipo():
    dados = dados_validos()
    dados["tipo"] = "docentes"
    dados["nivel"] = ""
    dados["tipo_auxilio"] = ""
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio


def test_campo_obrigatorio_vazio():
    dados = dados_validos()
    dados["nome"] = ""
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 422
    assert "Preencha todos os campos" in resposta.json()["erros"]


def test_nusp_somente_digitos():
    dados = dados_validos()
    dados["numero_usp"] = "123abc"
    resposta = client.post("/solicitacao", json=dados)
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_somente_digitos():
    dados = dados_validos()
    dados["pagamento"]["agencia"] = "12-4"
    resposta = client.post("/solicitacao", json=dados)
    assert "Número da agência deve conter apenas números" in resposta.json()["erros"]


def test_valor_maior_que_zero():
    dados = dados_validos()
    dados["valor_solicitado"] = "0"
    resposta = client.post("/solicitacao", json=dados)
    assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_invalido():
    dados = dados_validos()
    dados["email"] = "maria@ime"
    resposta = client.post("/solicitacao", json=dados)
    assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_formato_errado():
    dados = dados_validos()
    dados["pagamento"]["cpf"] = "123.456.789-0"
    resposta = client.post("/solicitacao", json=dados)
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cpf_verificador_errado():
    dados = dados_validos()
    dados["pagamento"]["cpf"] = "12345678900"
    resposta = client.post("/solicitacao", json=dados)
    assert "CPF inválido" in resposta.json()["erros"]


def test_cep_formato_errado():
    dados = dados_validos()
    dados["endereco"]["cep"] = "05508-09"
    resposta = client.post("/solicitacao", json=dados)
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_formato_errado():
    dados = dados_validos()
    dados["pagamento"]["data_nascimento"] = "01021980"
    resposta = client.post("/solicitacao", json=dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]


def test_data_inexistente():
    dados = dados_validos()
    dados["pagamento"]["data_nascimento"] = "31/02/1980"
    resposta = client.post("/solicitacao", json=dados)
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_multiplos_erros_de_uma_vez():
    dados = dados_validos()
    dados["numero_usp"] = "abc"
    dados["email"] = "sem-arroba"
    resposta = client.post("/solicitacao", json=dados)
    erros = resposta.json()["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros


def test_frontend_e_estatico():
    for caminho in ("/", "/style.css", "/app.js", "/assets/usp-logo.png"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200
