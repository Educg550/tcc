from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

# Contrato do backend: POST /solicitacao recebe {"aba": "alunos" | "docentes",
# "dados": {<rótulo exato do campo>: <valor digitado>}} e responde
# {"erros": [...], "oficio": <texto do ofício>}, sem "oficio" enquanto houver erro.


def dados_validos(aba):
    dados = {
        "NOME COMPLETO - SEM ABREVIAR": "Maria de Souza",
        "N. USP": "1234567",
        "PROGRAMA": "Ciência da Computação",
        "E-MAIL": "maria@usp.br",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Simpósio Brasileiro de Computação",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "1 a 5 de setembro de 2025",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "Salvador",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "BA",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://sbc.org.br/simposio",
        "VALOR SOLICITADO (R$)": "R$ 1.500,00",
        "DETALHAMENTO DO PEDIDO": "Inscrição e passagem aérea",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "DATA DE NASCIMENTO": "01/02/1980",
        "LOGRADOURO": "Rua do Anfiteatro",
        "NÚMERO": "181",
        "COMPLEMENTO": "Sala 222",
        "BAIRRO": "Butantã",
        "CEP": "05508-090",
        "CIDADE": "São Paulo",
        "ESTADO": "SP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "111.444.777-35",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "NOME DO BANCO": "Banco do Brasil",
        "NÚMERO DA AGÊNCIA": "1234",
        "NÚMERO DA CONTA": "98765-4",
    }
    if aba == "alunos":
        dados["NÍVEL"] = "Doutorado"
        dados["TIPO DE AUXÍLIO"] = "Participação em evento"
    return dados


def enviar(aba, **substituicoes):
    dados = dados_validos(aba)
    dados.update(substituicoes)
    resposta = client.post("/solicitacao", ={"aba": aba, "dados": dados})
    assert resposta.status_code == 200
    return resposta.()


def tela():
    return client.get("/").text + client.get("/app.js").text


ROTULOS = [
    "ALUNOS",
    "DOCENTES",
    "SOLICITANTE E EVENTO",
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
    "ENDEREÇO DO SOLICITANTE",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]


def test_pagina_e_arquivos_estaticos_servidos():
    pagina = client.get("/")
    assert pagina.status_code == 200
    assert "text/html" in pagina.headers["content-type"]
    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        assert client.get(caminho).status_code == 200, caminho


def test_tela_mostra_abas_blocos_rotulos_e_opcoes_exatos():
    texto_tela = tela()
    for texto in ROTULOS + OPCOES + ["Enviar solicitação", "Solicitação registrada"]:
        assert texto in texto_tela, texto
    assert texto_tela.index("ALUNOS") < texto_tela.index("DOCENTES")
    assert "placeholder" in texto_tela.lower()


def test_identidade_visual_da_usp():
    texto_tela = tela()
    assert "assets/usp-logo.png" in texto_tela
    assert "Universidade de São Paulo" in texto_tela
    css = client.get("/style.css").text
    assert "#1094ab" in css
    assert "sans-serif" in css


def test_nenhum_recurso_vem_da_rede():
    html = client.get("/").text
    js = client.get("/app.js").text
    css = client.get("/style.css").text
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert "http" not in css
    assert 'src="http' not in js
    assert 'fetch("http' not in js
    assert "fetch('http" not in js


