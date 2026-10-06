def normalizar(texto):
    return texto.replace("\r\n", "\n").strip()


OFICIO_ALUNOS = """\
Interessada(o): Maria da Silva - 1234567
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Simpósio Brasileiro de Computação
Período: 1 a 5 de julho de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://evento.example.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Inscrição e passagens aéreas.

Endereço da(o) interessada(o)
Rua do Anfiteatro, 181
Complemento: Sala 5
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 529.982.247-25
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_DOCENTES = """\
Interessada(o): João Pereira - 7654321
E-mail: joao@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Estatística

A CCP-Estatística aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Banca de defesa de mestrado
Período: 10 de agosto de 2025
Local: Campinas - SP - Brasil
Apresentação de trabalho: Não irá apresentar trabalho
Valor solicitado: R$ 300,00
Detalhamento: Reembolso de transporte.

Endereço da(o) interessada(o)
Av. Professor Lineu Prestes, 338
CEP: 05508-000
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 15/03/1975
CPF: 529.982.247-25
RG / RNM: 98.765.432-1
Banco: Itaú
Agência: 0912
Conta: 45678-9

Encaminhe-se ao Serviço Financeiro para providências."""


def enviar(client, base, **mudancas):
    resposta = client.post("/solicitacao", ={**base, **mudancas})
    assert resposta.status_code == 200
    corpo = resposta.()
    assert corpo["valido"] is True, corpo
    return corpo["oficio"]


def test_oficio_da_aba_alunos(client, dados_alunos):
    assert normalizar(enviar(client, dados_alunos)) == OFICIO_ALUNOS


def test_oficio_da_aba_docentes(client, dados_docentes):
    assert normalizar(enviar(client, dados_docentes)) == OFICIO_DOCENTES


def test_valores_solicitados_formatados_como_moeda(client, dados_alunos):
    casos = {
        "1500": "R$ 15,00",
        "150000": "R$ 1.500,00",
        "150000000": "R$ 1.500.000,00",
    }
    for centavos, moeda in casos.items():
        oficio = enviar(client, dados_alunos, valor_solicitado=centavos)
        assert f"Valor solicitado: {moeda}" in oficio


def test_campos_opcionais_vazios_saem_do_oficio(client, dados_alunos):
    oficio = enviar(client, dados_alunos, link_evento="", complemento="")
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "CEP: 05508-090" in oficio


def test_detalhamento_em_varias_linhas(client, dados_alunos):
    oficio = enviar(client, dados_alunos, detalhamento="linha um\nlinha dois")
    assert "Detalhamento: linha um\nlinha dois" in oficio
