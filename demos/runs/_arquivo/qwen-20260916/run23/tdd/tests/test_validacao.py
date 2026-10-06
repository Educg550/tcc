import pytest

ALUNOS = {
    "aba": "alunos",
    "NOME COMPLETO - SEM ABREVIAR": "Ana Souza",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "ana@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBIE 2025",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "01/09/2025 a 05/09/2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Fortaleza",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "CE",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbie.org",
    "VALOR SOLICITADO (R$)": "150000",
    "DETALHAMENTO DO PEDIDO": "Custo de inscrição",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Apto 2",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "56789-0",
}

DOCENTES = {k: v for k, v in ALUNOS.items() if k not in ("NÍVEL", "TIPO DE AUXÍLIO")}
DOCENTES["aba"] = "docentes"


def _post(client, dados):
    return client.post("/solicitacao", json=dados)


@pytest.mark.parametrize("dados", [ALUNOS, DOCENTES], ids=["alunos", "docentes"])
def test_valido_nao_erros(client, dados):
    assert "erros" not in _post(client, dados).json()


def _erro(client, campo, valor, dados=None):
    d = dict(dados or ALUNOS)
    d[campo] = valor
    r = _post(client, d)
    assert r.status_code >= 400, "resposta inválida deve ser de erro"
    return r.json()["erros"]


@pytest.mark.parametrize(
    "campo,valor,esperado",
    [
        ("N. USP", "12a34", "N. USP deve conter apenas números"),
        ("NÚMERO DA AGÊNCIA", "12x4", "Número da agência deve conter apenas números"),
        ("VALOR SOLICITADO (R$)", "0", "Valor solicitado deve ser maior que 0"),
        ("VALOR SOLICITADO (R$)", "-5", "Valor solicitado deve ser maior que 0"),
        ("VALOR SOLICITADO (R$)", "1,5", "Valor solicitado deve ser maior que 0"),
        ("E-MAIL", "sem-arroba", "E-mail inválido"),
        ("E-MAIL", "a@", "E-mail inválido"),
        ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "123.456.789", "CPF deve estar no formato 000.000.000-00"),
        ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "111.111.111-11", "CPF inválido"),
        ("CEP", "05508090", "CEP deve estar no formato 00000-000"),
        ("DATA DE NASCIMENTO", "01-02-1980", "Data de nascimento deve estar no formato dd/mm/aaaa"),
        ("DATA DE NASCIMENTO", "31/02/1980", "Data de nascimento inválida"),
        ("DATA DE NASCIMENTO", "01/13/1980", "Data de nascimento inválida"),
    ],
)
def test_mensagens_de_erro(client, campo, valor, esperado):
    erros = _erro(client, campo, valor)
    assert esperado in erros
    assert "Preencha todos os campos" not in erros


@pytest.mark.parametrize("campo", ["NOME COMPLETO - SEM ABREVIAR", "PROGRAMA", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"])
def test_obrigatorio_vazio(client, campo):
    assert _erro(client, campo, "") == ["Preencha todos os campos"]


@pytest.mark.parametrize("campo", ["LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"])
def test_ocionais_vazios(client, campo):
    assert "erros" not in _post(client, {**ALUNOS, campo: ""}).json()


def test_apenas_um_obrigatorio_faltante(client):
    erros = _erro(client, "NOME COMPLETO - SEM ABREVIAR", "")
    assert erros.count("Preencha todos os campos") == 1


def test_erros_se_acumulam(client):
    erros = _erro(client, "N. USP", "", {**ALUNOS, "CEP": "0"})
    assert "Preencha todos os campos" in erros
    assert "CEP deve estar no formato 00000-000" in erros
