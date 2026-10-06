from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)


CAMPOS = {
    "aba": "ALUNOS",
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "Congresso Brasileiro de Computação",
    "periodo": "01 a 05 de janeiro de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://evento.example.com",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e hospedagem",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Avenida Paulista",
    "numero": "100",
    "complemento": "Apto 10",
    "bairro": "Bela Vista",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def alunos(**alteracoes):
    dados = dict(CAMPOS)
    dados.update(alteracoes)
    return dados


def docentes(**alteracoes):
    dados = dict(CAMPOS)
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["aba"] = "DOCENTES"
    dados.update(alteracoes)
    return dados


def enviar(dados):
    return cliente.post("/solicitar", json=dados)


def corpo(resposta):
    return resposta.text.replace("\\n", "\n")


def test_pagina_inicial_tem_cabecalho_e_abas():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    texto = resposta.text
    assert "Universidade de São Paulo" in texto
    assert "ALUNOS" in texto
    assert "DOCENTES" in texto
    assert texto.index("ALUNOS") < texto.index("DOCENTES")


def test_pagina_inicial_tem_blocos_e_botao():
    texto = cliente.get("/").text
    assert "SOLICITANTE E EVENTO" in texto
    assert "ENDEREÇO DO SOLICITANTE" in texto
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in texto
    assert "Enviar solicitação" in texto


def test_logo_usp_servido_como_estatico():
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_oficio_alunos_tem_dados_preenchidos():
    texto = corpo(enviar(alunos()))
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Período: 01 a 05 de janeiro de 2025" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://evento.example.com" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e hospedagem" in texto
    assert "Avenida Paulista, 100" in texto
    assert "Complemento: Apto 10" in texto
    assert "CEP: 05508-090" in texto
    assert "Bela Vista, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_docentes_sem_nivel_nem_tipo():
    texto = corpo(enviar(docentes()))
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação - Mestrado" not in texto


def test_link_vazio_sai_do_oficio():
    texto = corpo(enviar(alunos(link_evento="")))
    assert "Link do evento" not in texto


def test_complemento_vazio_sai_do_oficio():
    texto = corpo(enviar(alunos(complemento="")))
    assert "Complemento" not in texto


def test_campo_obrigatorio_vazio_uma_vez():
    texto = corpo(enviar(alunos(nome_completo="")))
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1
    assert "Interessada(o)" not in texto


def test_n_usp_apenas_numeros():
    texto = corpo(enviar(alunos(n_usp="12ab34")))
    assert "N. USP deve conter apenas números" in texto


def test_agencia_apenas_numeros():
    texto = corpo(enviar(alunos(agencia="12a4")))
    assert "Número da agência deve conter apenas números" in texto


def test_valor_maior_que_zero():
    texto = corpo(enviar(alunos(valor_solicitado="R$ 0,00")))
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_invalido():
    texto = corpo(enviar(alunos(email="maria")))
    assert "E-mail inválido" in texto


def test_cpf_formato():
    texto = corpo(enviar(alunos(cpf="12345678909")))
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cep_formato():
    texto = corpo(enviar(alunos(cep="05508090")))
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_nascimento_formato():
    texto = corpo(enviar(alunos(data_nascimento="01021980")))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_cpf_invalido():
    texto = corpo(enviar(alunos(cpf="123.456.789-00")))
    assert "CPF inválido" in texto


def test_data_nascimento_invalida():
    texto = corpo(enviar(alunos(data_nascimento="31/02/1980")))
    assert "Data de nascimento inválida" in texto


def test_varios_erros_de_uma_vez():
    texto = corpo(enviar(alunos(nome_completo="", n_usp="abc", email="x")))
    assert "Preencha todos os campos" in texto
    assert "N. USP deve conter apenas números" in texto
    assert "E-mail inválido" in texto


def test_solicitacao_valida_nao_tem_erros():
    texto = corpo(enviar(alunos()))
    assert "Preencha todos os campos" not in texto
    assert "E-mail inválido" not in texto
    assert "CPF inválido" not in texto
