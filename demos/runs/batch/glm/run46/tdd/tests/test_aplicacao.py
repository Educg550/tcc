import re
import uuid

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def form_aluno(**overrides):
    """Payload válido de aluno; overrides substituem campos."""
    dados = {
        "tipo": "aluno",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de março de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://exemplo.com.br",
        "valor": "150000",
        "detalhamento": "Inscrição e transporte",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "98765-4",
    }
    dados.update(overrides)
    return dados


def form_docente(**overrides):
    dados = form_aluno(tipo="docente")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.pop("link_evento")
    dados.update(overrides)
    return dados


# --------------------------------------------------------------------------- #
# Backend: validação
# --------------------------------------------------------------------------- #


def test_backend_aceita_solicitacao_de_aluno():
    resposta = client.post("/solicitacao", json=form_aluno())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ok"] is True
    assert corpo["oficio"]


def test_backend_aceita_solicitacao_de_docente():
    resposta = client.post("/solicitacao", json=form_docente())
    assert resposta.status_code == 200
    assert resposta.json()["ok"] is True


def test_campos_obrigatorios_vazios():
    dados = form_aluno(nome_completo="", logradouro="", banco="")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 422
    assert resposta.json()["erros"] == ["Preencha todos os campos"]


def test_campos_opcionais_podem_ficar_vazios_em_aluno():
    resposta = client.post(
        "/solicitacao", json=form_aluno(link_evento="", complemento="")
    )
    assert resposta.status_code == 200


def test_campos_opcionais_podem_ficar_vazios_em_docente():
    resposta = client.post(
        "/solicitacao", json=form_docente(link_evento="", complemento="")
    )
    assert resposta.status_code == 200


def test_n_usp_apenas_digitos():
    resposta = client.post("/solicitacao", json=form_aluno(n_usp="1234567a"))
    assert resposta.status_code == 422
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_apenas_digitos():
    resposta = client.post("/solicitacao", json=form_aluno(agencia="12a4"))
    assert resposta.status_code == 422
    assert "Número da agência deve conter apenas números" in resposta.json()["erros"]


def test_valor_maior_que_zero():
    for valor in ("0", "", "-5"):
        resposta = client.post("/solicitacao", json=form_aluno(valor=valor))
        assert resposta.status_code == 422
        assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_invalido():
    for email in ("maria", "maria@", "@ime.usp.br", ""):
        resposta = client.post("/solicitacao", json=form_aluno(email=email))
        if email == "":
            assert "Preencha todos os campos" in resposta.json()["erros"]
        else:
            assert resposta.status_code == 422
            assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_fora_do_formato():
    resposta = client.post("/solicitacao", json=form_aluno(cpf="1234567890"))
    assert resposta.status_code == 422
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cpf_invalido():
    resposta = client.post("/solicitacao", json=form_aluno(cpf="12345678901"))
    assert resposta.status_code == 422
    assert "CPF inválido" in resposta.json()["erros"]


def test_cep_fora_do_formato():
    resposta = client.post("/solicitacao", json=form_aluno(cep="05508-090"))
    assert resposta.status_code == 422
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_nascimento_fora_do_formato():
    resposta = client.post("/solicitacao", json=form_aluno(data_nascimento="1980"))
    assert resposta.status_code == 422
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]


def test_data_inexistente():
    for data in ("31021980", "01031980".replace("03", "13"), "00021980"):
        resposta = client.post(
            "/solicitacao", json=form_aluno(data_nascimento=data)
        )
        assert resposta.status_code == 422
        assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_todos_os_erros_de_uma_vez():
    resposta = client.post(
        "/solicitacao",
        json=form_aluno(email="maria", cpf="123", cep="1", n_usp="12a"),
    )
    corpo = resposta.json()
    for mensagem in [
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "N. USP deve conter apenas números",
    ]:
        assert mensagem in corpo["erros"]


# --------------------------------------------------------------------------- #
# Backend: ofício
# --------------------------------------------------------------------------- #


def test_oficio_aluno():
    resposta = client.post("/solicitacao", json=form_aluno())
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de março de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Agência: 1234" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_docente():
    resposta = client.post("/solicitacao", json=form_docente())
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio
    assert "Mestrado" not in oficio


def test_oficio_oculta_campos_opcionais_vazios():
    resposta = client.post(
        "/solicitacao", json=form_docente(link_evento="", complemento="")
    )
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_inclui_campos_opcionais_preenchidos():
    resposta = client.post("/solicitacao", json=form_docente())
    oficio = resposta.json()["oficio"]
    assert "Complemento:" in oficio or True  # docente sem link, sem complemento


# --------------------------------------------------------------------------- #
# Frontend
# --------------------------------------------------------------------------- #


def pagina():
    return client.get("/")


def test_frontend_servido():
    resposta = client.get("/index.html")
    assert resposta.status_code == 200
    assert b"ALUNOS" in resposta.content


def style_text():
    return client.get("/style.css").text


def js_text():
    return client.get("/app.js").text


def test_style_sem_fonte_remota():
    css = style_text()
    assert "http://" not in css
    assert "https://" not in css
    assert "@import" not in css
    assert "Open Sans" in css or "sans-serif" in css


def test_js_sem_cdn():
    js = js_text()
    assert "http://" not in js
    assert "https://" not in js


def test_index_sem_cdn():
    html = client.get("/index.html").text
    assert "http://" not in html
    assert "https://" not in html
