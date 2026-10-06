import re
from html.parser import HTMLParser

TITULOS_DOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS_SO_DA_ABA_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]

ROTULOS_DAS_DUAS_ABAS = [
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

ORDEM_DA_ABA_ALUNOS = [
    "SOLICITANTE E EVENTO",
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
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
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
    "Enviar solicitação",
]

ORDEM_DA_ABA_DOCENTES = [
    rotulo for rotulo in ORDEM_DA_ABA_ALUNOS if rotulo not in ROTULOS_SO_DA_ABA_ALUNOS
]


class _Pagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.textareas = []
        self.imagens = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "input":
            self.inputs.append(atributos)
        elif tag == "textarea":
            self.textareas.append(atributos)
        elif tag == "img":
            self.imagens.append(atributos.get("src", ""))


def _html(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    return resposta.text


def _fora_de_ordem(html, rotulos):
    posicao = 0
    for rotulo in rotulos:
        achado = html.find(rotulo, posicao)
        if achado < 0:
            return rotulo
        posicao = achado + len(rotulo)
    return None


def test_pagina_inicial_e_html(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_arquivos_estaticos_sao_servidos(client):
    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200
        assert resposta.content


def test_pagina_referencia_o_css_e_o_js(client):
    html = _html(client)
    assert "style.css" in html
    assert "app.js" in html


def test_abas_alunos_e_docentes_nesta_ordem(client):
    html = _html(client)
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cada_aba_tem_seu_botao_de_envio(client):
    html = _html(client)
    assert html.count("Enviar solicitação") == 2


def test_todos_os_rotulos_estao_na_pagina(client):
    html = _html(client)
    for rotulo in TITULOS_DOS_BLOCOS + ROTULOS_DAS_DUAS_ABAS + ROTULOS_SO_DA_ABA_ALUNOS:
        assert rotulo in html, rotulo


def test_campos_comuns_aparecem_nas_duas_abas(client):
    html = _html(client)
    lenientes = {"PROGRAMA", "NÚMERO", "CIDADE", "ESTADO", "CEP"}
    for rotulo in ROTULOS_DAS_DUAS_ABAS:
        if rotulo not in lenientes:
            assert html.count(rotulo) == 2, rotulo
    assert html.count("PROGRAMA") >= 2
    assert html.count("CEP") >= 2
    restantes = (
        html.count("NÚMERO")
        - html.count("NÚMERO DA AGÊNCIA")
        - html.count("NÚMERO DA CONTA")
    )
    assert restantes == 2
    assert html.count("CIDADE") - html.count("CIDADE DO EVENTO, EXAME OU DEFESA") == 2
    assert html.count("ESTADO") - html.count("ESTADO DO EVENTO, EXAME OU DEFESA") == 2


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos(client):
    html = _html(client)
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


def test_campos_na_ordem_do_requisito(client):
    html = _html(client)
    problema = _fora_de_ordem(html, ORDEM_DA_ABA_ALUNOS + ORDEM_DA_ABA_DOCENTES)
    assert problema is None, problema


def test_opcoes_das_selecoes(client):
    html = _html(client)
    for opcao in OPCOES:
        assert opcao in html, opcao


def test_todo_campo_tem_placeholder_com_exemplo(client):
    html = _html(client)
    pagina = _Pagina()
    pagina.feed(html)
    rotulos = {
        rotulo.casefold()
        for rotulo in ROTULOS_DAS_DUAS_ABAS + ROTULOS_SO_DA_ABA_ALUNOS
    }
    sem_placeholder = {"submit", "button", "reset", "hidden", "radio", "checkbox", "file"}
    for atributos in pagina.inputs + pagina.textareas:
        if atributos.get("type") in sem_placeholder:
            continue
        exemplo = (atributos.get("placeholder") or "").strip()
        assert exemplo, atributos
        assert exemplo.casefold() not in rotulos, atributos
    assert len(pagina.textareas) == 2


def test_cabecalho_institucional_da_usp(client):
    html = _html(client)
    css = client.get("/style.css").text
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html or "usp-logo.png" in css
    pagina = _Pagina()
    pagina.feed(html)
    for src in pagina.imagens:
        assert src.strip("/") == "assets/usp-logo.png", src


def test_cores_e_fonte_da_usp(client):
    css = client.get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, cor
    assert "open sans" in css or "sans-serif" in css


def test_nenhum_recurso_externo(client):
    html = _html(client).lower()
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert 'src="//' not in html
    assert 'href="//' not in html
    css = client.get("/style.css").text.lower()
    assert "@import" not in css
    for url in re.findall(r"url\(([^)]*)\)", css):
        assert "usp-logo.png" in url, url


def test_texto_da_confirmacao(client):
    html = _html(client)
    js = client.get("/app.js").text
    assert "Solicitação registrada" in html or "Solicitação registrada" in js
