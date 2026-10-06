import re

import pytest


ALL_LABELS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NIVEL",
    "TIPO DE AUXILIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERIODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAIS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRA APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NUMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRACO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRACO)",
    "NOME DO BANCO",
    "NUMERO DA AGENCIA",
    "NUMERO DA CONTA",
]

BLOCKS = ["SOLICITANTE E EVENTO", "ENDERECO DO SOLICITANTE", "INFORMACOES PARA PAGAMENTO / REEMBOLSO"]


def test_tabs_present(html):
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_tab_initial_active(html):
    m = re.search(r'<[^>]+data-tab=["\']alunos["\'][^>]*class=["\']([^"]*)["\']', html, re.I)
    assert m is not None
    assert "active" in m.group(1)


def test_blocks_present(html):
    for b in BLOCKS:
        assert b in html


@pytest.mark.parametrize("label", ALL_LABELS)
def test_label_present(html, labels, label):
    assert label in labels


def test_level_only_alunos(labels):
    assert labels.count("NIVEL") == 1
    assert labels.count("TIPO DE AUXILIO") == 1


def test_send_button_two_times(html):
    assert html.count("Enviar solicitacao") == 2


def test_select_options(html):
    assert re.search(r"<select[^>]*>(?:(?!</select>).)*Mestrado", html, re.S | re.I) is not None
    assert re.search(r"<select[^>]*>(?:(?!</select>).)*Doutorado", html, re.S | re.I) is not None
    for opt in ("Participacao em evento", "Banca de exame ou defesa", "Outro", "Poster", "Apresentacao oral", "Nao ira apresentar trabalho"):
        assert opt in html


def test_placeholders(html):
    assert html.count("placeholder=") >= len(ALL_LABELS)


def test_assets_logotipo_referenced(html):
    assert "assets/usp-logo.png" in html


def test_no_remote_or_framework(html, css, js):
    assert "cdn" not in html.lower()
    assert "@import" not in css.lower()
    assert "http://" not in css.lower()
    assert "https://" not in css.lower()
    assert "http://" not in js.lower()
    assert "https://" not in js.lower()
