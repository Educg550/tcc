"""Testes do backend que decide a validade e redige o oficio."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


CAMPOS = {
    "aba": (["aba", "tipo_formulario", "formulario", "publico"], "alunos"),
    "nome": (
        ["nome_completo", "nome_completo_sem_abreviar", "nomeCompleto", "nome"],
        "Fulano de Tal",
    ),
    "nusp": (["n_usp", "nusp", "numero_usp", "numero_do_usp", "num_usp"], "12345678"),
    "programa": (["programa"], "Ciência da Computação"),
    "nivel": (["nivel", "nível"], "Mestrado"),
    "tipo_auxilio": (["tipo_de_auxilio", "tipo_auxilio"], "Participação em evento"),
    "email": (["email", "e_mail", "e-mail"], "fulano@usp.br"),
    "evento": (["nome_do_evento", "nome_evento", "evento"], "Congresso de Teste"),
    "periodo": (
        ["periodo", "periodo_do_evento", "período", "periodo_evento"],
        "01/01/2024 a 05/01/2024",
    ),
    "cidade_evento": (["cidade_do_evento", "cidade_evento"], "Campinas"),
    "estado_evento": (["estado_do_evento", "estado_evento"], "RJ"),
    "pais_evento": (["pais_do_evento", "pais_evento", "país_do_evento", "pais"], "Brasil"),
    "link_evento": (["link_do_evento", "link_evento", "link"], ""),
    "valor": (["valor_solicitado", "valor"], "R$ 15,00"),
    "detalhamento": (
        ["detalhamento", "detalhamento_do_pedido"],
        "Passagens e hospedagem",
    ),
    "apresentacao": (
        ["ira_apresentar_trabalho", "apresentar_trabalho", "tipo_apresentacao"],
        "Pôster",
    ),
    "nascimento": (["data_de_nascimento", "data_nascimento", "nascimento"], "01/02/1980"),
    "logradouro": (["logradouro"], "Av. Prof. Luciano Gualberto"),
    "numero_endereco": (["numero", "número", "num"], "100"),
    "complemento": (["complemento"], ""),
    "bairro": (["bairro"], "Butantã"),
    "cep": (["cep"], "05508-090"),
    "cidade_endereco": (["cidade"], "São Paulo"),
    "estado_endereco": (["estado"], "SP"),
    "cpf": (["cpf"], "111.444.777-35"),
    "rg": (["rg", "rnm", "rg_rnm"], "12.345.678-9"),
    "banco": (["banco", "nome_do_banco"], "Banco do Brasil"),
    "agencia": (
        ["agencia", "agência", "numero_da_agencia", "numero_agencia", "n_agencia"],
        "1234",
    ),
    "conta": (["conta", "numero_da_conta", "numero_conta"], "5678-9"),
}


def _spec():
    r = client.get("/openapi.json")
    assert r.status_code == 200, "a aplicacao deve expor /openapi.json"
    return r.json()


def _posts():
    achados = []
    for caminho, operacoes in _spec().get("paths", {}).items():
        if "post" in operacoes:
            achados.append((caminho, operacoes["post"]))
    return achados


def _content_type(op):
    conteudo = op.get("requestBody", {}).get("content", {})
    if "application/json" in conteudo:
        return "application/json"
    if conteudo:
        return next(iter(conteudo))
    return "application/json"


def _post(dados, endpoint=None):
    if endpoint is None:
        posts = _posts()
        assert posts, "a aplicacao deve expor um endpoint POST para receber a solicitacao"
        endpoint = posts[0]
    caminho, operacoes = endpoint
    if _content_type(operacoes) == "application/json":
        return client.post(caminho, json=dados)
    return client.post(caminho, data=dados)


def _endpoint_docentes():
    posts = _posts()
    assert posts
    for caminho, operacoes in posts:
        if "docente" in caminho.lower():
            return (caminho, operacoes)
    return posts[0]


def _payload(trocas=None):
    trocas = trocas or {}
    dados = {}
    for chave, (aliases, valor) in CAMPOS.items():
        v = trocas.get(chave, valor)
        for alias in aliases:
            dados[alias] = v
    return dados


def test_solicitacao_vazia_exige_todos_os_campos():
    r = _post({})
    assert "Preencha todos os campos" in r.text


def test_envio_valido_gera_oficio():
    r = _post(_payload())
    assert r.status_code == 200
    t = r.text
    assert "Interessada(o): Fulano de Tal - 12345678" in t
    assert "E-mail: fulano@usp.br" in t
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in t
    assert "Programa: Ciência da Computação - Mestrado" in t
    assert "Evento: Congresso de Teste" in t
    assert "Período: 01/01/2024 a 05/01/2024" in t
    assert "Local: Campinas - RJ - Brasil" in t
    assert "Apresentação de trabalho: Pôster" in t
    assert "Valor solicitado: R$ 15,00" in t
    assert "Detalhamento: Passagens e hospedagem" in t
    assert "Av. Prof. Luciano Gualberto, 100" in t
    assert "CEP: 05508-090" in t
    assert "Butantã, São Paulo - SP" in t
    assert "Data de nascimento: 01/02/1980" in t
    assert "CPF: 111.444.777-35" in t
    assert "RG / RNM: 12.345.678-9" in t
    assert "Banco: Banco do Brasil" in t
    assert "Agência: 1234" in t
    assert "Conta: 5678-9" in t
    assert "Encaminhe-se ao Serviço Financeiro para providências." in t


def test_campos_opcionais_vazios_saem_do_oficio():
    r = _post(_payload())
    assert r.status_code == 200
    t = r.text
    assert "Link do evento:" not in t
    assert "Complemento:" not in t


def test_oficio_docentes_usa_verba_do_programa():
    dados = _payload({"aba": "docentes"})
    for chave in ("nivel", "tipo_auxilio"):
        for alias in CAMPOS[chave][0]:
            dados.pop(alias, None)
    r = _post(dados, endpoint=_endpoint_docentes())
    assert r.status_code == 200
    t = r.text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in t
    assert "Programa: Ciência da Computação" in t


def test_n_usp_nao_numerico():
    r = _post(_payload({"nusp": "abc"}))
    assert "N. USP deve conter apenas números" in r.text


def test_agencia_nao_numerica():
    r = _post(_payload({"agencia": "12a4"}))
    assert "Número da agência deve conter apenas números" in r.text


def test_valor_solicitado_nao_positivo():
    r = _post(_payload({"valor": "R$ 0,00"}))
    assert "Valor solicitado deve ser maior que 0" in r.text


def test_email_invalido():
    r = _post(_payload({"email": "fulano"}))
    assert "E-mail inválido" in r.text


def test_cpf_fora_do_formato():
    r = _post(_payload({"cpf": "12345678909"}))
    assert "CPF deve estar no formato 000.000.000-00" in r.text


def test_cep_fora_do_formato():
    r = _post(_payload({"cep": "1234567"}))
    assert "CEP deve estar no formato 00000-000" in r.text


def test_data_fora_do_formato():
    r = _post(_payload({"nascimento": "1980-02-01"}))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.text


def test_cpf_com_digitos_verificadores_errados():
    r = _post(_payload({"cpf": "111.444.777-00"}))
    assert "CPF inválido" in r.text


def test_data_inexistente():
    r = _post(_payload({"nascimento": "32/13/1980"}))
    assert "Data de nascimento inválida" in r.text


def test_multiplos_erros_aparecem_juntos():
    r = _post(_payload({"email": "fulano", "cep": "1234567"}))
    assert "E-mail inválido" in r.text
    assert "CEP deve estar no formato 00000-000" in r.text


def test_erro_nao_gera_oficio():
    r = _post(_payload({"email": "fulano"}))
    assert "Interessada(o):" not in r.text
