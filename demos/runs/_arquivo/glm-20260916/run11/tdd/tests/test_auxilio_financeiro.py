"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

A página é verificada como documento institucional: cabeçalho, abas, títulos de
bloco, rótulos exatos, opções, placeholders e arquivos estáticos. O envio é
exercitado no backend: mensagens de erro exatas e o ofício devolvido já
preenchido com os dados.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="session")
def cliente():
    return TestClient(app)


@pytest.fixture(scope="session")
def pagina(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.text


# ---------------------------------------------------------------------------
# Solicitações válidas de exemplo (as chaves são os rótulos exatos dos campos)
# ---------------------------------------------------------------------------

DADOS_ALUNOS = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria Souza da Silva",
    "N. USP": "9876543",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Doutorado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.souza@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBES 2025",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "15/09/2025 a 19/09/2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Porto Alegre",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "RS",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbes.org.br/2025",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Inscrição e passagem aérea para o SBES 2025.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "375",
    "COMPLEMENTO": "Sala 2",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "0123",
    "NÚMERO DA CONTA": "45678-9",
}

DADOS_DOCENTES = {
    "NOME COMPLETO - SEM ABREVIAR": "João Prado Martins",
    "N. USP": "1234567",
    "PROGRAMA": "Física Matemática",
    "E-MAIL": "joao.prado@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Banca de mestrado de Ana Lima",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "03/11/2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "",
    "VALOR SOLICITADO (R$)": "R$ 300,00",
    "DETALHAMENTO DO PEDIDO": "Passagem rodoviária para participação em banca de mestrado.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Não irá apresentar trabalho",
    "DATA DE NASCIMENTO": "10/12/1975",
    "LOGRADOURO": "Av. Professor Lineu Prestes",
    "NÚMERO": "910",
    "COMPLEMENTO": "",
    "BAIRRO": "Cidade Universitária",
    "CEP": "05508-000",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "987.654.321-00",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "98.765.432-1",
    "NOME DO BANCO": "Itaú",
    "NÚMERO DA AGÊNCIA": "0999",
    "NÚMERO DA CONTA": "11223-3",
}

OFICIO_ALUNOS = [
    "Interessada(o): Maria Souza da Silva - 9876543",
    "E-mail: maria.souza@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Doutorado",
    "A CCP-Ciência da Computação aprovou na data de hoje",
    "Evento: SBES 2025",
    "Período: 15/09/2025 a 19/09/2025",
    "Local: Porto Alegre - RS - Brasil",
    "Link do evento: https://sbes.org.br/2025",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição e passagem aérea para o SBES 2025.",
    "Rua do Anfiteatro, 375",
    "Complemento: Sala 2",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 0123",
    "Conta: 45678-9",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]

OFICIO_DOCENTES = [
    "Interessada(o): João Prado Martins - 1234567",
    "E-mail: joao.prado@ime.usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
    "Programa: Física Matemática",
    "A CCP-Física Matemática aprovou na data de hoje",
    "Evento: Banca de mestrado de Ana Lima",
    "Local: São Paulo - SP - Brasil",
    "Apresentação de trabalho: Não irá apresentar trabalho",
    "Valor solicitado: R$ 300,00",
    "Av. Professor Lineu Prestes, 910",
    "Cidade Universitária, São Paulo - SP",
    "Data de nascimento: 10/12/1975",
    "CPF: 987.654.321-00",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]

# ---------------------------------------------------------------------------
# Textos visíveis exatos
# ---------------------------------------------------------------------------

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

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

MENSAGENS_DE_FORMATO = [
    "N. USP deve conter apenas números",
    "Número da agência deve conter apenas números",
    "E-mail inválido",
    "Valor solicitado deve ser maior que 0",
    "CEP deve estar no formato 00000-000",
    "CPF deve estar no formato 000.000.000-00",
    "Data de nascimento deve estar no formato dd/mm/aaaa",
]


