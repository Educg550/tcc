import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


@pytest.fixture
def index():
    r = client.get("/")
    assert r.status_code == 200
    return r.text


ALUNOS = {
    "nome": "Maria da Silva Souza",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "Congresso Nacional de Matemática",
    "periodo": "10 a 12 de outubro de 2024",
    "cidade": "São Paulo",
    "estado": "SP",
    "pais": "Brasil",
    "link": "https://exemplo.org",
    "valor": "R$ 1.500,00",
    "detalhamento": "Inscrição no evento",
    "apresentacao": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade_end": "São Paulo",
    "estado_end": "SP",
    "cpf": "153.509.460-56",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


DOCENTES = dict(ALUNOS, nivel="", tipo="")


def sol(d):
    base = {
        "aba": d.get("aba", "ALUNOS"),
        "nome": d["nome"],
        "n_usp": d["n_usp"],
        "programa": d["programa"],
        "email": d["email"],
        "evento": d["evento"],
        "periodo": d["periodo"],
        "cidade": d["cidade"],
        "estado": d["estado"],
        "pais": d["pais"],
        "link": d["link"],
        "valor": d["valor"],
        "detalhamento": d["detalhamento"],
        "apresentacao": d["apresentacao"],
        "nascimento": d["nascimento"],
        "logradouro": d["logradouro"],
        "numero": d["numero"],
        "complemento": d["complemento"],
        "bairro": d["bairro"],
        "cep": d["cep"],
        "cidade_end": d["cidade_end"],
        "estado_end": d["estado_end"],
        "cpf": d["cpf"],
        "rg": d["rg"],
        "banco": d["banco"],
        "agencia": d["agencia"],
        "conta": d["conta"],
    }
    if base["aba"] == "ALUNOS":
        base["nivel"] = d["nivel"]
        base["tipo"] = d["tipo"]
    return base


def test_estaticos_disponiveis():
    for nome in ("app.js", "style.css"):
        r = client.get(f"/{nome}")
        assert r.status_code == 200, nome
        assert len(r.content) > 0


def test_cabecalho(index):
    assert 'src="assets/usp-logo.png"' in index
    assert "Universidade de São Paulo" in index
    assert "assets/brasao.png" not in index
    assert 'href="style.css"' in index
    assert '<script src="app.js">' in index


def test_abas(index):
    assert "ALUNOS" in index
    assert "DOCENTES" in index
    assert index.index("ALUNOS") < index.index("DOCENTES")
    assert 'id="aba-alunos"' in index
    assert 'id="aba-docentes"' in index


def test_rotulos(index):
    esperados = [
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
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Enviar solicitação",
    ]
    for rotulo in esperados:
        assert rotulo in index, rotulo


def test_campos_exclusivos_por_aba(index):
    alunos = index.split('id="aba-alunos"')[1].split('id="aba-docentes"')[0]
    docentes = index.split('id="aba-docentes"')[1]
    for campo in ("NÍVEL", "TIPO DE AUXÍLIO"):
        assert campo in alunos
        assert campo not in docentes


def test_placeholders(index):
    r = re.findall(r"placeholder=\"([^\"]+)\"", index)
    assert len(r) >= 25
    rotulos = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "LOGRADOURO",
        "COMPLEMENTO",
        "CEP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA CONTA",
        "DATA DE NASCIMENTO",
    ]
    for rotulo in rotulos:
        for ph in r:
            assert ph != rotulo, rotulo


def test_valido_alunos():
    r = client.post("/api/solicitacao", json=sol(ALUNOS))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("ok") is True
    oficio = d["oficio"]
    esperado = [
        "Interessada(o): Maria da Silva Souza - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "Dados do evento",
        "Evento: Congresso Nacional de Matemática",
        "Período: 10 a 12 de outubro de 2024",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.org",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição no evento",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 153.509.460-56",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    for linha in esperado:
        assert linha in oficio, linha
    assert "Complemento:" not in oficio


def test_valido_docentes():
    r = client.post("/api/solicitacao", json=sol(dict(ALUNOS, aba="DOCENTES", nivel="", tipo="")))
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Programa: Matemática - " not in oficio


def test_opcionais_vazios_somem():
    dados = sol(dict(ALUNOS, link="", complemento="x"))
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento: x" in oficio


def test_campo_obrigatorio_vazio():
    for campo in [
        "nome", "n_usp", "programa", "nivel", "tipo", "email", "evento",
        "periodo", "cidade", "estado", "pais", "valor", "detalhamento",
        "apresentacao", "nascimento", "logradouro", "numero", "bairro",
        "cep", "cidade_end", "estado_end", "cpf", "rg", "banco",
        "agencia", "conta",
    ]:
        d = sol(ALUNOS)
        d[campo] = ""
        r = client.post("/api/solicitacao", json=d)
        assert r.status_code == 400, campo
        assert "Preencha todos os campos" in r.json()["erros"]


def test_nusp_agencia_digitos():
    d = sol(ALUNOS)
    d.update(n_usp="12a3", agencia="12-3")
    r = client.post("/api/solicitacao", json=d)
    assert r.status_code == 400
    assert "N. USP deve conter apenas números" in r.json()["erros"]
    assert "Número da agência deve conter apenas números" in r.json()["erros"]


def test_valor_invalido():
    d = sol(ALUNOS)
    d.update(valor="R$ 0,00")
    assert "Valor solicitado deve ser maior que 0" in client.post("/api/solicitacao", json=d).json()["erros"]


def test_email_invalido():
    for email in ("sem-arroba", "a@", "@b.com"):
        d = sol(dict(ALUNOS, email=email))
        assert "E-mail inválido" in client.post("/api/solicitacao", json=sol(d)).json()["erros"], email


def test_cpf_formatos_e_dv():
    for cpf, erro in [
        ("123.456", "CPF deve estar no formato 000.000.000-00"),
        ("123.456.789-00", "CPF inválido"),
    ]:
        d = sol(dict(ALUNOS, cpf=cpf))
        assert erro in client.post("/api/solicitacao", json=sol(d)).json()["erros"], cpf


def test_cep_invalido():
    d = sol(dict(ALUNOS, cep="05508-0"))
    assert "CEP deve estar no formato 00000-000" in client.post("/api/solicitacao", json=sol(d)).json()["erros"]


def test_data_nascimento():
    for data, erro in [
        ("01-02-1980", "Data de nascimento deve estar no formato dd/mm/aaaa"),
        ("31/02/1980", "Data de nascimento inválida"),
        ("01/13/1980", "Data de nascimento inválida"),
    ]:
        d = sol(dict(ALUNOS, nascimento=data))
        assert erro in client.post("/api/solicitacao", json=sol(d)).json()["erros"], data


def test_erro_nao_gera_oficio():
    d = sol(ALUNOS)
    d["nome"] = ""
    assert "oficio" not in client.post("/api/solicitacao", json=d).json()


def test_mensagens_js():
    js = client.get("/app.js").text
    for frase in [
        "R$ 15,00",
        "123.456.789-09",
        "05508-090",
        "01/02/1980",
        "blur",
    ]:
        assert frase in js, frase
