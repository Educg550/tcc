"""Testes do formulário de solicitação de auxílio financeiro da Pós do IME-USP.

Contrato do backend exercitado aqui:

POST /solicitacao com corpo {"aba": "alunos" | "docentes", "campos": {rótulo exato: valor}}
  - solicitação válida:   200 e {"oficio": "<texto integral do ofício>"}
  - solicitação inválida: 400 e {"erros": ["<mensagem>", ...]}

Os valores viajam como exibidos nos campos (CPF, CEP e data já pontuados); o
VALOR SOLICITADO (R$) viaja como os dígitos digitados (ex.: "150000") e volta
formatado no ofício ("R$ 1.500,00").
"""

import re

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

MSG_OBRIGATORIO = "Preencha todos os campos"

CAMPOS_VALIDOS = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria Augusta da Silva Souza",
    "N. USP": "8765432",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Doutorado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.souza@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBBD 2025",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "6 a 9 de outubro de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Petrópolis",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "RJ",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbbd.org.br",
    "VALOR SOLICITADO (R$)": "150000",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e duas diárias.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "03/12/1995",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Sala 214",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "0246",
    "NÚMERO DA CONTA": "13579-1",
}

OFICIO_ALUNOS = """Interessada(o): Maria Augusta da Silva Souza - 8765432
E-mail: maria.souza@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Doutorado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 6 a 9 de outubro de 2025
Local: Petrópolis - RJ - Brasil
Link do evento: https://sbbd.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagem aérea e duas diárias.

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Sala 214
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 03/12/1995
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 0246
Conta: 13579-1

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_DOCENTES = """Interessada(o): Maria Augusta da Silva Souza - 8765432
E-mail: maria.souza@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Ciência da Computação

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 6 a 9 de outubro de 2025
Local: Petrópolis - RJ - Brasil
Link do evento: https://sbbd.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagem aérea e duas diárias.

Endereço da(o) interessada(o)
Rua do Matão, 1010
Complemento: Sala 214
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 03/12/1995
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 0246
Conta: 13579-1

Encaminhe-se ao Serviço Financeiro para providências."""

OFICIO_SEM_OPCIONAIS = """Interessada(o): Maria Augusta da Silva Souza - 8765432
E-mail: maria.souza@ime.usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Doutorado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 6 a 9 de outubro de 2025
Local: Petrópolis - RJ - Brasil
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagem aérea e duas diárias.

Endereço da(o) interessada(o)
Rua do Matão, 1010
CEP: 05508-090
Butantã, São Paulo - SP

Dados para pagamento
Data de nascimento: 03/12/1995
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 0246
Conta: 13579-1