# ---------------------------------------------------------------------------
# Apoio para enviar a solicitação ao backend
# ---------------------------------------------------------------------------

ENDPOINTS_CANDIDATOS = [
    "/api/solicitacao",
    "/solicitacao",
    "/api/solicitacoes",
    "/api/solicitar",
    "/solicitar",
    "/api/enviar",
    "/enviar",
    "/api/submeter",
    "/submeter",
    "/api/auxilio",
    "/auxilio",
    "/api/validar",
    "/api/oficio",
    "/submit",
]

CHAVES_SNAKE = {
    "NOME COMPLETO - SEM ABREVIAR": "nome_completo",
    "N. USP": "n_usp",
    "PROGRAMA": "programa",
    "NÍVEL": "nivel",
    "TIPO DE AUXÍLIO": "tipo_auxilio",
    "E-MAIL": "email",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "nome_evento",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "periodo_evento",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "cidade_evento",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "estado_evento",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "pais_evento",
    "LINK DO EVENTO, EXAME OU DEFESA": "link_evento",
    "VALOR SOLICITADO (R$)": "valor_solicitado",
    "DETALHAMENTO DO PEDIDO": "detalhamento",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "apresentacao_trabalho",
    "DATA DE NASCIMENTO": "data_nascimento",
    "LOGRADOURO": "logradouro",
    "NÚMERO": "numero",
    "COMPLEMENTO": "complemento",
    "BAIRRO": "bairro",
    "CEP": "cep",
    "CIDADE": "cidade",
    "ESTADO": "estado",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "cpf",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "rg_rnm",
    "NOME DO BANCO": "nome_banco",
    "NÚMERO DA AGÊNCIA": "numero_agencia",
    "NÚMERO DA CONTA": "numero_conta",
}

_contratos = {}


def _norm(texto):
    return " ".join(texto.split())


def _texto(resposta):
    """Texto útil da resposta: as strings dentro do JSON, ou o corpo bruto."""
    try:
        corpo = resposta.()
    except ValueError:
        return resposta.text
    partes = []

    def passeia(pedaco):
        if isinstance(pedaco, str):
            partes.append(pedaco)
        elif isinstance(pedaco, dict):
            for valor in pedaco.values():
                passeia(valor)
        elif isinstance(pedaco, (list, tuple)):
            for valor in pedaco:
                passeia(valor)

    passeia(corpo)
    return "\n".join(partes)


def _corpos(dados, aba):
    """Corpos de requisição candidatos; primeiro com os rótulos como chaves."""
    por_rotulo = dict(dados)
    por_rotulo.update(aba=aba.lower(), ABA=aba, tipo=aba.lower(), tipo_solicitacao=aba.lower())
    por_chave = {CHAVES_SNAKE[chave]: valor for chave, valor in dados.items()}
    por_chave.update(aba=aba.lower(), tipo=aba.lower(), tipo_solicitacao=aba.lower())
    return {
        "rotulos-": {"": por_rotulo},
        "snake-": {"": por_chave},
        "rotulos-form": {"data": por_rotulo},
    }


def _endpoints(cliente):
    """Caminhos de envio: os que o app.js usa primeiro, depois candidatos comuns."""
    resposta = cliente.get("/app.js")
    js = resposta.text if resposta.status_code == 200 else ""
    urls = re.findall(r'''fetch\(\s*[`'"]([^`'"\s]+)''', js)
    urls += re.findall(r'''[`'"](/api/[^'"`\s]*)[`'"]''', js)
    caminhos = []
    for url in urls:
        if url.startswith("http"):
            continue
        if not url.startswith("/"):
            url = "/" + url
        if re.search(r"\.(html?|css|js|png|jpe?g|svg|ico|woff2?)$", url):
            continue
        if url not in caminhos:
            caminhos.append(url)
    for url in ENDPOINTS_CANDIDATOS:
        if url not in caminhos:
            caminhos.append(url)
    return caminhos


