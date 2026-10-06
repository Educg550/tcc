from html.parser import HTMLParser

TITULOS_E_ROTULOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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


class ColetorDeCampos(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos = []

    def handle_starttag(self, tag, attrs):
        if tag in ("input", "textarea", "select"):
            self.campos.append((tag, dict(attrs).get("placeholder", "")))


def pagina(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.text


def test_arquivos_da_aplicacao_sao_servidos(cliente):
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_abas_alunos_e_docentes_nessa_ordem(cliente):
    html = pagina(cliente)
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos_e_rotulos_dos_campos(cliente):
    html = pagina(cliente)
    for rotulo in TITULOS_E_ROTULOS:
        assert rotulo in html, f"ausente na página: {rotulo}"


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos(cliente):
    html = pagina(cliente)
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


def test_opcoes_das_selecoes(cliente):
    html = pagina(cliente)
    for opcao in OPCOES:
        assert opcao in html, f"opção ausente: {opcao}"


def test_botao_enviar_solicitacao_em_cada_aba(cliente):
    assert pagina(cliente).count("Enviar solicitação") == 2


def test_cabecalho_institucional_da_usp(cliente):
    html = pagina(cliente)
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html + cliente.get("/style.css").text


def test_todo_campo_tem_placeholder_de_exemplo(cliente):
    coletor = ColetorDeCampos()
    coletor.feed(pagina(cliente))
    entradas = [
        (tag, placeholder)
        for tag, placeholder in coletor.campos
        if tag in ("input", "textarea")
    ]
    assert len(entradas) >= 50
    rotulos = {rotulo.casefold() for rotulo in TITULOS_E_ROTULOS}
    for tag, placeholder in entradas:
        assert placeholder.strip(), f"<{tag}> sem placeholder"
        assert (
            placeholder.strip().casefold() not in rotulos
        ), f"placeholder repete o rótulo: {placeholder}"


def test_css_usa_as_cores_e_a_fonte_da_identidade(cliente):
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "open sans" in css
