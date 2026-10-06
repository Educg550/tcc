import re


def _client():
    from fastapi.testclient import TestClient
    import app as modulo
    return TestClient(modulo.app)


def _pagina(client, caminho="/"):
    resposta = client.get(caminho)
    assert resposta.status_code == 200
    return resposta.text


def test_index_eh_html(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "<!DOCTYPE html".lower() in resposta.text.lower()


def test_assets_logo(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_abas_na_ordem(client):
    pagina = _pagina(client)
    pos_alunos = pagina.find(">ALUNOS<")
    pos_docentes = pagina.find(">DOCENTES<")
    assert pos_alunos != -1
    assert pos_docentes != -1
    assert pos_alunos < pos_docentes


def test_alunos_ativa_no_inicio(client):
    pagina = _pagina(client)
    m = re.search(r"<button[^>]*id=\"aba-alunos\"[^>]*class=\"([^\"]*)\"", pagina)
    assert m and "ativa" in m.group(1)
    m = re.search(r"<button[^>]*id=\"aba-docentes\"[^>]*class=\"([^\"]*)\"", pagina)
    assert m and "ativa" not in m.group(1)


def test_formularios_e_ocultacao(client):
    pagina = _pagina(client)
    m = re.search(r"<form[^>]*id=\"form-alunos\"([^>]*)>", pagina)
    assert m
    assert "hidden" not in m.group(1)
    m = re.search(r"<form[^>]*id=\"form-docentes\"([^>]*)>", pagina)
    assert m and "hidden" in m.group(1)


def test_rotulos_presentes(client):
    pagina = _pagina(client)
    for rotulo in ROTULOS_COMUNS + ROTULOS_ALUNOS:
        assert rotulo in pagina


def test_rotulos_docentes_sem_exclusivos(client):
    pagina = _pagina(client)
    assert "NÍVEL" not in pagina
    assert "TIPO DE AUXÍLIO" not in pagina


def test_cabecalho_institucional(client):
    pagina = _pagina(client)
    assert "usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina
    assert "Pós-Graduação" in pagina


def test_brasao_ausente(client):
    pagina = _pagina(client)
    assert "brasao" not in pagina.lower()


def test_sem_rede_externa(client):
    pagina = _pagina(client)
    assert "http://" not in pagina and "https://" not in pagina


def test_submit_js(client):
    pagina = _pagina(client)
    assert "addEventListener(\"submit\"" in pagina or "addEventListener('submit'" in pagina


def test_confirmacao_js(client):
    pagina = _pagina(client)
    assert "confirmacao" in pagina.lower()
    assert "Solicitação registrada" in pagina or ("Solicita\u00e7\u00e3o registrada" in pagina and "registroConfirmado" in pagina)


def test_erros_js(client):
    pagina = _pagina(client)
    assert "Preencha todos os campos" in pagina
    assert "formatarMoeda" in pagina
    assert "formatarCPF" in pagina
    assert "formatarCEP" in pagina
    assert "formatarData" in pagina


def test_validar_cpf_js(client):
    pagina = _pagina(client)
    assert "validarCPF" in pagina


def test_css_fonte_cores(client):
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    css = resposta.text
    assert "Open Sans" in css or "sans-serif" in css
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_css_grid_varias_colunas(client):
    css = client.get("/style.css").text
    assert "grid-template-columns" in css


def test_campos_lado_a_lado(client):
    pagina = _pagina(client)
    assert re.search(r"class=\"linha\"", pagina)


def test_classe_erros(client):
    pagina = _pagina(client)
    assert re.search(r"class=\"erros\"", pagina)


def test_margem_logo(client):
    css = client.get("/style.css").text
    m = re.search(r"\.logo\s*\{[^}]*\}", css)
    assert m
    corpo = m.group(0)
    assert "padding" in corpo


def test_placeholder_sem_repetir_rotulo(client):
    pagina = _pagina(client)
    placeholders = re.findall(r"placeholder=\"([^\"]*)\"", pagina)
    assert len(placeholders) >= 25
    rotulos = ROTULOS_COMUNS + ROTULOS_ALUNOS
    for p in placeholders:
        assert p.upper() not in rotulos


def test_campos_plano(client):
    pagina = _pagina(client)
    assert re.search(r"name=\"tipo_auxilio\"", pagina)
    assert re.search(r"name=\"nivel\"", pagina)


def test_select_opcoes(client):
    pagina = _pagina(client)
    assert "Mestrado" in pagina and "Doutorado" in pagina
    assert "Participação em evento" in pagina
    assert "Banca de exame ou defesa" in pagina
    assert "Outra" in pagina
    assert "Não irá apresentar trabalho" in pagina


def test_appjs(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip() != ""


def test_ajax_post_js(client):
    pagina = _pagina(client)
    assert "fetch(" in pagina


def test_formatacao_campos_js(client):
    pagina = _pagina(client)
    assert 'addEventListener("blur"' in pagina or "addEventListener('blur'" in pagina


def test_botao_enviar(client):
    pagina = _pagina(client)
    assert pagina.count("Enviar solicitação") == 2


def test_confirmacao_preserva_quebras(client):
    pagina = _pagina(client)
    assert "pre" in pagina.lower() or "white-space" in client.get("/style.css").text.lower()
