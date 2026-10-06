from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_alunos():
    return {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática Aplicada",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de julho de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://congreso.br",
        "valor_solicitado": "150000",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Prédio 6",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def dados_docentes():
    d = dados_alunos()
    d["aba"] = "docentes"
    d.pop("nivel")
    d.pop("tipo_auxilio")
    return d


def post(dados):
    return client.post("/api/solicitacao", json=dados)


def oficio(**overrides):
    dados = dados_alunos()
    dados.update(overrides)
    resp = post(dados)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valido"] is True
    return body["oficio"]


def test_linhas_alunos():
    txt = oficio()
    esperadas = [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática Aplicada - Mestrado",
        "A CCP-Matemática Aplicada aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: Congresso Nacional de Matemática",
        "Período: 10 a 12 de julho de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://congreso.br",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e hospedagem",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "Complemento: Prédio 6",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-0",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    for linha in esperadas:
        assert linha in txt, linha


def test_linhas_docentes():
    dados = dados_docentes()
    resp = post(dados)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valido"] is True
    txt = body["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in txt
    assert "Programa: Matemática Aplicada" in txt
    # sem sufixo de nivel
    for linha in txt.splitlines():
        if linha.startswith("Programa:"):
            assert linha == "Programa: Matemática Aplicada"


def test_link_vazio_some():
    txt = oficio(link_evento="")
    assert "Link do evento:" not in txt


def test_complemento_vazio_some():
    txt = oficio(complemento="")
    assert "Complemento:" not in txt


def test_valor_formato_milhar():
    assert "Valor solicitado: R$ 15.000.000,00" in oficio(valor_solicitado="1500000000")
    assert "Valor solicitado: R$ 15,00" in oficio(valor_solicitado="1500")


def test_data_de_hoje_no_oficio():
    import datetime

    hoje = datetime.date.today().strftime("%d/%m/%Y")
    assert hoje in oficio()


def test_docentes_nao_tem_nivel_nem_tipo():
    dados = dados_docentes()
    dados["nivel"] = "Mestrado"
    resp = post(dados)
    body = resp.json()
    assert body["valido"] is True
    for linha in body["oficio"].splitlines():
        assert "Assunto:" not in linha or "Verba do programa" in linha


def test_alunos_outro_tipo_auxilio():
    txt = oficio(tipo_auxilio="Outro")
    assert "Assunto: Solicitação de Auxílio Financeiro - Outro" in txt


def test_alunos_banca():
    txt = oficio(tipo_auxilio="Banca de exame ou defesa")
    assert "Assunto: Solicitação de Auxílio Financeiro - Banca de exame ou defesa" in txt
