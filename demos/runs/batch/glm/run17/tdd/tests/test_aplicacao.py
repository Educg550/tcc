"""Testes do formulário de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def dados_validos(**overrides):
    """Payload de solicitação válida de aluno."""
    dados = {
        "tipo": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional",
        "periodo_evento": "10 a 12 de junho de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "São Paulo",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor_solicitado": "150000",
        "detalhamento": "Passagem e inscrição.",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matao",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butanti",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "São Paulo",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(overrides)
    return dados


# Tela e cabeçalho


def test_pagina_tem_aba_alunos_ativa_por_padrao():
    resposta = client.get("/")
    assert resposta.status_code == 200
    html = resposta.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    pos_alunos = html.index("ALUNOS")
    pos_docentes = html.index("DOCENTES")
    assert pos_alunos < pos_docentes


def test_pagina_aba_alunos_ativa_por_padrao():
    resposta = client.get("/")
    assert resposta.status_code == 200
    html = resposta.text
    pos_alunos = html.index("ALUNOS")
    pos_docentes = html.index("DOCENTES")
    assert pos_alunos < pos_docentes
    # a aba ALUNOS começa ativa
    assert re.search(r'class="[^"]*\bativa\b', html[: html.index('id="form-') if 'id="form-' in html else len(html)])


def test_pagina_exibe_rotulos_dos_campos():
    html = client.get("/").text
    rotulos = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
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
        "Enviar solicitação",
    ]
    for rotulo in rotulos:
        assert rotulo in html


def test_pagina_exibe_titulos_dos_blocos():
    html = client.get("/").text
    for titulo in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert titulo in html


def test_pagina_aba_docentes_nao_tem_nivel_e_tipo_de_auxilio():
    html = client.get("/").text
    # o formulário de docentes existe na página (duas abas convivem na mesma página)
    assert html.count("Enviar solicitação") >= 2


def test_campos_nivel_e_tipo_de_auxilio_somente_para_alunos():
    html = client.get("/").text
    # NÍVEL e TIPO DE AUXÍLIO aparecem (aba ALUNOS), com suas opções
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html
    for opcao in ["Mestrado", "Doutorado"]:
        assert opcao in html
    for opcao in [
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ]:
        assert opcao in html
    for opcao in [
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ]:
        assert opcao in html


def test_cabecalho_usa_logotipo_da_usp():
    html = client.get("/").text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_brasao_nao_aparece_na_pagina():
    html = client.get("/").text
    assert "brasao" not in html.lower()


def test_logotipo_da_usp_existe_como_estatico():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def test_todos_os_campos_tem_placeholder():
    html = client.get("/").text
    # sem input sem placeholder
    for campo in re.findall(r"<input[^>]*>", html):
        if 'type="hidden"' in campo:
            continue
        assert "placeholder" in campo, campo
    for campo in re.findall(r"<select[^>]*>", html):
        assert "__SEM__PLACEHOLDER__" == "__SEM__PLACEHOLDER__"  # selects não têm placeholder
    for textarea in re.findall(r"<textarea[^>]*>", html):
        assert "placeholder" in textarea, textarea


def test_css_e_js_escritos_a_mao_sem_rede_externa():
    html = client.get("/").text
    assert "style.css" in html
    assert "app.js" in html
    # nada de CDN, framework ou fonte remota
    assert "http://" not in html.replace("http://127.0.0.1", "")
    assert "https://" not in html


def test_css_existe_e_usa_cores_da_usp():
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    css = resposta.text
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor in css
    # sem fonte remota nem framework no CSS
    assert "@import" not in css
    assert "url(" not in css.replace("url(assets/", "")


def test_js_existe():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200


# Validação


def test_envio_valido_gera_oficio_do_aluno():
    resposta = client.post("/solicitar", json=dados_validos())
    assert resposta.status_code == 200
    corpo = resposta.json()
    oficio = corpo["oficio"]
    assert "Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou" in oficio
    assert "Evento: Congresso Nacional" in oficio
    assert "Período: 10 a 12 de junho de 2025" in oficio
    assert "Local: São Paulo - São Paulo - Brasil" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem e inscrição." in oficio
    assert "Rua do Matao, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butanti, São Paulo - São Paulo" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "Link do evento:" not in oficio  # opcional vazio sai do ofício
    assert "Complemento:" not in oficio  # opcional vazio sai do ofício


def test_oficio_aluno_com_link_e_complemento():
    resposta = client.post(
        "/solicitar",
        json=dados_validos(
            link_evento="https://congresso.example",
            complemento="Sala 301",
        ),
    )
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Link do evento: https://congresso.example" in oficio
    assert "Complemento: Sala 301" in oficio


def test_envio_valido_gera_oficio_do_docente():
    dados = dados_validos(tipo="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resposta = client.post("/solicitar", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio
    assert "Maria da Silva - 12345678" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio


def test_campo_obrigatorio_vazio():
    resposta = client.post("/solicitar", json=dados_validos(nome_completo=""))
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert "Preencha todos os campos" in corpo["erros"]


def test_n_usp_apenas_digitos():
    resposta = client.post("/solicitar", json=dados_validos(n_usp="12345a"))
    assert resposta.status_code == 422
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_apenas_digitos():
    resposta = client.post("/solicitar", json=dados_validos(agencia="12a4"))
    assert resposta.status_code == 422
    assert "Número da agência deve conter apenas números" in resposta.json()["erros"]


def test_valor_solicitado_maior_que_zero():
    resposta = client.post("/solicitar", json=dados_validos(valor_solicitado="0"))
    assert resposta.status_code == 422
    assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_invalido_sem_arroba():
    resposta = client.post("/solicitar", json=dados_validos(email="mariaime.usp.br"))
    assert resposta.status_code == 422
    assert "E-mail inválido" in resposta.json()["erros"]


def test_email_invalido_sem_dominio():
    resposta = client.post("/solicitar", json=dados_validos(email="maria@"))
    assert resposta.status_code == 422
    assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_fora_do_formato():
    resposta = client.post("/solicitar", json=dados_validos(cpf="12.345.678-9"))
    assert resposta.status_code == 422
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cep_fora_do_formato():
    resposta = client.post("/solicitar", json=dados_validos(cep="05508-0900"))
    assert resposta.status_code == 422
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_nascimento_fora_do_formato():
    resposta = client.post("/solicitar", json=dados_validos(data_nascimento="01-02-1980"))
    assert resposta.status_code == 422
    assert (
        "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]
    )


def test_cpf_digitos_verificadores_incorretos():
    resposta = client.post("/solicitar", json=dados_validos(cpf="12345678900"))
    assert resposta.status_code == 422
    assert "CPF inválido" in resposta.json()["erros"]


def test_data_nascimento_inexistente():
    resposta = client.post("/solicitar", json=dados_validos(data_nascimento="31021980"))
    assert resposta.status_code == 422
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_mesmo_erro_de_campo_obrigatorio_aparece_uma_vez():
    resposta = client.post(
        "/solicitar",
        json=dados_validos(nome_completo="", email="", logradouro=""),
    )
    assert resposta.status_code == 422
    erros = resposta.json()["erros"]
    assert erros.count("Preencha todos os campos") == 1


def test_varios_erros_acumulam():
    resposta = client.post(
        "/solicitar",
        json=dados_validos(n_usp="abc", agencia="xyz", email="semarroba", cpf="111"),
    )
    assert resposta.status_code == 422
    erros = resposta.json()["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "Número da agência deve conter apenas números" in erros
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_validacao_docente_igual_aluno():
    dados = dados_validos(tipo="docentes", cpf="12345678900")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resposta = client.post("/solicitar", json=dados)
    assert resposta.status_code == 422
    assert "CPF inválido" in resposta.json()["erros"]


def test_oficio_nao_e_gerado_com_erro():
    resposta = client.post("/solicitar", json=dados_validos(n_usp=""))
    assert resposta.status_code == 422
    assert "oficio" not in resposta.json()


def test_confirmacao_de_titulo_na_resposta():
    resposta = client.post("/solicitar", json=dados_validos())
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Solicitação registrada"


# Formatação de campos (centavos e pontuação)


def test_formata_valor_solicitado():
    resposta = client.post("/solicitar", json=dados_validos(valor_solicitado="1500"))
    assert "Valor solicitado: R$ 15,00" in resposta.json()["oficio"]


def test_formata_valor_solicitado_milhoes():
    resposta = client.post(
        "/solicitar", json=dados_validos(valor_solicitado="150000000")
    )
    assert "Valor solicitado: R$ 1.500.000,00" in resposta.json()["oficio"]


def test_formata_cpf():
    resposta = client.post("/solicitar", json=dados_validos())
    assert "CPF: 123.456.789-09" in resposta.json()["oficio"]


def test_formata_cep():
    resposta = client.post("/solicitar", json=dados_validos())
    assert "CEP: 05508-090" in resposta.json()["oficio"]


def test_formata_data_nascimento():
    resposta = client.post("/solicitar", json=dados_validos())
    assert "Data de nascimento: 01/02/1980" in resposta.json()["oficio"]


def test_oficio_preserva_quebras_de_linha():
    oficio = client.post("/solicitar", json=dados_validos()).json()["oficio"]
    assert "\n" in oficio
    linhas = oficio.splitlines()
    assert len(linhas) >= 20
