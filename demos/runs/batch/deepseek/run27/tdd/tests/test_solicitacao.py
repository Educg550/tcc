"""Testes da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

import pytest
from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

ROTULOS = [
    "SOLICITANTE E EVENTO",
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
    "ENDEREÇO DO SOLICITANTE",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

VALORES_ALUNOS = {
    "aba": "alunos",
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "12345678",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.silva@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Simpósio Brasileiro de Computação",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10 a 12 de março de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.exemplo.br",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Inscrição e hospedagem.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Bloco B",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "111.444.777-35",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "12345-6",
}

VALORES_DOCENTES = {
    chave: valor
    for chave, valor in VALORES_ALUNOS.items()
    if chave not in ("NÍVEL", "TIPO DE AUXÍLIO")
}
VALORES_DOCENTES["aba"] = "docentes"

LINHAS_DO_OFICIO = [
    "Interessada(o): Maria da Silva - 12345678",
    "E-mail: maria.silva@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "Dados do evento",
    "Evento: Simpósio Brasileiro de Computação",
    "Período: 10 a 12 de março de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://evento.exemplo.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição e hospedagem.",
    "Endereço da(o) interessada(o)",
    "Rua do Matão, 1010",
    "Complemento: Bloco B",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 111.444.777-35",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 12345-6",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def _strings(obj):
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for valor in obj.values() for s in _strings(valor)]
    if isinstance(obj, list):
        return [s for item in obj for s in _strings(item)]
    return []


def _texto(resposta):
    try:
        dados = resposta.json()
    except ValueError:
        return resposta.text
    return "\n".join(_strings(dados))


def _rota_de_envio():
    for rota in app.routes:
        if "POST" in (getattr(rota, "methods", None) or set()):
            return rota.path
    pytest.fail("a aplicação não expõe nenhuma rota POST para receber a solicitação")


def _enviar(dados):
    return cliente.post(_rota_de_envio(), json=dados)


def test_pagina_inicial_mostra_as_duas_abas():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    pagina = resposta.text
    assert "ALUNOS" in pagina
    assert "DOCENTES" in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")
    assert pagina.count("Enviar solicitação") >= 2


def test_formulario_traz_os_blocos_e_rotulos_exatos():
    pagina = cliente.get("/").text
    for rotulo in ROTULOS:
        assert rotulo in pagina, rotulo


def test_todo_campo_tem_placeholder_de_exemplo():
    pagina = cliente.get("/").text
    placeholders = re.findall(r'placeholder="([^"]*)"', pagina)
    assert placeholders
    assert all(texto.strip() for texto in placeholders)
    assert not set(placeholders) & set(ROTULOS)


def test_identidade_visual_da_universidade():
    pagina = cliente.get("/").text
    assert "assets/usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina
    logo = cliente.get("/assets/usp-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"].startswith("image/")
    css = cliente.get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, cor


def test_pagina_nao_carrega_recursos_externos():
    for caminho in ("/", "/style.css", "/app.js"):
        conteudo = cliente.get(caminho).text
        assert not re.search(r'(?:src|href)="https?://', conteudo), caminho
        assert not re.search(r'url\(\s*["\']?https?://', conteudo), caminho


def test_oficio_de_alunos_com_dados_preenchidos():
    resposta = _enviar(VALORES_ALUNOS)
    assert resposta.status_code == 200
    texto = _texto(resposta)
    for linha in LINHAS_DO_OFICIO:
        assert linha in texto, linha
    assert "<<" not in texto


def test_oficio_de_docentes_usa_a_verba_do_programa():
    resposta = _enviar(VALORES_DOCENTES)
    assert resposta.status_code == 200
    texto = _texto(resposta)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação -" not in texto
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "CPF: 111.444.777-35" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
    assert "<<" not in texto


def test_linhas_opcionais_somem_quando_vazias():
    valores = dict(VALORES_ALUNOS)
    valores["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    valores["COMPLEMENTO"] = ""
    texto = _texto(_enviar(valores))
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    valores = dict(VALORES_ALUNOS)
    valores["PROGRAMA"] = ""
    valores["NOME DO BANCO"] = ""
    texto = _texto(_enviar(valores))
    assert texto.count("Preencha todos os campos") == 1
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


@pytest.mark.parametrize(
    "campo, valor, mensagem",
    [
        ("N. USP", "12A45678", "N. USP deve conter apenas números"),
        ("NÚMERO DA AGÊNCIA", "12A4", "Número da agência deve conter apenas números"),
        ("VALOR SOLICITADO (R$)", "0", "Valor solicitado deve ser maior que 0"),
        ("E-MAIL", "maria.silva", "E-mail inválido"),
        ("E-MAIL", "maria@usp", "E-mail inválido"),
        (
            "CPF (SEPARADOS POR PONTOS E TRAÇO)",
            "111.444.777-3",
            "CPF deve estar no formato 000.000.000-00",
        ),
        ("CEP", "05508-09", "CEP deve estar no formato 00000-000"),
        (
            "DATA DE NASCIMENTO",
            "01-02-1980",
            "Data de nascimento deve estar no formato dd/mm/aaaa",
        ),
        ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "111.444.777-34", "CPF inválido"),
        ("DATA DE NASCIMENTO", "31/02/1980", "Data de nascimento inválida"),
    ],
)
def test_validacao_por_campo(campo, valor, mensagem):
    valores = dict(VALORES_ALUNOS)
    valores[campo] = valor
    texto = _texto(_enviar(valores))
    assert mensagem in texto
    assert "Encaminhe-se ao Serviço Financeiro" not in texto


def test_erros_simultaneos_aparecem_juntos():
    valores = dict(VALORES_ALUNOS)
    valores["E-MAIL"] = "maria.silva"
    valores["N. USP"] = "12A45678"
    texto = _texto(_enviar(valores))
    assert "E-mail inválido" in texto
    assert "N. USP deve conter apenas números" in texto
