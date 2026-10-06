import re

import pytest


def cliente():
    importorskip_backend = pytest.importorskip
    importorskip_backend("app")
    from fastapi.testclient import TestClient
    from app import app
    return TestClient(app)


def html():
    return cliente().get("/").text


def teste_pagina_abre_com_200():
    assert cliente().get("/").status_code == 200


def teste_titulo_da_pagina():
    conteudo = html()
    assert re.search(r"<title>[^<]*(?:Auxílio|Auxilio|auxílio|auxilio)[^<]*</title>", conteudo)


def teste_abas_alunos_docentes_nessa_ordem():
    conteudo = html()
    pos_alunos = conteudo.find("ALUNOS")
    pos_docentes = conteudo.find("DOCENTES")
    assert pos_alunos != -1, "aba ALUNOS ausente"
    assert pos_docentes != -1, "aba DOCENTES ausente"
    assert pos_alunos < pos_docentes


def teste_abas_sao_interativas_sem_recarregar():
    conteudo = html()
    assert "role=\"tab\"" in conteudo or "role='tab'" in conteudo
    assert "role=\"tabpanel\"" in conteudo or "role='tabpanel'" in conteudo


def teste_abas_selecionaveis():
    conteudo = html()
    assert 'type="radio"' in conteudo or "type='radio'" in conteudo


def teste_aba_alunos_ativa_inicialmente():
    conteudo = html()
    pos_alunos = conteudo.find("ALUNOS")
    pos_docentes = conteudo.find("DOCENTES")
    assert "checked" in conteudo[pos_alunos:pos_docentes]
    assert "checked" not in conteudo[pos_docentes:]


def teste_dois_botoes_enviar():
    assert html().lower().count("enviar solicitação") == 2


def teste_rotulos_exatos():
    rotulos = [
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
    ]
    conteudo = html()
    for rotulo in rotulos:
        assert rotulo in conteudo, f"rótulo ausente: {rotulo}"


def teste_titulos_de_bloco():
    conteudo = html()
    for bloco in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert bloco in conteudo, f"bloco ausente: {bloco}"


def teste_opcoes_de_selecao():
    conteudo = html()
    for opcao in [
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ]:
        assert opcao in conteudo, f"opção ausente: {opcao}"


def teste_campos_exclusivos_de_alunos_nao_aparecem_em_docentes():
    conteudo = html()
    inicio = conteudo.find("DOCENTES")
    assert inicio != -1
    docentes = conteudo[inicio:]
    assert "NÍVEL" not in docentes, "NÍVEL não deve aparecer na aba DOCENTES"
    assert "TIPO DE AUXÍLIO" not in docentes, "TIPO DE AUXÍLIO não deve aparecer na aba DOCENTES"


def teste_placeholders_presentes():
    assert html().count("placeholder") >= 29


def teste_css_js_servidos_localmente():
    assert re.search(r'<link[^>]+href=["\']style\.css["\']', html())
    assert re.search(r'<script[^>]+src=["\']app\.js["\']', html())


def teste_estaticos_disponiveis():
    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        resposta = cliente().get(caminho)
        assert resposta.status_code == 200, caminho


def teste_css_e_js_sem_arquivos_remotos():
    for caminho in ("/style.css", "/app.js"):
        conteudo = cliente().get(caminho).text
        assert "http://" not in conteudo
        assert "https://" not in conteudo


def teste_css_cores_identidade():
    conteudo = cliente().get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in conteudo, cor


def teste_css_sem_brasao():
    assert not re.search(r"brasao|coat-of-arms|coatofarms", cliente().get("/style.css").text.lower())
