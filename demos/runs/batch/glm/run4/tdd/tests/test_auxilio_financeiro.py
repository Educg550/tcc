"""Testes da aplicação de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import sys
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
API = "/api/solicitacao"

# ---------------------------------------------------------------------------
# Rótulos e textos visíveis, exatamente como no requisito
# ---------------------------------------------------------------------------

ROTULOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS_COMUNS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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

ROTULOS_SO_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]

OPCOES_SO_ALUNOS = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
]

OPCOES_DE_AMBAS = [
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]

# ---------------------------------------------------------------------------
# Dados de exemplo e ofícios esperados
# ---------------------------------------------------------------------------


def solicitacao_alunos(**alteracoes):
    dados = {
        "perfil": "alunos",
        "nome_completo": "Maria da Silva",
        "numero_usp": "12345678",
        "programa": "Matemática Aplicada",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional de Matemática",
        "periodo_evento": "10 a 12 de setembro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://example.com/congresso",
        "valor_solicitado": "150000",
        "detalhamento": "Inscrição e diárias para o congresso.",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Prédio da Computação",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg_rnm": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(alteracoes)
    return dados


def solicitacao_docentes(**alteracoes):
    dados = solicitacao_alunos()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.update(
        perfil="docentes",
        nome_completo="João Carlos Nogueira",
        numero_usp="98765432",
        programa="Estatística",
        email="jcn@ime.usp.br",
    )
    dados.update(alteracoes)
    return dados


OFICIO_ALUNOS = """Interessada(o): Maria da Silva - 12345678
E-mail: maria@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Matemática Aplicada - Mestrado

A CCP-Matemática Aplicada aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Congresso Nacional de Matemática
Período: 10 a 12 de setembro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://example.com/congresso
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Inscrição e diárias para o congresso.

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Prédio da Computação
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 12345-6

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_DOCENTES = """Interessada(o): João Carlos Nogueira - 98765432
E-mail: jcn@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Estatística

A CCP-Estatística aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: Congresso Nacional de Matemática
Período: 10 a 12 de setembro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://example.com/congresso
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Inscrição e diárias para o congresso.

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Prédio da Computação
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 12345-6

Encaminhe-se ao Serviço Financeiro para providências."""


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def enviar(dados):
    return client.post(API, json=dados)


def erros_de(dados):
    """Envia uma solicitação inválida e devolve a lista de mensagens de erro."""
    resposta = enviar(dados)
    assert resposta.status_code == 400
    corpo = resposta.json()
    assert "oficio" not in corpo
    return corpo["erros"]


def decodifica(conteudo):
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        return conteudo.decode("latin-1")


def ler(nome):
    return decodifica((RAIZ / nome).read_bytes())


class Analisador(HTMLParser):
    """Coleta, na ordem do documento, os textos, as imagens e os formulários."""

    def __init__(self, fonte):
        super().__init__(convert_charrefs=True)
        self.inicios_de_linha = [0]
        for indice, caractere in enumerate(fonte):
            if caractere == "\n":
                self.inicios_de_linha.append(indice + 1)
        self.pedacos = []
        self.imagens = []
        self.formularios = []
        self._formulario = None
        self._dentro_de_script = 0

    def _posicao_atual(self):
        linha, coluna = self.getpos()
        return self.inicios_de_linha[linha - 1] + coluna

    def handle_starttag(self, tag, atributos):
        posicao = self._posicao_atual()
        if tag == "form":
            self._formulario = {
                "inicio": posicao,
                "fim": None,
                "pedacos": [],
                "controles": [],
            }
        elif tag == "img":
            self.imagens.append((dict(atributos).get("src"), posicao))
        elif tag in ("script", "style"):
            self._dentro_de_script += 1
        elif tag in ("input", "select", "textarea") and self._formulario is not None:
            self._formulario["controles"].append((tag, dict(atributos), posicao))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._dentro_de_script = max(0, self._dentro_de_script - 1)
        elif tag == "form" and self._formulario is not None:
            self._formulario["fim"] = self._posicao_atual()
            self.formularios.append(self._formulario)
            self._formulario = None

    def handle_data(self, dados):
        if self._dentro_de_script:
            return
        texto = " ".join(dados.split())
        if not texto:
            return
        posicao = self._posicao_atual()
        self.pedacos.append((texto, posicao))
        if self._formulario is not None:
            self._formulario["pedacos"].append((texto, posicao))


def analisar(html):
    analisador = Analisador(html)
    analisador.feed(html)
    analisador.close()
    return analisador


def primeira_posicao_em(pedacos, texto):
    for trecho, posicao in pedacos:
        if trecho == texto:
            return posicao
    return None


