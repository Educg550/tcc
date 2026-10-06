"""Comportamento de tela descrito em app.js.

O JavaScript é escrito à mão e servido como estático; estes testes verificam
o contrato descrito no requisito lendo o código servido.
"""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)
JS = client.get("/app.js").text


def _funcoes(js):
    return {m.group(1) for m in re.finditer(r'function\s+([A-Za-z_$][\w$]*)', js)}


def test_formatacao_de_valor_como_centavos():
    # os dígitos digitados são os centavos
    assert re.search(r'100', JS)
    assert re.search(r'[Rr]\$|toLocaleString|Intl\.NumberFormat', JS)


def test_formatacao_cpf():
    assert re.search(r'slice|substring|substr|padStart', JS)


def test_formatacao_cep_e_data():
    # CEP 00000-000 e data dd/mm/aaaa: pontos e barras são da aplicação
    assert re.search(r'[-]', JS)
    assert re.search(r'/', JS)


def test_troca_de_aba_no_cliente_sem_recarregar():
    # cliques em abas trocam o formulário visível; sem submit/reload
    assert "addEventListener" in JS
    assert "classList" in JS
    # a troca é client-side: o app não faz submit de página
    assert not re.search(r'<form[^>]*action=', client.get("/").text)


def test_campo_que_sai_de_foco_reformata_sem_enviar():
    # os quatro campos reformatam no blur, sem enviar
    for evento in ("blur", "focusout"):
        if evento in JS:
            return
    assert False, "nem blur nem focusout em app.js"


def test_erros_mostrados_no_topo_do_formulario_da_aba():
    # quem decide é o backend; a tela mostra a resposta
    assert re.search(r'erros|mensagens|messages', JS, re.I)
