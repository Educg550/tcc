import re


def test_index_e_servido(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html


def test_index_cabecalho_institucional(client):
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    # o brasão (escudo) não aparece na página
    assert "escudo" not in html.lower()
    assert "brasao" not in html.lower()
    assert "brasão" not in html.lower()


def test_index_ordenacao_das_abas(client):
    html = client.get("/").text
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_index_blocos_e_campos_na_ordem(client):
    html = client.get("/").text
    ordem = [
        "SOLICITANTE E EVENTO",
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
        "ENDEREÇO DO SOLICITANTE",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ]
    pos = -1
    for rotulo in ordem:
        i = html.find(rotulo)
        assert i != -1, f"rótulo ausente: {rotulo}"
        assert i > pos, f"rótulo fora de ordem: {rotulo}"
        pos = i


def test_index_selecoes(client):
    html = client.get("/").text
    for opcao in ["Mestrado", "Doutorado",
                  "Participação em evento", "Banca de exame ou defesa", "Outro",
                  "Pôster", "Apresentação oral", "Não irá apresentar trabalho"]:
        assert opcao in html


def test_index_dois_botoes_de_envio(client):
    html = client.get("/").text
    assert html.count("Enviar solicitação") == 2


def test_style_css_e_servido_com_cores_institucionais(client):
    r = client.get("/style.css")
    assert r.status_code == 200
    css = r.text
    assert "#1094ab" in css
    assert "#64c4d2" in css or "#fcb421" in css


def test_style_css_fonte_sem_serifa(client):
    css = client.get("/style.css").text
    assert "Open Sans" in css
    assert "serif" not in css


def test_app_js_e_servido(client):
    r = client.get("/app.js")
    assert r.status_code == 200
    assert r.text.strip() != ""


def test_sem_fonte_ou_framework_remoto(client):
    for caminho in ["/", "/style.css", "/app.js"]:
        texto = client.get(caminho).text
        assert "https://" not in texto
        assert "http://" not in texto


def test_assets_logo_e_servido(client):
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
