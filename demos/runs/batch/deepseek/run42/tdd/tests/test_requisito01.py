import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def _get_frontend():
    r = client.get("/")
    assert r.status_code == 200
    return r.text


def _dados_aluno():
    return {
        "nome_completo": "Fulano de Tal",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulano@ime.usp.br",
        "nome_evento": "Simpósio de Testes",
        "periodo_evento": "01/02/2024 a 03/02/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "valor_solicitado": "150000",
        "detalhamento": "Passagens e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def _dados_docente():
    d = _dados_aluno()
    d.pop("nivel")
    d.pop("tipo_auxilio")
    return d


def test_pagina_inicial_tem_abas_alunos_e_docentes():
    html = _get_frontend()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cabecalho_institucional():
    html = _get_frontend()
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_blocos_de_campos_presentes():
    html = _get_frontend()
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_rotulos_dos_blocos():
    html = _get_frontend()
    rotulos = [
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
    ]
    for r in rotulos:
        assert r in html, r


def test_botao_enviar_solicitacao():
    html = _get_frontend()
    assert html.count("Enviar solicitação") >= 1


def test_envio_valido_aluno_retorna_oficio():
    r = client.post("/solicitar", json={"aba": "alunos", "dados": _dados_aluno()})
    assert r.status_code == 200
    body = r.json()
    texto = body.get("oficio", "")
    assert "Fulano de Tal" in texto
    assert "12345678" in texto
    assert "R$ 1.500,00" in texto
    assert "Passagens e hospedagem" in texto
    assert "Pôster" in texto
    assert "Banco do Brasil" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_aluno_linhas_de_auxilio_e_nivel():
    r = client.post("/solicitar", json={"aba": "alunos", "dados": _dados_aluno()})
    texto = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert re.search(r"Programa: Ciência da Computação - Mestrado", texto)


def test_oficio_docente_linhas_diferentes():
    r = client.post("/solicitar", json={"aba": "docentes", "dados": _dados_docente()})
    assert r.status_code == 200
    texto = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert re.search(r"Programa: Ciência da Computação\s*$", texto, re.M)


def test_oficio_omite_link_e_complemento_quando_vazios():
    d = _dados_aluno()
    d["link_evento"] = ""
    d["complemento"] = ""
    r = client.post("/solicitar", json={"aba": "alunos", "dados": d})
    texto = r.json()["oficio"]
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_envio_com_branco_retorna_preencha_todos():
    d = _dados_aluno()
    d["nome_completo"] = ""
    r = client.post("/solicitar", json={"aba": "alunos", "dados": d})
    body = r.json()
    assert "Preencha todos os campos" in body.get("erros", [])
    assert body.get("oficio", "") == ""


def test_n_usp_apenas_numeros():
    d = _dados_aluno()
    d["n_usp"] = "12a45"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "N. USP deve conter apenas números" in body.get("erros", [])


def test_agencia_apenas_numeros():
    d = _dados_aluno()
    d["agencia"] = "12a4"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "Número da agência deve conter apenas números" in body.get("erros", [])


def test_valor_solicitado_maior_que_zero():
    d = _dados_aluno()
    d["valor_solicitado"] = "0"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "Valor solicitado deve ser maior que 0" in body.get("erros", [])


def test_email_invalido():
    d = _dados_aluno()
    d["email"] = "fulano.ime.usp.br"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "E-mail inválido" in body.get("erros", [])


def test_cpf_formato():
    d = _dados_aluno()
    d["cpf"] = "1234"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "CPF deve estar no formato 000.000.000-00" in body.get("erros", [])


def test_cpf_digitos_verificadores():
    d = _dados_aluno()
    d["cpf"] = "11111111111"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "CPF inválido" in body.get("erros", [])


def test_cep_formato():
    d = _dados_aluno()
    d["cep"] = "123"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "CEP deve estar no formato 00000-000" in body.get("erros", [])


def test_data_nascimento_formato():
    d = _dados_aluno()
    d["data_nascimento"] = "010220"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body.get("erros", [])


def test_data_nascimento_invalida():
    d = _dados_aluno()
    d["data_nascimento"] = "31022020"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    assert "Data de nascimento inválida" in body.get("erros", [])


def test_varios_erros_retornados_juntos():
    d = _dados_aluno()
    d["nome_completo"] = ""
    d["n_usp"] = "abc"
    d["email"] = "x"
    body = client.post("/solicitar", json={"aba": "alunos", "dados": d}).json()
    erros = body.get("erros", [])
    assert "Preencha todos os campos" in erros
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros


def test_erros_iguais_nas_duas_abas():
    d = _dados_docente()
    d["agencia"] = "abc"
    d["cep"] = "xxx"
    body = client.post("/solicitar", json={"aba": "docentes", "dados": d}).json()
    erros = body.get("erros", [])
    assert "Número da agência deve conter apenas números" in erros
    assert "CEP deve estar no formato 00000-000" in erros


def test_oficio_preserva_quebras_de_linha():
    r = client.post("/solicitar", json={"aba": "alunos", "dados": _dados_aluno()})
    texto = r.json()["oficio"]
    assert "\n" in texto
    assert "Dados do evento" in texto
    assert "Dados para pagamento" in texto
