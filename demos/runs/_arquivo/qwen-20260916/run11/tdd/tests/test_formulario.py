import json
import re


DADOS_ALUNO = {
    "nome": "Maria da Silva",
    "nusp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "SBIAE 2026",
    "periodo": "10/06/2026 a 12/06/2026",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://sbiae.org",
    "valor": 150000,
    "detalhamento": "Apresentar artigo.",
    "apresentacao": "Apresentação oral",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Apto 20",
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

DADOS_DOCENTE = {
    k: v for k, v in DADOS_ALUNO.items() if k not in ("nivel", "tipo_auxilio")
}


def _alunos(client):
    return client.post("/solicitacoes/alunos", json=DADOS_ALUNO)


def _docentes(client):
    return client.post("/solicitacoes/docentes", json=DADOS_DOCENTE)


def _erros(client, dados):
    r = client.post("/solicitacoes/alunos", json=dados)
    assert r.status_code in (400, 422), r.text
    return r.json()["erros"]


def _dados(**mudancas):
    dados = dict(DADOS_ALUNO)
    dados.update(mudancas)
    return dados


def test_rota_inicial(client):
    r = client.get("/")
    assert r.status_code == 200


def test_estaticos_servidos(client):
    for caminho, texto in (
        ("/index.html", "ALUNOS"),
        ("/style.css", "#1094ab"),
        ("/app.js", "R$ "),
    ):
        r = client.get(caminho)
        assert r.status_code == 200, caminho
        assert texto in r.text, caminho


def test_abas_com_rotulos_exatos(client):
    corpo = client.get("/").text
    assert corpo.index("ALUNOS") < corpo.index("DOCENTES")


def test_bloco_solicitante_e_evento(client):
    corpo = client.get("/").text
    assert "SOLICITANTE E EVENTO" in corpo


def test_bloco_endereco(client):
    corpo = client.get("/").text
    assert "ENDEREÇO DO SOLICITANTE" in corpo


def test_bloco_pagamento(client):
    corpo = client.get("/").text
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in corpo


def test_rotulos_e_ordem(client):
    corpo = client.get("/").text
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
    posicoes = [corpo.index(label) for label in rotulos]
    assert posicoes == sorted(posicoes), rotulos


def test_niveis(client):
    corpo = client.get("/").text
    assert "Mestrado" in corpo and "Doutorado" in corpo


def test_tipos_de_auxilio(client):
    corpo = client.get("/").text
    for tipo in ("Participação em evento", "Banca de exame ou defesa", "Outro"):
        assert tipo in corpo


def test_apresentacao(client):
    corpo = client.get("/").text
    for opcao in (
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in corpo


def test_campos_formataveis_com_id(client):
    corpo = client.get("/").text
    for campo in ("valor", "cpf", "cep", "data_nascimento"):
        assert f'id="{campo}"' in corpo


def test_placeholder_em_todos_os_campos(client):
    corpo = client.get("/").text
    campos = set(re.findall(r'<(?:input|textarea|select)[^>]*name="([^"]+)"', corpo))
    assert campos
    com_placeholder = set(re.findall(r'<(?:input|textarea|select)[^>]*placeholder="[^"]+"', corpo))
    assert "input" in corpo
    assert campos == {"nome", "nusp", "programa", "nivel", "tipo_auxilio", "email",
                      "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
                      "link_evento", "valor", "detalhamento", "apresentacao",
                      "data_nascimento", "logradouro", "numero", "complemento", "bairro",
                      "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"}


def test_btn_enviar(client):
    assert "Enviar solicitação" in client.get("/").text


def test_logotipo(client):
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200


def test_oficio_aluno(client):
    r = _alunos(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Solicitação registrada" in body["titulo"]
    texto = body["oficio"]
    for marcador in ("<<", ">>"):
        assert marcador not in texto
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Doutorado" in texto
    assert "A CCP-Ciência da Computação" in texto
    assert "Evento: SBIAE 2026" in texto
    assert "Período: 10/06/2026 a 12/06/2026" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://sbiae.org" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Apresentar artigo." in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Apto 20" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_docente(client):
    r = _docentes(client)
    assert r.status_code == 200, r.text
    texto = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação\n" in texto
    assert "Participação em evento" not in texto
    assert "Doutorado" not in texto


def test_link_vazio_omisso(client):
    r = client.post("/solicitacoes/alunos", json=_dados(link_evento=""))
    assert r.status_code == 200, r.text
    texto = r.json()["oficio"]
    assert "Link do evento" not in texto


def test_complemento_vazio_omisso(client):
    r = client.post("/solicitacoes/alunos", json=_dados(complemento=""))
    assert r.status_code == 200, r.text
    texto = r.json()["oficio"]
    assert "Complemento" not in texto


def test_campo_obrigatorio_vazio(client):
    assert "Preencha todos os campos" in _erros(client, _dados(nome=""))


def test_unica_msg_campos_vazios(client):
    erros = _erros(client, _dados(nome="", email="", valor=0, programa=""))
    assert erros.count("Preencha todos os campos") == 1


def test_nusp_invalido(client):
    assert "N. USP deve conter apenas números" in _erros(client, _dados(nusp="12a34"))


def test_agencia_invalida(client):
    assert "Número da agência deve conter apenas números" in _erros(client, _dados(agencia="12a3"))


def test_valor_zero(client):
    assert "Valor solicitado deve ser maior que 0" in _erros(client, _dados(valor=0))


def test_valor_negativo(client):
    assert "Valor solicitado deve ser maior que 0" in _erros(client, _dados(valor=-100))


def test_email_invalido(client):
    assert "E-mail inválido" in _erros(client, _dados(email="maria@"))


def test_email_sem_arroba(client):
    assert "E-mail inválido" in _erros(client, _dados(email="maria.ime.usp.br"))


def test_cpf_formato_errado(client):
    assert "CPF deve estar no formato 000.000.000-00" in _erros(client, _dados(cpf="12345678909"))


def test_cep_formato_errado(client):
    assert "CEP deve estar no formato 00000-000" in _erros(client, _dados(cep="05508090"))


def test_data_formato_errado(client):
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _erros(client, _dados(data_nascimento="1980-02-01"))


def test_cpf_digito_verificador(client):
    assert "CPF inválido" in _erros(client, _dados(cpf="123.456.789-00"))


def test_data_inexistente(client):
    assert "Data de nascimento inválida" in _erros(client, _dados(data_nascimento="31/02/1980"))


def test_mes_invalido(client):
    assert "Data de nascimento inválida" in _erros(client, _dados(data_nascimento="01/13/1980"))


def test_varios_erros_simultaneos(client):
    erros = _erros(client, _dados(nusp="abc", cep="123456"))
    assert "N. USP deve conter apenas números" in erros
    assert "CEP deve estar no formato 00000-000" in erros


def test_erro_nao_gera_oficio(client):
    r = client.post("/solicitacoes/alunos", json=_dados(nome=""))
    assert "oficio" not in r.json()


def test_cliente_tem_metodo_post(client):
    assert hasattr(client, "post")
