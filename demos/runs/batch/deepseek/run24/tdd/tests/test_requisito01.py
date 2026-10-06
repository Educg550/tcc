from pathlib import Path

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


ROTULOS_CAMPOS = [
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

TITULOS_BLOCOS = [
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

MENSAGENS_ERRO = [
    "Preencha todos os campos",
    "N. USP deve conter apenas números",
    "Número da agência deve conter apenas números",
    "Valor solicitado deve ser maior que 0",
    "E-mail inválido",
    "CPF deve estar no formato 000.000.000-00",
    "CEP deve estar no formato 00000-000",
    "Data de nascimento deve estar no formato dd/mm/aaaa",
    "CPF inválido",
    "Data de nascimento inválida",
]

TRECHOS_OFICIO = [
    "Interessada(o):",
    "Assunto: Solicitação de Auxílio Financeiro",
    "Verba do programa",
    "Dados do evento",
    "Endereço da(o) interessada(o)",
    "Dados para pagamento",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def _texto(url):
    resposta = client.get(url)
    assert resposta.status_code == 200, url
    return resposta.text


def _backend():
    return "\n".join(
        caminho.read_text(encoding="utf-8") for caminho in Path(".").glob("*.py")
    )


def _tudo():
    return _texto("/") + _texto("/style.css") + _texto("/app.js") + _backend()


def test_pagina_inicial_responde():
    assert client.get("/").status_code == 200


def test_cabecalho_institucional():
    pagina = _texto("/")
    assert "Universidade de São Paulo" in pagina
    assert "usp-logo.png" in pagina


def test_abas_alunos_e_docentes_nessa_ordem():
    pagina = _texto("/")
    fonte = pagina if ("ALUNOS" in pagina and "DOCENTES" in pagina) else _texto("/app.js")
    assert "ALUNOS" in fonte
    assert "DOCENTES" in fonte
    assert fonte.index("ALUNOS") < fonte.index("DOCENTES")


def test_titulos_dos_blocos():
    pagina = _texto("/")
    for titulo in TITULOS_BLOCOS:
        assert titulo in pagina


def test_rotulos_dos_campos():
    pagina = _texto("/")
    for rotulo in ROTULOS_CAMPOS:
        assert rotulo in pagina


def test_opcoes_de_selecao():
    pagina = _texto("/")
    for opcao in OPCOES:
        assert opcao in pagina


def test_botao_enviar():
    assert "Enviar solicitação" in _texto("/")


def test_cores_da_universidade():
    css = _texto("/style.css").lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_sem_serifa():
    assert "sans-serif" in _texto("/style.css").lower()


def test_sem_brasao():
    pagina = _texto("/").lower()
    assert "brasao" not in pagina
    assert "brasão" not in pagina
    assert "escudo" not in pagina


def test_campos_com_placeholder():
    texto = (_texto("/") + _texto("/app.js")).lower()
    assert "placeholder" in texto


def test_mensagens_de_erro():
    tudo = _tudo()
    for mensagem in MENSAGENS_ERRO:
        assert mensagem in tudo


def test_titulo_da_confirmacao():
    assert "Solicitação registrada" in _tudo()


def test_trechos_do_oficio():
    tudo = _tudo()
    for trecho in TRECHOS_OFICIO:
        assert trecho in tudo
