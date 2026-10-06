import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_pagina_formulario_e_estaticos():
    r = client.get("/")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text

    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        assert client.get(caminho).status_code == 200


def test_tabs_e_campos_na_ordem():
    html = client.get("/").text

    alunos = html.index("ALUNOS")
    docentes = html.index("DOCENTES")
    assert alunos < docentes

    formulario_alunos = html.index('id="form-alunos"')
    formulario_docentes = html.index('id="form-docentes"')
    inicio = html.index('id="bloco-solicitante"')

    esperado = [
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
    ]
    for rotulo in esperado:
        assert html[inicio:].index(rotulo) >= 0

    # ordem dentro de cada formulário
    pos = [html[inicio:].index(r) for r in esperado]
    assert pos == sorted(pos)

    # ALUNOS tem NÍVEL e TIPO DE AUXÍLIO; DOCENTES não tem
    fim_alunos = html.index('id="bloco-endereco"')
    corpo_alunos = html[formulario_alunos:fim_alunos]
    fim_docentes = html.index('id="bloco-endereco"', formulario_docentes)
    corpo_docentes = html[formulario_docentes:fim_docentes]
    assert "NÍVEL" in corpo_alunos
    assert "TIPO DE AUXÍLIO" in corpo_alunos
    assert "NÍVEL" not in corpo_docentes
    assert "TIPO DE AUXÍLIO" not in corpo_docentes

    for texto in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert texto in corpo_alunos


def test_placeholders():
    html = client.get("/").text
    for bloco_id in ("solicitante", "endereco", "pagamento"):
        bloco = extrair_bloco(html, bloco_id)
        campos = re.findall(r"<input[^>]*>", bloco)
        assert campos
        for campo in campos:
            placeholder = re.search(r'placeholder="([^"]*)"', campo)
            assert placeholder, campo
            texto = placeholder.group(1).strip()
            assert texto
            rotulos = re.findall(r"<label[^>]*>([^<]*)</label>", bloco)
            assert texto not in [r.strip() for r in rotulos]


def extrair_bloco(html, bloco):
    inicio = html.index('id="bloco-%s"' % bloco)
    proximos = [html.find('id="bloco-', inicio + 1)]
    for marcador in ('id="form-docentes"', "</main>", "</body>"):
        p = html.find(marcador, inicio + 1)
        if p != -1:
            proximos.append(p)
    fim = min(p for p in proximos if p != -1)
    return html[inicio:fim]
