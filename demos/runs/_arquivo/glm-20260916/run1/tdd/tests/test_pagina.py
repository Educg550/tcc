"""A tela servida: abas, rótulos, blocos, placeholders e identidade visual."""

import re

ROTULOS_ALUNOS = [
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


def test_pagina_e_arquivos_estaticos_servidos(client):
    assert client.get("/").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_logotipo_da_usp_servido(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def test_cabecalho_institucional(html, css):
    assert "usp-logo.png" in html or "usp-logo" in css
    assert "Universidade de São Paulo" in html
    assert "Pós-Graduação" in html or "IME" in html


def test_abas_com_rotulos_exatos_nessa_ordem(pagina):
    alunos = pagina.find("ALUNOS")
    docentes = pagina.find("DOCENTES")
    assert alunos != -1
    assert docentes != -1
    assert alunos < docentes


def test_aba_alunos_ativa_ao_abrir(html):
    if "ALUNOS" not in html:
        return
    trecho = html[: html.index("DOCENTES")]
    ativa = re.search(
        r'class\s*=\s*["\'][^"\']*\b(ativa|active)\b'
        r'|aria-selected\s*=\s*["\']true'
        r"|data-(?:ativa|active)\b",
        trecho,
        re.IGNORECASE,
    )
    assert ativa


def test_blocos_com_titulo_visivel(pagina):
    for bloco in BLOCOS:
        assert bloco in pagina


def test_rotulos_exatos_na_ordem_na_aba_alunos(pagina):
    pos = 0
    for rotulo in ROTULOS_ALUNOS:
        i = pagina.find(rotulo, pos)
        assert i != -1, "rótulo ausente ou fora de ordem: " + rotulo
        pos = i + len(rotulo)


def test_opcoes_das_selecoes(pagina):
    for opcao in OPCOES:
        assert opcao in pagina


def test_campos_de_aluno_nao_aparecem_na_aba_docentes(html):
    if "NÍVEL" not in html:
        return
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


def test_aba_docentes_tem_os_mesmos_campos(html):
    comuns = [r for r in ROTULOS_ALUNOS if r not in ("NÍVEL", "TIPO DE AUXÍLIO")]
    for rotulo in comuns:
        if rotulo in html:
            assert html.count(rotulo) >= 2, rotulo + " deve aparecer nas duas abas"


def test_botao_enviar_em_cada_aba(pagina):
    assert pagina.count("Enviar solicitação") >= 2


def test_todo_campo_tem_placeholder_de_exemplo(pagina):
    rotulos = set(ROTULOS_ALUNOS)
    marcadores = re.findall(r'placeholder\s*=\s*"([^"]+)"', pagina)
    marcadores += re.findall(r"placeholder\s*=\s*'([^']+)'", pagina)
    assert len(marcadores) >= 30
    for marcador in marcadores:
        assert marcador not in rotulos


def test_titulo_da_confirmacao(pagina):
    assert "Solicitação registrada" in pagina


def test_oficio_preserva_quebras_de_linha(pagina, css):
    preserva = (
        re.search(r"white-space\s*:\s*pre", css, re.IGNORECASE)
        or re.search(r"<pre[\s>]", pagina, re.IGNORECASE)
        or re.search(r"<br", pagina, re.IGNORECASE)
    )
    assert preserva


def test_cores_da_identidade_usp(css):
    baixo = css.lower()
    assert "#1094ab" in baixo
    assert "#64c4d2" in baixo
    assert "#fcb421" in baixo


def test_fonte_open_sans_ou_outra_sem_serifa(css):
    baixo = css.lower()
    assert "open sans" in baixo or "sans-serif" in baixo


def test_campos_distribuidos_em_colunas(css):
    assert re.search(r"grid|flex", css, re.IGNORECASE)


def test_nenhum_recurso_vem_da_rede(html, css):
    externos = re.findall(
        r"<(?:script|img|link|source|iframe)[^>]+(?:src|href)\s*=\s*[\"']https?://",
        html,
    )
    assert externos == []
    assert not re.search(r"@import\s+(?:url\(\s*)?[\"']?https?://", css)
    assert not re.search(r"url\(\s*[\"']?https?://", css)
