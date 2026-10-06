import json
import re
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _payload(**overrides):
    """Dados validos de um aluno; campos opcionais por padrao preenchidos."""
    data = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional",
        "periodo": "10 a 12 de julho",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "http://exemplo.com",
        "valor": "1.500,00",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    data.update(overrides)
    return data


def _enviar(payload):
    return client.post("/solicitacao", data=payload)


def test_index_existe_e_serva_estaticos():
    r = client.get("/")
    assert r.status_code == 200
    assert "USP" in r.text or "usp-logo" in r.text
    assert "index" in r.headers.get("content-type", "").lower() or "text/html" in r.headers.get("content-type", "").lower()


def test_titulo_da_pagina():
    r = client.get("/")
    assert "<title>" in r.text


def test_estaticos_existem():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/assets/usp-logo.png").status_code == 200


def test_pagina_tem_abas_alunos_e_docentes():
    r = client.get("/")
    assert "ALUNOS" in r.text
    assert "DOCENTES" in r.text
    assert r.text.index("ALUNOS") < r.text.index("DOCENTES")


def test_pagina_tem_blocos():
    r = client.get("/")
    assert "SOLICITANTE E EVENTO" in r.text
    assert "ENDEREÇO DO SOLICITANTE" in r.text
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in r.text


def test_envio_valido_alunos_retorna_ok():
    r = _enviar(_payload())
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_campos_obrigatorios_vazios():
    data = _payload(nome_completo="", programa="", email="")
    r = _enviar(data)
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert "Preencha todos os campos" in r.json()["erros"]


def test_n_usp_nao_numerico():
    r = _enviar(_payload(n_usp="12a456"))
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_nao_numerica():
    r = _enviar(_payload(agencia="12-x"))
    assert "Número da agência deve conter apenas números" in r.json()["erros"]


def test_valor_zero_ou_invalido():
    r = _enviar(_payload(valor="0,00"))
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido():
    r = _enviar(_payload(email="maria-sem-arroba"))
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_formato_errado():
    r = _enviar(_payload(cpf="12345678909"))
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cep_formato_errado():
    r = _enviar(_payload(cep="05508 090"))
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_nascimento_formato_errado():
    r = _enviar(_payload(data_nascimento="1980-02-01"))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]


def test_cpf_digitos_verificadores_errados():
    r = _enviar(_payload(cpf="123.456.789-00"))
    assert "CPF inválido" in r.json()["erros"]


def test_data_nascimento_inexistente():
    r = _enviar(_payload(data_nascimento="31/02/1980"))
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_erros_multiplos_devem_aparecer_todos():
    data = _payload(n_usp="abc", email="x")
    erros = _enviar(data).json()["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros


def test_campos_opcionais_vazios_ok():
    r = _enviar(_payload(link="", complemento=""))
    assert r.json()["ok"] is True


def test_oficio_alunos():
    r = _enviar(_payload())
    oficio = r.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso Nacional" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio


def test_oficio_docentes():
    data = _payload(aba="docentes")
    data.pop("nivel"); data.pop("tipo_auxilio")
    r = _enviar(data)
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio


def test_oficio_omitir_campos_opcionais_vazios():
    r = _enviar(_payload(link="", complemento=""))
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_tem_estrutura_esperada():
    r = _enviar(_payload())
    oficio = r.json()["oficio"]
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Dados do evento" in oficio
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Dados para pagamento" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Período: 10 a 12 de julho" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