def posicao_do_texto_contendo(pedacos, texto):
    for trecho, posicao in pedacos:
        if texto in trecho:
            return posicao
    return None


def rotulos_do_formulario(formulario):
    return {trecho for trecho, _ in formulario["pedacos"]}


# ---------------------------------------------------------------------------
# Página e arquivos estáticos
# ---------------------------------------------------------------------------


def test_estaticos_sao_servidos_dos_arquivos_da_raiz():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert resposta.content == (RAIZ / "index.html").read_bytes()

    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert "text/css" in resposta.headers["content-type"]
    assert resposta.content == (RAIZ / "style.css").read_bytes()

    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert "javascript" in resposta.headers["content-type"]
    assert resposta.content == (RAIZ / "app.js").read_bytes()

    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert "image/png" in resposta.headers["content-type"]
    assert resposta.content == (RAIZ / "assets" / "usp-logo.png").read_bytes()


def test_pagina_com_cabecalho_abas_blocos_rotulos_e_botoes():
    html = ler("index.html")
    analisador = analisar(html)

    pos_alunos = primeira_posicao_em(analisador.pedacos, "ALUNOS")
    pos_docentes = primeira_posicao_em(analisador.pedacos, "DOCENTES")
    assert pos_alunos is not None
    assert pos_docentes is not None
    assert pos_alunos < pos_docentes

    pos_usp = posicao_do_texto_contendo(analisador.pedacos, "Universidade de São Paulo")
    assert pos_usp is not None
    assert pos_usp < pos_alunos

    assert len(analisador.formularios) == 2

    de_alunos = [
        formulario
        for formulario in analisador.formularios
        if "NÍVEL" in rotulos_do_formulario(formulario)
    ]
    assert len(de_alunos) == 1
    form_alunos = de_alunos[0]
    form_docentes = next(
        formulario for formulario in analisador.formularios if formulario is not form_alunos
    )

    comuns = set(ROTULOS_COMUNS) | set(ROTULOS_BLOCOS)
    so_alunos = set(ROTULOS_SO_ALUNOS) | set(OPCOES_SO_ALUNOS)
    assert rotulos_do_formulario(form_alunos) >= comuns | so_alunos | set(OPCOES_DE_AMBAS)
    assert rotulos_do_formulario(form_docentes) >= comuns | set(OPCOES_DE_AMBAS)
    assert rotulos_do_formulario(form_docentes).isdisjoint(so_alunos)

    for formulario in analisador.formularios:
        ordem_dos_blocos = [
            primeira_posicao_em(formulario["pedacos"], titulo) for titulo in ROTULOS_BLOCOS
        ]
        assert all(posicao is not None for posicao in ordem_dos_blocos)
        assert ordem_dos_blocos == sorted(ordem_dos_blocos)

        interno = html[formulario["inicio"]:formulario["fim"]]
        pos_botao = interno.rfind("Enviar solicitação")
        assert pos_botao != -1
        for _, _, posicao in formulario["controles"]:
            assert posicao - formulario["inicio"] < pos_botao

    assert html.count("Enviar solicitação") == 2


def test_todo_campo_tem_placeholder_com_exemplo():
    analisador = analisar(ler("index.html"))
    rotulos_conhecidos = {
        rotulo.upper()
        for rotulo in (
            ROTULOS_COMUNS
            + ROTULOS_SO_ALUNOS
            + ROTULOS_BLOCOS
            + OPCOES_SO_ALUNOS
            + OPCOES_DE_AMBAS
        )
    }
    sem_placeholder = {
        "submit",
        "button",
        "reset",
        "hidden",
        "image",
        "file",
        "radio",
        "checkbox",
    }
    for formulario in analisador.formularios:
        for tag, atributos, _ in formulario["controles"]:
            if tag == "select":
                continue
            if (atributos.get("type") or "text").lower() in sem_placeholder:
                continue
            placeholder = (atributos.get("placeholder") or "").strip()
            assert placeholder, f"campo sem placeholder: {atributos}"
            assert placeholder.upper() not in rotulos_conhecidos


def test_cabecalho_com_logotipo_da_usp():
    html = ler("index.html")
    css = ler("style.css")
    assert "assets/usp-logo.png" in html or "assets/usp-logo.png" in css

    analisador = analisar(html)
    for origem, _ in analisador.imagens:
        assert origem is not None and "assets/usp-logo.png" in origem
    if analisador.imagens:
        pos_alunos = primeira_posicao_em(analisador.pedacos, "ALUNOS")
        assert analisador.imagens[0][1] < pos_alunos


def test_cores_e_fonte_da_identidade_visual():
    css = ler("style.css").lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css
    assert "open sans" in css or "sans-serif" in css


