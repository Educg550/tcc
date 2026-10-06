import pytest
from fastapi.testclient import TestClient

from app import app


cliente = TestClient(app)


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


OFICIO_FINAL = "Encaminhe-se ao Serviço Financeiro para providências."


def _pagina():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.text


def _recurso(nome):
    for caminho in ("/" + nome, "/static/" + nome):
        resposta = cliente.get(caminho)
        if resposta.status_code == 200:
            return resposta
    pytest.fail(nome + " não é servido pela aplicação")


def dados_validos(aba="alunos"):
    dados = {
        "nome_completo": "Maria da Silva Santos",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "email": "maria@ime.usp.br",
        "nome_evento": "Simpósio Brasileiro de Computação",
        "periodo": "10 a 15 de julho de 2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.ime.usp.br",
        "valor": "150000",
        "detalhamento": "Passagens e hospedagem.",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
        "aba": aba,
    }
    if aba == "alunos":
        dados["nivel"] = "Mestrado"
        dados["tipo_auxilio"] = "Participação em evento"
    return dados


def _caminhos(aba):
    return [
        "/api/" + aba,
        "/" + aba,
        "/api/solicitacao/" + aba,
        "/api/solicitacao",
        "/solicitacao",
        "/api/solicitar",
        "/solicitar",
        "/api/enviar",
        "/enviar",
    ]


def enviar(dados, aba="alunos"):
    for caminho in _caminhos(aba):
        resposta = cliente.post(caminho, json=dados)
        if resposta.status_code != 404:
            return resposta
    pytest.fail("endpoint de solicitação não encontrado")


def enviar_com_erro(**campos):
    dados = dados_validos()
    dados.update(campos)
    return enviar(dados)


def test_pagina_tem_as_duas_abas_na_ordem():
    pagina = _pagina()
    assert "ALUNOS" in pagina
    assert "DOCENTES" in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")


def test_pagina_tem_os_titulos_dos_blocos():
    pagina = _pagina()
    assert "SOLICITANTE E EVENTO" in pagina
    assert "ENDEREÇO DO SOLICITANTE" in pagina
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in pagina


def test_pagina_tem_os_rotulos_dos_campos():
    pagina = _pagina()
    for rotulo in ROTULOS:
        assert rotulo in pagina, rotulo


def test_pagina_tem_botao_enviar_solicitacao_em_cada_aba():
    pagina = _pagina()
    assert pagina.count("Enviar solicitação") >= 2


def test_pagina_tem_as_opcoes_de_selecao():
    pagina = _pagina()
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
        assert opcao in pagina, opcao


def test_pagina_tem_placeholder_em_cada_campo():
    pagina = _pagina()
    assert pagina.count("placeholder=") >= len(ROTULOS)


def test_cabecalho_institucional():
    pagina = _pagina()
    assert "Universidade de São Paulo" in pagina
    assert "usp-logo.png" in pagina


def test_css_com_as_cores_da_universidade():
    css = _recurso("style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_sem_fonte_remota_e_com_sem_serifa():
    css = _recurso("style.css").text.lower()
    assert "@import" not in css
    assert "url(http" not in css
    assert "sans-serif" in css


def test_js_servido():
    js = _recurso("app.js").text
    assert js.strip()


def test_logo_usp_servido():
    resposta = _recurso("assets/usp-logo.png")
    assert resposta.content


def test_solicitacao_valida_de_aluno_gera_oficio():
    texto = enviar(dados_validos("alunos"), "alunos").text
    assert "Interessada(o): Maria da Silva Santos - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    )
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Simpósio Brasileiro de Computação" in texto
    assert "Período: 10 a 15 de julho de 2024" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://evento.ime.usp.br" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagens e hospedagem." in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Bloco B" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert OFICIO_FINAL in texto


def test_solicitacao_valida_de_docente_gera_oficio():
    texto = enviar(dados_validos("docentes"), "docentes").text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Mestrado" not in texto
    assert "Interessada(o): Maria da Silva Santos - 12345678" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert OFICIO_FINAL in texto


def test_link_e_complemento_vazios_saem_do_oficio():
    dados = dados_validos()
    dados["link_evento"] = ""
    dados["complemento"] = ""
    texto = enviar(dados).text
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto
    assert OFICIO_FINAL in texto


def test_campos_obrigatorios_vazios():
    dados = dados_validos()
    for chave in dados:
        if chave != "aba":
            dados[chave] = ""
    texto = enviar(dados).text
    assert "Preencha todos os campos" in texto
    assert OFICIO_FINAL not in texto


def test_n_usp_com_letras():
    texto = enviar_com_erro(n_usp="12a45678").text
    assert "N. USP deve conter apenas números" in texto
    assert OFICIO_FINAL not in texto


def test_agencia_com_letras():
    texto = enviar_com_erro(agencia="12a4").text
    assert "Número da agência deve conter apenas números" in texto
    assert OFICIO_FINAL not in texto


def test_valor_zero():
    texto = enviar_com_erro(valor="0").text
    assert "Valor solicitado deve ser maior que 0" in texto
    assert OFICIO_FINAL not in texto


def test_email_invalido():
    texto = enviar_com_erro(email="maria.ime.usp.br").text
    assert "E-mail inválido" in texto
    assert OFICIO_FINAL not in texto


def test_cpf_fora_do_formato():
    texto = enviar_com_erro(cpf="12345678909").text
    assert "CPF deve estar no formato 000.000.000-00" in texto
    assert OFICIO_FINAL not in texto


def test_cep_fora_do_formato():
    texto = enviar_com_erro(cep="05508090").text
    assert "CEP deve estar no formato 00000-000" in texto
    assert OFICIO_FINAL not in texto


def test_data_fora_do_formato():
    texto = enviar_com_erro(data_nascimento="1980-02-01").text
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto
    assert OFICIO_FINAL not in texto


def test_cpf_com_digitos_verificadores_invalidos():
    texto = enviar_com_erro(cpf="123.456.789-00").text
    assert "CPF inválido" in texto
    assert OFICIO_FINAL not in texto


def test_data_inexistente():
    texto = enviar_com_erro(data_nascimento="31/02/1980").text
    assert "Data de nascimento inválida" in texto
    assert OFICIO_FINAL not in texto


def test_varias_mensagens_de_erro_de_uma_vez():
    texto = enviar_com_erro(
        n_usp="12a45678", agencia="12a4", email="sem-arroba"
    ).text
    assert "N. USP deve conter apenas números" in texto
    assert "Número da agência deve conter apenas números" in texto
    assert "E-mail inválido" in texto
    assert OFICIO_FINAL not in texto
