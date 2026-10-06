import pytest
from fastapi.testclient import TestClient

from app import app


def _dados_alunos():
    return {
        "ABA": "ALUNOS",
        "NOME COMPLETO - SEM ABREVIAR": "Maria Souza",
        "N. USP": "1234567",
        "PROGRAMA": "Ciência da Computação",
        "NÍVEL": "Mestrado",
        "TIPO DE AUXÍLIO": "Participação em evento",
        "E-MAIL": "maria@usp.br",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBBD 2025",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "1 a 4 de outubro de 2025",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://sbbd.org.br",
        "VALOR SOLICITADO (R$)": "R$ 1.500,00",
        "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição no evento",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "DATA DE NASCIMENTO": "01/02/1980",
        "LOGRADOURO": "Rua do Anfiteatro",
        "NÚMERO": "123",
        "COMPLEMENTO": "Sala 5",
        "BAIRRO": "Cidade Universitária",
        "CEP": "05508-090",
        "CIDADE": "São Paulo",
        "ESTADO": "SP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "NOME DO BANCO": "Banco do Brasil",
        "NÚMERO DA AGÊNCIA": "1234",
        "NÚMERO DA CONTA": "98765-4",
    }


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def dados_alunos():
    return _dados_alunos()


@pytest.fixture
def dados_docentes():
    dados = _dados_alunos()
    dados["ABA"] = "DOCENTES"
    del dados["NÍVEL"]
    del dados["TIPO DE AUXÍLIO"]
    return dados


@pytest.fixture
def oficio_esperado():
    def construir(dados):
        if dados.get("ABA") == "DOCENTES":
            assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
            programa = f"Programa: {dados['PROGRAMA']}"
        else:
            assunto = f"Solicitação de Auxílio Financeiro - {dados['TIPO DE AUXÍLIO']}"
            programa = f"Programa: {dados['PROGRAMA']} - {dados['NÍVEL']}"

        linhas = [
            f"Interessada(o): {dados['NOME COMPLETO - SEM ABREVIAR']} - {dados['N. USP']}",
            f"E-mail: {dados['E-MAIL']}",
            f"Assunto: {assunto}",
            programa,
            "",
            f"A CCP-{dados['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
            "interessada(o) acima, conforme segue:",
            "",
            "Dados do evento",
            f"Evento: {dados['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
            f"Período: {dados['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
            f"Local: {dados['CIDADE DO EVENTO, EXAME OU DEFESA']} - {dados['ESTADO DO EVENTO, EXAME OU DEFESA']} - {dados['PAÍS DO EVENTO, EXAME OU DEFESA']}",
        ]
        if dados.get("LINK DO EVENTO, EXAME OU DEFESA"):
            linhas.append(f"Link do evento: {dados['LINK DO EVENTO, EXAME OU DEFESA']}")
        linhas += [
            f"Apresentação de trabalho: {dados['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
            f"Valor solicitado: {dados['VALOR SOLICITADO (R$)']}",
            f"Detalhamento: {dados['DETALHAMENTO DO PEDIDO']}",
            "",
            "Endereço da(o) interessada(o)",
            f"{dados['LOGRADOURO']}, {dados['NÚMERO']}",
        ]
        if dados.get("COMPLEMENTO"):
            linhas.append(f"Complemento: {dados['COMPLEMENTO']}")
        linhas += [
            f"CEP: {dados['CEP']}",
            f"{dados['BAIRRO']}, {dados['CIDADE']} - {dados['ESTADO']}",
            "",
            "Dados para pagamento",
            f"Data de nascimento: {dados['DATA DE NASCIMENTO']}",
            f"CPF: {dados['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
            f"RG / RNM: {dados['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
            f"Banco: {dados['NOME DO BANCO']}",
            f"Agência: {dados['NÚMERO DA AGÊNCIA']}",
            f"Conta: {dados['NÚMERO DA CONTA']}",
            "",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ]
        return linhas

    return construir