def test_sem_recurso_remoto():
    for nome in ("index.html", "style.css", "app.js"):
        conteudo = ler(nome)
        assert "http://" not in conteudo
        assert "https://" not in conteudo
        assert '="//' not in conteudo


def test_titulo_da_confirmacao():
    assert "Solicitação registrada" in ler("index.html") + ler("app.js")


# ---------------------------------------------------------------------------
# Envio válido e ofício
# ---------------------------------------------------------------------------


def test_oficio_de_aluno():
    resposta = enviar(solicitacao_alunos())
    assert resposta.status_code == 200
    assert resposta.json()["oficio"].strip() == OFICIO_ALUNOS.strip()


def test_oficio_de_docente():
    resposta = enviar(solicitacao_docentes())
    assert resposta.status_code == 200
    assert resposta.json()["oficio"].strip() == OFICIO_DOCENTES.strip()


def test_linhas_opcionais_somem_do_oficio_quando_vazias():
    resposta = enviar(solicitacao_alunos(link_evento="", complemento=""))
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    esperado = "\n".join(
        linha
        for linha in OFICIO_ALUNOS.split("\n")
        if not linha.startswith("Link do evento")
        and not linha.startswith("Complemento")
    )
    assert oficio.strip() == esperado.strip()

    resposta = enviar(solicitacao_alunos(link_evento=""))
    oficio = resposta.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento: Prédio da Computação" in oficio


def test_valor_do_oficio_vem_formatado_como_moeda_brasileira():
    for digitado, formatado in (
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
        ("R$ 1.500,00", "R$ 1.500,00"),
    ):
        resposta = enviar(solicitacao_alunos(valor_solicitado=digitado))
        assert resposta.status_code == 200
        assert f"Valor solicitado: {formatado}" in resposta.json()["oficio"]


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------


def test_campo_obrigatorio_vazio():
    assert erros_de(solicitacao_alunos(bairro="")) == ["Preencha todos os campos"]


def test_todos_os_campos_vazios_pedem_preenchimento_uma_unica_vez():
    vazios = {campo: "" for campo in solicitacao_alunos()}
    vazios["perfil"] = "alunos"
    assert erros_de(vazios) == ["Preencha todos os campos"]


def test_n_usp_apenas_numeros():
    assert erros_de(solicitacao_alunos(numero_usp="12345a")) == [
        "N. USP deve conter apenas números"
    ]


def test_agencia_apenas_numeros():
    assert erros_de(solicitacao_alunos(agencia="12a4")) == [
        "Número da agência deve conter apenas números"
    ]


def test_valor_deve_ser_maior_que_zero():
    assert erros_de(solicitacao_alunos(valor_solicitado="0")) == [
        "Valor solicitado deve ser maior que 0"
    ]


def test_email_invalido():
    for email in ("mariaime.usp.br", "maria@"):
        assert erros_de(solicitacao_alunos(email=email)) == ["E-mail inválido"]


def test_cpf_fora_do_formato():
    for cpf in ("12345678909", "123.456.789-0", "123.456.789-090"):
        assert erros_de(solicitacao_alunos(cpf=cpf)) == [
            "CPF deve estar no formato 000.000.000-00"
        ]


def test_cpf_com_digitos_verificadores_errados():
    assert erros_de(solicitacao_alunos(cpf="123.456.789-00")) == ["CPF inválido"]


def test_cep_fora_do_formato():
    assert erros_de(solicitacao_alunos(cep="05508090")) == [
        "CEP deve estar no formato 00000-000"
    ]


def test_data_fora_do_formato():
    for data in ("01021980", "1980-02-01"):
        assert erros_de(solicitacao_alunos(data_nascimento=data)) == [
            "Data de nascimento deve estar no formato dd/mm/aaaa"
        ]


def test_data_inexistente():
    for data in ("31/04/1990", "01/13/1980", "01/00/1980", "29/02/2023"):
        assert erros_de(solicitacao_alunos(data_nascimento=data)) == [
            "Data de nascimento inválida"
        ]


def test_29_de_fevereiro_de_ano_bissexto_e_data_valida():
    resposta = enviar(solicitacao_alunos(data_nascimento="29/02/2024"))
    assert resposta.status_code == 200


def test_todos_os_erros_aplicaveis_aparecem_de_uma_vez():
    erros = erros_de(
        solicitacao_alunos(
            numero_usp="12345a",
            email="mariaime.usp.br",
            cpf="12345678909",
            cep="0550809",
        )
    )
    assert set(erros) == {
        "N. USP deve conter apenas números",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
    }


def test_validacao_vale_igual_para_as_duas_abas():
    for dados in (solicitacao_alunos(cpf="12345678909"), solicitacao_docentes(cpf="12345678909")):
        assert erros_de(dados) == ["CPF deve estar no formato 000.000.000-00"]
