"""Tests for Requirement 01: IME-USP Post-Graduation financial aid request form."""
import json
import re
import urllib.request

BASE_URL = "http://127.0.0.1:8123"

import pytest

# ── Helpers ─────────────────────────────────────────────────────────────────

def _html():
    resp = urllib.request.urlopen(BASE_URL + "/")
    return resp.read().decode("utf-8")


def _css():
    resp = urllib.request.urlopen(BASE_URL + "/style.css")
    return resp.read().decode("utf-8")


def _js():
    resp = urllib.request.urlopen(BASE_URL + "/app.js")
    return resp.read().decode("utf-8")


def _post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        resp = e
    text = resp.read().decode("utf-8")
    try:
        return resp.status, json.loads(text)
    except json.JSONDecodeError:
        return resp.status, text


_ALUNOS_BASE = {
    "nome": "Maria Silva",
    "nusp": "1234567",
    "programa": "Matematica",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participacao em evento",
    "email": "maria@ime.usp.br",
    "evento": "CMUC 2025",
    "periodo": "15/01/2025 - 20/01/2025",
    "cidade_evento": "Coimbra",
    "estado_evento": "Coimbra",
    "pais_evento": "Portugal",
    "link": "https://cmuc.org",
    "valor": "R$ 1.500,00",
    "detalhamento": "Apresentacao de artigo.",
    "apresentar": "Poster",
    "data_nasc": "01/02/1980",
    "logradouro": "Rua do Matrao",
    "numero": "101",
    "complemento": "Apto 5",
    "bairro": "Butanta",
    "cep": "05508-090",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

_DOCENTES_BASE = {
    "nome": "Carlos Santos",
    "nusp": "7654321",
    "programa": "Estatistica",
    "email": "carlos@ime.usp.br",
    "evento": "Seminario interno",
    "periodo": "01/02/2025",
    "cidade_evento": "Sao Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link": "",
    "valor": "R$ 200,00",
    "detalhamento": "Reuniao de coordenaao.",
    "apresentar": "Nao ira apresentar trabalho",
    "data_nasc": "15/03/1975",
    "logradouro": "Av. Prof. Lineu Prestes",
    "numero": "1100",
    "complemento": "",
    "bairro": "Butanta",
    "cep": "05508-000",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "98.765.432-1",
    "banco": "Itau",
    "agencia": "4321",
    "conta": "10293-8",
}


# ═══════════════════════════════════════════════════════════════════════════
#  A. Static files are served
# ═══════════════════════════════════════════════════════════════════════════

class TestStaticFiles:
    def test_index(self):
        r = urllib.request.urlopen(BASE_URL + "/")
        assert r.status == 200

    def test_css(self):
        r = urllib.request.urlopen(BASE_URL + "/style.css")
        assert r.status == 200

    def test_js(self):
        r = urllib.request.urlopen(BASE_URL + "/app.js")
        assert r.status == 200

    def test_logo(self):
        r = urllib.request.urlopen(BASE_URL + "/assets/usp-logo.png")
        assert r.status == 200


# ═══════════════════════════════════════════════════════════════════════════
#  B. Tab structure in the HTML
# ═══════════════════════════════════════════════════════════════════════════

class TestTabs:
    def test_tab_alunos(self):
        assert "ALUNOS" in _html()

    def test_tab_docentes(self):
        assert "DOCENTES" in _html()

    def test_alunos_before_docentes(self):
        h = _html()
        assert h.index("ALUNOS") < h.index("DOCENTES")

    def test_submit_button(self):
        assert "Enviar solicita\u00e7\u00e3o" in _html()


# ═══════════════════════════════════════════════════════════════════════════
#  C. Block headings
# ═══════════════════════════════════════════════════════════════════════════

class TestBlockHeadings:
    def test_solicitante(self):
        assert "SOLICITANTE E EVENTO" in _html()

    def test_endereco(self):
        assert "ENDERE\u00c7O DO SOLICITANTE" in _html()

    def test_pagamento(self):
        assert "INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO" in _html()


# ═══════════════════════════════════════════════════════════════════════════
#  D. SOLICITANTE E EVENTO field labels
# ═══════════════════════════════════════════════════════════════════════════

class TestSolicitanteLabels:
    LABELS = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "N\u00cdVEL",
        "TIPO DE AUX\u00cdLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    ]

    def test_label(self, label):
        assert label in _html()

    @pytest.mark.parametrize("label", LABELS)
    def test_order(self, label):
        pass

    def test_order_sequence(self):
        h = _html()
        for a, b in zip(self.LABELS, self.LABELS[1:]):
            assert h.index(a) < h.index(b), f"{a} must precede {b}"


# ═══════════════════════════════════════════════════════════════════════════
#  E. ENDEREÇO field labels
# ═══════════════════════════════════════════════════════════════════════════

class TestEnderecoLabels:
    LABELS = [
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "N\u00daMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
    ]

    def test_order_sequence(self):
        h = _html()
        for a, b in zip(self.LABELS, self.LABELS[1:]):
            assert h.index(a) < h.index(b), f"{a} must precede {b}"


# ═══════════════════════════════════════════════════════════════════════════
#  F. PAGAMENTO field labels
# ═══════════════════════════════════════════════════════════════════════════

class TestPagamentoLabels:
    LABELS = [
        "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "NOME DO BANCO",
        "N\u00daMERO DA AG\u00caNCIA",
        "N\u00daMERO DA CONTA",
    ]

    def test_order_sequence(self):
        h = _html()
        for a, b in zip(self.LABELS, self.LABELS[1:]):
            assert h.index(a) < h.index(b), f"{a} must precede {b}"


# ═══════════════════════════════════════════════════════════════════════════
#  G. Level / type select options (ALUNOS only)
# ═══════════════════════════════════════════════════════════════════════════

class TestSelectOptions:
    def test_mestrado(self):
        assert "Mestrado" in _html()

    def test_doutorado(self):
        assert "Doutorado" in _html()

    def test_participacao(self):
        assert "Participa\u00e7\u00e3o em evento" in _html()

    def test_banca(self):
        assert "Banca de exame ou defesa" in _html()

    def test_poster(self):
        assert "P\u00f4ster" in _html()

    def test_apresentacao_oral(self):
        assert "Apresenta\u00e7\u00e3o oral" in _html()

    def test_nao_apresentar(self):
        assert "N\u00e3o ir\u00e1 apresentar trabalho" in _html()


# ═══════════════════════════════════════════════════════════════════════════
#  H. Validation errors returned by backend
# ═══════════════════════════════════════════════════════════════════════════

class TestValidation:
    # ── empty required fields ──
    def test_empty(self):
        _, errs = _post("/alunos", {})
        assert isinstance(errs, list)
        assert "Preencha todos os campos" in errs

    # ── N. USP not digits ──
    def test_nusp_letters(self):
        d = {**_ALUNOS_BASE, "nusp": "abc"}
        _, errs = _post("/alunos", d)
        assert "N. USP deve conter apenas n\u00fameros" in errs

    def test_nusp_ok(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "N. USP deve conter apenas n\u00fameros" not in errs

    # ── agência not digits ──
    def test_agencia_letters(self):
        d = {**_ALUNOS_BASE, "agencia": "xy"}
        _, errs = _post("/alunos", d)
        assert "N\u00famero da ag\u00eancia deve conter apenas n\u00fameros" in errs

    # ── valor ≤ 0 ──
    def test_valor_zero(self):
        d = {**_ALUNOS_BASE, "valor": "R$ 0,00"}
        _, errs = _post("/alunos", d)
        assert "Valor solicitado deve ser maior que 0" in errs

    def test_valor_negative(self):
        d = {**_ALUNOS_BASE, "valor": "R$ -1,00"}
        _, errs = _post("/alunos", d)
        assert "Valor solicitado deve ser maior que 0" in errs

    def test_valor_ok(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "Valor solicitado deve ser maior que 0" not in errs

    # ── e-mail ──
    def test_email_no_at(self):
        d = {**_ALUNOS_BASE, "email": "abc"}
        _, errs = _post("/alunos", d)
        assert "E-mail inv\u00e1lido" in errs

    def test_email_no_domain(self):
        d = {**_ALUNOS_BASE, "email": "abc@"}
        _, errs = _post("/alunos", d)
        assert "E-mail inv\u00e1lido" in errs

    def test_email_ok(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "E-mail inv\u00e1lido" not in errs

    # ── CPF format ──
    def test_cpf_format(self):
        d = {**_ALUNOS_BASE, "cpf": "12345678909"}
        _, errs = _post("/alunos", d)
        assert "CPF deve estar no formato 000.000.000-00" in errs

    def test_cpf_ok_format(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "CPF deve estar no formato 000.000.000-00" not in errs

    # ── CPF check digits ──
    def test_cpf_invalid_digits(self):
        d = {**_ALUNOS_BASE, "cpf": "111.111.111-11"}
        _, errs = _post("/alunos", d)
        assert "CPF inv\u00e1lido" in errs

    def test_cpf_valid(self):
        d = {**_ALUNOS_BASE, "cpf": "529.982.247-25"}
        _, errs = _post("/alunos", d)
        assert "CPF inv\u00e1lido" not in errs

    # ── CEP format ──
    def test_cep_format(self):
        d = {**_ALUNOS_BASE, "cep": "05508090"}
        _, errs = _post("/alunos", d)
        assert "CEP deve estar no formato 00000-000" in errs

    def test_cep_ok(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "CEP deve estar no formato 00000-000" not in errs

    # ── Data format ──
    def test_data_format(self):
        d = {**_ALUNOS_BASE, "data_nasc": "01-02-1980"}
        _, errs = _post("/alunos", d)
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" in errs

    def test_data_ok(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in errs

    # ── Data invalid ──
    def test_data_invalid_day(self):
        d = {**_ALUNOS_BASE, "data_nasc": "31/02/1980"}
        _, errs = _post("/alunos", d)
        assert "Data de nascimento inv\u00e1lida" in errs

    def test_data_invalid_month(self):
        d = {**_ALUNOS_BASE, "data_nasc": "01/13/1980"}
        _, errs = _post("/alunos", d)
        assert "Data de nascimento inv\u00e1lida" in errs

    def test_data_valid(self):
        _, errs = _post("/alunos", _ALUNOS_BASE)
        assert "Data de nascimento inv\u00e1lida" not in errs

    # ── multiple errors ──
    def test_multiple(self):
        d = {**_ALUNOS_BASE, "nusp": "x", "email": "no"}
        _, errs = _post("/alunos", d)
        assert "N. USP deve conter apenas n\u00fameros" in errs
        assert "E-mail inv\u00e1lido" in errs


# ═══════════════════════════════════════════════════════════════════════════
#  I. Officio – ALUNOS
# ═══════════════════════════════════════════════════════════════════════════

class TestOfficioAlunos:
    @pytest.fixture()
    def self(self):
        sc, resp = _post("/alunos", _ALUNOS_BASE)
        assert sc == 200
        assert "oficio" in resp
        return resp["oficio"]

    def test_interest(self, self):
        assert "Maria Silva - 1234567" in self["oficio"]

    def test_email(self, self):
        assert "E-mail: maria@ime.usp.br" in self["oficio"]

    def test_assunto(self, self):
        assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Participa\u00e7\u00e3o em evento" in self["oficio"]

    def test_programa(self, self):
        assert "Programa: Matematica - Doutorado" in self["oficio"]

    def test_evento(self, self):
        assert "Evento: CMUC 2025" in self["oficio"]

    def test_local(self, self):
        assert "Local: Coimbra - Coimbra - Portugal" in self["oficio"]

    def test_link(self, self):
        assert "Link do evento: https://cmuc.org" in self["oficio"]

    def test_valor(self, self):
        assert "Valor solicitado: R$ 1.500,00" in self["oficio"]

    def test_endereco(self, self):
        assert "Rua do Matrao, 101" in self["oficio"]

    def test_complemento(self, self):
        assert "Complemento: Apto 5" in self["oficio"]

    def test_cep(self, self):
        assert "CEP: 05508-090" in self["oficio"]

    def test_bairro(self, self):
        assert "Butanta, Sao Paulo - SP" in self["oficio"]

    def test_cpf(self, self):
        assert "CPF: 123.456.789-09" in self["oficio"]

    def test_final(self, self):
        assert "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias." in self["oficio"]


# ═══════════════════════════════════════════════════════════════════════════
#  J. Officio – DOCENTES
# ═══════════════════════════════════════════════════════════════════════════

class TestOfficioDocentes:
    @pytest.fixture()
    def self(self):
        sc, resp = _post("/docentes", _DOCENTES_BASE)
        assert sc == 200
        assert "oficio" in resp
        return resp

    def test_success(self, self):
        assert "errors" not in self

    def test_assunto_verba(self, self):
        assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa" in self["oficio"]

    def test_no_tipo_auxilio(self, self):
        assert "Tipo de aux\u00edlio" not in self["oficio"]

    def test_programa_no_nivel(self, self):
        assert "Programa: Estatistica" in self["oficio"]
        line = [l for l in self["oficio"].split("\n") if l.startswith("Programa:")][0]
        assert " - " not in line


# ═══════════════════════════════════════════════════════════════════════════
#  K. Optional fields omitted
# ═══════════════════════════════════════════════════════════════════════════

class TestOmittedLines:
    def test_link(self):
        d = {**_ALUNOS_BASE, "link": ""}
        sc, resp = _post("/alunos", d)
        assert "Link do evento:" not in resp["oficio"]

    def test_complemento(self):
        d = {**_ALUNOS_BASE, "complemento": ""}
        sc, resp = _post("/alunos", d)
        assert "Complemento:" not in resp["oficio"]


# ═══════════════════════════════════════════════════════════════════════════
#  L. JS: no async, no remote resources
# ═══════════════════════════════════════════════════════════════════════════

class TestNoAsync:
    def test_js(self):
        assert "async" not in _js()

    def test_js_no_fetch_async(self):
        assert "fetch(" not in _js() or "async" not in _js()


class TestNoCDN:
    def test_html_no_google_apis(self):
        assert "googleapis.com" not in _html()

    def test_html_no_cdns(self):
        h = _html()
        assert "cdn" not in h.lower()

    def test_html_no_jsdelivr(self):
        assert "jsdelivr.net" not in _html()

    def test_html_no_unpkg(self):
        assert "unpkg.com" not in _html()


# ═══════════════════════════════════════════════════════════════════════════
#  M. JS: client-side auto-formatting
# ═══════════════════════════════════════════════════════════════════════════

class TestFormattingJS:
    def test_cpf(self):
        assert "CPF" in _js()

    def test_cep(self):
        assert "CEP" in _js() or "cep" in _js()

    def test_data(self):
        assert "DATA" in _js() or "data" in _js().lower() or "nasc" in _js().lower()

    def test_valor(self):
        assert "R$" in _js()

    def test_blur(self):
        assert "blur" in _js()

    def test_1500(self):
        assert "1500" in _js()

    def test_150000(self):
        assert "150000" in _js()


# ═══════════════════════════════════════════════════════════════════════════
#  N. CSS
# ═══════════════════════════════════════════════════════════════════════════

class TestCSS:
    def test_primary(self):
        assert "#1094ab" in _css()

    def test_secondary(self):
        assert "#64c4d2" in _css()

    def test_yellow(self):
        assert "#fcb421" in _css()

    def test_open_sans(self):
        assert "Open Sans" in _css() or "sans-serif" in _css()

    def test_usp_logo(self):
        assert "usp-logo.png" in _html()

    def test_usp_text(self):
        assert "Universidade de S\u00e3o Paulo" in _html()


# ═══════════════════════════════════════════════════════════════════════════
#  O. DOCENTES validation uses the same rules
# ═══════════════════════════════════════════════════════════════════════════

class TestDocentesValidation:
    def test_empty(self):
        _, errs = _post("/docentes", {})
        assert "Preencha todos os campos" in errs

    def test_nusp(self):
        d = {**_DOCENTES_BASE, "nusp": "abc"}
        _, errs = _post("/docentes", d)
        assert "N. USP deve conter apenas n\u00fameros" in errs

    def test_cpf_invalid(self):
        d = {**_DOCENTES_BASE, "cpf": "111.111.111-11"}
        _, errs = _post("/docentes", d)
        assert "CPF inv\u00e1lido" in errs

    def test_cep(self):
        d = {**_DOCENTES_BASE, "cep": "bad"}
        _, errs = _post("/docentes", d)
        assert "CEP deve estar no formato 00000-000" in errs

    def test_data(self):
        d = {**_DOCENTES_BASE, "data_nasc": "32/01/2000"}
        _, errs = _post("/docentes", d)
        assert "Data de nascimento inv\u00e1lida" in errs
