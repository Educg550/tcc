import re

import pytest

from tests.conftest import field_id, find_tag, form_block, has_field_in_form, label_for, select_options

TABS = ["ALUNOS", "DOCENTES"]
LABELS_SOLICITANTE = [
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
]
LABELS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]
LABELS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
ALL_LABELS = LABELS_SOLICITANTE + LABELS_ENDERECO + LABELS_PAGAMENTO


def test_tabs_in_order(html):
    ids = re.findall(r'<button[^>]*data-tab[^>]*id="([^"]+)"', html)
    assert ids == ["ALUNOS", "DOCENTES"]


def test_active_tab_on_load(html):
    assert 'class="tab active" id="ALUNOS"' in html or 'id="ALUNOS" class="tab active"' in html


def test_alunos_form(html):
    f = form_block(html, "alunos")
    for lbl in ALL_LABELS:
        assert has_field_in_form(html, "alunos", lbl), lbl
    assert has_field_in_form(html, "alunos", "NÍVEL")
    assert has_field_in_form(html, "alunos", "TIPO DE AUXÍLIO")


def test_docentes_form(html):
    f = form_block(html, "docentes")
    for lbl in ALL_LABELS:
        assert has_field_in_form(html, "docentes", lbl), lbl
    assert not has_field_in_form(html, "docentes", "NÍVEL")
    assert not has_field_in_form(html, "docentes", "TIPO DE AUXÍLIO")


def test_select_options(html):
    assert set(select_options(html, "NÍVEL")) == {"", "Mestrado", "Doutorado"}
    assert set(select_options(html, "TIPO DE AUXÍLIO")) == {"", "Participação em evento", "Banca de exame ou defesa", "Outro"}
    assert set(select_options(html, "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?")) == {
        "", "Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho",
    }


def test_block_titles(html):
    for t in ["SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"]:
        assert t in html


def test_placeholders(html):
    for lbl in ALL_LABELS:
        fid = field_id(html, lbl)
        m = re.search(r'<[^>]*\bid="' + re.escape(fid) + r'"[^>]*placeholder="([^"]+)"', html)
        assert m, lbl
        p = m.group(1)
        assert p.strip(), lbl
        assert p != lbl, lbl


def test_input_types(html):
    assert find_tag(html, "input", "id", field_id(html, "N. USP")).lower().count('type="number"') + find_tag(html, "input", "id", field_id(html, "N. USP")).lower().count('type="text"') >= 1
    assert 'inputmode="numeric"' in find_tag(html, "input", "id", field_id(html, "N. USP")).lower()
    assert find_tag(html, "input", "id", field_id(html, "E-MAIL")).lower().count('type="email"') >= 1
    assert 'type="number"' in find_tag(html, "input", "id", field_id(html, "NÚMERO DA AGÊNCIA")).lower()


def test_required(html):
    for lbl in ALL_LABELS:
        if lbl in ["LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"]:
            continue
        fid = field_id(html, lbl)
        m = re.search(r'<[^>]*\bid="' + re.escape(fid) + r'"[^>]*>', html)
        assert m and 'required' in m.group(0).lower(), lbl


def test_submit_button(html):
    assert html.count("Enviar solicitação") == 2


def test_labels_match(html):
    for lbl in ALL_LABELS:
        fid = field_id(html, lbl)
        assert label_for(html, fid) == lbl
