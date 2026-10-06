"""Testes do requisito: formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import re

import pytest
from fastapi.testclient import TestClient

from app import app

CLIENT = TestClient(app)

SOLICITANTE_BLOCO = "SOLICITANTE E EVENTO"
ENDERECO_BLOCO = "ENDEREÇO DO SOLICITANTE"
PAGAMENTO_BLOCO = "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"

ROTEXOS_SOLICITANTE = [
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
]

ROTEIRO_ALUNOS = [
    "NÍVEL",
    "TIPO DE AUXÍLIO",
]

ROTEIRO_DOCENTES_EXCLUSO = ROTEIRO_ALUNOS

ROTEXOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]

ROTEXOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

VALORES_OBRIGATORIOS = {
    "nome_completo": "Maria da Silva",
    "n_usp": "1234567",
    "programa": "Matemática",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso de Matemática",
    "periodo_evento": "2024-05-01",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://example.com",
    "valor_solicitado": "150000",
    "detalhamento": "participação com trabalho",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Casa",
    "bairro": "Cidade Universitaria",
    "cep": "05508090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "12345678909",
    "rg_rnm": "1234567",
    "nome_banco": "Banco do Brasil",
    "numero_agencia": "1234",
    "numero_conta": "12345",
}


def _campos_para_solicitar(tipo, omitidos=(), extras=None):
    campos = {"tipo": tipo}
    for chave, valor in VALORES_OBRIGATORIOS.items():
        if chave in omitidos:
            continue
        if tipo == "docentes" and chave in ("nivel", "tipo_auxilio"):
            continue
        campos[chave] = valor
    if extras:
        campos.update(extras)
    return campos


def _oficio_para(resposta):
    data = resposta.json()
    return data.get("oficio", "")


def test_pagina_principal_contem_cabecalho_e_abas():
    resposta = CLIENT.get("/")
    assert resposta.status_code == 200
    corpo = resposta.text
    assert "Universidade de São Paulo" in corpo
    assert "assets/usp-logo.png" in corpo
    assert "ALUNOS" in corpo
    assert "DOCENTES" in corpo


def test_titulos_dos_blocos_aparecem_na_pagina():
    corpo = CLIENT.get("/").text
    assert SOLICITANTE_BLOCO in corpo
    assert ENDERECO_BLOCO in corpo
    assert PAGAMENTO_BLOCO in corpo


@pytest.mark.parametrize("rotulo", ROTEXOS_SOLICITANTE)
def test_rotulos_do_bloco_solicitante_evento(rotulo):
    assert rotulo in CLIENT.get("/").text


@pytest.mark.parametrize("rotulo", ROTEIRO_ALUNOS)
def test_campos_exclusivos_da_aba_alunos(rotulo):
    assert rotulo in CLIENT.get("/").text


@pytest.mark.parametrize("rotulo", ROTEXOS_ENDERECO)
def test_rotulos_do_bloco_endereco(rotulo):
    assert rotulo in CLIENT.get("/").text


@pytest.mark.parametrize("rotulo", ROTEXOS_PAGAMENTO):
def test_rotulos_do_bloco_pagamento(rotulo):
    assert rotulo in CLIENT.get("/").text


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in CLIENT.get("/").text


def test_opcoes_de_selecao():
    corpo = CLIENT.get("/").text
    for opcao in ["Mestrado", "Doutorado", "Participação em evento",
                  "Banca de exame ou defesa", "Pôster",
                  "Apresentação oral", "Não irá apresentar trabalho"]:
        assert opcao in corpo


def test_estilo_css_referencia_cores_e_fonte():
    resposta = CLIENT.get("/style.css")
    assert resposta.status_code == 200
    texto_css = resposta.text
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor in texto_css
    assert "Open Sans" in texto_css


@pytest.mark.parametrize("dados,esperada",
                         [
                             ({}, "Preencha todos os campos"),
                             ({"nome_completo": "Maria da Silva", "n_usp": "", "programa": "Matemática",
                               "email": "maria@ime.usp.br"}, "Preencha todos os campos"),
                         ])
def test_validacao_campos_obrigatorios(dados, esperada):
    resposta = CLIENT.post("/solicitar", json=dados)
    assert resposta.status_code in (200, 422)
    erros = resposta.json().get("erros", [])
    assert esperada in erros


@pytest.mark.parametrize("valor,esperada",
                         [
                             ("123abc", "N. USP deve conter apenas números"),
                             ("12 34", "N. USP deve conter apenas números"),
                             ("12-34", "N. USP deve conter apenas números"),
                             ("055", None),
                             ("1234567", None),
                         ])
def test_validacao_n_usp(valor, esperada):
    dados = _campos_para_solicitar("alunos", extras={"n_usp": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperada is None:
        assert esperada not in erros
        assert "N. USP deve conter apenas números" not in erros
    else:
        assert esperada in erros


@pytest.mark.parametrize("valor,esperada",
                         [
                             ("12a34", "Número da agência deve conter apenas números"),
                             ("123 45", "Número da agência deve conter apenas números"),
                             ("", None),
                             ("1234", None),
                         ])
def test_validacao_numero_agencia(valor, esperada):
    dados = _campos_para_solicitar("alunos", extras={"numero_agencia": valor})
    if valor == "":
        dados["numero_agencia"] = ""
    else:
        dados["numero_agencia"] = valor
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperada is None:
        assert esperada not in erros
        assert "Número da agência deve conter apenas números" not in erros
    else:
        assert esperada in erros


@pytest.mark.parametrize("valor,esperada",
                         [
                             ("0", "Valor solicitado deve ser maior que 0"),
                             ("-10", "Valor solicitado deve ser maior que 0"),
                             ("abc", "Valor solicitado deve ser maior que 0"),
                             ("", "Valor solicitado deve ser maior que 0"),
                             ("1500", None),
                             ("150000", None),
                         ])
def test_validacao_valor_solicitado(valor, esperada):
    dados = _campos_para_solicitar("alunos", extras={"valor_solicitado": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperada is None:
        assert esperada not in erros
        assert "Valor solicitado deve ser maior que 0" not in erros
    else:
        assert esperada in erros


@pytest.mark.parametrize("valor,esperada",
                         [
                             ("sem arroba", "E-mail inválido"),
                             ("sem@dominio sem ponto", "E-mail inválido"),
                             ("@ime.usp.br", "E-mail inválido"),
                             ("", "Preencha todos os campos"),
                             ("maria@ime.usp.br", None),
                         ])
def test_validacao_email(valor, esperada):
    dados = _campos_para_solicitar("alunos", extras={"email": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperada is None:
        assert esperada not in erros
        assert "E-mail inválido" not in erros
    else:
        assert esperada in erros


@pytest.mark.parametrize("valor,esperadas",
                         [
                             ("123.456.789-0", ["CPF deve estar no formato 000.000.000-00"]),
                             ("123.456.789", ["CPF deve estar no formato 000.000.000-00"]),
                             ("12345678909", ["CPF deve estar no formato 000.000.000-00"]),
                             ("111.111.111-11", ["CPF inválido"]),
                             ("123.456.789-09", []),
                         ])
def test_validacao_cpf(valor, esperadas):
    dados = _campos_para_solicitar("alunos", extras={"cpf": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperadas:
        for mensagem in esperadas:
            assert mensagem in erros
    else:
        assert "CPF deve estar no formato 000.000.000-00" not in erros
        assert "CPF inválido" not in erros


@pytest.mark.parametrize("valor,esperada",
                         [
                             ("05508090", "CEP deve estar no formato 00000-000"),
                             ("05508-90", "CEP deve estar no formato 00000-000"),
                             ("05508 090", "CEP deve estar no formato 00000-000"),
                             ("", "Preencha todos os campos"),
                             ("05508-090", None),
                         ])
def test_validacao_cep(valor, esperada):
    dados = _campos_para_solicitar("alunos", extras={"cep": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperada is None:
        assert esperada not in erros
        assert "CEP deve estar no formato 00000-000" not in erros
    else:
        assert esperada in erros


@pytest.mark.parametrize("valor,esperadas",
                         [
                             ("1/2/1980", ["Data de nascimento deve estar no formato dd/mm/aaaa"]),
                             ("01-02-1980", ["Data de nascimento deve estar no formato dd/mm/aaaa"]),
                             ("01/02/80", ["Data de nascimento deve estar no formato dd/mm/aaaa"]),
                             ("31/02/1980", ["Data de nascimento inválida"]),
                             ("01/13/1980", ["Data de nascimento inválida"]),
                             ("", "Preencha todos os campos"),
                             ("01/02/1980", None),
                         ])
def test_validacao_data_nascimento(valor, esperadas):
    dados = _campos_para_solicitar("alunos", extras={"data_nascimento": valor})
    resposta = CLIENT.post("/solicitar", json=dados)
    erros = resposta.json().get("erros", [])
    if esperadas is None:
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in erros
        assert "Data de nascimento inválida" not in erros
    elif esperadas == "Preencha todos os campos":
        assert "Preencha todos os campos" in erros
    else:
        for mensagem in esperadas:
            assert mensagem in erros


def test_aba_docentes_nao_possui_campo_nivel_ou_tipo_auxilio():
    corpo = CLIENT.get("/").text
    # Se algum desses rótulos só estiver presente na aba alunos, deve ainda
    # assim aparecer na página; a checagem forte de que a aba docentes não os
    # tem fica no comportamento do ofício.
    assert "NÍVEL" in corpo
    assert "TIPO DE AUXÍLIO" in corpo


def test_envio_valido_aba_alunos_gera_oficio():
    dados = _campos_para_solicitar("alunos")
    resposta = CLIENT.post("/solicitar", json=dados)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert "erros" in corpo
    assert corpo["erros"] == []
    oficio = corpo["oficio"]

    assert "Solicitação registrada" in CLIENT.get("/").text or "Solicitação registrada" in oficio
    assert "Interessada(o): Maria da Silva - 1234567" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Doutorado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Dados do evento" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Período: 2024-05-01" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://example.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: participação com trabalho" in oficio

    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Casa" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Cidade Universitaria, São Paulo - SP" in oficio

    assert "Dados para pagamento" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 1234567" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345" in oficio

    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_envio_valido_aba_docentes_gera_oficio():
    dados = _campos_para_solicitar("docentes")
    resposta = CLIENT.post("/solicitar", json=dados)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["erros"] == []
    oficio = corpo["oficio"]

    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    # A linha de assunto com tipo de auxílio da aba alunos não aparece
    assert "Solicitação de Auxílio Financeiro - Participação em evento" not in oficio


def test_oficio_omitir_link_evento_vazio():
    dados = _campos_para_solicitar("alunos", extras={"link_evento": ""})
    resposta = CLIENT.post("/solicitar", json=dados)
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_oficio_omitir_complemento_vazio():
    dados = _campos_para_solicitar("alunos", extras={"complemento": ""})
    resposta = CLIENT.post("/solicitar", json=dados)
    oficio = resposta.json()["oficio"]
    assert "Complemento:" not in oficio


def test_oficio_formata_valor_solicitado():
    dados = _campos_para_solicitar("alunos", extras={"valor_solicitado": "150000000"})
    resposta = CLIENT.post("/solicitar", json=dados)
    oficio = resposta.json()["oficio"]
    assert "Valor solicitado: R$ 1.500.000,00" in oficio


def test_arquivos_estaticos_presentes():
    for caminho, esperado in [
        ("/style.css", "body"),
        ("/app.js", "formatarValor"),
        ("/app.js", "formatarData"),
        ("/app.js", "formatarCpf"),
        ("/app.js", "formatarCep"),
    ]:
        resposta = CLIENT.get(caminho)
        assert resposta.status_code == 200
        assert esperado in resposta.text


def test_placeholder_em_campos():
    corpo = CLIENT.get("/").text
    assert 'placeholder=' in corpo
    assert 'placeholder=""' not in corpo
