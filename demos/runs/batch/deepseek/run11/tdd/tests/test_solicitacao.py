from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

ENDPOINT = "/solicitacao"

ROTULOS = [
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
    "Pôster",
    "Apresentação oral",
    "Não irá apresentar trabalho",
]

CAMPOS_ALUNO = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "12345678",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Simpósio Brasileiro de Redes",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10 a 12 de outubro de 2024",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbrc.example.org",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e hospedagem",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Bloco B",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "12345-6",
}


def aluno(alteracoes=None):
    campos = dict(CAMPOS_ALUNO)
    campos.update(alteracoes or {})
    return campos


def docente(alteracoes=None):
    campos = dict(CAMPOS_ALUNO)
    del campos["NÍVEL"]
    del campos["TIPO DE AUXÍLIO"]
    campos.update(alteracoes or {})
    return campos


def enviar(aba, campos):
    return cliente.post(ENDPOINT, json={"aba": aba, "campos": campos})


def erros_de(campos, aba="ALUNOS"):
    return enviar(aba, campos).json()["erros"]


# --- página ---

def test_pagina_traz_a_identidade_da_universidade():
    html = cliente.get("/").text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_pagina_traz_as_duas_abas_na_ordem():
    html = cliente.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_pagina_traz_todos_os_rotulos():
    html = cliente.get("/").text
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_opcoes_das_selecoes_estao_na_pagina():
    html = cliente.get("/").text
    for opcao in OPCOES:
        assert opcao in html, opcao


def test_cada_aba_tem_seu_botao_de_envio():
    html = cliente.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_estilo_e_script_sao_servidos_como_estaticos():
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200
    html = cliente.get("/").text
    assert "style.css" in html
    assert "app.js" in html


def test_logo_e_servido_como_estatico():
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_css_usa_as_cores_da_universidade():
    css = cliente.get("/style.css").text
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_usa_a_fonte_indicada_pela_universidade():
    assert "Open Sans" in cliente.get("/style.css").text


def test_oficio_preserva_as_quebras_de_linha():
    css = cliente.get("/style.css").text
    html = cliente.get("/").text
    assert "pre-wrap" in css or "pre-line" in css or "<pre" in html


def test_a_confirmacao_tem_o_titulo():
    textos = cliente.get("/").text + cliente.get("/app.js").text
    assert "Solicitação registrada" in textos


# --- envio válido ---

def test_solicitacao_valida_de_aluno_devolve_o_oficio_preenchido():
    resposta = enviar("ALUNOS", aluno())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação" in oficio
    assert "Evento: Simpósio Brasileiro de Redes" in oficio
    assert "Período: 10 a 12 de outubro de 2024" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://sbrc.example.org" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem aérea e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco B" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_solicitacao_valida_de_docente_usa_a_verba_do_programa():
    resposta = enviar("DOCENTES", docente())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Programa: Ciência da Computação - Mestrado" not in oficio


def test_valor_aparece_no_oficio_ja_formatado():
    oficio = enviar("ALUNOS", aluno({"VALOR SOLICITADO (R$)": "R$ 1.500.000,00"})).json()["oficio"]
    assert "Valor solicitado: R$ 1.500.000,00" in oficio


def test_link_vazio_sai_do_oficio():
    oficio = enviar("ALUNOS", aluno({"LINK DO EVENTO, EXAME OU DEFESA": ""})).json()["oficio"]
    assert "Link do evento" not in oficio


def test_complemento_vazio_sai_do_oficio():
    oficio = enviar("ALUNOS", aluno({"COMPLEMENTO": ""})).json()["oficio"]
    assert "Complemento" not in oficio


# --- validação ---

def test_campo_obrigatorio_vazio_mostra_uma_unica_mensagem():
    campos = aluno({"NOME COMPLETO - SEM ABREVIAR": "", "PROGRAMA": "", "LOGRADOURO": ""})
    corpo = enviar("ALUNOS", campos).json()
    assert corpo["erros"].count("Preencha todos os campos") == 1
    assert not corpo.get("oficio")


def test_n_usp_so_digitos():
    assert "N. USP deve conter apenas números" in erros_de(aluno({"N. USP": "12A34"}))


def test_agencia_so_digitos():
    assert "Número da agência deve conter apenas números" in erros_de(aluno({"NÚMERO DA AGÊNCIA": "12-34"}))


def test_valor_precisa_ser_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in erros_de(aluno({"VALOR SOLICITADO (R$)": "R$ 0,00"}))


def test_email_invalido():
    assert "E-mail inválido" in erros_de(aluno({"E-MAIL": "maria"}))


def test_cpf_fora_do_formato():
    assert "CPF deve estar no formato 000.000.000-00" in erros_de(
        aluno({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})
    )


def test_cep_fora_do_formato():
    assert "CEP deve estar no formato 00000-000" in erros_de(aluno({"CEP": "05508090"}))


def test_data_de_nascimento_fora_do_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros_de(
        aluno({"DATA DE NASCIMENTO": "01-02-1980"})
    )


def test_cpf_com_digitos_verificadores_errados():
    assert "CPF inválido" in erros_de(
        aluno({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})
    )


def test_data_de_nascimento_inexistente():
    assert "Data de nascimento inválida" in erros_de(
        aluno({"DATA DE NASCIMENTO": "31/02/1980"})
    )


def test_mes_fora_de_1_a_12():
    assert "Data de nascimento inválida" in erros_de(
        aluno({"DATA DE NASCIMENTO": "01/13/1980"})
    )


def test_erro_nao_gera_oficio():
    assert not enviar("ALUNOS", aluno({"E-MAIL": "maria"})).json().get("oficio")
