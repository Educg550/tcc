from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

CAMINHO = "/api/solicitacao"


def enviar(dados):
    resposta = cliente.post(CAMINHO, json=dados)
    if resposta.status_code == 422:
        resposta = cliente.post(CAMINHO, data=dados)
    return resposta


def erros(resposta):
    return resposta.json().get("erros") or []


def oficio(resposta):
    return resposta.json().get("oficio") or ""


def validos(aba="ALUNOS"):
    return {
        "aba": aba,
        "nome_completo": "Maria Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@usp.br",
        "evento": "Congresso Brasileiro",
        "periodo": "10 a 12 de janeiro",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://evento.com",
        "valor": "R$ 1.500,00",
        "detalhamento": "Passagem e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua X",
        "numero": "100",
        "complemento": "Apto 1",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


# ---------- página e arquivos estáticos ----------


def test_pagina_inicial_responde_com_html():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_duas_abas_alunos_e_docentes_nessa_ordem():
    html = cliente.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_arquivos_estaticos_servidos():
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_cabecalho_institucional_e_logotipo():
    html = cliente.get("/").text
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html


def test_os_tres_blocos_e_o_botao():
    html = cliente.get("/").text
    for bloco in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert bloco in html
    assert "Enviar solicitação" in html


def test_rotulos_exatos_dos_campos():
    html = cliente.get("/").text
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
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ):
        assert rotulo in html


# ---------- ofício gerado no envio válido ----------


def test_oficio_do_aluno_com_os_dados_no_lugar_dos_marcadores():
    resposta = enviar(validos())
    assert resposta.status_code == 200
    texto = oficio(resposta)
    assert "Interessada(o): Maria Silva - 12345678" in texto
    assert "E-mail: maria@usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Dados do evento" in texto
    assert "Evento: Congresso Brasileiro" in texto
    assert "Período: 10 a 12 de janeiro" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: http://evento.com" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem e hospedagem" in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Rua X, 100" in texto
    assert "Complemento: Apto 1" in texto
    assert "CEP: 05508-090" in texto
    assert "Centro, São Paulo - SP" in texto
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_do_docente_sem_nivel_e_com_verba_do_programa():
    dados = validos("DOCENTES")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    texto = oficio(enviar(dados))
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação -" not in texto


def test_link_e_complemento_vazios_saem_do_oficio():
    dados = validos()
    dados["link_evento"] = ""
    dados["complemento"] = ""
    texto = oficio(enviar(dados))
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


# ---------- validação ----------


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    dados = validos()
    dados.pop("nome_completo")
    resposta = enviar(dados)
    lista = erros(resposta)
    assert "Preencha todos os campos" in lista
    assert lista.count("Preencha todos os campos") == 1
    assert oficio(resposta) == ""


def test_n_usp_apenas_numeros():
    dados = validos()
    dados["n_usp"] = "12abc"
    assert "N. USP deve conter apenas números" in erros(enviar(dados))


def test_agencia_apenas_numeros():
    dados = validos()
    dados["agencia"] = "12a"
    assert "Número da agência deve conter apenas números" in erros(enviar(dados))


def test_valor_deve_ser_maior_que_zero():
    dados = validos()
    dados["valor"] = "R$ 0,00"
    assert "Valor solicitado deve ser maior que 0" in erros(enviar(dados))


def test_email_invalido():
    dados = validos()
    dados["email"] = "maria"
    assert "E-mail inválido" in erros(enviar(dados))


def test_cpf_fora_do_formato():
    dados = validos()
    dados["cpf"] = "12345678909"
    assert "CPF deve estar no formato 000.000.000-00" in erros(enviar(dados))


def test_cep_fora_do_formato():
    dados = validos()
    dados["cep"] = "05508090"
    assert "CEP deve estar no formato 00000-000" in erros(enviar(dados))


def test_data_fora_do_formato():
    dados = validos()
    dados["data_nascimento"] = "1980-02-01"
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros(enviar(dados))


def test_cpf_com_digito_verificador_errado():
    dados = validos()
    dados["cpf"] = "123.456.789-00"
    assert "CPF inválido" in erros(enviar(dados))


def test_data_inexistente():
    dados = validos()
    dados["data_nascimento"] = "31/02/1980"
    assert "Data de nascimento inválida" in erros(enviar(dados))


def test_varias_mensagens_de_erro_ao_mesmo_tempo():
    dados = validos()
    dados["n_usp"] = "abc"
    dados["email"] = "invalido"
    lista = erros(enviar(dados))
    assert "N. USP deve conter apenas números" in lista
    assert "E-mail inválido" in lista


def test_sem_erros_o_oficio_e_gerado():
    resposta = enviar(validos())
    assert erros(resposta) == []
    assert oficio(resposta) != ""
