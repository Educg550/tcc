import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

CAMPOS_OBRIGATORIOS_ALUNOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "nome_banco",
    "agencia",
    "conta",
]

SOLICITACAO_VALIDA_ALUNOS = {
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso de Computação",
    "periodo_evento": "10 a 15 de outubro de 2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://evento.usp.br",
    "valor_solicitado": "1500",
    "detalhamento": "Inscrição e passagem",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Bloco B",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def test_frontend_serve_arquivos_estaticos():
    resposta = client.get("/")
    assert resposta.status_code == 200


def test_formulario_tem_duas_abas_com_rotulos_exatos():
    html = client.get("/").text
    assert html.index(">ALUNOS<") < html.index(">DOCENTES<")


def test_aba_alunos_ativa_quando_pagina_abre():
    html = client.get("/").text
    assert re.search(r'class="[^"]*ativa[^"]*"[^>]*>ALUNOS<', html) or re.search(
        r'ALUNOS[^<]*</[^>]+>', html
    )


def test_campos_exatos_bloco_solicitante_alunos():
    html = client.get("/").text
    for rotulo in [
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
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert rotulo in html


def test_aba_docentes_nao_tem_nivel_nem_tipo_auxilio_como_campo():
    html = client.get("/").text
    assert html.count("NÍVEL") == 1 or "DOCENTES" in html


def test_envio_valido_gera_oficio_alunos():
    resposta = client.post("/solicitar/alunos", json=SOLICITACAO_VALIDA_ALUNOS)
    assert resposta.status_code == 200
    dados = resposta.json()
    oficio = dados.get("oficio", "")
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "Evento: Congresso de Computação" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.usp.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 15,00" in oficio
    assert "CEP: 05508-090" in oficio
    assert "CPF: 123.456.789-09" in oficio


def test_oficio_docentes_substitui_assunto_e_programa():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resposta = client.post("/solicitar/docentes", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json().get("oficio", "")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Mestrado" not in oficio


def test_link_evento_vazio_remove_linha():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["link_evento"] = ""
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 200
    assert "Link do evento" not in resposta.json().get("oficio", "")


def test_complemento_vazio_remove_linha():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["complemento"] = ""
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 200
    assert "Complemento:" not in resposta.json().get("oficio", "")


def test_erro_obrigatorios_mensagem_unica():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["nome_completo"] = ""
    dados["email"] = ""
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    erros = resposta.json().get("erros", [])
    assert erros.count("Preencha todos os campos") == 1


def test_erro_n_usp_nao_numerico():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["n_usp"] = "12a"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "N. USP deve conter apenas números" in resposta.json().get("erros", [])


def test_erro_agencia_nao_numerica():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["agencia"] = "12a"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Número da agência deve conter apenas números" in resposta.json().get("erros", [])


def test_erro_valor_nao_positivo():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["valor_solicitado"] = "0"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Valor solicitado deve ser maior que 0" in resposta.json().get("erros", [])


def test_erro_email_invalido():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["email"] = "maria.ime.usp.br"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "E-mail inválido" in resposta.json().get("erros", [])


def test_erro_cpf_formato():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["cpf"] = "12345678909"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json().get("erros", [])


def test_erro_cpf_invalido_digitos():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["cpf"] = "111.111.111-11"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CPF inválido" in resposta.json().get("erros", [])


def test_erro_cep_formato():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["cep"] = "05508090"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CEP deve estar no formato 00000-000" in resposta.json().get("erros", [])


def test_erro_data_formato():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["data_nascimento"] = "1980-02-01"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json().get("erros", [])


def test_erro_data_inexistente():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["data_nascimento"] = "31/02/1980"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Data de nascimento inválida" in resposta.json().get("erros", [])


def test_multiplos_erros_aparecem_juntos():
    dados = dict(SOLICITACAO_VALIDA_ALUNOS)
    dados["n_usp"] = "abc"
    dados["cep"] = "05508090"
    resposta = client.post("/solicitar/alunos", json=dados)
    assert resposta.status_code == 400
    erros = resposta.json().get("erros", [])
    assert "N. USP deve conter apenas números" in erros
    assert "CEP deve estar no formato 00000-000" in erros
