import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def dados_alunos_completos():
    return {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_do_evento": "Congresso Nacional",
        "periodo_do_evento": "10 a 12 de outubro",
        "cidade_do_evento": "São Paulo",
        "estado_do_evento": "SP",
        "pais_do_evento": "Brasil",
        "link_do_evento": "",
        "valor_solicitado": "150000",
        "detalhamento": "Passagem e hospedagem",
        "apresentacao": "Pôster",
        "data_de_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }


def test_pagina_carrega_com_abas():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_aba_alunos_ativa_por_padrao():
    r = client.get("/")
    html = r.text
    alunos_pos = html.find('id="aba-alunos"')
    docentes_pos = html.find('id="aba-docentes"')
    assert alunos_pos != -1
    assert docentes_pos != -1
    alunos_class = re.search(r'id="aba-alunos" class="([^"]*)"', html)
    docentes_class = re.search(r'id="aba-docentes" class="([^"]*)"', html)
    assert "ativa" in alunos_class.group(1)
    assert "ativa" not in docentes_class.group(1)


def test_campos_exigidos_estao_na_pagina():
    r = client.get("/")
    html = r.text
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
    ]:
        assert rotulo in html, f"rótulo ausente: {rotulo}"


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos():
    html = client.get("/").text
    secoes = re.findall(r'<form[^>]*id="([^"]+)"[^>]*>(.*?)</form>', html, re.S)
    forms = {sid: corpo for sid, corpo in secoes}
    assert "form-alunos" in forms and "form-docentes" in forms
    for rotulo in ["NÍVEL", "TIPO DE AUXÍLIO"]:
        assert rotulo in forms["form-alunos"]
        assert rotulo not in forms["form-docentes"]


def test_envio_valido_alunos_devolve_oficio():
    r = client.post("/solicitar", json=dados_alunos_completos())
    assert r.status_code == 200
    corpo = r.json()
    assert "Solicitação registrada" in corpo
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    )
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso Nacional" in oficio
    assert "Período: 10 a 12 de outubro" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: " not in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: " not in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_docentes_tem_diferencas():
    dados = dados_alunos_completos()
    dados["aba"] = "docentes"
    dados.pop("nivel")
    dados.pop("tipo_de_auxilio")
    dados["link_do_evento"] = "https://exemplo.com"
    dados["complemento"] = "Sala 3"
    r = client.post("/solicitar", json=dados)
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio
    assert " - Mestrado" not in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Complemento: Sala 3" in oficio


def test_campo_vazio_erro_preenche_todos():
    dados = dados_alunos_completos()
    dados["nome_completo"] = ""
    r = client.post("/solicitar", json=dados)
    assert r.status_code == 422
    assert r.json()["erros"] == ["Preencha todos os campos"]


def test_n_usp_com_letras_erro():
    dados = dados_alunos_completos()
    dados["n_usp"] = "12a3"
    r = client.post("/solicitar", json=dados)
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_com_letras_erro():
    dados = dados_alunos_completos()
    dados["agencia"] = "12a4"
    r = client.post("/solicitar", json=dados)
    assert (
        "Número da agência deve conter apenas números" in r.json()["erros"]
    )


def test_valor_zero_erro():
    dados = dados_alunos_completos()
    dados["valor_solicitado"] = "0"
    r = client.post("/solicitar", json=dados)
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido_erro():
    dados = dados_alunos_completos()
    dados["email"] = "mariaime.usp.br"
    r = client.post("/solicitar", json=dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_mal_formatado_erro():
    dados = dados_alunos_completos()
    dados["cpf"] = "123.456.789"
    r = client.post("/solicitar", json=dados)
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cep_mal_formatado_erro():
    dados = dados_alunos_completos()
    dados["cep"] = "05508-0901"
    r = client.post("/solicitar", json=dados)
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_mal_formatada_erro():
    dados = dados_alunos_completos()
    dados["data_de_nascimento"] = "0102198"
    r = client.post("/solicitar", json=dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]


def test_cpf_formatado_mas_invalido_erro():
    dados = dados_alunos_completos()
    dados["cpf"] = "123.456.789-00"
    r = client.post("/solicitar", json=dados)
    assert "CPF inválido" in r.json()["erros"]


def test_data_formatada_mas_inexistente_erro():
    dados = dados_alunos_completos()
    dados["data_de_nascimento"] = "31/02/1980"
    r = client.post("/solicitar", json=dados)
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_todos_os_erros_aparecem_de_uma_vez():
    dados = dados_alunos_completos()
    dados["nome_completo"] = ""
    dados["n_usp"] = "12a"
    dados["agencia"] = "1a"
    dados["valor_solicitado"] = "0"
    dados["email"] = "sem-arroba"
    dados["cpf"] = "123"
    dados["cep"] = "123"
    dados["data_de_nascimento"] = "1234"
    r = client.post("/solicitar", json=dados)
    erros = r.json()["erros"]
    assert "Preencha todos os campos" in erros
    assert "N. USP deve conter apenas números" in erros
    assert "Número da agência deve conter apenas números" in erros
    assert "Valor solicitado deve ser maior que 0" in erros
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_erro_nao_gera_oficio():
    dados = dados_alunos_completos()
    dados["n_usp"] = "12a"
    r = client.post("/solicitar", json=dados)
    assert "oficio" not in r.json()


def test_opcionais_vazios_sao_validos():
    dados = dados_alunos_completos()
    dados["link_do_evento"] = ""
    dados["complemento"] = ""
    r = client.post("/solicitar", json=dados)
    assert r.status_code == 200


def test_campos_opcionais_nao_bloqueiam():
    dados = dados_alunos_completos()
    dados["link_do_evento"] = ""
    r = client.post("/solicitar", json=dados)
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_formato_de_moeda_no_oficio():
    dados = dados_alunos_completos()
    dados["valor_solicitado"] = "150000000"
    r = client.post("/solicitar", json=dados)
    assert "Valor solicitado: R$ 1.500.000,00" in r.json()["oficio"]


def test_logotipo_e_nome_da_usp_no_cabecalho():
    r = client.get("/")
    html = r.text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_cores_da_usp_no_css():
    r = client.get("/style.css")
    assert r.status_code == 200
    css = r.text
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_sem_serifa_no_css():
    css = client.get("/style.css").text
    assert "Open Sans" in css
    assert "sans-serif" in css


def test_brasao_nao_aparece_na_pagina():
    html = client.get("/").text
    assert "brasao" not in html.lower()


def test_appjs_disponivel():
    r = client.get("/app.js")
    assert r.status_code == 200
    js = r.text
    assert "VALOR SOLICITADO (R$)" in js or "blur" in js


def test_placeholders_nos_campos():
    html = client.get("/").text
    assert html.count('placeholder="') >= 20


def test_oficio_preserva_quebras_de_linha():
    dados = dados_alunos_completos()
    r = client.post("/solicitar", json=dados)
    oficio = r.json()["oficio"]
    assert "\nDados do evento\n" in oficio
    assert "\nEncaminhe-se ao Serviço Financeiro para providências.\n" in oficio
