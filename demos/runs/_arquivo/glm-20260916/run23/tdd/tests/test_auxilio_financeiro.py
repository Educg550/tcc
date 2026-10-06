import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app

client = TestClient(app)

MARCADOR_OFICIO = "Encaminhe-se ao Serviço Financeiro"

ALIASES = {
    "nome": ["nome", "nome_completo", "nomeCompleto", "NOME COMPLETO - SEM ABREVIAR"],
    "n_usp": ["n_usp", "nUsp", "numero_usp", "num_usp", "N. USP"],
    "programa": ["programa", "PROGRAMA"],
    "nivel": ["nivel", "NÍVEL"],
    "tipo_auxilio": ["tipo_auxilio", "tipoAuxilio", "tipo_de_auxilio", "auxilio", "TIPO DE AUXÍLIO"],
    "email": ["email", "e_mail", "E-MAIL"],
    "nome_evento": ["nome_evento", "nome_do_evento", "evento", "nomeEvento", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"],
    "periodo_evento": ["periodo_evento", "periodo", "periodo_do_evento", "PERÍODO DO EVENTO, EXAME OU DEFESA"],
    "cidade_evento": ["cidade_evento", "cidade_do_evento", "CIDADE DO EVENTO, EXAME OU DEFESA"],
    "estado_evento": ["estado_evento", "estado_do_evento", "ESTADO DO EVENTO, EXAME OU DEFESA"],
    "pais_evento": ["pais_evento", "pais_do_evento", "pais", "PAÍS DO EVENTO, EXAME OU DEFESA"],
    "link_evento": ["link_evento", "link_do_evento", "link", "LINK DO EVENTO, EXAME OU DEFESA"],
    "valor_solicitado": ["valor_solicitado", "valor", "valorSolicitado", "VALOR SOLICITADO (R$)"],
    "detalhamento": ["detalhamento", "detalhamento_do_pedido", "detalhamento_pedido", "DETALHAMENTO DO PEDIDO"],
    "apresentacao": ["apresentacao", "ira_apresentar_trabalho", "apresentacao_trabalho", "trabalho", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"],
    "data_nascimento": ["data_nascimento", "dataDeNascimento", "nascimento", "DATA DE NASCIMENTO"],
    "logradouro": ["logradouro", "endereco", "LOGRADOURO"],
    "numero": ["numero", "NÚMERO"],
    "complemento": ["complemento", "COMPLEMENTO"],
    "bairro": ["bairro", "BAIRRO"],
    "cep": ["cep", "CEP"],
    "cidade": ["cidade", "cidade_solicitante", "CIDADE"],
    "estado": ["estado", "estado_solicitante", "ESTADO"],
    "cpf": ["cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)"],
    "rg_rnm": ["rg_rnm", "rg", "rnm", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"],
    "nome_banco": ["nome_banco", "banco", "NOME DO BANCO"],
    "agencia": ["numero_agencia", "agencia", "NÚMERO DA AGÊNCIA"],
    "conta": ["numero_conta", "conta", "NÚMERO DA CONTA"],
}

CHAVES_ABA = [
    "aba",
    "formulario",
    "perfil",
    "categoria",
    "origem",
    "papel",
    "modo",
    "tipo_formulario",
    "tipo_de_formulario",
    "tipo_solicitante",
    "tipo_solicitacao",
    "tipo_de_solicitacao",
]

VALORES_ALUNOS = {
    "nome": "Maria de Souza",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria.souza@usp.br",
    "nome_evento": "Simpósio Brasileiro de Computação",
    "periodo_evento": "10 a 15 de julho de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://sbc.org.br/evento",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Inscrição e passagem aérea",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "101",
    "complemento": "Sala 12",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}

VALORES_DOCENTES = {
    campo: valor
    for campo, valor in VALORES_ALUNOS.items()
    if campo not in ("nivel", "tipo_auxilio")
}
VALORES_DOCENTES["programa"] = "Física Matemática"

ROTULOS = [
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

SEQUENCIA = [
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
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

LINHAS_OFICIO_ALUNOS = [
    "Interessada(o): Maria de Souza - 1234567",
    "E-mail: maria.souza@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "Dados do evento",
    "Evento: Simpósio Brasileiro de Computação",
    "Período: 10 a 15 de julho de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://sbc.org.br/evento",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição e passagem aérea",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 101",
    "Complemento: Sala 12",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 12345-6",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def _ocorre(texto, trecho):
    if trecho in texto:
        return True
    escapado = "".join(
        caractere if ord(caractere) < 128 else "\\u%04x" % ord(caractere)
        for caractere in trecho
    )
    return escapado in texto


def _rotas_post():
    return [
        rota.path
        for rota in app.routes
        if "POST" in (getattr(rota, "methods", None) or set())
    ]


def _caminho_envio(aba):
    caminhos = _rotas_post()
    if not caminhos:
        pytest.fail("O backend não declara rota POST para o envio da solicitação")
    if len(caminhos) > 1:
        for caminho in caminhos:
            if aba in caminho.lower():
                return caminho
    return caminhos[0]


def _payload(valores, aba, aba_em_maiusculas):
    payload = {}
    for campo, valor in valores.items():
        for chave in ALIASES[campo]:
            payload[chave] = valor
    valor_aba = aba.upper() if aba_em_maiusculas else aba
    for chave in CHAVES_ABA:
        payload[chave] = valor_aba
    return payload


def _enviar(valores, marcador, aba="alunos"):
    caminho = _caminho_envio(aba)
    com_aba_normal = _payload(valores, aba, False)
    com_aba_maiuscula = _payload(valores, aba, True)
    com_valor_em_digitos = dict(com_aba_normal)
    for chave in ALIASES["valor_solicitado"]:
        com_valor_em_digitos[chave] = "150000"
    tentativas = [
        (com_aba_normal, ""),
        (com_aba_maiuscula, ""),
        (com_aba_normal, "data"),
        (com_aba_maiuscula, "data"),
        (com_valor_em_digitos, ""),
    ]
    respostas = []
    for payload, modo in tentativas:
        try:
            if modo == "":
                respostas.append(client.post(caminho, =payload))
            else:
                respostas.append(client.post(caminho, data=payload))
        except Exception:
            continue
    for resposta in respostas:
        if _ocorre(resposta.text, marcador):
            return resposta
    if respostas:
        return respostas[0]
    pytest.fail("O backend não respondeu ao envio da solicitação")


def test_envio_valido_de_alunos_devolve_oficio_preenchido():
    resposta = _enviar(VALORES_ALUNOS, MARCADOR_OFICIO)
    texto = resposta.text
    for linha in LINHAS_OFICIO_ALUNOS:
        assert _ocorre(texto, linha)
    assert not _ocorre(texto, "Preencha todos os campos")


def test_envio_valido_de_docentes_devolve_oficio_de_docentes():
    resposta = _enviar(VALORES_DOCENTES, "Verba do programa", aba="docentes")
    texto = resposta.text
    assert _ocorre(texto, "Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
    assert _ocorre(texto, "Programa: Física Matemática")
    assert _ocorre(texto, "Interessada(o): Maria de Souza - 1234567")
    assert _ocorre(texto, MARCADOR_OFICIO)


def test_campos_opcionais_vazios_saem_do_oficio():
    valores = {**VALORES_ALUNOS, "link_evento": "", "complemento": ""}
    resposta = _enviar(valores, MARCADOR_OFICIO)
    texto = resposta.text
    assert not _ocorre(texto, "Link do evento:")
    assert not _ocorre(texto, "Complemento:")
    assert _ocorre(texto, "Local: São Paulo - SP - Brasil")


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    valores = {
        **VALORES_ALUNOS,
        "nome": "",
        "programa": "",
        "bairro": "",
        "cpf": "12345678999",
    }
    resposta = _enviar(valores, "CPF deve estar no formato 000.000.000-00")
    texto = resposta.text
    assert _ocorre(texto, "Preencha todos os campos")
    assert texto.count("Preencha todos os campos") == 1
    assert not _ocorre(texto, MARCADOR_OFICIO)


def test_envio_invalido_mostra_todas_as_mensagens_aplicaveis():
    valores = {
        **VALORES_ALUNOS,
        "nome": "",
        "n_usp": "12A3",
        "email": "maria.souza-atusp.br",
    }
    resposta = _enviar(valores, "N. USP deve conter apenas números")
    texto = resposta.text
    assert _ocorre(texto, "Preencha todos os campos")
    assert _ocorre(texto, "N. USP deve conter apenas números")
    assert _ocorre(texto, "E-mail inválido")
    assert not _ocorre(texto, MARCADOR_OFICIO)


def test_n_usp_deve_conter_apenas_numeros():
    resposta = _enviar(
        {**VALORES_ALUNOS, "n_usp": "1234A567"},
        "N. USP deve conter apenas números",
    )
    assert _ocorre(resposta.text, "N. USP deve conter apenas números")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_agencia_deve_conter_apenas_numeros():
    resposta = _enviar(
        {**VALORES_ALUNOS, "agencia": "12A4"},
        "Número da agência deve conter apenas números",
    )
    assert _ocorre(resposta.text, "Número da agência deve conter apenas números")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_valor_solicitado_deve_ser_maior_que_zero():
    resposta = _enviar(
        {**VALORES_ALUNOS, "valor_solicitado": "R$ 0,00"},
        "Valor solicitado deve ser maior que 0",
    )
    assert _ocorre(resposta.text, "Valor solicitado deve ser maior que 0")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_email_sem_arroba_ou_dominio_e_invalido():
    resposta = _enviar(
        {**VALORES_ALUNOS, "email": "maria.souza-atusp.br"},
        "E-mail inválido",
    )
    assert _ocorre(resposta.text, "E-mail inválido")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_cpf_fora_do_formato():
    resposta = _enviar(
        {**VALORES_ALUNOS, "cpf": "12345678909"},
        "CPF deve estar no formato 000.000.000-00",
    )
    assert _ocorre(resposta.text, "CPF deve estar no formato 000.000.000-00")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_cpf_com_digito_verificador_invalido():
    resposta = _enviar(
        {**VALORES_ALUNOS, "cpf": "123.456.789-99"},
        "CPF inválido",
    )
    assert _ocorre(resposta.text, "CPF inválido")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_cep_fora_do_formato():
    resposta = _enviar(
        {**VALORES_ALUNOS, "cep": "05508090"},
        "CEP deve estar no formato 00000-000",
    )
    assert _ocorre(resposta.text, "CEP deve estar no formato 00000-000")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_data_nascimento_fora_do_formato():
    resposta = _enviar(
        {**VALORES_ALUNOS, "data_nascimento": "01-02-1980"},
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    )
    assert _ocorre(resposta.text, "Data de nascimento deve estar no formato dd/mm/aaaa")
    assert not _ocorre(resposta.text, MARCADOR_OFICIO)


def test_data_de_nascimento_inexistente():
    resposta_dia = _enviar(
        {**VALORES_ALUNOS, "data_nascimento": "31/02/1980"},
        "Data de nascimento inválida",
    )
    assert _ocorre(resposta_dia.text, "Data de nascimento inválida")
    resposta_mes = _enviar(
        {**VALORES_ALUNOS, "data_nascimento": "05/13/1980"},
        "Data de nascimento inválida",
    )
    assert _ocorre(resposta_mes.text, "Data de nascimento inválida")


def test_pagina_inicial_e_servida_com_abas_scripts_e_estilos():
    resposta = client.get("/")
    assert resposta.status_code == 200
    html = resposta.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "app.js" in html
    assert "style.css" in html


def test_abas_estao_na_ordem_alunos_docentes():
    html = client.get("/").text
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_blocos_e_rotulos_exatos_estao_na_pagina():
    html = client.get("/").text
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in html
    for rotulo in ROTULOS:
        assert rotulo in html


def test_ordem_das_abas_blocos_e_rotulos():
    html = client.get("/").text
    indices = [html.index(texto) for texto in SEQUENCIA]
    assert indices == sorted(indices)


def test_opcoes_dos_campos_exclusivos_da_aba_alunos():
    html = client.get("/").text
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in html


def test_cada_aba_tem_seu_botao_enviar():
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_confirmacao_e_cabecalho_institucional():
    html = client.get("/").text
    assert "Solicitação registrada" in html
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_todo_campo_tem_placeholder():
    html = client.get("/").text
    assert html.lower().count("placeholder") >= 20


def test_css_com_identidade_visual_da_usp():
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert "text/css" in resposta.headers["content-type"]
    css = resposta.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "open sans" in css


def test_javascript_e_servido():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip() != ""


def test_logotipo_e_servido_como_imagem():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")
    assert len(resposta.content) > 0
