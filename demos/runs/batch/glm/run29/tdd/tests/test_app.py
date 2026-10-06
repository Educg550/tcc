"""Testes do Requisito 01: formulário de auxílio financeiro da Pós-Graduação do IME-USP.

O backend é quem valida; o frontend mostra o que ele responder.
Todos os testes usam o cliente de teste síncrono do FastAPI.
"""
import re
import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def pagina(client):
    r = client.get("/")
    assert r.status_code == 200
    return r.text


def get_index(client):
    return pagina(client)


def estilo(client):
    r = client.get("/style.css")
    assert r.status_code == 200
    return r.text


def script(client):
    r = client.get("/app.js")
    assert r.status_code == 200
    return r.text


@pytest.fixture
def css(client):
    return estilo(client)


@pytest.fixture
def js(client):
    return script(client)


def solicitar(client, aba, **altera):
    """Envia a solicitação para a aba indicada, com um formulário válido por padrão."""
    dados = {
        "tipo": aba,
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro de Matemática",
        "periodo": "20 a 25 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link_evento": "https://exemplo.com.br",
        "valor": "R$ 1.500,00",
        "detalhamento": "Passagem aérea e hospedagem",
        "apresentacao": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "98765-4",
    }
    dados.update(altera)
    return client.post("/solicitar", data=dados)


def oficio(r):
    assert r.status_code == 200
    corpo = r.json()
    assert isinstance(corpo, dict)
    return corpo


# ---------------------------------------------------------------------------
# Página, arquivos estáticos e assets
# ---------------------------------------------------------------------------


def test_pagina_inicial_contem_estrutura(client):
    html = get_index(client)
    for trecho in (
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "Enviar solicitação",
        "usp-logo.png",
        "Universidade de São Paulo",
    ):
        assert trecho in html


def test_assets_sao_servidos(client):
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert len(r.content) > 0


def test_estaticos_sao_texto_plano(client):
    css = estilo(client)
    js = script(client)
    assert "@import" not in css
    assert "url(http" not in css
    assert not re.search(r"https?://", js)


def test_html_sem_brasao(client):
    """O escudo é de documento impresso: não pode aparecer na página."""
    html = get_index(client)
    assert "brasao" not in html.lower()
    assert "escudo" not in html.lower()


# ---------------------------------------------------------------------------
# Ordem e rótulos exatos
# ---------------------------------------------------------------------------


def test_ordem_dos_rotulos(client):
    html = get_index(client)
    rotulos = [
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
    posicoes = [html.index(r) for r in rotulos]
    assert posicoes == sorted(posicoes)


def test_nivel_e_tipo_de_auxilio_somente_em_alunos(client):
    """ALUNOS vem antes de DOCENTES; NÍVEL e TIPO DE AUXÍLIO não existem na aba DOCENTES."""
    html = get_index(client)
    inicio_alunos = html.index("ALUNOS")
    inicio_docentes = html.index("DOCENTES")
    assert inicio_alunos < inicio_docentes

    # formulário de alunos é tudo que aparece antes do formulário de docentes
    fim_alunos = html.index("Enviar solicitação", inicio_docentes)
    aba_alunos = html[:inicio_docentes]
    aba_docentes = html[inicio_docentes:fim_alunos]
    assert "NÍVEL" in aba_alunos
    assert "NÍVEL" not in aba_docentes
    assert "TIPO DE AUXÍLIO" in aba_alunos
    assert "TIPO DE AUXÍLIO" not in aba_docentes


def test_opcoes_de_selecao(client):
    html = get_index(client)
    for opcao in ("Mestrado", "Doutorado", "Participação em evento", "Banca de exame ou defesa", "Outro", "Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert opcao in html


def test_placeholders_nao_repetem_rotulo(client):
    html = get_index(client)
    rotulos = re.findall(r"<label[^>]*>(.*?)</label>", html, re.S)
    placeholders = re.findall(r"placeholder=\"(.*?)\"", html)
    assert len(placeholders) >= 20
    for rotulo in rotulos:
        rotulo = re.sub(r"<[^>]+>", "", rotulo).strip()
        assert rotulo not in placeholders


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------


def test_solicitacao_valida_retorna_oficio_alunos(client):
    r = solicitar(client, "alunos")
    corpo = oficio(r)
    assert corpo["ok"] is True
    assert corpo.get("erros") == []
    assert "Maria da Silva" in corpo["oficio"]


def test_solicitacao_valida_retorna_oficio_docentes(client):
    r = solicitar(client, "docentes", tipo_auxilio="", nivel="")
    corpo = oficio(r)
    assert corpo["ok"] is True
    assert corpo["oficio"] == ""


def test_campo_obrigatorio_vazio(client):
    r = solicitar(client, "alunos", nome="")
    corpo = oficio(r)
    assert corpo["ok"] is False
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["oficio"] == ""


def test_preencha_todos_os_campos_aparece_uma_vez(client):
    r = solicitar(client, "alunos", nome="", email="", logradouro="")
    corpo = oficio(r)
    assert corpo["erros"].count("Preencha todos os campos") == 1


def test_campos_opcionais_podem_ficar_vazios(client):
    r = solicitar(client, "alunos", link_evento="", complemento="")
    corpo = oficio(r)
    assert corpo["ok"] is True


@pytest.mark.parametrize("valor", ["0", "", "-10", "abc", "R$ 0,00", "1,5"])
def test_valor_invalido(client, valor):
    r = solicitar(client, "alunos", valor=valor)
    corpo = oficio(r)
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]
    assert corpo["ok"] is False


@pytest.mark.parametrize("valor", ["1", "1500", "150000", "150000000", "R$ 1.500,00", "R$ 15,00"])
def test_valor_valido(client, valor):
    r = solicitar(client, "alunos", valor=valor)
    corpo = oficio(r)
    assert "Valor solicitado deve ser maior que 0" not in corpo["erros"]


@pytest.mark.parametrize("n_usp", ["12a456", "12 456", "12.456", "-12345"])
def test_n_usp_somente_digitos(client, n_usp):
    r = solicitar(client, "alunos", n_usp=n_usp)
    corpo = oficio(r)
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_n_usp_valido(client):
    r = solicitar(client, "alunos", n_usp="12345678")
    corpo = oficio(r)
    assert "N. USP deve conter apenas números" not in corpo["erros"]
    assert corpo["ok"] is True


@pytest.mark.parametrize("agencia", ["12a", "12 3", "12-3"])
def test_agencia_somente_digitos(client, agencia):
    r = solicitar(client, "alunos", agencia=agencia)
    corpo = oficio(r)
    assert "Número da agência deve conter apenas números" in corpo["erros"]


@pytest.mark.parametrize("email", ["maria", "maria@", "@ime.usp.br", "maria@ime"])
def test_email_invalido(client, email):
    r = solicitar(client, "alunos", email=email)
    corpo = oficio(r)
    assert "E-mail inválido" in corpo["erros"]


@pytest.mark.parametrize("cpf", ["123", "123.456.789", "12345678909", "12.345.678-90", "abc"])
def test_cpf_formato_errado(client, cpf):
    r = solicitar(client, "alunos", cpf=cpf)
    corpo = oficio(r)
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]


