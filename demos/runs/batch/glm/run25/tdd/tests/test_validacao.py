import copy

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_alunos():
    return {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional",
        "periodo": "10 a 12 de julho de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor_solicitado": "150000",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def dados_docentes():
    d = dados_alunos()
    d["aba"] = "docentes"
    d.pop("nivel")
    d.pop("tipo_auxilio")
    return d


def enviar_alunos(**overrides):
    dados = dados_alunos()
    dados.update(overrides)
    return client.post("/api/solicitacao", json=dados)


def enviar_docentes(**overrides):
    dados = dados_docentes()
    dados.update(overrides)
    return client.post("/api/solicitacao", json=dados)


def erros(resp):
    assert resp.status_code == 200
    body = resp.json()
    assert "valido" in body
    if body["valido"]:
        assert "erros" not in body or body["erros"] == []
        return []
    msgs = body["erros"]
    assert isinstance(msgs, list)
    assert msgs, "requisicao invalida deve ter erros"
    return msgs


def test_campo_obrigatorio_vazio_uma_mensagem():
    msgs = erros(enviar_alunos(nome_completo=""))
    assert "Preencha todos os campos" in msgs
    assert msgs.count("Preencha todos os campos") == 1


def test_varios_obrigatorios_vazios_uma_mensagem():
    msgs = erros(enviar_alunos(nome_completo="", bairro="", banco=""))
    assert msgs.count("Preencha todos os campos") == 1


def test_complemento_e_link_opcionais_nao_geram_erro():
    resp = enviar_alunos(complemento="", link_evento="")
    assert resp.status_code == 200
    assert resp.json()["valido"] is True


def test_n_usp_letras():
    msgs = erros(enviar_alunos(n_usp="12a456"))
    assert "N. USP deve conter apenas números" in msgs


def test_agencia_letras():
    msgs = erros(enviar_alunos(agencia="12a4"))
    assert "Número da agência deve conter apenas números" in msgs


def test_valor_zero():
    msgs = erros(enviar_alunos(valor_solicitado="0"))
    assert "Valor solicitado deve ser maior que 0" in msgs


def test_valor_negativo():
    msgs = erros(enviar_alunos(valor_solicitado="-100"))
    assert "Valor solicitado deve ser maior que 0" in msgs


def test_email_sem_arroba():
    msgs = erros(enviar_alunos(email="maria.ime.usp.br"))
    assert "E-mail inválido" in msgs


def test_email_sem_dominio():
    msgs = erros(enviar_alunos(email="maria@"))
    assert "E-mail inválido" in msgs


def test_cpf_formato_errado():
    msgs = erros(enviar_alunos(cpf="12345678909"))
    assert "CPF deve estar no formato 000.000.000-00" in msgs


def test_cpf_verificadores_errados():
    msgs = erros(enviar_alunos(cpf="123.456.789-00"))
    assert "CPF inválido" in msgs
    assert "CPF deve estar no formato 000.000.000-00" not in msgs


def test_cep_formato_errado():
    msgs = erros(enviar_alunos(cep="05508090"))
    assert "CEP deve estar no formato 00000-000" in msgs


def test_data_formato_errado():
    msgs = erros(enviar_alunos(data_nascimento="01021980"))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in msgs


def test_data_inexistivel():
    msgs = erros(enviar_alunos(data_nascimento="31/02/1980"))
    assert "Data de nascimento inválida" in msgs
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in msgs


def test_mes_inexistente():
    msgs = erros(enviar_alunos(data_nascimento="01/13/1980"))
    assert "Data de nascimento inválida" in msgs


def test_todos_os_erros_juntos():
    msgs = erros(
        enviar_alunos(
            n_usp="12a4",
            agencia="12a4",
            valor_solicitado="0",
            email="maria",
            cpf="12345678909",
            cep="05508090",
            data_nascimento="01021980",
        )
    )
    esperados = [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]
    for m in esperados:
        assert m in msgs, m


def test_validacoes_valem_para_docentes():
    msgs = erros(enviar_docentes(n_usp="12a4"))
    assert "N. USP deve conter apenas números" in msgs
    msgs = erros(enviar_docentes(email="sem-arroba"))
    assert "E-mail inválido" in msgs


def test_valido_nao_tem_erros():
    resp = enviar_alunos()
    assert resp.status_code == 200
    body = resp.json()
    assert body["valido"] is True
    assert not body.get("erros", [])
    assert body.get("oficio")
