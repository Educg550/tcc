import json

from app import app


def _texto(resposta):
    try:
        return json.dumps(resposta.json(), ensure_ascii=False)
    except Exception:
        return resposta.text


def _caminhos_post():
    caminhos = []
    for rota in getattr(app, "routes", []):
        if "POST" in (getattr(rota, "methods", None) or set()):
            caminhos.append(rota.path)
    return caminhos or ["/solicitar", "/api/solicitar", "/api/solicitacao"]


def _enviar(client, dados):
    respostas = []
    for caminho in _caminhos_post():
        respostas.append(client.post(caminho, json=dados))
        respostas.append(client.post(caminho, data=dados))
    return respostas


def _com(respostas, trecho):
    return [resposta for resposta in respostas if trecho in _texto(resposta)]


CAMPOS = {
    "aba": (["aba", "tipo", "tipo_formulario", "formulario", "solicitante", "perfil", "categoria"], "ALUNOS"),
    "nome": (["nome", "nome_completo", "NOME COMPLETO - SEM ABREVIAR"], "Maria Silva Santos"),
    "n_usp": (["n_usp", "nusp", "numero_usp"], "12345678"),
    "programa": (["programa"], "Ciência da Computação"),
    "nivel": (["nivel"], "Doutorado"),
    "tipo_auxilio": (["tipo_auxilio"], "Participação em evento"),
    "email": (["email", "e_mail"], "maria@ime.usp.br"),
    "evento": (["evento", "nome_evento"], "Simpósio Brasileiro de Computação"),
    "periodo": (["periodo", "periodo_evento"], "10/10/2024 a 12/10/2024"),
    "cidade_evento": (["cidade_evento"], "São Paulo"),
    "estado_evento": (["estado_evento"], "SP"),
    "pais_evento": (["pais_evento"], "Brasil"),
    "link": (["link", "link_evento"], "evento.usp.br"),
    "valor": (["valor", "valor_solicitado"], "150000"),
    "detalhamento": (["detalhamento"], "Passagem aérea e hospedagem."),
    "apresentacao": (["apresentacao", "apresenta_trabalho"], "Apresentação oral"),
    "nascimento": (["data_nascimento", "nascimento"], "01/02/1980"),
    "logradouro": (["logradouro"], "Rua do Matão"),
    "numero": (["numero"], "1010"),
    "complemento": (["complemento"], "Bloco B"),
    "bairro": (["bairro"], "Butantã"),
    "cep": (["cep"], "05508-090"),
    "cidade": (["cidade"], "São Paulo"),
    "estado": (["estado"], "SP"),
    "cpf": (["cpf"], "111.444.777-35"),
    "rg": (["rg", "rg_rnm"], "12.345.678-9"),
    "banco": (["banco", "nome_banco"], "Banco do Brasil"),
    "agencia": (["agencia", "numero_agencia"], "1234"),
    "conta": (["conta", "numero_conta"], "56789-0"),
}


OFICIO_OK = "Encaminhe-se ao Serviço Financeiro para providências."


def _dados(**overrides):
    dados = {}
    for chave, (aliases, padrao) in CAMPOS.items():
        valor = overrides.get(chave, padrao)
        if valor is None:
            continue
        for alias in aliases:
            dados[alias] = valor
    return dados


def test_envio_valido_gera_oficio(client):
    respostas = _enviar(client, _dados())
    for trecho in (
        "Interessada(o): Maria Silva Santos - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Doutorado",
        "Evento: Simpósio Brasileiro de Computação",
        "Período: 10/10/2024 a 12/10/2024",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: evento.usp.br",
        "Apresentação de trabalho: Apresentação oral",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea e hospedagem.",
        "Rua do Matão, 1010",
        "Complemento: Bloco B",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Data de nascimento: 01/02/1980",
        "CPF: 111.444.777-35",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-0",
        OFICIO_OK,
    ):
        assert _com(respostas, trecho), trecho


def test_link_e_complemento_vazios_somem_do_oficio(client):
    respostas = _enviar(client, _dados(link="", complemento=""))
    oficios = _com(respostas, OFICIO_OK)
    assert oficios
    for resposta in oficios:
        texto = _texto(resposta)
        assert "Link do evento:" not in texto
        assert "Complemento:" not in texto


def test_campo_obrigatorio_vazio(client):
    respostas = _enviar(client, _dados(nome=None))
    assert _com(respostas, "Preencha todos os campos")
    assert not _com(respostas, OFICIO_OK)


def test_mensagem_de_campo_obrigatorio_aparece_uma_unica_vez(client):
    respostas = _com(_enviar(client, _dados(nome=None, email=None, cpf=None)), "Preencha todos os campos")
    assert respostas
    for resposta in respostas:
        assert _texto(resposta).count("Preencha todos os campos") == 1


def test_n_usp_apenas_digitos(client):
    respostas = _enviar(client, _dados(n_usp="12a45678"))
    assert _com(respostas, "N. USP deve conter apenas números")


def test_agencia_apenas_digitos(client):
    respostas = _enviar(client, _dados(agencia="12a4"))
    assert _com(respostas, "Número da agência deve conter apenas números")


def test_valor_deve_ser_maior_que_zero(client):
    respostas = _enviar(client, _dados(valor="0"))
    assert _com(respostas, "Valor solicitado deve ser maior que 0")


def test_email_invalido(client):
    respostas = _enviar(client, _dados(email="maria.ime.usp.br"))
    assert _com(respostas, "E-mail inválido")


def test_cpf_fora_do_formato(client):
    respostas = _enviar(client, _dados(cpf="12345678909"))
    assert _com(respostas, "CPF deve estar no formato 000.000.000-00")


def test_cep_fora_do_formato(client):
    respostas = _enviar(client, _dados(cep="0550809"))
    assert _com(respostas, "CEP deve estar no formato 00000-000")


def test_data_de_nascimento_fora_do_formato(client):
    respostas = _enviar(client, _dados(nascimento="01021980"))
    assert _com(respostas, "Data de nascimento deve estar no formato dd/mm/aaaa")


def test_cpf_com_digitos_verificadores_errados(client):
    respostas = _enviar(client, _dados(cpf="123.456.789-00"))
    assert _com(respostas, "CPF inválido")


def test_data_de_nascimento_inexistente(client):
    respostas = _enviar(client, _dados(nascimento="31/02/1980"))
    assert _com(respostas, "Data de nascimento inválida")


def test_diversos_erros_aparecem_juntos(client):
    respostas = _enviar(client, _dados(nome=None, email="sem-arroba", n_usp="abc"))
    texto = " ".join(_texto(resposta) for resposta in respostas)
    assert "Preencha todos os campos" in texto
    assert "E-mail inválido" in texto
    assert "N. USP deve conter apenas números" in texto
    assert OFICIO_OK not in texto


def test_oficio_de_docentes_nao_tem_nivel_nem_tipo_de_auxilio(client):
    respostas = _enviar(client, _dados(aba="DOCENTES", nivel=None, tipo_auxilio=None))
    assert _com(respostas, "Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
    assert _com(respostas, "Programa: Ciência da Computação")
