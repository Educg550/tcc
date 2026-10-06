"""Backend: validação e resposta com o ofício.

A decisão sobre validade é do backend; o frontend só mostra a resposta.
"""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


ALUNO_OK = {
    "tipo": "alunos",
    "nome": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "Congresso de Álgebra",
    "periodo": "10 a 12 de outubro de 2025",
    "cidade": "São Paulo",
    "estado": "SP",
    "pais": "Brasil",
    "link": "https://exemplo.com",
    "valor": "R$ 1.500,00",
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


def post(payload):
    return client.post("/solicitacao", json=payload)


def test_caminho_de_solicitacao_existe():
    r = post(ALUNO_OK)
    assert r.status_code == 200, r.text


def test_resposta_traz_ok_e_oficio_para_aluno():
    r = post(ALUNO_OK)
    body = r.json()
    assert body.get("ok") is True
    oficio = body.get("oficio")
    assert oficio
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio


def test_oficio_aluno_bloco_evento():
    oficio = post(ALUNO_OK).json()["oficio"]
    assert "Dados do evento" in oficio
    assert "Evento: Congresso de Álgebra" in oficio
    assert "Período: 10 a 12 de outubro de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio


def test_oficio_aluno_endereco():
    oficio = post(ALUNO_OK).json()["oficio"]
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio


def test_oficio_aluno_pagamento():
    oficio = post(ALUNO_OK).json()["oficio"]
    assert "Dados para pagamento" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio


def test_oficio_frase_final():
    oficio = post(ALUNO_OK).json()["oficio"]
    assert oficio.strip().endswith("Encaminhe-se ao Serviço Financeiro para providências.")


def test_oficio_docente():
    docente = dict(ALUNO_OK)
    docente.update({"tipo": "docentes", "complemento": "Sala 12"})
    oficio = post(docente).json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert re.search(r"Programa: Matemática\s*$", oficio, re.M)
    assert "Complemento: Sala 12" in oficio


def test_oficio_sem_link_e_sem_complemento():
    dados = dict(ALUNO_OK)
    dados["link"] = ""
    dados["complemento"] = ""
    oficio = post(dados).json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_linha_com_link_quando_preenchido():
    dados = dict(ALUNO_OK)
    dados["complemento"] = "Bloco B"
    oficio = post(dados).json()["oficio"]
    assert "Complemento: Bloco B" in oficio


def test_valor_formatado_no_oficio_para_varias_ordens():
    for valor_enviado, esperado in (
        ("R$ 15,00", "R$ 15,00"),
        ("R$ 1.500,00", "R$ 1.500,00"),
        ("R$ 1.500.000,00", "R$ 1.500.000,00"),
    ):
        dados = dict(ALUNO_OK, valor=valor_enviado)
        oficio = post(dados).json()["oficio"]
        assert f"Valor solicitado: {esperado}" in oficio


def test_erro_campo_obrigatorio_vazio():
    for campo in (
        "nome",
        "n_usp",
        "programa",
        "email",
        "evento",
        "periodo",
        "cidade",
        "estado",
        "pais",
        "valor",
        "detalhamento",
        "apresentacao",
        "data_nascimento",
        "logradouro",
        "numero",
        "bairro",
        "cep",
        "cidade_end",
        "estado_end",
        "cpf",
        "rg",
        "banco",
        "agencia",
        "conta",
    ):
        dados = dict(ALUNO_OK)
        dados[campo] = ""
        body = post(dados).json()
        assert body.get("ok") is False
        erros = body.get("erros") or body.get("mensagens") or body.get("messages")
        assert erros, campo
        assert "Preencha todos os campos" in erros, campo


def test_erro_nivel_ou_tipo_vazio_para_aluno():
    for campo in ("nivel", "tipo_auxilio"):
        dados = dict(ALUNO_OK)
        dados[campo] = ""
        body = post(dados).json()
        assert "Preencha todos os campos" in _erros(body), campo


def _erros(body):
    return body.get("erros") or body.get("mensagens") or body.get("messages") or []


def test_erro_n_usp_nao_digitos():
    dados = dict(ALUNO_OK, n_usp="1234567a")
    erros = _erros(post(dados).json())
    assert "N. USP deve conter apenas números" in erros


def test_erro_agencia_nao_digitos():
    dados = dict(ALUNO_OK, agencia="12a4")
    erros = _erros(post(dados).json())
    assert "Número da agência deve conter apenas números" in erros


def test_erro_valor_zero():
    dados = dict(ALUNO_OK, valor="R$ 0,00")
    erros = _erros(post(dados).json())
    assert "Valor solicitado deve ser maior que 0" in erros


def test_erro_valor_nao_natural():
    dados = dict(ALUNO_OK, valor="abc")
    erros = _erros(post(dados).json())
    assert "Valor solicitado deve ser maior que 0" in erros


def test_erro_email_sem_arroba():
    dados = dict(ALUNO_OK, email="maria.ime.usp.br")
    erros = _erros(post(dados).json())
    assert "E-mail inválido" in erros


def test_erro_email_sem_dominio():
    dados = dict(ALUNO_OK, email="maria@")
    erros = _erros(post(dados).json())
    assert "E-mail inválido" in erros


def test_erro_cpf_formato_errado():
    dados = dict(ALUNO_OK, cpf="12.345.678-909")
    erros = _erros(post(dados).json())
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_erro_cpf_digitos_verificadores():
    dados = dict(ALUNO_OK, cpf="123.456.789-00")
    erros = _erros(post(dados).json())
    assert "CPF inválido" in erros


def test_erro_cep_formato():
    dados = dict(ALUNO_OK, cep="05508-0900")
    erros = _erros(post(dados).json())
    assert "CEP deve estar no formato 00000-000" in erros


def test_erro_data_formato():
    dados = dict(ALUNO_OK, data_nascimento="01021980")
    erros = _erros(post(dados).json())
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_erro_data_inexistente():
    dados = dict(ALUNO_OK, data_nascimento="31/02/1980")
    erros = _erros(post(dados).json())
    assert "Data de nascimento inválida" in erros


def test_erro_data_mes_fora():
    dados = dict(ALUNO_OK, data_nascimento="10/13/1980")
    erros = _erros(post(dados).json())
    assert "Data de nascimento inválida" in erros


def test_todos_os_erros_de_uma_vez():
    dados = dict(
        ALUNO_OK,
        email="sem-arroba",
        n_usp="12x",
        cpf="1",
        cep="1",
        data_nascimento="1",
        agencia="x",
        valor="R$ 0,00",
    )
    erros = _erros(post(dados).json())
    for msg in (
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert msg in erros, msg


def test_sem_oficio_quando_ha_erro():
    dados = dict(ALUNO_OK, email="errado")
    body = post(dados).json()
    assert body.get("ok") is False
    assert not body.get("oficio")


def test_docente_nao_exige_nivel_nem_tipo():
    docente = dict(ALUNO_OK, tipo="docentes")
    docente.pop("nivel")
    docente.pop("tipo_auxilio")
    body = post(docente).json()
    assert body.get("ok") is True, _erros(body)


def test_backupper_nao_persiste_nada():
    # sem banco, sem arquivo: a resposta carrega tudo que a tela precisa
    r = post(ALUNO_OK)
    assert r.status_code == 200
    body = r.json()
    assert set(body) <= {"ok", "oficio", "erros", "mensagens", "messages"}
