import re

LABELS = [
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


def test_cabecalho_institucional(cliente):
    pagina = cliente.get("/").text
    assert "assets/usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina


def test_abas_alunos_e_docentes_na_ordem(cliente):
    abas = re.findall(r">\s*(ALUNOS|DOCENTES)\s*<", cliente.get("/").text)
    assert abas[:2] == ["ALUNOS", "DOCENTES"]


def test_blocos_de_campos(cliente):
    pagina = cliente.get("/").text
    for bloco in BLOCOS:
        assert bloco in pagina


def test_rotulos_dos_campos(cliente):
    pagina = cliente.get("/").text
    for rotulo in LABELS:
        assert rotulo in pagina


def test_botao_enviar_em_cada_aba(cliente):
    pagina = cliente.get("/").text
    assert pagina.count("Enviar solicitação") >= 2


def test_campos_tem_placeholder_com_exemplo(cliente):
    pagina = cliente.get("/").text
    placeholders = re.findall(r'placeholder="([^"]*)"', pagina)
    assert len(placeholders) >= 25
    for placeholder in placeholders:
        assert placeholder.strip()
        assert placeholder not in LABELS


def test_arquivos_da_interface_e_do_logotipo(cliente):
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_identidade_visual_da_universidade(cliente):
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "sans-serif" in css


def test_titulo_da_confirmacao_no_frontend(cliente):
    frontend = cliente.get("/").text + cliente.get("/app.js").text
    assert "Solicitação registrada" in frontend
