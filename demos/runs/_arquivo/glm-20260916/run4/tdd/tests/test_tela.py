import re

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS_EM_ORDEM = [
    BLOCOS[0],
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
    BLOCOS[1],
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    BLOCOS[2],
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


def _compacto(texto):
    return re.sub(r"\s+", " ", texto)


def _posicao(pagina, trecho):
    achou = re.search(r">\s*" + re.escape(trecho) + r"\s*<", pagina)
    return achou.start() if achou else -1


def test_abas_com_rotulos_exatos_nessa_ordem(html):
    pagina = _compacto(html)
    alunos = _posicao(pagina, "ALUNOS")
    docentes = _posicao(pagina, "DOCENTES")
    assert alunos != -1, "aba com o rótulo exato ALUNOS não encontrada"
    assert docentes != -1, "aba com o rótulo exato DOCENTES não encontrada"
    assert alunos < docentes, "a aba ALUNOS deve vir antes da aba DOCENTES"


def test_titulos_dos_tres_blocos_visiveis(html):
    pagina = _compacto(html)
    faltando = [b for b in BLOCOS if _posicao(pagina, b) == -1]
    assert not faltando, f"títulos de bloco ausentes: {faltando}"


def test_rotulos_exatos_e_nessa_ordem(html):
    pagina = _compacto(html)
    faltando = []
    posicoes = []
    for rotulo in ROTULOS_EM_ORDEM:
        posicao = _posicao(pagina, rotulo)
        if posicao == -1:
            faltando.append(rotulo)
        else:
            posicoes.append(posicao)
    assert not faltando, f"rótulos ausentes: {faltando}"
    assert all(a < b for a, b in zip(posicoes, posicoes[1:])), "rótulos fora da ordem"


def test_opcoes_das_selecoes(html):
    pagina = _compacto(html)
    faltando = [o for o in OPCOES if _posicao(pagina, o) == -1]
    assert not faltando, f"opções de seleção ausentes: {faltando}"


def test_botao_enviar_solicitacao(html):
    assert "Enviar solicitação" in _compacto(html)


def test_cabecalho_institucional_com_logotipo(html):
    pagina = _compacto(html)
    assert "Universidade de São Paulo" in pagina
    assert "assets/usp-logo.png" in pagina


def test_titulo_da_confirmacao(html, js):
    assert "Solicitação registrada" in html or "Solicitação registrada" in js


def test_todo_campo_tem_placeholder_de_exemplo(html, js):
    fonte = html + js
    placeholders = re.findall(r"placeholder\s*[=:]\s*['\"]([^'\"]+)['\"]", fonte)
    assert len(placeholders) >= 20, "todo campo deve ter placeholder visível"
    rotulos = set(ROTULOS_EM_ORDEM) - set(BLOCOS)
    repetidos = [p for p in placeholders if p.strip() in rotulos]
    assert not repetidos, f"placeholder não deve repetir o rótulo: {repetidos}"


def test_sem_recursos_remotos(html, css):
    assert not re.search(r"<(?:script|link|img)[^>]*https?://", html)
    assert "http://" not in css
    assert "https://" not in css


def test_cores_da_identidade_usp(css):
    folha = css.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in folha, f"cor {cor} ausente do style.css"


def test_fonte_open_sans_com_fallback_sem_serifa(css):
    assert "Open Sans" in css
    assert "sans-serif" in css


def test_oficio_preserva_quebras_de_linha(css, js):
    com_pre = re.search(r"white-space\s*:\s*[^;{}]*pre", css, re.IGNORECASE)
    com_br = re.search(r"<br\b", js, re.IGNORECASE)
    assert com_pre or com_br, "o ofício deve preservar as quebras de linha"
