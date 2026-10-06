import re
from fastapi.testclient import TestClient
from app import app


def get_client():
    return TestClient(app)


def elemento(texto_html, id_):
    m = re.search(r'id="%s"[^>]*>(.*?)</' % id_, texto_html, re.S)
    assert m
    return m.group(1)


def valor_campo(texto_html, id_):
    m = re.search(r'<input[^>]*id="%s"[^>]*>' % id_, texto_html)
    assert m
    tag = m.group(0)
    vm = re.search(r'value="([^"]*)"', tag)
    return vm.group(1) if vm else ""


def aba_ativa(texto_html, aba):
    padrao = r'<button[^>]*id="tab-%s"[^>]*class="([^"]*)"' % aba
    m = re.search(padrao, texto_html)
    assert m
    return "ativa" in m.group(1)


def contem_campo(texto_html, id_):
    return bool(re.search(r'id="%s"' % id_, texto_html))


def valor_textarea(texto_html, id_):
    m = re.search(r'<textarea[^>]*id="%s"[^>]*>(.*?)</textarea>' % id_, texto_html, re.S)
    assert m
    return m.group(1)


def dados_alunos(**sobreposicao):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_do_evento": "Congresso Nacional de Matemática",
        "periodo_do_evento": "10 a 12 de outubro de 2025",
        "cidade_do_evento": "São Paulo",
        "estado_do_evento": "São Paulo",
        "pais_do_evento": "Brasil",
        "link_do_evento": "",
        "valor_solicitado": "1500",
        "detalhamento_do_pedido": "Inscrição e hospedagem",
        "apresentacao_de_trabalho": "Pôster",
        "data_de_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "São Paulo",
        "cpf": "12345678909",
        "rg_rnm": "12.345.678-9",
        "nome_do_banco": "Banco do Brasil",
        "numero_da_agencia": "1234",
        "numero_da_conta": "12345-6",
    }
    dados.update(sobreposicao)
    return dados


def dados_docentes(**sobreposicao):
    dados = dados_alunos()
    dados.pop("nivel", None)
    dados.pop("tipo_de_auxilio", None)
    dados["aba"] = "docentes"
    dados["nome_completo"] = "João Ninguém"
    dados["n_usp"] = "87654321"
    dados["email"] = "joao@ime.usp.br"
    dados.update(sobreposicao)
    return dados


def test_pagina_carrega_com_abas_na_ordem():
    r = get_client().get("/")
    assert r.status_code == 200
    ia = r.text.index(">ALUNOS<")
    idoc = r.text.index(">DOCENTES<")
    assert ia < idoc


def test_aba_alunos_ativa_por_padrao_e_campos_presentes():
    r = get_client().get("/")
    assert aba_ativa(r.text, "alunos")
    assert not aba_ativa(r.text, "docentes")
    for campo in [
        "nome_completo", "n_usp", "programa", "nivel",
        "tipo_de_auxilio", "email", "nome_do_evento",
        "periodo_do_evento", "cidade_do_evento", "estado_do_evento",
        "pais_do_evento", "link_do_evento", "valor_solicitado",
        "detalhamento_do_pedido", "apresentacao_de_trabalho",
        "data_de_nascimento", "logradouro", "numero", "complemento",
        "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm",
        "nome_do_banco", "numero_da_agencia", "numero_da_conta",
    ]:
        assert contem_campo(r.text, campo), campo


def test_aba_docentes_nao_tem_nem_nivel_nem_tipo_de_auxilio():
    r = get_client().get("/")
    m = re.search(r'id="form-docentes".*?id="form-alunos"', r.text, re.S)
    secao = m.group(0) if m else r.text
    assert not contem_campo(secao, "nivel")
    assert not contem_campo(secao, "tipo_de_auxilio")
    assert contem_campo(secao, "nome_completo")


def test_placeholders_sao_exemplos_diferentes_dos_rotulos():
    r = get_client().get("/")
    for campo in ["nome_completo", "n_usp", "programa", "email"]:
        m = re.search(r'<input[^>]*id="%s"[^>]*placeholder="([^"]+)"' % campo, r.text)
        assert m, campo
        assert m.group(1).strip() != ""


