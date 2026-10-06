import json
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[1]

ERROS = {
    "vazio": "Preencha todos os campos",
    "nusp": "N. USP deve conter apenas números",
    "agencia": "Número da agência deve conter apenas números",
    "valor": "Valor solicitado deve ser maior que 0",
    "email": "E-mail inválido",
    "cpf_fmt": "CPF deve estar no formato 000.000.000-00",
    "cep": "CEP deve estar no formato 00000-000",
    "data_fmt": "Data de nascimento deve estar no formato dd/mm/aaaa",
    "cpf_inv": "CPF inválido",
    "data_inv": "Data de nascimento inválida",
}


def cpf_valido():
    nove = "123456789"
    d1 = (sum(int(n) * (10 - i) for i, n in enumerate(nove)) * 10) % 11 % 10
    d2 = (sum(int(n) * (11 - i) for i, n in enumerate(nove + str(d1))) * 10) % 11 % 10
    return f"{nove}{d1}{d2}"


CPF_OK = cpf_valido()


def base_alunos(**extra):
    dados = {
        "aba": "alunos",
        "nome_completo": "Fulana de Tal",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulana@ime.usp.br",
        "nome_evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://exemplo.com.br",
        "valor_solicitado": 150000,
        "detalhamento": "Inscrição e passagem aérea.",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": CPF_OK,
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(extra)
    return {k: v for k, v in dados.items() if v is not None}


def base_docentes(**extra):
    dados = base_alunos(
        aba="docentes",
        nivel=None,
        tipo_auxilio=None,
        n_usp="12345678",
        email="docente@ime.usp.br",
    )
    return dados


@pytest.fixture()
def cliente():
    sys.path.insert(0, str(RAIZ))
    import app

    return TestClient(app.app)


def post(cliente, dados):
    return cliente.post("/api/solicitar", data=dados)


def limpa(dados, *chaves):
    return {k: v for k, v in dados.items() if k not in chaves}


# ------------------------------ Página ------------------------------


def test_pagina_existe(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200


def test_pagina_tem_abas_e_blocos(cliente):
    pagina = cliente.get("/").text
    for rotulo in ("ALUNOS", "DOCENTES", "SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", "Enviar solicitação"):
        assert rotulo in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")


# ------------------------------ Formatação do valor ------------------------------


def test_valor_em_centavos_para_moeda(cliente):
    resposta = cliente.post("/api/formatar", json={"campo": "valor_solicitado", "valor": "150000"})
    assert resposta.json() == "R$ 1.500,00"


# ------------------------------ Validação: campo vazio ------------------------------


def test_campo_obrigatorio_vazio(cliente):
    dados = base_alunos(email="")
    resposta = post(cliente, dados)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("oficio") is None
    mensagens = corpo.get("erros", [])
    assert ERROS["vazio"] in mensagens
    assert ERROS["email"] not in mensagens


def test_campos_opcionais_podem_ficar_vazios(cliente):
    dados = base_alunos()
    dados.pop("complemento", None)
    dados.pop("link_evento", None)
    resposta = post(cliente, dados)
    corpo = resposta.json()
    assert corpo.get("erros") == []
    assert "Link do evento:" not in (corpo.get("oficio") or "")
    assert "Complemento:" not in (corpo.get("oficio") or "")


@pytest.mark.parametrize("campo", [
    "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao", "data_nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
])
def test_todos_os_campos_obrigatorios_alunos(cliente, campo):
    dados = base_alunos()
    dados.pop(campo, None)
    corpo = post(cliente, dados).json()
    assert ERROS["vazio"] in corpo["erros"]


# ------------------------------ Validação: formatos ------------------------------


@pytest.mark.parametrize("nusp", ["12a45678", "1234 5678", "12.345678"])
def test_n_usp_so_digitos(cliente, nusp):
    corpo = post(cliente, base_alunos(n_usp=nusp)).json()
    assert ERROS["nusp"] in corpo["erros"]


def test_n_usp_sozinho_nao_dispara_vazio(cliente):
    corpo = post(cliente, base_alunos(n_usp="12a3")).json()
    assert ERROS["vazio"] not in corpo["erros"]


@pytest.mark.parametrize("agencia", ["123a", "12.34", "123 4"])
def test_agencia_so_digitos(cliente, agencia):
    corpo = post(cliente, base_alunos(agencia=agencia)).json()
    assert ERROS["agencia"] in corpo["erros"]


@pytest.mark.parametrize("valor,erro", [
    (0, "valor"),
    ("-10", "valor"),
    ("abc", "valor"),
    ("12.5", "valor"),
])
def test_valor_invalido(cliente, valor, erro):
    corpo = post(cliente, base_alunos(valor_solicitado=valor)).json()
    assert ERROS[erro] in corpo["erros"]


def test_valor_inteiro_maior_que_zero_aceito(cliente):
    corpo = post(cliente, base_alunos(valor_solicitado=1)).json()
    assert ERROS["valor"] not in corpo["erros"]


@pytest.mark.parametrize("email", ["fulana.ime.usp.br", "fulana@", "@ime.usp.br", "a@b"])
def test_email_invalido(cliente, email):
    corpo = post(cliente, base_alunos(email=email)).json()
    assert ERROS["email"] in corpo["erros"]


def test_email_invalido_nao_dispara_vazio(cliente):
    corpo = post(cliente, base_alunos(email="a@b")).json()
    assert ERROS["vazio"] not in corpo["erros"]


@pytest.mark.parametrize("cpf", ["1234567890", "123.456.7890-9", "123456789099", "12345678-90"])
def test_cpf_fora_do_formato(cliente, cpf):
    corpo = post(cliente, base_alunos(cpf=cpf)).json()
    assert ERROS["cpf_fmt"] in corpo["erros"]


@pytest.mark.parametrize("cpf", [
    "123.456.789-00",
    "111.111.111-11",
    "123.456.789-98",
])
def test_cpf_formato_certo_digitos_errados(cliente, cpf):
    corpo = post(cliente, base_alunos(cpf=cpf)).json()
    assert ERROS["cpf_inv"] in corpo["erros"]
    assert ERROS["cpf_fmt"] not in corpo["erros"]


def test_cpf_valido_aceito(cliente):
    corpo = post(cliente, base_alunos(cpf=CPF_OK)).json()
    for erro in (ERROS["cpf_fmt"], ERROS["cpf_inv"]):
        assert erro not in corpo["erros"]


@pytest.mark.parametrize("cep", ["05508090", "05508-0900", "0550-090", "ab508-090"])
def test_cep_fora_do_formato(cliente, cep):
    corpo = post(cliente, base_alunos(cep=cep)).json()
    assert ERROS["cep"] in corpo["erros"]


@pytest.mark.parametrize("data,esperado", [
    ("01021980", "data_fmt"),
    ("1980-02-01", "data_fmt"),
    ("1/2/1980", "data_fmt"),
    ("32/02/1980", "data_inv"),
    ("01/13/1980", "data_inv"),
    ("31/04/1980", "data_inv"),
    ("29/02/1981", "data_inv"),
])
def test_data_nascimento_invalida(cliente, data, esperado):
    corpo = post(cliente, base_alunos(data_nascimento=data)).json()
    assert ERROS[esperado] in corpo["erros"]
    outro = "data_inv" if esperado == "data_fmt" else "data_fmt"
    assert ERROS[outro] not in corpo["erros"]


def test_data_29_de_fevereiro_bissexto_aceita(cliente):
    corpo = post(cliente, base_alunos(data_nascimento="29/02/1980")).json()
    assert ERROS["data_fmt"] not in corpo["erros"]
    assert ERROS["data_inv"] not in corpo["erros"]


# ------------------------------ Vários erros de uma vez ------------------------------


def test_todos_os_erros_de_uma_vez(cliente):
    dados = {
        "aba": "alunos",
        "nome_completo": "Fulana de Tal",
        "n_usp": "12a3",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulana",
        "nome_evento": "Congresso",
        "periodo": "outubro",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "valor_solicitado": 0,
        "detalhamento": "Inscrição.",
        "apresentacao": "Pôster",
        "data_nascimento": "32/13/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "1234567890",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "12a4",
        "conta": "56789-0",
    }
    corpo = post(cliente, dados).json()
    mensagens = corpo["erros"]
    for chave in ("nusp", "agencia", "valor", "email", "cpf_fmt", "cep", "data_fmt"):
        assert ERROS[chave] in mensagens
    assert corpo.get("oficio") is None


def test_mensagem_de_vazio_aparece_uma_vez(cliente):
    dados = base_alunos(email="", nome_completo="")
    mensagens = post(cliente, dados).json()["erros"]
    assert mensagens.count(ERROS["vazio"]) == 1


# ------------------------------ Ofício: alunos ------------------------------


def test_oficio_alunos_completo(cliente):
    corpo = post(cliente, base_alunos()).json()
    oficio = corpo["oficio"]
    assert corpo["erros"] == []
    linhas = oficio.split("\n")
    assert linhas[0] == "Interessada(o): Fulana de Tal - 12345678"
    assert linhas[1] == "E-mail: fulana@ime.usp.br"
    assert linhas[2] == "Assunto: Solicitação de Auxílio Financeiro - Participação em evento"
    assert linhas[3] == "Programa: Matemática - Mestrado"
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de outubro de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com.br" in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e passagem aérea." in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert f"CPF: {CPF_OK[:3]}.{CPF_OK[3:6]}.{CPF_OK[6:9]}-{CPF_OK[9:]}" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_cabecalho_dois_blocos(cliente):
    linhas = post(cliente, base_alunos()).json()["oficio"].split("\n")
    assert "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a" in linhas
    assert "interessada(o) acima, conforme segue:" in linhas
    assert "Dados do evento" in linhas
    idx_dados = linhas.index("Dados do evento")
    assert "Endereço da(o) interessada(o)" in linhas
    idx_end = linhas.index("Endereço da(o) interessada(o)")
    assert "Dados para pagamento" in linhas
    idx_pag = linhas.index("Dados para pagamento")
    assert idx_dados < idx_end < idx_pag
    assert idx_end - idx_dados == 9
    assert idx_pag - idx_end == 7


@pytest.mark.parametrize("centavos,moeda", [
    (1500, "R$ 15,00"),
    (150000, "R$ 1.500,00"),
    (150000000, "R$ 1.500.000,00"),
    (5, "R$ 0,05"),
])
def test_valor_formatado_no_oficio(cliente, centavos, moeda):
    corpo = post(cliente, base_alunos(valor_solicitado=centavos)).json()
    assert f"Valor solicitado: {moeda}" in corpo["oficio"]


def test_oficio_alunos_linha_do_valor_esta_no_bloco_certo(cliente):
    linhas = post(cliente, base_alunos()).json()["oficio"].split("\n")
    idx_dados = linhas.index("Dados do evento")
    idx_valor = next(i for i, l in enumerate(linhas) if l.startswith("Valor solicitado:"))
    assert idx_dados < idx_valor < idx_dados + 9


# ------------------------------ Ofício: docentes ------------------------------


def test_oficio_docentes(cliente):
    corpo = post(cliente, base_docentes()).json()
    oficio = corpo["oficio"]
    assert corpo["erros"] == []
    linhas = oficio.split("\n")
    assert linhas[2] == "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
    assert linhas[3] == "Programa: Matemática"


def test_docentes_nao_requer_nivel_nem_tipo(cliente):
    dados = base_docentes()
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    corpo = post(cliente, dados).json()
    assert corpo["erros"] == []


# ------------------------------ Arquivos estáticos ------------------------------


def test_estaticos_existem(cliente):
    for nome in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        assert cliente.get(nome).status_code == 200


def test_arquivos_estao_na_raiz():
    for nome in ("index.html", "style.css", "app.js"):
        assert (RAIZ / nome).is_file()


@pytest.mark.parametrize("campo,rotulo", [
    ("VALOR SOLICITADO (R$)", "VALOR SOLICITADO"),
    ("CPF (SEPARADOS POR PONTOS E TRAÇO)", None),
    ("N. USP", None),
    ("DATA DE NASCIMENTO", None),
])
def test_rotulos_do_html(cliente, campo, rotulo):
    assert campo in cliente.get("/").text


def test_html_sem_fonte_remota(cliente):
    html = cliente.get("/").text
    assert "http://" not in html.replace("http://127.0.0.1", "")
    assert "https://" not in html
    assert "cdn" not in html.lower()
