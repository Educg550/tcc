from pathlib import Path
import re

import pytest

RAIZ = Path(__file__).resolve().parents[1]

ROTULOS_SOLICITANTE = [
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
]

ROTULOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]

ROTULOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

TITULOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS = ROTULOS_SOLICITANTE + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO + TITULOS_BLOCOS


def _arquivo(nome):
    candidatos = [RAIZ / nome, RAIZ / "static" / nome, RAIZ / "frontend" / nome]
    for caminho in candidatos:
        if caminho.is_file():
            return caminho.read_text(encoding="utf-8")
    encontrados = [p for p in RAIZ.rglob(nome) if p.is_file() and ".venv" not in p.parts]
    assert encontrados, f"{nome} não encontrado no projeto"
    return encontrados[0].read_text(encoding="utf-8")


HTML = _arquivo("index.html")
CSS = _arquivo("style.css")
JS = _arquivo("app.js")


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_rotulo_visivel_no_formulario(rotulo):
    assert rotulo in HTML


def test_cabecalho_institucional():
    assert "Universidade de São Paulo" in HTML
    assert "assets/usp-logo.png" in HTML


def test_abas_na_ordem_alunos_antes_de_docentes():
    assert "ALUNOS" in HTML
    assert "DOCENTES" in HTML
    assert HTML.index("ALUNOS") < HTML.index("DOCENTES")


def test_botao_enviar_em_cada_aba():
    assert HTML.count("Enviar solicitação") >= 2


def test_placeholders_sao_exemplos_e_nao_rotulos():
    valores = re.findall(r"placeholder\s*=\s*[\"']([^\"']*)[\"']", HTML)
    assert len(valores) >= 15
    assert not (set(valores) & set(ROTULOS))


def test_cores_da_identidade_usp():
    css = CSS.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_sem_serifa():
    assert "sans-serif" in CSS.lower()


def test_oficio_preserva_as_quebras_de_linha():
    assert "white-space" in CSS.lower() or "<pre" in HTML.lower()


def test_oficio_com_os_textos_do_requisito():
    texto = "\n".join([HTML, CSS, JS, _arquivo("app.py")])
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
    assert "Dados do evento" in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Dados para pagamento" in texto
    assert "Verba do programa" in texto
