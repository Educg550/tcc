from conftest import client, html_da_pagina, texto_de_app_js, texto_de_style_css


def test_rota_raiz_responde():
    assert client().get("/").status_code == 200


def test_abas_e_botao_enviar():
    html = html_da_pagina()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")
    assert html.count("Enviar solicita\u00e7\u00e3o") == 2


def test_titulos_dos_blocos():
    html = html_da_pagina()
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDERE\u00c7O DO SOLICITANTE" in html
    assert "INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO" in html


def test_rotulos_obrigatorios():
    html = html_da_pagina()
    for rotulo in (
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "N\u00daMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "NOME DO BANCO",
        "N\u00daMERO DA AG\u00caNCIA",
        "N\u00daMERO DA CONTA",
    ):
        assert rotulo in html


def test_rotulos_exclusivos_da_aba_alunos():
    html = html_da_pagina()
    assert "N\u00cdVEL" in html
    assert "TIPO DE AUX\u00cdLIO" in html


def test_opcoes_de_selecao():
    html = html_da_pagina()
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participa\u00e7\u00e3o em evento",
        "Banca de exame ou defesa",
        "Outro",
        "P\u00f4ster",
        "Apresenta\u00e7\u00e3o oral",
        "N\u00e3o ir\u00e1 apresentar trabalho",
    ):
        assert opcao in html


def test_cabecalho_institucional():
    html = html_da_pagina()
    assert "assets/usp-logo.png" in html
    assert "Universidade de S\u00e3o Paulo" in html


def test_ambiente_de_execucao_naotem_recurso_externo():
    html = html_da_pagina() + texto_de_app_js() + texto_de_style_css()
    for marcador in ("http://", "https://", "//cdn"):
        assert marcador not in html


def test_paleta_institucional_no_css():
    css = texto_de_style_css()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css
    assert "Open Sans" in css
