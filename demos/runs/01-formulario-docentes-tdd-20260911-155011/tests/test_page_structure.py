import re

from fastapi.testclient import TestClient

from app import app
from tests.helpers import get_forms, placeholder_after_label

client = TestClient(app)


def test_pagina_inicial_carrega():
    resp = client.get("/")
    assert resp.status_code == 200


def test_cabecalho_institucional():
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    low = html.lower()
    assert "brasao" not in low
    assert "escudo" not in low


def test_abas_alunos_docentes_na_ordem():
    html = client.get("/").text
    pos_alunos = html.find("ALUNOS")
    pos_docentes = html.find("DOCENTES")
    assert pos_alunos != -1
    assert pos_docentes != -1
    assert pos_alunos < pos_docentes


def test_titulos_dos_blocos_presentes():
    html = client.get("/").text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_dois_formularios_presentes():
    html = client.get("/").text
    forms = re.findall(r"<form.*?</form>", html, re.DOTALL)
    assert len(forms) == 2


def test_form_alunos_tem_nivel_e_tipo_auxilio():
    html = client.get("/").text
    alunos, docentes = get_forms(html)
    assert "NÍVEL" in alunos
    assert "TIPO DE AUXÍLIO" in alunos


def test_form_docentes_nao_tem_nivel_nem_tipo_auxilio():
    html = client.get("/").text
    alunos, docentes = get_forms(html)
    assert "NÍVEL" not in docentes
    assert "TIPO DE AUXÍLIO" not in docentes


def test_rotulos_comuns_presentes_nas_duas_abas():
    html = client.get("/").text
    alunos, docentes = get_forms(html)
    rotulos_comuns = [
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
    for rotulo in rotulos_comuns:
        assert rotulo in alunos, f"faltando na aba ALUNOS: {rotulo}"
        assert rotulo in docentes, f"faltando na aba DOCENTES: {rotulo}"


def test_botao_enviar_solicitacao_presente_nas_duas_abas():
    html = client.get("/").text
    alunos, docentes = get_forms(html)
    assert "Enviar solicitação" in alunos
    assert "Enviar solicitação" in docentes


def test_placeholders_nao_repetem_rotulo():
    html = client.get("/").text
    alunos, _ = get_forms(html)
    for rotulo in [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "VALOR SOLICITADO (R$)",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "CEP",
        "DATA DE NASCIMENTO",
    ]:
        placeholder = placeholder_after_label(alunos, rotulo)
        assert placeholder.strip() != ""
        assert placeholder.strip() != rotulo


def test_cores_institucionais_presentes():
    html = client.get("/").text.lower()
    assert "#1094ab" in html
    assert "#64c4d2" in html
    assert "#fcb421" in html


def test_fonte_sem_serifa_ou_open_sans():
    html = client.get("/").text.lower()
    assert "sans-serif" in html or "open sans" in html


def test_css_e_js_embutidos_na_pagina():
    html = client.get("/").text
    assert "<style" in html
    assert "<script" in html


def test_sem_recursos_externos():
    html = client.get("/").text
    low = html.lower()
    assert "cdn." not in low
    assert "googleapis" not in low
    assert not re.search(r'<link[^>]+href="https?://', html)
    assert not re.search(r'<script[^>]+src="https?://', html)
    assert not re.search(r'<link[^>]+rel="stylesheet"[^>]+href="[^"]+\.css"', html)
