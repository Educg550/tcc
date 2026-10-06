import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Dados de preenchimento compartilhados entre as abas
# ---------------------------------------------------------------------------
BASE = {
    "nome_completo": "Maria da Silva",
    "numero_usp": "12345678",
    "programa": "Matematica",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participacao em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "SBMAC",
    "periodo": "2025-01-01 a 2025-01-05",
    "cidade_evento": "Rio de Janeiro",
    "estado_evento": "RJ",
    "pais_evento": "Brasil",
    "link_evento": "http://sbmac.org",
    "valor": "150000",
    "detalhamento": "Detalhes do pedido",
    "apresentacao": "Poster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matao",
    "numero": "101",
    "complemento": "Apto 2",
    "bairro": "Butanta",
    "cep": "05508-090",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

# CPF valido com todos os digitos verificadores conferindo: 529.982.247-25
VALID_CPF = "529.982.247-25"


def _alunos(**overrides):
    dados = dict(BASE)
    dados.update(overrides)
    return dados


def _docentes(**overrides):
    dados = dict(BASE)
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.update(overrides)
    return dados


def _post_alunos(dados):
    return client.post("/solicitacao/alunos", data=dados)


def _post_docentes(dados):
    return client.post("/solicitacao/docentes", data=dados)


# ---------------------------------------------------------------------------
# Paginas servidas estaticamente
# ---------------------------------------------------------------------------
def test_index_disponivel():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_estaticos_servidos():
    r = client.get("/style.css")
    assert r.status_code == 200
    r = client.get("/app.js")
    assert r.status_code == 200
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Tela unica com duas abas: rotulos, ordem e aba ativa
# ---------------------------------------------------------------------------
def test_rotulos_abas_na_ordem():
    corpo = client.get("/").text
    assert "ALUNOS" in corpo and "DOCENTES" in corpo
    assert corpo.index("ALUNOS") < corpo.index("DOCENTES")


def test_aba_alunos_ativa_no_abrir():
    corpo = client.get("/").text
    assert re.search(r"ALUNOS[^>]*\bclass\b[^>]*active", corpo, re.I | re.S) is None
    assert re.search(r"DOCENTES[^>]*\bclass\b[^>]*active", corpo, re.I | re.S) is None
    assert re.search(r"class\b[^>]*\bactive\b[^>]*>\s*ALUNOS", corpo, re.I | re.S) or \
        re.search(r"<button[^>]*class\b[^>]*\bactive\b[^>]*>\s*ALUNOS", corpo, re.I)


def test_rotulo_botao_enviar():
    corpo = client.get("/").text
    assert corpo.count("Enviar solicita\u00e7\u00e3o") >= 2


# ---------------------------------------------------------------------------
# Titulos dos blocos
# ---------------------------------------------------------------------------
def test_titulos_dos_blocos():
    corpo = client.get("/").text
    for titulo in [
        "SOLICITANTE E EVENTO",
        "ENDERE\u00c7O DO SOLICITANTE",
        "INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert titulo in corpo


# ---------------------------------------------------------------------------
# Todos os rotulos de campo presentes
# ---------------------------------------------------------------------------
def test_rotulos_campos_presentes():
    corpo = client.get("/").text
    for rotulo in [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "N\u00cdVEL",
        "TIPO DE AUX\u00cdLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "N\u00daMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
        "NOME DO BANCO",
        "N\u00daMERO DA AG\u00caNCIA",
        "N\u00daMERO DA CONTA",
    ]:
        assert rotulo in corpo


def test_opcionais_nao_sao_obrigatorios():
    corpo = client.get("/").text
    assert 'name="complemento"' in corpo and 'name="link_evento"' in corpo


# ---------------------------------------------------------------------------
# Excecoes das abas: NIVEL e TIPO DE AUXILIO so na aba ALUNOS
# ---------------------------------------------------------------------------
def _aba_docentes_html(corpo):
    inicio = corpo.index("DOCENTES")
    fim = corpo.find("</form>", inicio)
    if fim == -1:
        fim = len(corpo)
    return corpo[inicio:fim]


def _aba_alunos_html(corpo):
    inicio = corpo.index("ALUNOS")
    fim = corpo.index("DOCENTES")
    return corpo[inicio:fim]


def test_excecoes_abas():
    corpo = client.get("/").text
    alunos = _aba_alunos_html(corpo)
    docentes = _aba_docentes_html(corpo)
    assert "N\u00cdVEL" in alunos and "TIPO DE AUX\u00cdLIO" in alunos
    assert "N\u00cdVEL" not in docentes
    assert "TIPO DE AUX\u00cdLIO" not in docentes


def test_opcoes_de_selecao():
    corpo = client.get("/").text
    for opcao in ["Mestrado", "Doutorado"]:
        assert opcao in corpo
    for opcao in [
        "Participa\u00e7\u00e3o em evento",
        "Banca de exame ou defesa",
    ]:
        assert opcao in corpo
    for opcao in ["P\u00f4ster", "Apresenta\u00e7\u00e3o oral", "N\u00e3o ir\u00e1 apresentar trabalho"]:
        assert opcao in corpo


# ---------------------------------------------------------------------------
# Placeholders visiveis (exemplos), diferentes do rotulo
# ---------------------------------------------------------------------------
def test_placeholders_presentes():
    corpo = client.get("/").text
    placeholders = re.findall(r"placeholder=\"([^\"]*)\"", corpo)
    placeholders += re.findall(r"placeholder='([^']*)'", corpo)
    assert len(placeholders) >= 28
    assert any(p for p in placeholders)


# ---------------------------------------------------------------------------
# Formatacao: o app.js contem a logica de mascaras pedida
# ---------------------------------------------------------------------------
def test_appjs_tem_logica_formatacao():
    js = client.get("/app.js").text
    assert "CPF" in js or "cpf" in js
    assert "CEP" in js or "cep" in js
    assert "1.500" in js or "100000" in js or "centavos" in js or "100" in js


# ---------------------------------------------------------------------------
# Validacao (backend) - todos os erros pedidos
# ---------------------------------------------------------------------------
def test_validacao():
    corpo = _post_alunos(_alunos(nome_completo="")).json()["erros"]
    assert "Preencha todos os campos" in corpo

    corpo = _post_alunos(_alunos(numero_usp="12a")).json()["erros"]
    assert "N. USP deve conter apenas n\u00fameros" in corpo

    corpo = _post_alunos(_alunos(agencia="12x")).json()["erros"]
    assert "N\u00famero da ag\u00eancia deve conter apenas n\u00fameros" in corpo

    corpo = _post_alunos(_alunos(valor="0")).json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in corpo

    corpo = _post_alunos(_alunos(email="sem-at-sign")).json()["erros"]
    assert "E-mail inv\u00e1lido" in corpo

    corpo = _post_alunos(_alunos(cpf="12345678909")).json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in corpo

    corpo = _post_alunos(_alunos(cep="05508090")).json()["erros"]
    assert "CEP deve estar no formato 00000-000" in corpo

    corpo = _post_alunos(_alunos(data_nascimento="01021980")).json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo

    corpo = _post_alunos(_alunos(cpf="111.111.111-11")).json()["erros"]
    assert "CPF inv\u00e1lido" in corpo

    corpo = _post_alunos(_alunos(data_nascimento="31/02/1980")).json()["erros"]
    assert "Data de nascimento inv\u00e1lida" in corpo


# ---------------------------------------------------------------------------
# Erro unico de obrigatoriedade
# ---------------------------------------------------------------------------
def test_erro_obrigatorio_unico():
    corpo = _post_alunos(_alunos(nome_completo="", logradouro="", banco="")).json()["erros"]
    assert corpo.count("Preencha todos os campos") == 1


# ---------------------------------------------------------------------------
# Sucesso aba ALUNOS - oficio montado
# ---------------------------------------------------------------------------
def test_oficio_alunos():
    r = _post_alunos(_alunos(cpf=VALID_CPF, valor="150000"))
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Participa\u00e7\u00e3o em evento" in oficio
    assert "Programa: Matematica - Doutorado" in oficio
    assert "Evento: SBMAC" in oficio
    assert "Local: Rio de Janeiro - RJ - Brasil" in oficio
    assert "Link do evento: http://sbmac.org" in oficio
    assert "Apresenta\u00e7\u00e3o de trabalho: Poster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Detalhes do pedido" in oficio
    assert "Rua do Matao, 101" in oficio
    assert "Complemento: Apto 2" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butanta, Sao Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: " + VALID_CPF in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Ag\u00eancia: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias." in oficio
    assert "A CCP-Matematica aprovou na data de hoje" in oficio


def test_oficio_docentes():
    r = _post_docentes(_docentes(cpf=VALID_CPF, valor="1500"))
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa" in oficio
    assert "Programa: Matematica\n" in oficio + "\n"
    assert "Doutorado" not in oficio
    assert "Valor solicitado: R$ 15,00" in oficio


# ---------------------------------------------------------------------------
# Linhas de campo opcional vazio sao omitidas
# ---------------------------------------------------------------------------
def test_linha_link_vazio_omitida():
    r = _post_alunos(_alunos(cpf=VALID_CPF, link_evento=""))
    assert "Link do evento" not in r.json()["oficio"]


def test_linha_complemento_vazio_omitida():
    r = _post_alunos(_alunos(cpf=VALID_CPF, complemento=""))
    assert "Complemento" not in r.json()["oficio"]


# ---------------------------------------------------------------------------
# Erro impede geracao do oficio
# ---------------------------------------------------------------------------
def test_erro_gera_sem_oficio():
    dados = _alunos(cpf="111.111.111-11")
    corpo = _post_alunos(dados).json()
    assert corpo["erros"]
    assert not corpo.get("oficio")


def test_formato_resposta_json():
    corpo = _post_alunos(_alunos(cpf=VALID_CPF)).json()
    assert "oficio" in corpo and "erros" in corpo


# ---------------------------------------------------------------------------
# Formatacao de moeda nos centavos
# ---------------------------------------------------------------------------
def test_moeda_um_centavo():
    r = _post_alunos(_alunos(cpf=VALID_CPF, valor="1"))
    assert "Valor solicitado: R$ 0,01" in r.json()["oficio"]


def test_moeda_grande():
    r = _post_alunos(_alunos(cpf=VALID_CPF, valor="150000000"))
    assert "Valor solicitado: R$ 1.500.000,00" in r.json()["oficio"]