def test_blocos_com_titulos_visiveis():
    r = get_client().get("/")
    assert "SOLICITANTE E EVENTO" in r.text
    assert "ENDEREÇO DO SOLICITANTE" in r.text
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in r.text


def test_cabecalho_institucional():
    r = get_client().get("/")
    assert "assets/usp-logo.png" in r.text
    assert "Universidade de São Paulo" in r.text
    assert not re.search(r"escudo", r.text, re.I)


def test_estaticos_servidos():
    c = get_client()
    for caminho in ["/style.css", "/app.js", "/assets/usp-logo.png"]:
        r = c.get(caminho)
        assert r.status_code == 200, caminho


def test_envio_valido_alunos_gera_oficio():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    assert r.status_code == 200
    corpo = r.json()
    assert "Solicitação registrada" in r.text
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva Souza - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento"
        in oficio
    )
    assert "Programa: Matemática - Mestrado" in oficio
    assert "CCP-Matemática" in oficio
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de outubro de 2025" in oficio
    assert "Local: São Paulo - São Paulo - Brasil" in oficio
    assert "Link do evento:" not in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 15,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - São Paulo" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_preserva_quebras_de_linha():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    assert "Dados do evento\n" in oficio
    assert "Endereço da(o) interessada(o)\n" in oficio
    assert "Dados para pagamento\n" in oficio


def test_complemento_e_link_preenchidos_aparecem_no_oficio():
    r = get_client().post(
        "/api/solicitar",
        json=dados_alunos(
            complemento="Sala 305",
            link_do_evento="https://exemplo.com",
        ),
    )
    oficio = r.json()["oficio"]
    assert "Complemento: Sala 305" in oficio
    assert "Link do evento: https://exemplo.com" in oficio


def test_oficio_docentes_sem_nivel_e_sem_tipo():
    r = get_client().post("/api/solicitar", json=dados_docentes())
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        in oficio
    )
    assert "Programa: Matemática\n" in oficio


def test_valor_formatado_com_milhar():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(valor_solicitado="150000")
    )
    oficio = r.json()["oficio"]
    assert "Valor solicitado: R$ 1.500,00" in oficio


def test_campo_obrigatorio_vazio():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(programa="")
    )
    assert r.status_code == 400
    corpo = r.json()
    assert corpo["erros"] == ["Preencha todos os campos"]


def test_campos_opcionais_podem_ficar_vazios():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(complemento="", link_do_evento="")
    )
    assert r.status_code == 200


def test_n_usp_apenas_digitos():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(n_usp="12a34567")
    )
    assert r.status_code == 400
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_apenas_digitos():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(numero_da_agencia="12a3")
    )
    assert r.status_code == 400
    assert (
        "Número da agência deve conter apenas números" in r.json()["erros"]
    )


def test_valor_maior_que_zero():
    for valor in ["0", ""]:
        r = get_client().post(
            "/api/solicitar", json=dados_alunos(valor_solicitado=valor)
        )
        assert r.status_code == 400, valor
        assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido():
    for email in ["mariaime.usp.br", "maria@"]:
        r = get_client().post(
            "/api/solicitar", json=dados_alunos(email=email)
        )
        assert r.status_code == 400, email
        assert "E-mail inválido" in r.json()["erros"]


def test_cpf_fora_do_formato():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(cpf="1234567890")
    )
    assert r.status_code == 400
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cpf_invalido_formato_certo():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(cpf="123.456.789-00")
    )
    assert r.status_code == 400
    assert "CPF inválido" in r.json()["erros"]


def test_cep_fora_do_formato():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(cep="05508-0900")
    )
    assert r.status_code == 400
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_fora_do_formato():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(data_de_nascimento="0102198")
    )
    assert r.status_code == 400
    assert (
        "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]
    )


