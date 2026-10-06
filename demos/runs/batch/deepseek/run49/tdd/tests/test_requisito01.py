import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture
def client():
    return TestClient(app.app)


ROOT = Path(__file__).resolve().parents[1]


def _valid_form(nivel="Mestrado", tipo="Participação em evento"):
    return {
        "nome_completo": "Maria Silva Santos",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": nivel,
        "tipo_auxilio": tipo,
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Computação",
        "periodo": "10/10/2024 a 12/10/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://evento.example.com",
        "valor": "150000",
        "detalhamento": "Participação em evento internacional.",
        "apresentacao": "Pôster",
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
    }


# --- frontend estático -------------------------------------------------------


def test_index_contem_abas_e_rotulos():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    for bloco in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert bloco in html


def test_index_contem_campos_texto_exatos():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
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
        assert rotulo in html, rotulo


def test_index_tem_botao_enviar_solicitacao():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "Enviar solicitação" in html


def test_index_referencia_logo_usp():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_css_nao_referencia_brasao():
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    assert "brasao" not in css.lower()
    assert "escudo" not in css.lower()


def test_css_usa_cores_da_universidade():
    css = (ROOT / "style.css").read_text(encoding="utf-8").lower()
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor in css, cor


def test_assets_contem_logo():
    assert (ROOT / "assets" / "usp-logo.png").exists()


# --- backend: validação ------------------------------------------------------


@pytest.mark.parametrize("campo", ["nome_completo", "n_usp", "programa", "email", "evento", "valor"])
def test_obrigatorio_vazio_retorna_preencha_todos_os_campos(client, campo):
    dados = _valid_form()
    dados[campo] = ""
    resp = client.post("/solicitacao", json=dados)
    assert resp.status_code == 200
    corpo = resp.json()
    erros = corpo.get("erros", [])
    assert "Preencha todos os campos" in erros


def test_n_usp_nao_numerico(client):
    dados = _valid_form()
    dados["n_usp"] = "12a34"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "N. USP deve conter apenas números" in erros


def test_agencia_nao_numerica(client):
    dados = _valid_form()
    dados["agencia"] = "12a4"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "Número da agência deve conter apenas números" in erros


def test_valor_zero(client):
    dados = _valid_form()
    dados["valor"] = "000"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_invalido(client):
    dados = _valid_form()
    dados["email"] = "maria-ime.usp.br"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "E-mail inválido" in erros


def test_cpf_fora_de_formato(client):
    dados = _valid_form()
    dados["cpf"] = "12345678909"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cep_fora_de_formato(client):
    dados = _valid_form()
    dados["cep"] = "05508090"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_nascimento_fora_de_formato(client):
    dados = _valid_form()
    dados["data_nascimento"] = "1980-02-01"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_cpf_digito_verificador_invalido(client):
    dados = _valid_form()
    dados["cpf"] = "123.456.789-00"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "CPF inválido" in erros


def test_data_nascimento_inexistente(client):
    dados = _valid_form()
    dados["data_nascimento"] = "30/02/1980"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    assert "Data de nascimento inválida" in erros


def test_erros_retornam_todas_as_mensagens(client):
    dados = _valid_form()
    dados["nome_completo"] = ""
    dados["n_usp"] = "abc"
    dados["agencia"] = "xy"
    dados["valor"] = "0"
    dados["email"] = "sem-arroba"
    dados["cpf"] = "111"
    dados["cep"] = "123"
    dados["data_nascimento"] = "31/13/1980"
    erros = client.post("/solicitacao", json=dados).json()["erros"]
    for esperado in [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
    ]:
        assert esperado in erros, (esperado, erros)
    assert erros.count("Preencha todos os campos") == 1


# --- backend: geração do ofício ---------------------------------------------


def test_solicitacao_valida_retorna_oficio(client):
    dados = _valid_form()
    resp = client.post("/solicitacao", json=dados)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo.get("erros", []) == []
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria Silva Santos - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "Evento: Congresso de Computação" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: http://evento.example.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Participação em evento internacional." in oficio
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


def test_sem_link_e_sem_complemento_remove_linhas(client):
    dados = _valid_form()
    dados["link_evento"] = ""
    dados["complemento"] = ""
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento:" not in oficio


def test_docente_assunto_e_programa_sem_nivel(client):
    dados = _valid_form()
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert " - Mestrado" not in oficio


def test_endpoint_correto_ignora_campos_de_nivel_no_docente(client):
    dados = _valid_form()
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    resp = client.post("/solicitacao", json=dados)
    assert resp.status_code == 200
    assert resp.json().get("erros", []) == []
