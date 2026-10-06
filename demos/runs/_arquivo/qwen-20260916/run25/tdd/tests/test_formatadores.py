import re

from conftest import texto_de_app_js

CAMPOS_FORMATADOS = (
    "VALOR SOLICITADO (R$)",
    "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "CEP",
    "DATA DE NASCIMENTO",
)


def _funcao(nome):
    texto = texto_de_app_js()
    inicio = re.search(r"(?:^|\s)(?:function|const|let|var)\s+" + nome + r"\b", texto)
    assert inicio, "n\u00e3o encontrada a fun\u00e7\u00e3o %s em app.js" % nome
    corpo = texto[inicio.start() :]
    chaves, fim, dentro_de_string = 0, None, None
    for i, ch in enumerate(corpo):
        if dentro_de_string:
            if ch == "\\\\":
                continue
            if ch == dentro_de_string:
                dentro_de_string = None
            continue
        if ch in "\"'`":
            dentro_de_string = ch
            continue
        if ch == "{":
            chaves += 1
        elif ch == "}":
            chaves -= 1
            if chaves == 0:
                fim = i
                break
    assert fim is not None
    return corpo[: fim + 1]


def _executa(nome, valor):
    codigo = _funcao(nome) + "\nreturn " + nome + "(arguments[0]);"
    return js_ctx.call(codigo, valor)


import pytest

try:
    import jscontext
except Exception:
    js_ctx = pytest.skip("sem JS", allow_module_level=True)
else:
    js_ctx = jscontext.JSContext(texto_de_app_js())


def test_mostra_valor_em_moeda_brasileira():
    assert _executa("formatarValor", "1500") == "R$ 15,00"


def test_valor_com_milhar():
    assert _executa("formatarValor", "150000") == "R$ 1.500,00"


def test_valor_com_dois_pontos_de_milhar():
    assert _executa("formatarValor", "150000000") == "R$ 1.500.000,00"


def test_mostra_cpf_formatado():
    assert _executa("formatarCpf", "12345678909") == "123.456.789-09"


def test_mostra_cep_formatado():
    assert _executa("formatarCep", "05508090") == "05508-090"


def test_mostra_data_formatada():
    assert _executa("formatarData", "01021980") == "01/02/1980"


def test_formatadores_estao_ligados_ao_evento_blur():
    texto = texto_de_app_js()
    assert "blur" in texto
    for nome in ("formatarValor", "formatarCpf", "formatarCep", "formatarData"):
        assert nome in texto


def test_quatro_campos_recebem_formatador():
    texto = texto_de_app_js()
    for campo in CAMPOS_FORMATADOS:
        assert campo in texto
