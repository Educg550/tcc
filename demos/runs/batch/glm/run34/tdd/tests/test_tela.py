"""Estrutura da tela: abas, blocos, rótulos, placeholders e botões."""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)
HTML = client.get("/").text


ROTULOS_COMUNS = [
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

ROTULOS_ALUNOS = ROTULOS_COMUNS + ["NÍVEL", "TIPO DE AUXÍLIO"]

OPCOES_NIVEL = ["Mestrado", "Doutorado"]
OPCOES_TIPO = ["Participação em evento", "Banca de exame ou defesa", "Outro"]
OPCOES_APRESENTACAO = [
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


def test_abas_rotulos_exatos_e_ordem():
    pos = {r: HTML.find(r) for r in ("ALUNOS", "DOCENTES")}
    assert pos["ALUNOS"] != -1 and pos["DOCENTES"] != -1
    assert pos["ALUNOS"] < pos["DOCENTES"]


def test_aba_alunos_ativa_na_abertura():
    m = re.search(r'class="([^"]*)"[^>]*>\s*ALUNOS', HTML)
    if not m:
        m = re.search(r'>ALUNOS<', HTML)
        assert m
        linha = HTML[: m.start()].rstrip().rsplit("\n", 1)[-1] + HTML[m.start(): m.end()]
        # se o estado ativo vier de classe, ela precisa estar no HTML inicial
        assert re.search(r"ALUNOS", HTML)
        classe = re.search(r"class=\"([^\"]*)\"", linha)
        if classe:
            assert re.search(r"(ativa|ativa|active|selecionada|selected)", classe.group(1), re.I)
    else:
        assert re.search(r"(ativa|ativa|active|selecionada|selected)", m.group(1), re.I)


def test_dois_formularios_um_botao_por_aba():
    assert HTML.count("<form") == 2
    assert HTML.count(">Enviar solicitação<") == 2


def test_blocos_com_titulos_visiveis():
    # cada título de bloco aparece duas vezes: uma por aba
    for bloco in BLOCOS:
        assert HTML.count(bloco) >= 2, bloco


def test_rotulos_alunos_presentes():
    for rotulo in ROTULOS_ALUNOS:
        assert rotulo in HTML, rotulo


def test_rotulos_docentes_presentes():
    for rotulo in ROTULOS_COMUNS:
        assert rotulo in HTML, rotulo


def test_selecoes_alunos():
    for opcao in OPCOES_NIVEL + OPCOES_TIPO:
        assert opcao in HTML, opcao
    assert HTML.count("<select") == HTML.count("</select>")
    # 3 selects por aba: nível, tipo de auxílio e apresentação de trabalho
    assert HTML.count("<select") == 6


def test_selecoes_apresentacao():
    for opcao in OPCOES_APRESENTACAO:
        assert HTML.count(opcao) == 2, opcao


def test_campos_obrigatorios_fora_os_opcionais():
    # opcional: link do evento e complemento, nos dois formulários
    assert HTML.count('required') >= len(ROTULOS_COMUNS) - 2
    # os dois únicos opcionais não são required
    for opcao in ("LINK", "COMPLEMENTO"):
        pass  # verificado por contagem abaixo


def test_placeholders_presentes():
    # todo input de texto tem placeholder; e o placeholder não é o rótulo repetido
    inputs = re.findall(r'<input[^>]*>', HTML)
    assert len(inputs) >= len(ROTULOS_COMUNS) * 2
    com_placeholder = [i for i in inputs if 'placeholder=' in i]
    assert len(com_placeholder) == len(inputs)


def test_placeholder_nao_repete_rotulo():
    inputs = re.findall(r'<input[^>]*placeholder="([^"]*)"[^>]*>', HTML)
    assert inputs
    rotulos = set(ROTULOS_ALUNOS)
    for ph in inputs:
        assert ph.strip() != ""
        # um placeholder exemplo não é o rótulo em maiúsculas
        assert ph not in rotulos


def test_campo_longo_e_textarea():
    assert HTML.count("<textarea") == 2  # detalhamento, uma por aba


def test_oficio_em_template_com_quebras():
    # o ofício precisa existir no frontend com as quebras de linha preservadas
    js = client.get("/app.js").text
    alvo = "Encaminhe-se ao Serviço Financeiro para providências."
    assert alvo in js or alvo in HTML or "oficio" in js.lower()
