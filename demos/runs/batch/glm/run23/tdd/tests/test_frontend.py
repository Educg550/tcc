"""Testes para o frontend estático (index.html, style.css, app.js)."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ler(caminho):
    return (RAIZ / caminho).read_text(encoding="utf-8")


def test_arquivos_existem():
    for nome in ("index.html", "style.css", "app.js"):
        assert (RAIZ / nome).is_file(), f"Falta {nome} na raiz"


def test_html_e_valido():
    html = ler("index.html")
    assert "<!doctype html>" in html.lower()
    assert "<html" in html
    assert "</html>" in html


def test_style_e_app_sao_estaticos():
    """Nenhum dos três arquivos é gerado por Python."""
    for nome in ("index.html", "style.css", "app.js"):
        conteudo = ler(nome)
        assert "{{" not in conteudo, f"{nome} parece template gerado"


def test_estilos_e_script_sao_locais():
    html = ler("index.html")
    assert 'href="style.css"' in html
    assert 'src="app.js"' in html
    assert "http://" not in html and "https://" not in html


def test_aba_alunos_e_docentes():
    html = ler("index.html")
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_rotulos_dos_campos():
    html = ler("index.html")
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
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "SOLICITANTE E EVENTO",
        "Enviar solicitação",
    ]
    for rotulo in rotulos:
        assert rotulo in html, f"Falta rótulo {rotulo!r}"


def test_dois_formularios_dois_botoes():
    html = ler("index.html")
    assert html.count("<form") >= 2
    assert html.count("Enviar solicitação") == 2


def test_campos_exclusivos_dos_alunos():
    """NÍVEL e TIPO DE AUXÍLIO existem e pertencem ao formulário de ALUNOS."""
    html = ler("index.html")
    m_alunos = re.search(r"id=[\"']?form-alunos", html)
    assert m_alunos, "Formulário de alunos não identificado"
    # trecho do html até o próximo form
    inicio = m_alunos.end()
    fim = html.find("<form", inicio)
    trecho_alunos = html[inicio: fim if fim != -1 else len(html)]
    assert "NÍVEL" in trecho_alunos
    assert "TIPO DE AUXÍLIO" in trecho_alunos
    # a partir do form seguinte não deve existir NÍVEL
    restante = html[fim:] if fim != -1 else ""
    assert "NÍVEL" not in restante
    assert "TIPO DE AUXÍLIO" not in restante


def test_titulos_de_blocos_visiveis():
    html = ler("index.html")
    for bloco in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert html.count(bloco) == 2, f"Bloco {bloco!r} deveria aparecer nas duas abas"


def test_css_tem_variaveis_de_cor():
    css = ler("style.css")
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, f"Cor {cor} ausente no style.css"


def test_css_usa_fonte_sem_serifa():
    css = ler("style.css")
    assert "sans-serif" in css


def test_layout_em_colunas():
    css = ler("style.css")
    assert "grid" in css or "flex" in css


def test_app_js_existe_e_tem_tamanho_esperado():
    js = ler("app.js")
    assert len(js) > 100, "app.js parece implementação vazia"