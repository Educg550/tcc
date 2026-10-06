import app as app_module
from fastapi.testclient import TestClient

cliente = TestClient(app_module.app)

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

BLOCOS = [
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

CAMINHOS_CSS = ["/style.css", "/static/style.css", "/css/style.css"]
CAMINHOS_JS = ["/app.js", "/static/app.js", "/js/app.js"]
CAMINHOS_HTML = ["/", "/index.html"]


def buscar(caminhos):
    for caminho in caminhos:
        resposta = cliente.get(caminho)
        if resposta.status_code == 200:
            return resposta.text
    return None


def pagina():
    return (buscar(CAMINHOS_HTML) or "") + "\n" + (buscar(CAMINHOS_JS) or "")


def test_serve_o_index():
    assert buscar(CAMINHOS_HTML) is not None


def test_serve_o_css():
    assert buscar(CAMINHOS_CSS) is not None


def test_serve_o_js():
    assert buscar(CAMINHOS_JS) is not None


def test_serve_o_logotipo():
    assert buscar(["/assets/usp-logo.png", "/static/assets/usp-logo.png", "assets/usp-logo.png"]) is not None


def test_abas_na_ordem():
    html = buscar(CAMINHOS_HTML) or ""
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_rotulos_dos_campos():
    texto = pagina()
    faltando = [rotulo for rotulo in ROTULOS if rotulo not in texto]
    assert faltando == []


def test_titulos_dos_blocos():
    texto = pagina()
    faltando = [bloco for bloco in BLOCOS if bloco not in texto]
    assert faltando == []


def test_opcoes_de_selecao():
    texto = pagina()
    faltando = [opcao for opcao in OPCOES if opcao not in texto]
    assert faltando == []


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in pagina()


def test_cabecalho_institucional():
    html = buscar(CAMINHOS_HTML) or ""
    assert "universidade de são paulo" in html.lower()
    assert "usp-logo.png" in html


def test_sem_brasao():
    texto = pagina().lower()
    assert "brasão" not in texto
    assert "brasao" not in texto
    assert "escudo" not in texto


def test_cor_azul_primaria():
    css = buscar(CAMINHOS_CSS) or ""
    assert "#1094ab" in css.lower()


def test_fonte_sem_serifa():
    css = buscar(CAMINHOS_CSS) or ""
    assert "sans-serif" in css.lower()


def test_sem_recurso_de_cdn():
    texto = (pagina() + (buscar(CAMINHOS_CSS) or "")).lower()
    for host in ["cdnjs", "jsdelivr", "unpkg", "googleapis", "fonts.gstatic", "bootstrapcdn"]:
        assert host not in texto


def test_titulo_da_confirmacao():
    assert "Solicitação registrada" in pagina()
