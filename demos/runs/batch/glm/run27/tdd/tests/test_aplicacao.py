"""Testes da aplicação de auxílio financeiro da Pós-Graduação do IME-USP.

Todo teste usa apenas o cliente de teste síncrono do FastAPI e a
biblioteca padrão. O frontend é inspecionado como texto estático
(index.html, style.css, app.js) e como documento renderizado pelo
mesmo cliente, pois o servidor entrega esses arquivos.
"""

import json
import os
import re
from pathlib import Path

from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parent.parent


def cliente():
    os.chdir(RAIZ)
    from app import app
    return TestClient(app)


def texto(caminho):
    return (RAIZ / caminho).read_text(encoding="utf-8")


SOLICITACAO_ALUNO = {
    "perfil": "aluno",
    "nome_completo": "Fulana da Silva",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_de_auxilio": "Participação em evento",
    "email": "fulana@ime.usp.br",
    "nome_do_evento": "Congresso Nacional de Matemática",
    "periodo_do_evento": "10 a 14 de março de 2025",
    "cidade_do_evento": "São Paulo",
    "estado_do_evento": "SP",
    "pais_do_evento": "Brasil",
    "link_do_evento": "https://exemplo.com",
    "valor_solicitado": "150000",
    "detalhamento": "Inscrição no congresso.",
    "apresentacao": "Pôster",
    "data_de_nascimento": "01021980",
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


def solicitudes(**sobreposicoes):
    dados = dict(SOLICITACAO_ALUNO)
    dados.update(sobreposicoes)
    return dados


OFICIO_ALUNO = [
    "Interessada(o): Fulana da Silva - 12345678",
    "E-mail: fulana@ime.usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Matemática - Mestrado",
    "",
    "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
    "interessada(o) acima, conforme segue:",
    "",
    "Dados do evento",
    "Evento: Congresso Nacional de Matemática",
    "Período: 10 a 14 de março de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://exemplo.com",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição no congresso.",
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
    "Conta: 98765-4",
    "",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


class TestOficioAlunos:
    def test_oficio_completo(self):
        r = cliente().post("/enviar", data=SOLICITACAO_ALUNO)
        assert r.status_code == 200
        corpo = r.json()
        assert "oficio" in corpo
        linhas = corpo["oficio"].split("\n")
        assert linhas == OFICIO_ALUNO

    def test_campos_opcionais_vazios_omitem_linhas(self):
        r = cliente().post(
            "/enviar",
            data=solicitudes(link_do_evento="", complemento="Bloco A"),
        )
        linhas = r.json()["oficio"].split("\n")
        assert not any(l.startswith("Link do evento") for l in linhas)
        assert "Complemento: Bloco A" in linhas


class TestOficioDocentes:
    def test_oficio_sem_nivel_e_sem_tipo(self):
        dados = dict(SOLICITACAO_ALUNO)
        dados["perfil"] = "docente"
        r = cliente().post("/enviar", data=dados)
        assert r.status_code == 200
        linhas = r.json()["oficio"].split("\n")
        assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in linhas
        assert "Programa: Matemática" in linhas
        assert not any("Mestrado" in l for l in linhas)


class TestValidacao:
    def test_ok(self):
        r = cliente().post("/enviar", data=SOLICITACAO_ALUNO)
        assert r.status_code == 200
        assert "erros" not in r.json()

    def test_campo_obrigatorio_vazio(self):
        r = cliente().post("/enviar", data=solicitudes(nome_completo=""))
        assert r.status_code == 400
        assert "Preencha todos os campos" in r.json()["erros"]

    def test_n_usp_com_letras(self):
        r = cliente().post("/enviar", data=solicitudes(n_usp="12a45678"))
        assert r.status_code == 400
        assert "N. USP deve conter apenas números" in r.json()["erros"]

    def test_agencia_com_letras(self):
        r = cliente().post("/enviar", data=solicitudes(agencia="12a4"))
        assert r.status_code == 400
        assert "Número da agência deve conter apenas números" in r.json()["erros"]

    def test_valor_maior_que_zero(self):
        r = cliente().post("/enviar", data=solicitudes(valor_solicitado="0"))
        assert r.status_code == 400
        assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]

    def test_email_sem_arroba(self):
        r = cliente().post("/enviar", data=solicitudes(email="fulana ime.usp.br"))
        assert r.status_code == 400
        assert "E-mail inválido" in r.json()["erros"]

    def test_cpf_formato_errado(self):
        r = cliente().post("/enviar", data=solicitudes(cpf="1234567890"))
        assert r.status_code == 400
        assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]

    def test_cpf_invalido(self):
        r = cliente().post("/enviar", data=solicitudes(cpf="12345678900"))
        assert r.status_code == 400
        assert "CPF inválido" in r.json()["erros"]

    def test_cep_formato_errado(self):
        r = cliente().post("/enviar", data=solicitudes(cep="05508-09"))
        assert r.status_code == 400
        assert "CEP deve estar no formato 00000-000" in r.json()["erros"]

    def test_data_formato_errado(self):
        r = cliente().post("/enviar", data=solicitudes(data_de_nascimento="1/2/1980"))
        assert r.status_code == 400
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]

    def test_data_inexistente(self):
        r = cliente().post("/enviar", data=solicitudes(data_de_nascimento="31022000"))
        assert r.status_code == 400
        assert "Data de nascimento inválida" in r.json()["erros"]

    def test_multiplos_erros_de_uma_vez(self):
        r = cliente().post(
            "/enviar",
            data=solicitudes(n_usp="abc", email="sem.arroba"),
        )
        assert r.status_code == 400
        erros = r.json()["erros"]
        assert "N. USP deve conter apenas números" in erros
        assert "E-mail inválido" in erros


class TestFormatacaoDeCampos:
    def test_valor(self):
        r = cliente().post("/enviar", data=solicitudes(valor_solicitado="150000"))
        assert "R$ 1.500,00" in r.json()["oficio"]

    def test_cep(self):
        r = cliente().post("/enviar", data=solicitudes(cep="05508090"))
        assert "CEP: 05508-090" in r.json()["oficio"]

    def test_cpf(self):
        r = cliente().post("/enviar", data=solicitudes(cpf="12345678909"))
        assert "CPF: 123.456.789-09" in r.json()["oficio"]

    def test_data(self):
        r = cliente().post("/enviar", data=solicitudes(data_de_nascimento="01021980"))
        assert "Data de nascimento: 01/02/1980" in r.json()["oficio"]


class TestEstáticos:
    def test_index(self):
        r = cliente().get("/")
        assert r.status_code == 200

    def test_style(self):
        r = cliente().get("/style.css")
        assert r.status_code == 200

    def test_app_js(self):
        r = cliente().get("/app.js")
        assert r.status_code == 200

    def test_logo(self):
        r = cliente().get("/assets/usp-logo.png")
        assert r.status_code == 200


class TestFrontendEscritoAMao:
    def test_sem_cdn(self):
        html = texto("index.html")
        assert "http://" not in html and "https://" not in html
        js = texto("app.js")
        assert "http://" not in js and "https://" not in js
        css = texto("style.css")
        assert "http://" not in css and "https://" not in css
