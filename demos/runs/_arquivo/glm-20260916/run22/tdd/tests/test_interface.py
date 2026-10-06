import re
from html.parser import HTMLParser

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

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


class ColetorPlaceholders(HTMLParser):
    def __init__(self):
        super().__init__()
        self.placeholders = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "placeholder" in atributos:
            self.placeholders.append(atributos["placeholder"] or "")


def _html(client):
    return client.get("/").text


def _local(client, caminho):
    if not caminho.startswith("/"):
        caminho = "/" + caminho
    return client.get(caminho)


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = _html(client)
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_blocos_e_rotulos_exatos(client):
    html = _html(client)
    for texto in BLOCOS + ROTULOS:
        assert texto in html, f"ausente: {texto}"


def test_campos_exclusivos_da_aba_alunos(client):
    html = _html(client)
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


def test_dois_formularios_com_botao_enviar(client):
    html = _html(client)
    assert html.count("<form") >= 2
    assert html.count("<textarea") >= 2
    assert html.count("Enviar solicitação") == 2


def test_opcoes_das_selecoes(client):
    html = _html(client)
    for opcao in OPCOES:
        assert opcao in html, f"opção ausente: {opcao}"


def test_placeholders_sao_exemplos(client):
    coletor = ColetorPlaceholders()
    coletor.feed(_html(client))
    assert len(coletor.placeholders) >= 20
    for placeholder in coletor.placeholders:
        assert placeholder.strip()
        assert placeholder not in ROTULOS


def test_cabecalho_institucional(client):
    html = _html(client)
    folhas = re.findall(r'href="([^"]+\.css)"', html)
    conteudo = html + "".join(_local(client, folha).text for folha in folhas)
    assert "usp-logo.png" in conteudo
    assert "Universidade de São Paulo" in conteudo


def test_todos_os_arquivos_referenciados_sao_servidos(client):
    html = _html(client)
    referencias = [
        r
        for r in re.findall(r'(?:href|src)="([^"]+)"', html)
        if r.endswith((".css", ".js", ".png"))
        and not r.startswith(("http://", "https://", "data:"))
    ]
    assert any(r.endswith(".css") for r in referencias)
    assert any(r.endswith(".js") for r in referencias)
    assert any(r.endswith(".png") for r in referencias)
    for caminho in referencias:
        assert _local(client, caminho).status_code == 200, caminho


def test_imagens_apenas_o_logotipo(client):
    html = _html(client)
    imagens = re.findall(r'<img[^>]+src="([^"]+)"', html)
    assert all("usp-logo" in caminho for caminho in imagens)


def test_titulo_da_confirmacao_esta_no_frontend(client):
    html = _html(client)
    scripts = re.findall(r'src="([^"]+\.js)"', html)
    conteudo = html + "".join(_local(client, script).text for script in scripts)
    assert "Solicitação registrada" in conteudo
