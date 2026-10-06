import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def _html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    return resposta.text


def _campos_obrigatorios(**overrides):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "numusp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "SBIA",
        "periodo_evento": "10 a 15 de março de 2026",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://sbia.org",
        "valor_solicitado": "150000",
        "detalhamento": "Apresentar artigo no evento.",
        "apresentar_trabalho": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco C",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "56789-0",
    }
    dados.update(overrides)
    return dados


def _campos_docentes(**overrides):
    dados = _campos_obrigatorios()
    dados["aba"] = "docentes"
    for chave in ("nivel", "tipo_auxilio"):
        dados.pop(chave, None)
    dados.update(overrides)
    return dados


def _mensagens(conteudo):
    return [m.strip() for m in re.findall(r"<li[^>]*>(.*?)</li>", conteudo, re.DOTALL)]


def test_pagina_principal_contem_as_duas_abas_na_ordem():
    conteudo = _html()
    assert "ALUNOS" in conteudo
    assert "DOCENTES" in conteudo
    assert conteudo.index("ALUNOS") < conteudo.index("DOCENTES")


def test_pagina_principal_contem_todos_os_rotulos_exatos():
    conteudo = _html()
    rotulos = [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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
    for rotulo in rotulos:
        assert rotulo in conteudo


def test_abas_contem_os_itens_de_selecao_exatos():
    conteudo = _html()
    for opcao in ("Mestrado", "Doutorado"):
        assert opcao in conteudo
    for opcao in ("Participação em evento", "Banca de exame ou defesa", "Outro"):
        assert opcao in conteudo
    for opcao in (
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in conteudo


def test_pagina_principal_contem_os_arquivos_estaticos():
    conteudo = _html()
    assert "app.js" in conteudo
    assert "style.css" in conteudo


def test_pagina_principal_contem_a_identidade_institucional():
    conteudo = _html()
    assert "assets/usp-logo.png" in conteudo
    assert "Universidade de São Paulo" in conteudo
    assert "IMe-USP" in conteudo or "IME-USP" in conteudo
    assert "Solicitação de Auxílio Financeiro" in conteudo


def test_arquivo_estatico_style_existe():
    resposta = client.get("/style.css")
    assert resposta.status_code == 200


def test_arquivo_estatico_app_existe():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200


def test_app_js_contem_a_formatacao_dos_campos():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    conteudo = resposta.text
    assert "R$" in conteudo
    assert "" in conteudo
    assert "-" in conteudo


def test_envio_valido_alunos_devolve_oficio_aluno():
    resposta = client.post("/solicitacao", json=_campos_obrigatorios())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is True
    assert corpo.get("erros") == []
    oficio = corpo.get("oficio")
    assert oficio
    assert "Solicitação registrada" in oficio
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Doutorado" in oficio
    assert "A CCP-Ciência da Computação" in oficio
    assert "Dados do evento" in oficio
    assert "Evento: SBIA" in oficio
    assert "Período: 10 a 15 de março de 2026" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: http://sbia.org" in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Apresentar artigo no evento." in oficio
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco C" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Cidade Universitária, São Paulo - SP" in oficio
    assert "Dados para pagamento" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_envio_valido_docentes_devolve_oficio_docente():
    resposta = client.post("/solicitacao", json=_campos_docentes())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is True
    oficio = corpo.get("oficio")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Programa: Ciência da Computação - " not in oficio


def test_campos_opcionais_em_branco_omitem_as_linhas_do_oficio():
    dados = _campos_obrigatorios(link_evento="", complemento="")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is True
    oficio = corpo.get("oficio")
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_campos_formatados_aparecem_formatados_no_oficio():
    dados = _campos_obrigatorios(valor_solicitado="150000000")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json().get("oficio")
    assert "Valor solicitado: R$ 1.500.000,00" in oficio


def test_obrigatorio_vazio_retorna_preencha_todos_os_campos():
    dados = _campos_obrigatorios(nome_completo="")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is False
    assert "Preencha todos os campos" in _mensagens("\n".join(corpo.get("erros")))


def test_numusp_com_letra():
    dados = _campos_obrigatorios(numusp="12a3")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "N. USP deve conter apenas números" in _mensagens("\n".join(erros))


def test_numero_agencia_com_letra():
    dados = _campos_obrigatorios(numero_agencia="12a")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "Número da agência deve conter apenas números" in _mensagens("\n".join(erros))


def test_valor_solicitado_igual_a_zero():
    dados = _campos_obrigatorios(valor_solicitado="0")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "Valor solicitado deve ser maior que 0" in _mensagens("\n".join(erros))


def test_valor_solicitado_negativo():
    dados = _campos_obrigatorios(valor_solicitado="-5")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "Valor solicitado deve ser maior que 0" in _mensagens("\n".join(erros))


def test_email_sem_arroba():
    dados = _campos_obrigatorios(email="maria.ime.usp.br")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "E-mail inválido" in _mensagens("\n".join(erros))


def test_email_sem_dominio():
    dados = _campos_obrigatorios(email="maria@")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "E-mail inválido" in _mensagens("\n".join(erros))


def test_cpf_fora_de_formato():
    dados = _campos_obrigatorios(cpf="123.456.78909")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "CPF deve estar no formato 000.000.000-00" in _mensagens("\n".join(erros))


def test_cep_fora_de_formato():
    dados = _campos_obrigatorios(cep="05508090")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "CEP deve estar no formato 00000-000" in _mensagens("\n".join(erros))


def test_data_nascimento_fora_de_formato():
    dados = _campos_obrigatorios(data_nascimento="1-2-1980")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _mensagens("\n".join(erros))


def test_cpf_formato_ok_digito_verificador_errado():
    dados = _campos_obrigatorios(cpf="123.456.789-00")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "CPF inválido" in _mensagens("\n".join(erros))


def test_data_nascimento_formato_ok_mas_data_inexistente():
    dados = _campos_obrigatorios(data_nascimento="30/02/1980")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    erros = resposta.json().get("erros")
    assert "Data de nascimento inválida" in _mensagens("\n".join(erros))