def enviar(cliente, aba, dados, marcadores):
    """Envia a solicitação e devolve o texto devolvido pelo backend.

    Na primeira chamada de cada aba, descobre qual endpoint e formato de corpo o
    backend entende (a resposta precisa reconhecer os dados enviados, contendo
    todos os marcadores pedidos) e guarda esse contrato para as demais chamadas.
    """
    corpos = _corpos(dados, aba)
    if aba in _contratos:
        url, formato = _contratos[aba]
        try:
            resposta = cliente.post(url, **corpos[formato])
        except Exception as erro:
            pytest.fail(f"POST {url} falhou: {erro}")
        return _texto(resposta)
    for url in _endpoints(cliente):
        for formato, kwargs in corpos.items():
            try:
                resposta = cliente.post(url, **kwargs)
            except Exception:
                continue
            texto = _texto(resposta)
            if all(_norm(marcador) in _norm(texto) for marcador in marcadores):
                _contratos[aba] = (url, formato)
                return texto
    pytest.fail(f"Nenhum endpoint do backend aceitou a solicitação da aba {aba}")


def _rotulos_em_ordem(pagina, rotulos):
    for rotulo in rotulos:
        assert rotulo in pagina
    posicoes = [pagina.index(rotulo) for rotulo in rotulos]
    assert posicoes == sorted(posicoes), f"fora de ordem: {rotulos}"


# ---------------------------------------------------------------------------
# A página
# ---------------------------------------------------------------------------


