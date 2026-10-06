import re
from html.parser import HTMLParser
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.labels = []
        self.in_label = False
        self.current_label = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input":
            self.inputs.append(attrs)
        elif tag == "label":
            self.in_label = True
            self.current_label = ""

    def handle_endtag(self, tag):
        if tag == "label":
            self.in_label = False
            self.labels.append(self.current_label.strip())

    def handle_data(self, data):
        if self.in_label:
            self.current_label += data


def test_index_has_tabs():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_form_labels():
    response = client.get("/")
    html = response.text
    labels = [
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
    for label in labels:
        assert label in html, f"Label '{label}' not found"


def test_alunos_specific_fields():
    response = client.get("/")
    html = response.text
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html


def test_css_colors():
    response = client.get("/style.css")
    assert response.status_code == 200
    css = response.text
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_app_js_exists():
    response = client.get("/app.js")
    assert response.status_code == 200
    assert len(response.text) > 0


def test_inputs_have_placeholders():
    response = client.get("/")
    parser = FormParser()
    parser.feed(response.text)
    for inp in parser.inputs:
        if inp.get("type") in ("text", "number", "email", None):
            assert "placeholder" in inp, f"Input missing placeholder: {inp}"
            assert inp["placeholder"] != "", "Placeholder empty"