def test_data_inexistente():
    r = get_client().post(
        "/api/solicitar", json=dados_alunos(data_de_nascimento="31/02/1980")
    )
    assert r.status_code == 400
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_todos_os_erros_de_uma_vez():
    r = get_client().post(
        "/api/solicitar",
        json=dados_alunos(
            n_usp="12a34567",
            numero_da_agencia="12a3",
            valor_solicitado="0",
            email="maria",
            cpf="123.456.789-00",
            cep="0550",
            data_de_nascimento="31/02/1980",
        ),
    )
    assert r.status_code == 400
    erros = r.json()["erros"]
    esperados = [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF inválido",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
    ]
    for e in esperados:
        assert e in erros, e


def test_erro_mantem_aba_ativa_e_valores():
    c = get_client()
    r = c.post("/api/solicitar", json=dados_docentes(email="joaoime.usp.br"))
    assert r.status_code == 400
    assert r.json()["aba"] == "docentes"


def test_docentes_validacao_igual_alunos():
    r = get_client().post(
        "/api/solicitar", json=dados_docentes(n_usp="12a34567")
    )
    assert r.status_code == 400
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_css_contem_cores_oficiais():
    r = get_client().get("/style.css")
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor in r.text, cor


def test_app_js_existe_e_tem_logica_de_mascara():
    r = get_client().get("/app.js")
    assert r.status_code == 200
    js = r.text
    assert "valor_solicitado" in js
    assert "cpf" in js
    assert "cep" in js
    assert "data_de_nascimento" in js
    assert "addEventListener" in js
    assert "fetch" in js


def test_sem_recursos_remotos():
    c = get_client()
    r = c.get("/")
    assert "http://" not in r.text.replace("http://localhost", "")
    assert "https://" not in r.text
    r_css = c.get("/style.css")
    assert "@import" not in r_css.text


def test_rotulo_enviar_solicitacao():
    r = get_client().get("/")
    assert r.text.count(">Enviar solicitação</button>") >= 2


def test_oficio_preserva_quebras_no_html():
    r = get_client().post(
        "/api/solicitar",
        json=dados_alunos(complemento="Sala 305"),
    )
    corpo = r.json()
    oficio = corpo["oficio"]
    linhas = oficio.split("\n")
    assert linhas[0] == "Interessada(o): Maria da Silva Souza - 12345678"


def test_linha_local_do_evento_no_oficio():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    assert (
        "Local: São Paulo - São Paulo - Brasil" in oficio
    )


def test_endereco_no_oficio():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    m = re.search(
        r"Endereço da\(o\) interessada\(o\)\n(.*?)\n\nDados para pagamento",
        oficio,
        re.S,
    )
    assert m
    assert m.group(1) == "Rua do Matão, 1010\nCEP: 05508-090\nButantã, São Paulo - São Paulo"


def test_oficio_secao_pagamento():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    m = re.search(
        r"Dados para pagamento\n(.*?)\n\nEncaminhe-se",
        oficio,
        re.S,
    )
    assert m
    assert m.group(1) == (
        "Data de nascimento: 01/02/1980\n"
        "CPF: 123.456.789-09\n"
        "RG / RNM: 12.345.678-9\n"
        "Banco: Banco do Brasil\n"
        "Agência: 1234\n"
        "Conta: 12345-6"
    )


def test_oficio_secao_evento_alunos():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    m = re.search(
        r"conforme segue:\n\nDados do evento\n(.*?)\n\nEndereço da\(o\) interessada\(o\)",
        oficio,
        re.S,
    )
    assert m
    assert m.group(1) == (
        "Evento: Congresso Nacional de Matemática\n"
        "Período: 10 a 12 de outubro de 2025\n"
        "Local: São Paulo - São Paulo - Brasil\n"
        "Apresentação de trabalho: Pôster\n"
        "Valor solicitado: R$ 15,00\n"
        "Detalhamento: Inscrição e hospedagem"
    )


def test_oficio_cabecalho_alunos():
    r = get_client().post("/api/solicitar", json=dados_alunos())
    oficio = r.json()["oficio"]
    assert oficio.startswith(
        "Interessada(o): Maria da Silva Souza - 12345678\n"
        "E-mail: maria@ime.usp.br\n"
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento\n"
        "Programa: Matemática - Mestrado\n"
    )
    assert (
        "\n\nA CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a\n"
        "interessada(o) acima, conforme segue:" in oficio
    )
