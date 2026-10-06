from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)


def _endpoint():
    caminhos = cliente.get("/openapi.json").json()["paths"]
    posts = [caminho for caminho, metodos in caminhos.items() if "post" in metodos]
    assert posts, "a aplicação deve receber a solicitação por POST"
    return posts[0]


def _enviar(dados):
    caminho = _endpoint()
    resposta = cliente.post(caminho, json=dados)
    if resposta.status_code == 422:
        resposta = cliente.post(caminho, data=dados)
    return resposta


def _dados_alunos(**alteracoes):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento_nome": "Congresso Brasileiro de Computação",
        "evento_periodo": "01/03/2025 a 05/03/2025",
        "evento_cidade": "São Paulo",
        "evento_estado": "SP",
        "evento_pais": "Brasil",
        "evento_link": "https://evento.exemplo.com",
        "valor": "R$ 1.500,00",
        "detalhamento": "Passagem aérea e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(alteracoes)
    return dados


def _dados_docentes(**alteracoes):
    dados = _dados_alunos()
    dados["aba"] = "docentes"
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.update(alteracoes)
    return dados


def test_oficio_da_aba_alunos():
    resposta = _enviar(_dados_alunos())
    assert resposta.status_code < 400
    texto = resposta.text
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "A CCP-Ciência da Computação aprovou na data de hoje" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Período: 01/03/2025 a 05/03/2025" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://evento.exemplo.com" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e hospedagem" in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Bloco B" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_da_aba_docentes():
    texto = _enviar(_dados_docentes()).text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação -" not in texto


def test_campos_obrigatorios_vazios():
    dados = {chave: "" for chave in _dados_alunos()}
    dados["aba"] = "alunos"
    texto = _enviar(dados).text
    assert texto.count("Preencha todos os campos") == 1
    assert "Interessada(o):" not in texto


def test_n_usp_apenas_digitos():
    texto = _enviar(_dados_alunos(n_usp="12A45")).text
    assert "N. USP deve conter apenas números" in texto


def test_agencia_apenas_digitos():
    texto = _enviar(_dados_alunos(agencia="12-34")).text
    assert "Número da agência deve conter apenas números" in texto


def test_valor_maior_que_zero():
    texto = _enviar(_dados_alunos(valor="R$ 0,00")).text
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_invalido():
    texto = _enviar(_dados_alunos(email="maria.ime.usp.br")).text
    assert "E-mail inválido" in texto


def test_cpf_fora_do_formato():
    texto = _enviar(_dados_alunos(cpf="12345678909")).text
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cep_fora_do_formato():
    texto = _enviar(_dados_alunos(cep="05508090")).text
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_de_nascimento_fora_do_formato():
    texto = _enviar(_dados_alunos(data_nascimento="01021980")).text
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_cpf_invalido():
    texto = _enviar(_dados_alunos(cpf="123.456.789-00")).text
    assert "CPF inválido" in texto


def test_data_de_nascimento_inexistente():
    texto = _enviar(_dados_alunos(data_nascimento="31/02/1980")).text
    assert "Data de nascimento inválida" in texto


def test_varios_erros_ao_mesmo_tempo():
    texto = _enviar(_dados_alunos(n_usp="12A45", email="maria.ime.usp.br")).text
    assert "N. USP deve conter apenas números" in texto
    assert "E-mail inválido" in texto
    assert "Interessada(o):" not in texto


def test_link_do_evento_vazio_sai_do_oficio():
    texto = _enviar(_dados_alunos(evento_link="")).text
    assert "Interessada(o): Maria da Silva" in texto
    assert "Link do evento" not in texto


def test_complemento_vazio_sai_do_oficio():
    texto = _enviar(_dados_alunos(complemento="")).text
    assert "Interessada(o): Maria da Silva" in texto
    assert "Complemento" not in texto
