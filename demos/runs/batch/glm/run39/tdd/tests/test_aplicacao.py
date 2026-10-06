"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

from fastapi.testclient import TestClient

from app import app


def _basico():
    """Dados válidos comuns às duas abas."""
    return {
        "nome": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com.br",
        "valor": "150000",
        "detalhamento": "Inscrição no evento e passagens aéreas.",
        "apresentacao": "Pôster",
        "nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade_endereco": "São Paulo",
        "estado_endereco": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }


def _aluno(dados=None):
    dados = _basico()
    dados.update({"nivel": "Mestrado", "tipo": "Participação em evento"})
    if dados is not None:
        pass
    return dados


def _docente():
    dados = _basico()
    dados.pop("nivel", None)
    dados.pop("tipo", None)
    return dados


# --------------------------------------------------------------------- frontend


def test_pagina_inicial_contem_abas_e_rotulos(client):
    r = client.get("/")
    html = r.text
    for rotulo in (
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert rotulo in html
    # ordem das abas
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_pagina_inicial_tem_campos_do_bloco_solicitante(client):
    html = client.get("/").text
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
        assert rotulo in html


def test_pagina_inicial_tem_campos_dos_outros_blocos(client):
    html = client.get("/").text
    for rotulo in (
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
    ):
        assert rotulo in html


def test_campos_da_aba_alunos_exclusivos(client):
    html = client.get("/").text
    assert "Mestrado" in html
    assert "Doutorado" in html
    assert "Participação em evento" in html
    assert "Banca de exame ou defesa" in html
    assert "Outro" in html


def test_campos_apresentacao(client):
    html = client.get("/").text
    for opcao in ("Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert opcao in html


def test_estaticos_estao_disponiveis(client):
    for caminho in ("/static/style.css", "/static/app.js", "/static/usp-logo.png"):
        assert client.get(caminho).status_code == 200


def test_css_sem_fonte_remota(client):
    css = client.get("/static/style.css").text
    assert "@import" not in css
    assert not re.search(r"url\(\s*[\"']?https?://", css)


def test_cabecalho_universidade(client):
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    # o brasão (escudo) não aparece na página
    assert "escudo" not in html.lower()
    assert "brasao" not in html.lower()
    assert "brasão" not in html.lower()


def test_css_usa_cores_da_usp(client):
    css = client.get("/static/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_css_familia_de_fonte_sem_serifa(client):
    css = client.get("/static/style.css").text.lower()
    assert "font-family" in css
    assert "open sans" in css or "sans-serif" in css


def test_oficio_preserva_quebras_de_linha(client):
    r = _enviar(client, "alunos", _aluno())
    assert r.json() == {
        "oficio": r.json()["oficio"],
        "titulo": "Solicitação registrada",
    }
    oficio = r.json()["oficio"]
    # o ofício tem a estrutura de linhas do requisito
    assert oficio.startswith("Interessada(o): ")
    assert "\n" in oficio


# --------------------------------------------------------------------- backend


def _enviar(client, aba, dados):
    carga = dict(dados)
    carga["aba"] = aba
    return client.post("/solicitacao", json=carga)


def test_aluno_valido_recebe_oficio(client):
    r = _enviar(client, "alunos", _aluno())
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["titulo"] == "Solicitação registrada"
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva Souza - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de outubro de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição no evento e passagens aéreas." in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "Complemento:" not in oficio


def test_docente_valido_recebe_oficio(client):
    r = _enviar(client, "docentes", _docente())
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio


def test_link_vazio_sai_do_oficio(client):
    dados = _aluno()
    dados["link"] = ""
    oficio = _enviar(client, "alunos", dados).json()["oficio"]
    assert "Link do evento" not in oficio


def test_complemento_vazio_sai_do_oficio(client):
    dados = _aluno()
    dados["complemento"] = "Apto 12"
    oficio1 = _enviar(client, "alunos", dados).json()["oficio"]
    assert "Complemento: Apto 12" in oficio1
    dados["complemento"] = ""
    oficio2 = _enviar(client, "alunos", dados).json()["oficio"]
    assert "Complemento" not in oficio2


def test_oficio_aluno_estrutura_completa(client):
    oficio = _enviar(client, "alunos", _aluno()).json()["oficio"]
    esperado = [
        "Interessada(o): Maria da Silva Souza - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: Congresso Nacional de Matemática",
        "Período: 10 a 12 de outubro de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição no evento e passagens aéreas.",
        "",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    assert oficio == "\n".join(esperado)


def test_oficio_docente_estrutura_completa(client):
    oficio = _enviar(client, "docentes", _docente()).json()["oficio"]
    esperado = [
        "Interessada(o): Maria da Silva Souza - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
        "Programa: Matemática",
        "",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: Congresso Nacional de Matemática",
        "Período: 10 a 12 de outubro de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição no evento e passagens aéreas.",
        "",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    assert oficio == "\n".join(esperado)


# ------------------------------------------------------------------- validação


def test_campo_obrigatorio_vazio(client):
    dados = _aluno()
    dados["nome"] = ""
    r = _enviar(client, "alunos", dados)
    assert r.status_code == 400
    assert "Preencha todos os campos" in r.json()["erros"]


def test_mensagem_campo_vazio_aparece_uma_vez(client):
    dados = _aluno()
    dados["nome"] = ""
    dados["programa"] = ""
    r = _enviar(client, "alunos", dados)
    assert r.json()["erros"].count("Preencha todos os campos") == 1


def test_campo_opcional_vazio_nao_gera_erro(client):
    dados = _aluno()
    dados["link"] = ""
    dados["complemento"] = ""
    r = _enviar(client, "alunos", dados)
    assert r.status_code == 200


def test_n_usp_somente_digitos(client):
    dados = _aluno()
    dados["n_usp"] = "1234567a"
    r = _enviar(client, "alunos", dados)
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_somente_digitos(client):
    dados = _aluno()
    dados["agencia"] = "1234-x"
    r = _enviar(client, "alunos", dados)
    assert "Número da agência deve conter apenas números" in r.json()["erros"]


def test_valor_maior_que_zero(client):
    dados = _aluno()
    dados["valor"] = "000"
    r = _enviar(client, "alunos", dados)
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_valor_negativo(client):
    dados = _aluno()
    dados["valor"] = "-100"
    r = _enviar(client, "alunos", dados)
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido(client):
    dados = _aluno()
    dados["email"] = "maria ime.usp.br"
    r = _enviar(client, "alunos", dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_email_sem_dominio(client):
    dados = _aluno()
    dados["email"] = "maria@"
    r = _enviar(client, "alunos", dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_formato_errado(client):
    dados = _aluno()
    dados["cpf"] = "1234567890"
    r = _enviar(client, "alunos", dados)
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cpf_invalido_verificador(client):
    dados = _aluno()
    dados["cpf"] = "12345678900"
    r = _enviar(client, "alunos", dados)
    assert "CPF inválido" in r.json()["erros"]


def test_cep_formato_errado(client):
    dados = _aluno()
    dados["cep"] = "05508-09"
    r = _enviar(client, "alunos", dados)
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_nascimento_formato_errado(client):
    dados = _aluno()
    dados["nascimento"] = "01-02-1980"
    r = _enviar(client, "alunos", dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]


def test_data_nascimento_inexistente(client):
    dados = _aluno()
    dados["nascimento"] = "31021980"
    r = _enviar(client, "alunos", dados)
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_data_nascimento_mes_invalido(client):
    dados = _aluno()
    dados["nascimento"] = "01131980"
    r = _enviar(client, "alunos", dados)
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_validacao_igual_para_docentes(client):
    dados = _docente()
    dados["email"] = "invalido"
    r = _enviar(client, "docentes", dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_varios_erros_de_uma_vez(client):
    dados = _aluno()
    dados["n_usp"] = "abc"
    dados["email"] = "sem-arroba"
    r = _enviar(client, "alunos", dados)
    erros = r.json()["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros


def test_com_erro_nao_gera_oficio(client):
    dados = _aluno()
    dados["email"] = "invalido"
    r = _enviar(client, "alunos", dados)
    assert "oficio" not in r.json()


# ------------------------------------------------------------------ formatação


def test_formata_valor_moeda(client):
    for digitado, mostrado in (
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ):
        r = client.get("/formatar/valor", params={"digitado": digitado})
        assert r.status_code == 200
        assert r.json()["formatado"] == mostrado


def test_formata_cpf(client):
    r = client.get("/formatar/cpf", params={"digitado": "12345678909"})
    assert r.json()["formatado"] == "123.456.789-09"


def test_formata_cep(client):
    r = client.get("/formatar/cep", params={"digitado": "05508090"})
    assert r.json()["formatado"] == "05508-090"


def test_formata_data(client):
    r = client.get("/formatar/data", params={"digitado": "01021980"})
    assert r.json()["formatado"] == "01/02/1980"
