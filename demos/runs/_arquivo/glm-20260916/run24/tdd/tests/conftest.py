import os
import sys
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def client():
    from app import app

    with TestClient(app, raise_server_exceptions=False) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def pagina(client):
    resposta = client.get("/")
    assert resposta.status_code == 200, "a página do formulário não foi servida em /"
    assert "text/html" in resposta.headers.get("content-type", "")
    return resposta.text


VAZIOS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class Analisador(HTMLParser):
    """Coleta (tag, atributos, texto interno) de todos os elementos do HTML."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elementos = []
        self.pilha = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in VAZIOS:
            self.elementos.append((tag, dict(attrs), ""))
            return
        self.pilha.append([tag, dict(attrs), []])

    def handle_startendtag(self, tag, attrs):
        self.elementos.append((tag, dict(attrs), ""))

    def handle_data(self, dados):
        if self.pilha:
            self.pilha[-1][2].append(dados)

    def handle_endtag(self, tag):
        for indice in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[indice][0] == tag:
                nome, atributos, textos = self.pilha.pop(indice)
                if self.pilha:
                    self.pilha[-1][2].extend(textos)
                self.elementos.append((nome, atributos, "".join(textos).strip()))
                return


@pytest.fixture(scope="session")
def elementos(pagina):
    return Analisador(pagina).elementos


def folhas_de_estilo(pagina):
    return [
        attrs["href"]
        for tag, attrs, _ in Analisador(pagina).elementos
        if tag == "link"
        and "stylesheet" in (attrs.get("rel") or "").lower()
        and attrs.get("href")
    ]


def roteiros(pagina):
    return [
        attrs["src"]
        for tag, attrs, _ in Analisador(pagina).elementos
        if tag == "script" and attrs.get("src")
    ]


@pytest.fixture(scope="session")
def css(client, pagina):
    caminhos = folhas_de_estilo(pagina)
    assert caminhos, "a página não referencia nenhuma folha de estilo"
    conteudos = []
    for caminho in caminhos:
        assert not caminho.startswith(("http://", "https://", "//")), (
            f"folha de estilo remota: {caminho}"
        )
        resposta = client.get(caminho)
        assert resposta.status_code == 200, f"folha de estilo não servida: {caminho}"
        conteudos.append(resposta.text)
    return "\n".join(conteudos)


@pytest.fixture(scope="session")
def appjs(client, pagina):
    caminhos = roteiros(pagina)
    assert caminhos, "a página não referencia nenhum arquivo JavaScript"
    conteudos = []
    for caminho in caminhos:
        assert not caminho.startswith(("http://", "https://", "//")), (
            f"JavaScript remoto: {caminho}"
        )
        resposta = client.get(caminho)
        assert resposta.status_code == 200, f"JavaScript não servido: {caminho}"
        conteudos.append(resposta.text)
    return "\n".join(conteudos)


def rotas_post(client):
    return [
        rota.path
        for rota in client.app.routes
        if getattr(rota, "methods", None) and "POST" in rota.methods
    ]


@pytest.fixture(scope="session")
def enviar(client):
    rotas = rotas_post(client)
    assert rotas, "o backend não expõe nenhuma rota POST para receber a solicitação"

    def _enviar(payload):
        respostas = []
        for rota in rotas:
            respostas.append(client.post(rota, =payload))
            respostas.append(client.post(rota, data=payload))
        return respostas

    return _enviar


@pytest.fixture(scope="session")
def achar_resposta(enviar):
    """Devolve a resposta cujo corpo contém todos os trechos pedidos, ou None."""

    def _achar(payload, trechos):
        for resposta in enviar(payload):
            if all(trecho in resposta.text for trecho in trechos):
                return resposta
        return None

    return _achar


@pytest.fixture(scope="session")
def alterar():
    def _alterar(payload, valores=None, remover=()):
        novo = dict(payload)
        for chave, valor in (valores or {}).items():
            novo[chave] = valor
        for chave in remover:
            novo.pop(chave, None)
        return novo

    return _alterar


@pytest.fixture(scope="session")
def solicitacao_alunos():
    return {
        "aba": "alunos",
        "perfil": "alunos",
        "tipo_solicitante": "alunos",
        "nome_completo": "Maria Souza da Silva",
        "nome": "Maria Souza da Silva",
        "nomeCompleto": "Maria Souza da Silva",
        "NOME COMPLETO - SEM ABREVIAR": "Maria Souza da Silva",
        "n_usp": "1234567",
        "numero_usp": "1234567",
        "nUSP": "1234567",
        "numeroUSP": "1234567",
        "N. USP": "1234567",
        "programa": "Ciência da Computação",
        "PROGRAMA": "Ciência da Computação",
        "nivel": "Mestrado",
        "NÍVEL": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "tipo_auxilio": "Participação em evento",
        "tipoDeAuxilio": "Participação em evento",
        "TIPO DE AUXÍLIO": "Participação em evento",
        "email": "maria@ime.usp.br",
        "e_mail": "maria@ime.usp.br",
        "E-MAIL": "maria@ime.usp.br",
        "nome_do_evento": "Congresso Brasileiro de Computação",
        "evento": "Congresso Brasileiro de Computação",
        "nomeDoEvento": "Congresso Brasileiro de Computação",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Computação",
        "periodo": "10/03/2025 a 14/03/2025",
        "periodo_do_evento": "10/03/2025 a 14/03/2025",
        "periodoDoEvento": "10/03/2025 a 14/03/2025",
        "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/03/2025 a 14/03/2025",
        "cidade_do_evento": "Campinas",
        "cidade_evento": "Campinas",
        "cidadeDoEvento": "Campinas",
        "CIDADE DO EVENTO, EXAME OU DEFESA": "Campinas",
        "estado_do_evento": "SP",
        "estado_evento": "SP",
        "estadoDoEvento": "SP",
        "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
        "pais_do_evento": "Brasil",
        "pais_evento": "Brasil",
        "paisDoEvento": "Brasil",
        "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
        "link_do_evento": "https://cmyc.ime.usp.br",
        "link": "https://cmyc.ime.usp.br",
        "linkDoEvento": "https://cmyc.ime.usp.br",
        "LINK DO EVENTO, EXAME OU DEFESA": "https://cmyc.ime.usp.br",
        "valor_solicitado": "R$ 1.500,00",
        "valor": "R$ 1.500,00",
        "valorSolicitado": "R$ 1.500,00",
        "VALOR SOLICITADO (R$)": "R$ 1.500,00",
        "detalhamento": "Inscrição no evento e passagem aérea",
        "detalhamento_do_pedido": "Inscrição no evento e passagem aérea",
        "detalhamentoDoPedido": "Inscrição no evento e passagem aérea",
        "DETALHAMENTO DO PEDIDO": "Inscrição no evento e passagem aérea",
        "apresentacao_trabalho": "Pôster",
        "ira_apresentar_trabalho": "Pôster",
        "apresentacaoTrabalho": "Pôster",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
        "data_de_nascimento": "01/02/1980",
        "data_nascimento": "01/02/1980",
        "dataDeNascimento": "01/02/1980",
        "DATA DE NASCIMENTO": "01/02/1980",
        "logradouro": "Rua do Anfiteatro",
        "LOGRADOURO": "Rua do Anfiteatro",
        "numero": "181",
        "numero_endereco": "181",
        "NÚMERO": "181",
        "complemento": "Sala 212",
        "COMPLEMENTO": "Sala 212",
        "bairro": "Butantã",
        "BAIRRO": "Butantã",
        "cep": "05508-090",
        "CEP": "05508-090",
        "cidade": "São Paulo",
        "CIDADE": "São Paulo",
        "estado": "SP",
        "ESTADO": "SP",
        "cpf": "529.982.247-25",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": "529.982.247-25",
        "rg": "12.345.678-9",
        "rg_rnm": "12.345.678-9",
        "rgRnm": "12.345.678-9",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
        "nome_do_banco": "Banco do Brasil",
        "banco": "Banco do Brasil",
        "nomeDoBanco": "Banco do Brasil",
        "NOME DO BANCO": "Banco do Brasil",
        "agencia": "1234",
        "numero_da_agencia": "1234",
        "numeroDaAgencia": "1234",
        "NÚMERO DA AGÊNCIA": "1234",
        "numero_da_conta": "98765-4",
        "conta": "98765-4",
        "numeroDaConta": "98765-4",
        "NÚMERO DA CONTA": "98765-4",
    }


@pytest.fixture(scope="session")
def solicitacao_docentes(solicitacao_alunos):
    docentes = {
        chave: valor
        for chave, valor in solicitacao_alunos.items()
        if chave
        not in (
            "nivel",
            "NÍVEL",
            "tipo_de_auxilio",
            "tipo_auxilio",
            "tipoDeAuxilio",
            "TIPO DE AUXÍLIO",
        )
    }
    docentes["aba"] = "docentes"
    docentes["perfil"] = "docentes"
    docentes["tipo_solicitante"] = "docentes"
    return docentes
