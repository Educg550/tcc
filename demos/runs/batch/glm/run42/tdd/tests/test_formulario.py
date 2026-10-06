"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app import app

    return TestClient(app)


SOLICITACAO_ALUNO = {
    "tipo": "ALUNOS",
    "nome": "Fulano da Silva",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "fulano@usp.br",
    "evento": "Congresso de Matemática",
    "periodo": "10 a 12 de março de 2026",
    "cidade": "São Paulo",
    "estado": "SP",
    "pais": "Brasil",
    "link": "",
    "valor": "1.500,00",
    "detalhamento": "Passagem e hospedagem.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade_endereco": "São Paulo",
    "estado_endereco": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def enviar(client, **sobreposicoes):
    dados = dict(SOLICITACAO_ALUNO)
    dados.update(sobreposicoes)
    return client.post("/solicitacao", data=dados, follow_redirects=True)


# ---------- Página e abas ----------


def test_pagina_cabe_usp(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    texto = resposta.text
    assert "assets/usp-logo.png" in texto
    assert "Universidade de São Paulo" in texto


def test_abas_rotulos(client):
    texto = client.get("/").text
    assert texto.index(">ALUNOS<") < texto.index(">DOCENTES<")


def test_aba_alunos_ativa_ao_abrir(client):
    texto = client.get("/").text
    assert 'id="tab-alunos"' in texto
    assert 'id="form-alunos"' in texto
    assert 'id="form-docentes"' in texto


def test_campos_aluno(client):
    texto = client.get("/").text
    for rotulo in (
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
    ):
        assert rotulo in texto


def test_nivel_tem_mestrado_e_doutorado(client):
    texto = client.get("/").text
    assert ">Mestrado<" in texto
    assert ">Doutorado<" in texto


def test_tipo_auxilio_tem_as_tres_opcoes(client):
    texto = client.get("/").text
    for opcao in (
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ):
        assert opcao in texto


def test_apresentacao_tem_as_quatro_opcoes(client):
    texto = client.get("/").text
    for opcao in (
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in texto


def test_nivel_e_tipo_auxilio_so_na_aba_alunos(client):
    texto = client.get("/").text
    indice_form_docentes = texto.index('id="form-docentes"')
    assert texto.index("NÍVEL") > indice_form_docentes
    assert texto.index("TIPO DE AUXÍLIO") > indice_form_docentes


def test_bloco_endereco(client):
    texto = client.get("/").text
    for rotulo in (
        "ENDEREÇO DO SOLICITANTE",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
    ):
        assert rotulo in texto


def test_bloco_pagamento(client):
    texto = client.get("/").text
    for rotulo in (
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ):
        assert rotulo in texto


def test_botao_enviar_existe(client):
    texto = client.get("/").text
    assert texto.count(">Enviar solicitação<") == 2


# ---------- Ofício ----------


def test_oficio_aluno(client):
    resposta = enviar(client)
    assert resposta.status_code == 200
    texto = resposta.text

    assert "Solicitação registrada" in texto
    assert "Interessada(o): Fulano da Silva - 12345678" in texto
    assert "E-mail: fulano@usp.br" in texto
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    )
    assert "Programa: Matemática - Mestrado" in texto
    assert "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a" in texto
    assert "interessada(o) acima, conforme segue:" in texto
    assert "Dados do evento" in texto
    assert "Evento: Congresso de Matemática" in texto
    assert "Período: 10 a 12 de março de 2026" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem e hospedagem." in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Rua do Matão, 1010" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_nao_mostra_linhas_opcionais_vazias(client):
    resposta = enviar(client)
    texto = resposta.text
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_oficio_mostra_campos_opcionais_preenchidos(client):
    resposta = enviar(
        client,
        link="https://exemplo.com.br",
        complemento="Sala 12",
    )
    texto = resposta.text
    assert "Link do evento: https://exemplo.com.br" in texto
    assert "Complemento: Sala 12" in texto


def test_oficio_docente(client):
    dados = dict(SOLICITACAO_ALUNO)
    dados["tipo"] = "DOCENTES"
    del dados["nivel"]
    del dados["tipo_auxilio"]
    resposta = client.post("/solicitacao", data=dados)
    assert resposta.status_code == 200
    texto = resposta.text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática" in texto
    assert "Programa: Matemática -" not in texto


def test_oficio_com_quebras_de_linha_preservadas(client):
    resposta = enviar(client)
    texto = resposta.text
    corpo = texto.split("<pre", 1)[1].split("</pre", 1)[0]
    assert "Interessada(o):" in corpo
    assert "Dados do evento" in corpo
    assert "Endereço da(o) interessada(o)" in corpo
    assert "Dados para pagamento" in corpo
    assert "Encaminhe-se ao Serviço Financeiro para providências." in corpo


def test_confirmacao_mantem_cabecalho_usp(client):
    resposta = enviar(client)
    assert "assets/usp-logo.png" in resposta.text
    assert "Universidade de São Paulo" in resposta.text


# ---------- Validac\u0323ões ----------


def test_campo_obrigatorio_vazio(client):
    resposta = enviar(client, nome="")
    assert resposta.status_code == 200
    assert "Preencha todos os campos" in resposta.text
    assert "Solicitação registrada" not in resposta.text


def test_n_usp_com_letras(client):
    resposta = enviar(client, n_usp="12a3456")
    assert "N. USP deve conter apenas números" in resposta.text


def test_agencia_com_letras(client):
    resposta = enviar(client, agencia="12a4")
    assert "Número da agência deve conter apenas números" in resposta.text


def test_valor_zero(client):
    resposta = enviar(client, valor="0,00")
    assert "Valor solicitado deve ser maior que 0" in resposta.text


def test_email_invalido(client):
    resposta = enviar(client, email="fulano Sem dominio")
    assert "E-mail inválido" in resposta.text


def test_cpf_mal_formatado(client):
    resposta = enviar(client, cpf="12345678909")
    assert "CPF deve estar no formato 000.000.000-00" in resposta.text


def test_cep_mal_formatado(client):
    resposta = enviar(client, cep="05508-0")
    assert "CEP deve estar no formato 00000-000" in resposta.text


def test_data_mal_formatada(client):
    resposta = enviar(client, data_nascimento="01-02-1980")
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.text


def test_cpf_com_dvs_errados(client):
    resposta = enviar(client, cpf="123.456.789-00")
    assert "CPF inválido" in resposta.text


def test_data_inexistente(client):
    resposta = enviar(client, data_nascimento="31/02/1980")
    assert "Data de nascimento inválida" in resposta.text


def test_data_mes_inexistente(client):
    resposta = enviar(client, data_nascimento="01/13/1980")
    assert "Data de nascimento inválida" in resposta.text


def test_varias_mensagens_de_erro_juntas(client):
    resposta = enviar(
        client,
        email="sem-arroba",
        cpf="12345678909",
        cep="12345-67",
    )
    texto = resposta.text
    assert "E-mail inválido" in texto
    assert "CPF deve estar no formato 000.000.000-00" in texto
    assert "CEP deve estar no formato 00000-000" in texto


def test_erro_mantem_aba_e_campos(client):
    resposta = enviar(client, email="sem-arroba")
    texto = resposta.text
    assert "Solicitação registrada" not in texto
    assert 'value="Fulano da Silva"' in texto
    assert 'value="12345678"' in texto
    assert 'selected>Mestrado<' in texto
    assert 'selected>Participação em evento<' in texto
    assert "Passagem e hospedagem." in texto
    assert 'selected>Pôster<' in texto


def test_erro_docente_mantem_campos(client):
    dados = dict(SOLICITACAO_ALUNO)
    dados["tipo"] = "DOCENTES"
    del dados["nivel"]
    del dados["tipo_auxilio"]
    dados["email"] = "sem-arroba"
    resposta = client.post("/solicitacao", data=dados)
    texto = resposta.text
    assert "Solicitação registrada" not in texto
    assert 'value="Fulano da Silva"' in texto
    assert 'value="Matemática"' in texto


# ---------- Arquivos estáticos ----------


def test_style_css(client):
    resposta = client.get("/style.css")
    assert resposta.status_code == 200


def test_app_js(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200


def test_logo_usp(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
