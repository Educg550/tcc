from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ler(nome):
    return (RAIZ / nome).read_text(encoding="utf-8")


def test_abas_com_rotulos_exatos_e_nessa_ordem():
    html = ler("index.html")
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos():
    html = ler("index.html")
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in html, titulo


def test_rotulos_dos_campos():
    html = ler("index.html")
    for rotulo in (
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
    ):
        assert rotulo in html, rotulo


def test_botao_enviar_e_titulo_da_confirmacao():
    assert "Enviar solicitação" in ler("index.html")
    assert "Solicitação registrada" in ler("index.html") + ler("app.js")


def test_cabecalho_institucional_com_o_logotipo():
    html = ler("index.html")
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html + ler("style.css")


def test_cores_da_universidade_no_css():
    css = ler("style.css").lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_sem_serifa():
    tela = (ler("index.html") + ler("style.css")).lower()
    assert "open sans" in tela or "sans-serif" in tela
