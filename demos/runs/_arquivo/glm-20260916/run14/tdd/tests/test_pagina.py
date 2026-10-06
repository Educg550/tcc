import re

ROTULOS = [
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


def test_arquivos_estaticos_sao_servidos(cliente):
    pagina = cliente.get("/")
    assert pagina.status_code == 200
    assert "text/html" in pagina.headers["content-type"]
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_cabecalho_institucional_usp(cliente):
    pagina = cliente.get("/").text
    assert "assets/usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina


def test_abas_alunos_e_docentes_nessa_ordem(cliente):
    pagina = cliente.get("/").text
    assert "ALUNOS" in pagina
    assert "DOCENTES" in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")


def test_titulos_dos_tres_blocos(cliente):
    pagina = cliente.get("/").text
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in pagina


def test_rotulos_dos_campos_presentes_e_na_ordem(cliente):
    pagina = cliente.get("/").text
    posicao = 0
    for rotulo in ROTULOS:
        posicao = pagina.find(rotulo, posicao)
        assert posicao != -1, f"rótulo ausente ou fora de ordem: {rotulo}"
        posicao += len(rotulo)


def test_nivel_e_tipo_auxilio_so_na_aba_alunos(cliente):
    pagina = cliente.get("/").text
    assert pagina.count("NÍVEL") == 1
    assert pagina.count("TIPO DE AUXÍLIO") == 1


def test_opcoes_das_selecoes(cliente):
    pagina = cliente.get("/").text
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in pagina


def test_cada_aba_tem_botao_enviar_solicitacao(cliente):
    pagina = cliente.get("/").text
    assert pagina.count("Enviar solicitação") == 2


def test_inputs_e_textareas_tem_placeholder(cliente):
    pagina = cliente.get("/").text
    tags = re.findall(r"<(?:input|textarea)\b[^>]*>", pagina)
    assert tags, "nenhum campo encontrado na página"
    sem_placeholder = [
        tag
        for tag in tags
        if not re.search(r"placeholder\s*=\s*(\"[^\"]+\"|'[^']+')", tag)
    ]
    assert sem_placeholder == []


def test_so_o_logotipo_da_usp_e_referenciado_como_imagem(cliente):
    conteudo = (
        cliente.get("/").text
        + cliente.get("/style.css").text
        + cliente.get("/app.js").text
    )
    referencias = set(re.findall(r"assets/[\w.\-]+", conteudo))
    assert referencias == {"assets/usp-logo.png"}


def test_oficio_preserva_quebras_de_linha(cliente):
    pagina = cliente.get("/").text
    css = cliente.get("/style.css").text
    js = cliente.get("/app.js").text
    assert re.search(r"white-space\s*:\s*pre", css) or "<pre" in pagina or "<pre" in js
