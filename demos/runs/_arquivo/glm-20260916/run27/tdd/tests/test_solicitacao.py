import pytest

# Contrato testado: POST /solicitacao recebe em JSON os campos do formulário
# (chaves em snake_case) mais a aba ("alunos" ou "docentes"). Solicitação
# válida responde 200 com {"oficio": <texto do ofício>}; inválida responde
# 400 com {"erros": [<mensagens>]}. Os valores chegam como estão nos campos,
# já formatados pelo frontend (R$ 1.500,00, 000.000.000-00, 00000-000,
# dd/mm/aaaa).

DADOS_ALUNOS = {
    "aba": "alunos",
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "Simpósio Brasileiro de Engenharia de Software",
    "periodo_evento": "20 a 26 de setembro de 2026",
    "cidade_evento": "Vitória",
    "estado_evento": "ES",
    "pais_evento": "Brasil",
    "link_evento": "https://sbes.org.br",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e inscrição no evento",
    "apresentacao_trabalho": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "181",
    "complemento": "Sala 2",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "98765-4",
}

OFICIO_ALUNOS = """\
Interessada(o): Maria da Silva - 12345678
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:

Dados do evento
Evento: Simpósio Brasileiro de Engenharia de Software
Período: 20 a 26 de setembro de 2026
Local: Vitória - ES - Brasil
Link do evento: https://sbes.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagem aérea e inscrição no evento

Endereço da(o) interessada(o)
Rua do Anfiteatro, 181
Complemento: Sala 2
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências.
"""

OFICIO_DOCENTES = OFICIO_ALUNOS.replace(
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
).replace(
    "Programa: Ciência da Computação - Mestrado",
    "Programa: Ciência da Computação",
)

DADOS_DOCENTES = {
    chave: valor
    for chave, valor in DADOS_ALUNOS.items()
    if chave not in ("nivel", "tipo_auxilio")
}
DADOS_DOCENTES["aba"] = "docentes"


def enviar(cliente, **substituicoes):
    dados = {**DADOS_ALUNOS, **substituicoes}
    return cliente.post("/solicitacao", =dados)


def enviar_docentes(cliente, **substituicoes):
    dados = {**DADOS_DOCENTES, **substituicoes}
    return cliente.post("/solicitacao", =dados)


def mensagens(resposta):
    return resposta.()["erros"]


def sem_quebras(texto):
    return " ".join(texto.split())


def test_solicitacao_valida_de_alunos_recebe_o_oficio(cliente):
    resposta = enviar(cliente)
    assert resposta.status_code == 200
    assert sem_quebras(resposta.()["oficio"]) == sem_quebras(OFICIO_ALUNOS)


def test_solicitacao_valida_de_docentes_recebe_o_oficio(cliente):
    resposta = enviar_docentes(cliente)
    assert resposta.status_code == 200
    assert sem_quebras(resposta.()["oficio"]) == sem_quebras(OFICIO_DOCENTES)


def test_oficio_preserva_as_quebras_de_linha(cliente):
    oficio = enviar(cliente).()["oficio"]
    linhas = [linha.strip() for linha in oficio.splitlines() if linha.strip()]
    assert linhas[0] == "Interessada(o): Maria da Silva - 12345678"
    assert "Dados do evento" in linhas
    assert "Endereço da(o) interessada(o)" in linhas
    assert "Dados para pagamento" in linhas
    assert linhas[-1] == "Encaminhe-se ao Serviço Financeiro para providências."


def test_linhas_de_campos_opcionais_vazios_nao_aparecem(cliente):
    resposta = enviar(cliente, link_evento="", complemento="")
    oficio = resposta.()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    assert "Evento: Simpósio Brasileiro de Engenharia de Software" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "CEP: 05508-090" in oficio


def test_campos_obrigatorios_vazios_geram_um_unico_aviso(cliente):
    vazios = {campo: "" for campo in DADOS_ALUNOS if campo != "aba"}
    resposta = enviar(cliente, **vazios)
    assert resposta.status_code == 400
    assert mensagens(resposta) == ["Preencha todos os campos"]


def test_n_usp_deve_conter_apenas_numeros(cliente):
    resposta = enviar(cliente, n_usp="12a45678")
    assert resposta.status_code == 400
    assert mensagens(resposta) == ["N. USP deve conter apenas números"]


def test_numero_da_agencia_deve_conter_apenas_numeros(cliente):
    resposta = enviar(cliente, agencia="12a4")
    assert mensagens(resposta) == ["Número da agência deve conter apenas números"]


@pytest.mark.parametrize("valor", ["R$ 0,00", "texto sem número"])
def test_valor_solicitado_deve_ser_maior_que_zero(cliente, valor):
    resposta = enviar(cliente, valor_solicitado=valor)
    assert mensagens(resposta) == ["Valor solicitado deve ser maior que 0"]


@pytest.mark.parametrize("email", ["maria.usp.br", "maria@"])
def test_email_invalido(cliente, email):
    resposta = enviar(cliente, email=email)
    assert mensagens(resposta) == ["E-mail inválido"]


def test_cpf_fora_do_formato(cliente):
    resposta = enviar(cliente, cpf="12345678909")
    assert mensagens(resposta) == ["CPF deve estar no formato 000.000.000-00"]


def test_cep_fora_do_formato(cliente):
    resposta = enviar(cliente, cep="05508090")
    assert mensagens(resposta) == ["CEP deve estar no formato 00000-000"]


def test_data_de_nascimento_fora_do_formato(cliente):
    resposta = enviar(cliente, data_nascimento="01021980")
    assert mensagens(resposta) == [
        "Data de nascimento deve estar no formato dd/mm/aaaa"
    ]


def test_cpf_com_digito_verificador_incorreto(cliente):
    resposta = enviar(cliente, cpf="123.456.789-00")
    assert mensagens(resposta) == ["CPF inválido"]


@pytest.mark.parametrize("data", ["31/02/1980", "10/13/1980"])
def test_data_de_nascimento_inexistente(cliente, data):
    resposta = enviar(cliente, data_nascimento=data)
    assert mensagens(resposta) == ["Data de nascimento inválida"]


def test_todas_as_mensagens_que_se_aplicam_aparecem(cliente):
    resposta = enviar(
        cliente,
        n_usp="12a45678",
        email="maria.usp.br",
        cpf="123.456.789-00",
    )
    assert set(mensagens(resposta)) == {
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CPF inválido",
    }


def test_a_validacao_vale_na_aba_docentes(cliente):
    resposta = enviar_docentes(cliente, n_usp="12a45678")
    assert mensagens(resposta) == ["N. USP deve conter apenas números"]


def test_com_erro_o_oficio_nao_e_gerado(cliente):
    resposta = enviar(cliente, n_usp="12a45678")
    assert resposta.status_code == 400
    assert "oficio" not in resposta.()


def test_confirmacao_mostra_o_titulo_solicitacao_registrada(cliente):
    resposta = enviar(cliente)
    assert resposta.status_code == 200
    tela = cliente.get("/").text + cliente.get("/app.js").text
    assert "Solicitação registrada" in tela + resposta.text
