import re

ROTULOS = [
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

SOMENTE_NA_ABA_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]

TITULOS_DE_BLOCO = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]


def _atributo(tag, nome):
    m = re.search(rf'{nome}\s*=\s*[\'"]([^\'"]*)[\'"]', tag, re.I)
    return m.group(1) if m else None


def test_cabecalho_institucional(html):
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_abas_alunos_e_docentes_nessa_ordem(html):
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_de_bloco(html):
    for titulo in TITULOS_DE_BLOCO:
        assert titulo in html


def test_rotulos_presentes(html):
    for rotulo in ROTULOS:
        assert rotulo in html, f"rótulo ausente: {rotulo}"


def test_campos_comuns_nas_duas_abas(html):
    for rotulo in ROTULOS:
        if rotulo in SOMENTE_NA_ABA_ALUNOS:
            continue
        assert html.count(rotulo) >= 2, f"rótulo deveria estar nas duas abas: {rotulo}"


def test_nivel_e_tipo_so_na_aba_alunos(html):
    for rotulo in SOMENTE_NA_ABA_ALUNOS:
        assert html.count(rotulo) == 1, f"deveria aparecer só na aba ALUNOS: {rotulo}"


def test_opcoes_de_selecao(html):
    for opcao in OPCOES:
        assert opcao in html, f"opção ausente: {opcao}"


def test_botao_enviar_em_cada_aba(html):
    assert html.count("Enviar solicitação") >= 2


def test_todo_campo_tem_placeholder_de_exemplo(html):
    rotulos = {rotulo.lower() for rotulo in ROTULOS}
    campos = 0
    for tag in re.findall(r"<(?:input|textarea)\b[^>]*>", html, re.I):
        tipo = (_atributo(tag, "type") or "text").lower()
        if tipo in {"hidden", "submit", "button", "reset", "checkbox", "radio", "image"}:
            continue
        valor = _atributo(tag, "placeholder")
        assert valor is not None, f"campo sem placeholder: {tag}"
        valor = valor.strip()
        assert valor, f"placeholder vazio: {tag}"
        assert valor.lower() not in rotulos, f"placeholder repete o rótulo: {valor}"
        campos += 1
    assert campos >= 24, "menos campos de texto com placeholder do que o esperado"


def test_css_e_js_locais_servidos(css, js):
    assert css.strip(), "index.html não referencia nenhum CSS"
    assert js.strip(), "index.html não referencia nenhum JS"


def test_nenhum_recurso_remoto(html, css, js):
    for url in re.findall(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", html):
        assert not re.match(r"https?://", url), f"recurso remoto no index.html: {url}"
    for texto, nome in ((css, "style.css"), (js, "app.js")):
        assert "@import" not in texto.lower(), f"@import no {nome}"
        for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", texto, re.I):
            assert not re.match(r"https?://", url), f"recurso remoto no {nome}: {url}"
    for url in re.findall(r"(?:import|fetch)\(\s*['\"]([^'\"]+)", js):
        assert not re.match(r"https?://", url), f"recurso remoto no app.js: {url}"


def test_identidade_visual_usp(css):
    baixo = css.lower()
    assert "#1094ab" in baixo, "azul primário da USP ausente do CSS"
    assert "#64c4d2" in baixo or "#fcb421" in baixo, "cores de apoio ausentes do CSS"
    assert "open sans" in baixo or "sans-serif" in baixo


def test_oficio_preserva_quebras_de_linha(html, css, js):
    assert (
        re.search(r"white-space\s*:[^;]*\bpre", css, re.I)
        or re.search(r"<pre\b", html, re.I)
        or re.search(r"<pre\b", js, re.I)
    )


def test_logo_da_usp_servido(client):
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/")