Encaminhe-se ao Serviço Financeiro para providências."""


def enviar(aba="alunos", **substituicoes):
    campos = dict(CAMPOS_VALIDOS)
    for rotulo, valor in substituicoes.items():
        if valor is None:
            campos.pop(rotulo, None)
        else:
            campos[rotulo] = valor
    return client.post("/solicitacao", ={"aba": aba, "campos": campos})


def test_envio_valido_de_alunos_gera_oficio():
    resposta = enviar("alunos")
    assert resposta.status_code == 200
    assert resposta.()["oficio"].strip() == OFICIO_ALUNOS.strip()


def test_envio_valido_de_docentes_gera_oficio():
    resposta = enviar("docentes", **{"NÍVEL": None, "TIPO DE AUXÍLIO": None})
    assert resposta.status_code == 200
    assert resposta.()["oficio"].strip() == OFICIO_DOCENTES.strip()


@pytest.mark.parametrize(
    "digitos, formatado",
    [
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ],
)
def test_valor_solicitado_aparece_formatado_no_oficio(digitos, formatado):
    resposta = enviar("alunos", **{"VALOR SOLICITADO (R$)": digitos})
    assert resposta.status_code == 200
    assert f"Valor solicitado: {formatado}" in resposta.()["oficio"]


def test_campos_opcionais_vazios_saem_do_oficio():
    resposta = enviar(
        "alunos",
        **{"LINK DO EVENTO, EXAME OU DEFESA": "", "COMPLEMENTO": ""},
    )
    assert resposta.status_code == 200
    oficio = resposta.()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio
    assert oficio.strip() == OFICIO_SEM_OPCIONAIS.strip()


def test_campos_obrigatorios_vazios_geram_uma_unica_mensagem():
    vazios = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "DETALHAMENTO DO PEDIDO",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "CEP",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
    ]
    resposta = enviar("alunos", **{rotulo: "" for rotulo in vazios})
    assert resposta.status_code == 400
    erros = resposta.()["erros"]
    assert erros.count(MSG_OBRIGATORIO) == 1


def test_campo_vazio_e_erro_especifico_aparecem_juntos():
    resposta = enviar(
        "alunos",
        **{
            "NOME COMPLETO - SEM ABREVIAR": "",
            "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00",
        },
    )
    assert resposta.status_code == 400
    erros = resposta.()["erros"]
    assert MSG_OBRIGATORIO in erros
    assert "CPF inválido" in erros


@pytest.mark.parametrize(
    "rotulo, valor, mensagem",
    [
        ("N. USP", "8765a32", "N. USP deve conter apenas números"),
        ("NÚMERO DA AGÊNCIA", "02a6", "Número da agência deve conter apenas números"),
        ("VALOR SOLICITADO (R$)", "0", "Valor solicitado deve ser maior que 0"),
        ("VALOR SOLICITADO (R$)", "15a0", "Valor solicitado deve ser maior que 0"),
        ("E-MAIL", "maria.souza", "E-mail inválido"),
        ("E-MAIL", "maria@", "E-mail inválido"),
        (
            "CPF (SEPARADOS POR PONTOS E TRAÇO)",
            "12345678909",
            "CPF deve estar no formato 000.000.000-00",
        ),
        ("CEP", "05508090", "CEP deve estar no formato 00000-000"),
        (
            "DATA DE NASCIMENTO",
            "1995-12-03",
            "Data de nascimento deve estar no formato dd/mm/aaaa",
        ),
        ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "123.456.789-00", "CPF inválido"),
        ("DATA DE NASCIMENTO", "31/02/1995", "Data de nascimento inválida"),
        ("DATA DE NASCIMENTO", "05/13/1995", "Data de nascimento inválida"),
    ],
)
def test_erro_especifico_unico(rotulo, valor, mensagem):
    resposta = enviar("alunos", **{rotulo: valor})
    assert resposta.status_code == 400
    assert resposta.()["erros"] == [mensagem]


def test_varios_erros_aparecem_juntos():
    resposta = enviar(
        "alunos",
        **{
            "N. USP": "8765a32",
            "CEP": "05508090",
            "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00",
        },
    )
    assert resposta.status_code == 400
    erros = resposta.()["erros"]
    assert set(erros) == {
        "N. USP deve conter apenas números",
        "CEP deve estar no formato 00000-000",
        "CPF inválido",
    }


def test_validacao_vale_na_aba_docentes():
    resposta = enviar(
        "docentes",
        **{"NÍVEL": None, "TIPO DE AUXÍLIO": None, "NÚMERO DA AGÊNCIA": "02a6"},
    )
    assert resposta.status_code == 400
    assert resposta.()["erros"] == ["Número da agência deve conter apenas números"]


TITULOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS = [
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

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]


def conteudo_da_pagina():
    return client.get("/").text + client.get("/app.js").text


def test_pagina_inicial_e_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_abas_alunos_e_docentes_nessa_ordem():
    conteudo = conteudo_da_pagina()
    assert conteudo.find("ALUNOS") != -1
    assert conteudo.find("DOCENTES") != -1
    assert conteudo.find("ALUNOS") < conteudo.find("DOCENTES")


def test_titulos_dos_tres_blocos():
    conteudo = conteudo_da_pagina()
    for titulo in TITULOS_BLOCOS:
        assert titulo in conteudo


def test_rotulos_dos_campos_exatos():
    conteudo = conteudo_da_pagina()
    for rotulo in ROTULOS:
        assert rotulo in conteudo


def test_opcoes_das_selecoes():
    conteudo = conteudo_da_pagina()
    for opcao in OPCOES:
        assert opcao in conteudo


def test_botao_enviar_em_cada_aba():
    assert conteudo_da_pagina().count("Enviar solicitação") >= 2


def test_cabecalho_institucional_com_logotipo():
    conteudo = conteudo_da_pagina()
    assert "Universidade de São Paulo" in conteudo
    assert "assets/usp-logo.png" in conteudo


def test_logotipo_e_servido():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content


def test_arquivos_estaticos_servidos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_index_referencia_style_e_app():
    html = client.get("/").text.lower()
    assert "style.css" in html
    assert "app.js" in html


def test_cores_e_fonte_da_identidade_visual():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "open sans" in css


def test_titulo_da_confirmacao():
    assert "Solicitação registrada" in conteudo_da_pagina()


def test_todo_campo_tem_placeholder_de_exemplo():
    conteudo = conteudo_da_pagina()
    tags = re.findall(r"<(?:input|textarea)\b[^>]*>", conteudo, flags=re.IGNORECASE)
    placeholders = []
    for tag in tags:
        achou = re.search(r'placeholder\s*=\s*"([^"]+)"', tag, flags=re.IGNORECASE)
        if achou is None:
            achou = re.search(r"placeholder\s*=\s*'([^']+)'", tag, flags=re.IGNORECASE)
        assert achou is not None, f"Campo sem placeholder: {tag}"
        placeholders.append(achou.group(1).strip().upper())
    assert placeholders
    for rotulo in ROTULOS:
        assert rotulo.upper() not in placeholders, f"Placeholder repete o rótulo: {rotulo}"
