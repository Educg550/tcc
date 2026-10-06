import re

TITULOS_DOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


def _visivel(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def test_abas_com_rotulos_exatos_nessa_ordem(pagina):
    visivel = _visivel(pagina)
    assert "ALUNOS" in visivel
    assert "DOCENTES" in visivel
    assert visivel.index("ALUNOS") < visivel.index("DOCENTES")


def test_cabecalho_institucional_com_nome_e_logotipo(pagina):
    assert "Universidade de São Paulo" in _visivel(pagina)
    imagens = re.findall(r'<img[^>]+src="([^"]+)"', pagina.replace("'", '"'))
    assert any("usp-logo" in imagem for imagem in imagens), (
        "o cabeçalho não traz assets/usp-logo.png"
    )
    for imagem in imagens:
        assert "usp-logo" in imagem, "só o logotipo da USP pode aparecer na página"


def test_logotipo_referenciado_e_servido(cliente, pagina):
    logo = re.search(r'<img[^>]+src="([^"]*usp-logo[^"]*)"', pagina.replace("'", '"'))
    assert logo, "a página não usa o assets/usp-logo.png"
    resposta = cliente.get(logo.group(1))
    assert resposta.status_code == 200
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_titulos_dos_blocos_e_rotulos_exatos(pagina, rotulos_alunos):
    visivel = _visivel(pagina)
    for titulo in TITULOS_DOS_BLOCOS:
        assert titulo in visivel, f"título de bloco ausente: {titulo}"
    for rotulo in rotulos_alunos:
        assert rotulo in visivel, f"rótulo ausente: {rotulo}"


def test_rotulos_na_ordem_do_requisito(pagina, rotulos_alunos):
    visivel = _visivel(pagina)
    posicao = -1
    for rotulo in rotulos_alunos:
        posicao = visivel.find(rotulo, posicao + 1)
        assert posicao != -1, f"rótulo ausente ou fora de ordem: {rotulo}"


def test_todo_campo_tem_placeholder_com_exemplo(pagina, estaticos, rotulos_alunos):
    _, js = estaticos
    fonte = pagina + js
    exemplos = re.findall(r'placeholder\s*=\s*"([^"]*)"', fonte)
    exemplos += re.findall(r"placeholder\s*=\s*'([^']*)'", fonte)
    assert len(exemplos) >= 40, "faltam placeholders nos campos"
    for exemplo in exemplos:
        assert exemplo.strip(), "há placeholder vazio"
        for rotulo in rotulos_alunos:
            assert exemplo.strip().casefold() != rotulo.casefold(), (
                f"placeholder repete o rótulo: {exemplo}"
            )


def test_nenhum_recurso_vem_da_rede(pagina, estaticos):
    css, js = estaticos
    tudo = pagina + css + js
    proibidos = [
        r'<script[^>]+src="https?:',
        r'<link[^>]+href="https?:',
        r'<img[^>]+src="https?:',
        r"@import\s+url\(\s*[\"']?https?:",
        r"url\(\s*[\"']?https?:",
        r"fonts\.googleapis",
        r"<iframe",
    ]
    for padrao in proibidos:
        assert not re.search(padrao, tudo, re.IGNORECASE), (
            f"referência externa proibida: {padrao}"
        )


def test_identidade_visual_da_usp(estaticos):
    css, _ = estaticos
    css = css.lower()
    assert "#1094ab" in css, "falta o azul primário #1094ab"
    assert "#64c4d2" in css or "#fcb421" in css, "faltam as cores de apoio"
    assert "open sans" in css or "sans-serif" in css, "falta a fonte sem serifa"


def test_titulo_da_confirmacao(pagina, estaticos):
    _, js = estaticos
    assert "Solicitação registrada" in pagina or "Solicitação registrada" in js