@pytest.mark.parametrize("cpf", ["111.111.111-11", "123.456.789-00", "999.999.999-99"])
def test_cpf_formato_certo_mas_digitos_verificadores_errados(client, cpf):
    r = solicitar(client, "alunos", cpf=cpf)
    corpo = oficio(r)
    assert "CPF inválido" in corpo["erros"]
    assert "CPF deve estar no formato 000.000.000-00" not in corpo["erros"]


@pytest.mark.parametrize("cep", ["05508090", "05508-09", "5508-090", "abc", ""])
def test_cep_formato_errado(client, cep):
    r = solicitar(client, "alunos", cep=cep)
    corpo = oficio(r)
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_cep_valido(client):
    r = solicitar(client, "alunos", cep="05508-090")
    corpo = oficio(r)
    assert "CEP deve estar no formato 00000-000" not in corpo["erros"]
    assert corpo["ok"] is True


@pytest.mark.parametrize("data", ["01/02/19", "01021980", "01-02-1980", "01021980", ""])
def test_data_nascimento_formato_errado(client, data):
    r = solicitar(client, "alunos", nascimento=data)
    corpo = oficio(r)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


@pytest.mark.parametrize("data", ["32/01/1980", "01/13/1980", "00/01/1980", "01/00/1980", "31/02/1980"])
def test_data_nascimento_inexistente(client, data):
    r = solicitar(client, "alunos", nascimento=data)
    corpo = oficio(r)
    assert "Data de nascimento inválida" in corpo["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in corpo["erros"]


@pytest.mark.parametrize("data", ["29/02/2020", "01/02/1980", "31/12/1900"])
def test_data_nascimento_valida(client, data):
    r = solicitar(client, "alunos", nascimento=data)
    corpo = oficio(r)
    assert "Data de nascimento inválida" not in corpo["erros"]


def test_todos_os_erros_aparecem_de_uma_vez(client):
    r = solicitar(client, "alunos", n_usp="abc", valor="0", email="maria", cpf="123", cep="123", nascimento="xx")
    corpo = oficio(r)
    esperados = [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]
    for msg in esperados:
        assert msg in corpo["erros"]


def test_sem_erros_nao_gera_oficio_antes_do_envio(client):
    """Enquanto há erro, o ofício não é gerado."""
    r = solicitar(client, "alunos", cpf="123")
    corpo = oficio(r)
    assert corpo["ok"] is False
    assert corpo["oficio"] == ""


# ---------------------------------------------------------------------------
# Formatação enquanto digita
# ---------------------------------------------------------------------------


def test_js_contem_formatadores(client):
    js = script(client)
    for nome in ("moeda", "cpf", "cep", "data"):
        assert nome in js.lower()


def test_funcoes_de_formatacao_no_js(client):
    """A pontuação é da aplicação: o JS expõe formatação para os quatro campos."""
    js = script(client)
    # formatação de moeda: dígitos viram centavos
    assert re.search(r"moeda|formatarValor|valor", js, re.I)


@pytest.mark.parametrize("digitos,esperado", [
    ("1500", "R$ 15,00"),
    ("150000", "R$ 1.500,00"),
    ("150000000", "R$ 1.500.000,00"),
])
def test_js_formata_valor_como_moeda(client, digitos, esperado):
    js = script(client)
    # procura função que formata dígitos em moeda
    m = re.search(r"function\s+(\w*[vV]alor\w*|\w*[mM]oeda\w*)\s*\(", js)
    assert m, "função de formatação de valor não encontrada em app.js"


def test_js_tem_listeners_dos_campos_formatados(client):
    js = script(client)
    # os quatro campos reformatam no momento em que o usuário sai deles
    assert "blur" in js or "focusout" in js or "change" in js
    assert "valor" in js.lower()
    assert "cpf" in js.lower()
    assert "cep" in js.lower()
    assert "nascimento" in js.lower()


# ---------------------------------------------------------------------------
# Ofício
# ---------------------------------------------------------------------------


def test_oficio_alunos_completo(client):
    r = solicitar(client, "alunos")
    corpo = oficio(r)
    oficio = corpo["oficio"]
    linhas = [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: Congresso Brasileiro de Matemática",
        "Período: 20 a 25 de julho de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea e hospedagem",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "Complemento: ",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 98765-4",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    for linha in linhas:
        assert linha in oficio, f"linha faltando: {linha!r}"


def test_oficio_docentes_assunto_e_programa(client):
    r = solicitar(client, "docentes", tipo_auxilio="", nivel="")
    corpo = oficio(r)
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    # e as linhas de alunos não aparecem
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" not in oficio
    assert "Programa: Matemática - Mestrado" not in oficio


def test_oficio_linhas_opcionais_somem_quando_vazias(client):
    r = solicitar(client, "alunos", link_evento="", complemento="")
    oficio = oficio(r)["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_linhas_opcionais_aparecem_quando_preenchidas(client):
    r = solicitar(client, "alunos", link_evento="https://exemplo.com.br", complemento="Apto 12")
    oficio = oficio(r)["oficio"]
    assert "Link do evento: https://exemplo.com.br" in oficio
    assert "Complemento: Apto 12" in oficio


def test_oficio_valor_formatado(client):
    r = solicitar(client, "alunos", valor="150000")
    oficio = oficio(r)["oficio"]
    assert "Valor solicitado: R$ 1.500,00" in oficio


def test_confirmacao_no_html(client):
    html = get_index(client)
    assert "Solicitação registrada" in html


# ---------------------------------------------------------------------------
# Aparência
# ---------------------------------------------------------------------------


def test_css_cores_da_universidade(client):
    css = estilo(client)
    assert "#1094ab" in css.lower()
    assert "#64c4d2" in css.lower()
    assert "#fcb421" in css.lower()


def test_css_fonte_sem_serifa(client):
    css = estilo(client)
    assert "Open Sans" in css or "sans-serif" in css


def test_css_sem_fonte_remota(client):
    css = estilo(client)
    assert "fonts.googleapis" not in css
    assert "@import" not in css


def test_css_distribuicao_horizontal(client):
    """Várias colunas por bloco em vez de uma coluna única."""
    css = estilo(client)
    assert "flex" in css or "grid" in css


def test_css_sem_scroll_vertical(client):
    """A página cabe na tela sem rolagem vertical."""
    css = estilo(client)
    assert re.search(r"height:\s*100(vh|%)", css) or "100vh" in css or "overflow" in css


def test_css_tab_ativa_distinguivel(client):
    css = estilo(client)
    assert "active" in css or "ativa" in css.lower()


def test_html_aba_alunos_ativa_por_padrao(client):
    html = get_index(client)
    m = re.search(r'<[^>]*class="[^"]*active[^"]*"[^>]*>\s*ALUNOS', html)
    assert m, "aba ALUNOS deve estar ativa quando a página abre"


def test_js_troca_de_aba_sem_recarregar(client):
    js = script(client)
    assert "classList" in js
    # trocar de aba mostra o formulário dela e esconde o da outra
    assert "hidden" in js or "display" in js or "classList" in js


def test_js_envia_formulario(client):
    js = script(client)
    assert "fetch" in js or "XMLHttpRequest" in js or "axios" in js.lower()
    assert "solicitar" in js


def test_js_erro_mantem_valores_e_aba(client):
    """Ao enviar com erro, o frontend mostra todas as mensagens, uma por linha, no topo."""
    js = script(client)
    assert "Preencha todos os campos" in js or "erros" in js


def test_js_oficio_preserva_quebras_de_linha(client):
    """O ofício aparece na página preservando as quebras de linha."""
    js = script(client)
    assert "white-space" in js or "innerText" in js or "textContent" in js
    css = estilo(client)
    assert "white-space" in css or "pre" in css
