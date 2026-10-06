"""A API devolve o ofício com os dados no lugar dos marcadores."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _dados(overrides=None):
    dados = {
        "nomeCompleto": "Maria da Silva",
        "numeroUsp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipoAuxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nomeEvento": "Congresso Nacional",
        "periodo": "10 a 12 de outubro de 2025",
        "cidadeEvento": "São Paulo",
        "estadoEvento": "SP",
        "paisEvento": "Brasil",
        "linkEvento": "",
        "valorSolicitado": "R$ 1.500,00",
        "detalhamento": "Passagem aérea",
        "apresentacao": "Pôster",
        "dataNascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numeroEndereco": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "nomeBanco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    if overrides:
        dados.update(overrides)
    return dados


def _oficio(overrides=None):
    r = client.post("/api/solicitar/alunos", json=_dados(overrides))
    assert r.status_code == 200, r.text
    return r.json()["oficio"]


def test_linhas_fixas_do_oficio():
    oficio = _oficio()
    for linha in [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: Congresso Nacional",
        "Período: 10 a 12 de outubro de 2025",
        "Local: São Paulo - SP - Brasil",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert linha in oficio, linha


def test_linha_link_sai_quando_vazio():
    oficio = _oficio()
    assert "Link do evento:" not in oficio


def test_linha_link_aparece_preenchido():
    oficio = _oficio({"linkEvento": "http://congresso.br"})
    assert "Link do evento: http://congresso.br" in oficio


def test_linha_complemento_sai_quando_vazio():
    oficio = _oficio()
    assert "Complemento:" not in oficio


def test_linha_complemento_aparece_preenchido():
    oficio = _oficio({"complemento": "Sala 12"})
    assert "Complemento: Sala 12" in oficio


def test_oficio_docentes_sem_nivel_e_tipo():
    dados = _dados()
    dados.pop("nivel")
    dados.pop("tipoAuxilio")
    r = client.post("/api/solicitar/docentes", json=dados)
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert not any(linha.startswith("Programa: Matemática -") for linha in oficio.splitlines())