def test_pagina_inicial_e_html(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_cabecalho_institucional_da_usp(pagina):
    assert "usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina
    assert any(
        nome in pagina
        for nome in ("IME", "Instituto de Matemática e Estatística", "Pós-Graduação")
    )
    assert "brasao" not in pagina.lower()


def test_abas_com_rotulos_exatos_alunos_e_docentes_nessa_ordem(pagina):
    assert re.search(r">\s*ALUNOS\s*<", pagina)
    assert re.search(r">\s*DOCENTES\s*<", pagina)
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")


def test_blocos_com_titulos_na_ordem(pagina):
    _rotulos_em_ordem(pagina, BLOCOS)


def test_rotulos_do_bloco_solicitante_e_evento_na_ordem(pagina):
    _rotulos_em_ordem(pagina, ROTULOS_SOLICITANTE)


def test_rotulos_do_bloco_endereco_na_ordem(pagina):
    _rotulos_em_ordem(pagina, ROTULOS_ENDERECO)


def test_rotulos_do_bloco_pagamento_na_ordem(pagina):
    _rotulos_em_ordem(pagina, ROTULOS_PAGAMENTO)


def test_opcoes_das_selecoes(pagina):
    for opcao in OPCOES:
        assert opcao in pagina


def test_botao_enviar_solicitacao_em_cada_aba(pagina):
    assert pagina.count("Enviar solicitação") >= 2


def test_todo_campo_tem_placeholder_com_exemplo(pagina):
    campos = re.findall(r"<(?:input|textarea)\b[^>]*>", pagina)
    assert len(campos) >= 20
    rotulos = ROTULOS_SOLICITANTE + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO
    for campo in campos:
        exemplo = re.search(r'placeholder\s*=\s*"([^"]*)"', campo) or re.search(
            r"placeholder\s*=\s*'([^']*)'", campo
        )
        assert exemplo, f"campo sem placeholder: {campo}"
        valor = exemplo.group(1).strip()
        assert valor, f"placeholder vazio: {campo}"
        assert valor.upper() not in rotulos, f"placeholder repete o rótulo: {campo}"


# ---------------------------------------------------------------------------
# Arquivos estáticos
# ---------------------------------------------------------------------------


def test_css_servido(cliente):
    resposta = cliente.get("/style.css")
    assert resposta.status_code == 200
    assert "css" in resposta.headers["content-type"]


def test_css_usa_as_cores_e_a_fonte_da_usp(cliente):
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css or "#fcb421" in css
    assert "open sans" in css or "sans-serif" in css


def test_app_js_servido(cliente):
    assert cliente.get("/app.js").status_code == 200


def test_logo_da_usp_servida(cliente):
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content.startswith(b"\x89PNG")


# ---------------------------------------------------------------------------
# Envio: casos válidos
# ---------------------------------------------------------------------------


def test_envio_valido_de_alunos_recebe_o_oficio_preenchido(cliente):
    texto = enviar(cliente, "ALUNOS", DADOS_ALUNOS, OFICIO_ALUNOS)
    norm = _norm(texto)
    for linha in OFICIO_ALUNOS:
        assert _norm(linha) in norm
    front = cliente.get("/").text + cliente.get("/app.js").text
    assert "Solicitação registrada" in (texto + front)


def test_envio_valido_de_docentes_gera_oficio_de_verba_do_programa(cliente):
    texto = enviar(cliente, "DOCENTES", DADOS_DOCENTES, OFICIO_DOCENTES)
    norm = _norm(texto)
    for linha in OFICIO_DOCENTES:
        assert _norm(linha) in norm
    assert "Programa: Física Matemática -" not in norm
    assert "Link do evento:" not in norm
    assert "Complemento:" not in norm


def test_opcionais_vazios_saem_do_oficio(cliente):
    dados = dict(DADOS_ALUNOS)
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    dados["COMPLEMENTO"] = ""
    marcador = "Interessada(o): Maria Souza da Silva - 9876543"
    texto = enviar(
        cliente,
        "ALUNOS",
        dados,
        [marcador, "Encaminhe-se ao Serviço Financeiro para providências."],
    )
    norm = _norm(texto)
    assert marcador in norm
    assert "Link do evento:" not in norm
    assert "Complemento:" not in norm


# ---------------------------------------------------------------------------
# Envio: validação
# ---------------------------------------------------------------------------


def test_envio_vazio_pede_para_preencher_apenas_uma_vez(cliente):
    vazios = {chave: "" for chave in DADOS_ALUNOS}
    texto = enviar(cliente, "ALUNOS", vazios, ["Preencha todos os campos"])
    assert texto.count("Preencha todos os campos") == 1
    assert "Interessada(o):" not in _norm(texto)


def test_todas_as_mensagens_de_formato_aparecem_juntas(cliente):
    dados = dict(DADOS_ALUNOS)
    dados["N. USP"] = "12a45"
    dados["NÚMERO DA AGÊNCIA"] = "12a4"
    dados["E-MAIL"] = "maria.souza"
    dados["VALOR SOLICITADO (R$)"] = "R$ 0,00"
    dados["CEP"] = "05508-09"
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123456789"
    dados["DATA DE NASCIMENTO"] = "01-02-1980"
    texto = enviar(cliente, "ALUNOS", dados, MENSAGENS_DE_FORMATO)
    norm = _norm(texto)
    for mensagem in MENSAGENS_DE_FORMATO:
        assert mensagem in norm
    assert "Interessada(o):" not in norm


def test_cpf_com_digito_verificador_errado(cliente):
    dados = dict(DADOS_ALUNOS)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123.456.789-00"
    texto = enviar(cliente, "ALUNOS", dados, ["CPF inválido"])
    norm = _norm(texto)
    assert "CPF inválido" in norm
    assert "CPF deve estar no formato 000.000.000-00" not in norm
    assert "Interessada(o):" not in norm


@pytest.mark.parametrize("data_invalida", ["31/02/1980", "15/13/1980"])
def test_data_de_nascimento_inexistente(cliente, data_invalida):
    dados = dict(DADOS_ALUNOS)
    dados["DATA DE NASCIMENTO"] = data_invalida
    texto = enviar(cliente, "ALUNOS", dados, ["Data de nascimento inválida"])
    norm = _norm(texto)
    assert "Data de nascimento inválida" in norm
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in norm
    assert "Interessada(o):" not in norm