def test_solicitacao_valida_de_alunos_gera_oficio():
    resposta = enviar("alunos")
    assert resposta["erros"] == []
    oficio = resposta["oficio"]
    for linha in [
        "Interessada(o): Maria de Souza - 1234567",
        "E-mail: maria@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Doutorado",
        "A CCP-Ciência da Computação aprovou",
        "Dados do evento",
        "Evento: Simpósio Brasileiro de Computação",
        "Período: 1 a 5 de setembro de 2025",
        "Local: Salvador - BA - Brasil",
        "Link do evento: https://sbc.org.br/simposio",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e passagem aérea",
        "Endereço da(o) interessada(o)",
        "Rua do Anfiteatro, 181",
        "Complemento: Sala 222",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 111.444.777-35",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 98765-4",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert linha in oficio, linha


def test_solicitacao_valida_de_docentes_gera_oficio():
    resposta = enviar("docentes")
    assert resposta["erros"] == []
    oficio = resposta["oficio"]
    linhas = oficio.splitlines()
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in linhas
    assert "Programa: Ciência da Computação" in linhas
    assert "Interessada(o): Maria de Souza - 1234567" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_campo_obrigatorio_vazio_gera_unica_mensagem():
    resposta = enviar("alunos", **{"NOME COMPLETO - SEM ABREVIAR": ""})
    assert resposta["erros"] == ["Preencha todos os campos"]
    assert not resposta.get("oficio")


def test_varios_campos_vazios_geram_apenas_uma_mensagem():
    resposta = enviar(
        "alunos",
        **{"NOME COMPLETO - SEM ABREVIAR": "", "BAIRRO": "", "NOME DO BANCO": ""},
    )
    assert resposta["erros"] == ["Preencha todos os campos"]
    assert not resposta.get("oficio")


def test_numero_usp_deve_conter_apenas_numeros():
    resposta = enviar("alunos", **{"N. USP": "123a567"})
    assert resposta["erros"] == ["N. USP deve conter apenas números"]


def test_numero_da_agencia_deve_conter_apenas_numeros():
    resposta = enviar("docentes", **{"NÚMERO DA AGÊNCIA": "12x4"})
    assert resposta["erros"] == ["Número da agência deve conter apenas números"]


def test_valor_solicitado_zero_e_rejeitado():
    resposta = enviar("alunos", **{"VALOR SOLICITADO (R$)": "R$ 0,00"})
    assert resposta["erros"] == ["Valor solicitado deve ser maior que 0"]
    assert not resposta.get("oficio")


def test_valor_solicitado_aparece_formatado_no_oficio():
    resposta = enviar("docentes", **{"VALOR SOLICITADO (R$)": "R$ 15,00"})
    assert resposta["erros"] == []
    assert "Valor solicitado: R$ 15,00" in resposta["oficio"]


def test_email_sem_arroba_e_rejeitado():
    resposta = enviar("alunos", **{"E-MAIL": "maria.usp.br"})
    assert "E-mail inválido" in resposta["erros"]


def test_email_sem_dominio_e_rejeitado():
    resposta = enviar("alunos", **{"E-MAIL": "maria@"})
    assert "E-mail inválido" in resposta["erros"]


def test_cpf_fora_do_formato_e_rejeitado():
    resposta = enviar("alunos", **{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})
    assert resposta["erros"] == ["CPF deve estar no formato 000.000.000-00"]


def test_cpf_com_digito_verificador_errado_e_rejeitado():
    resposta = enviar(
        "alunos", **{"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"}
    )
    assert resposta["erros"] == ["CPF inválido"]
    assert not resposta.get("oficio")


def test_cep_fora_do_formato_e_rejeitado():
    resposta = enviar("docentes", **{"CEP": "05508090"})
    assert resposta["erros"] == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato_e_rejeitada():
    resposta = enviar("alunos", **{"DATA DE NASCIMENTO": "01021980"})
    assert resposta["erros"] == ["Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_data_de_nascimento_inexistente_e_rejeitada():
    resposta = enviar("alunos", **{"DATA DE NASCIMENTO": "31/02/1980"})
    assert resposta["erros"] == ["Data de nascimento inválida"]


def test_data_de_nascimento_com_mes_fora_do_intervalo_e_rejeitada():
    resposta = enviar("alunos", **{"DATA DE NASCIMENTO": "05/13/1980"})
    assert resposta["erros"] == ["Data de nascimento inválida"]


def test_todos_os_erros_aplicaveis_sao_reportados():
    resposta = enviar(
        "alunos",
        **{
            "N. USP": "12a4567",
            "E-MAIL": "maria.usp.br",
            "CEP": "05508090",
        },
    )
    erros = resposta["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert not resposta.get("oficio")


def test_opcionais_vazios_sao_aceitos_e_linhas_saem_do_oficio():
    resposta = enviar(
        "alunos",
        **{"LINK DO EVENTO, EXAME OU DEFESA": "", "COMPLEMENTO": ""},
    )
    assert resposta["erros"] == []
    oficio = resposta["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
