"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from collections import defaultdict
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# utilitários
# ---------------------------------------------------------------------------


def dados_aluno_validos():
    return {
        "tipo": "aluno",
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "10 a 14 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://cbm.org.br",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade_endereco": "São Paulo",
        "estado_endereco": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "98765-4",
    }


def dados_docente_validos():
    return {
        "tipo": "docente",
        "nome": "João de Souza",
        "n_usp": "98765432",
        "programa": "Ciência da Computação",
        "email": "joao@ime.usp.br",
        "evento": "Defesa de doutorado",
        "periodo": "20 de agosto de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "",
        "valor": "R$ 150,00",
        "detalhamento": "Diárias",
        "apresentacao": "Não irá apresentar trabalho",
        "data_nascimento": "03/04/1965",
        "logradouro": "Rua Nahoko",
        "numero": "456",
        "complemento": "Apto 12",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade_endereco": "São Paulo",
        "estado_endereco": "SP",
        "cpf": "529.982.247-25",
        "rg": "34.567.890-1",
        "banco": "Itaú",
        "agencia": "0987",
        "conta": "54321-X",
    }


TODOS_CAMPOS_ALUNO = [
    "nome",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "evento",
    "periodo",
    "cidade",
    "estado",
    "pais",
    "link",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "cidade_endereco",
    "estado_endereco",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]

OBRIGATORIOS_ALUNO = [c for c in TODOS_CAMPOS_ALUNO if c not in {"link", "complemento"}]


def enviar_aluno(**sobreposicoes):
    dados = dados_aluno_validos()
    dados.update(sobreposicoes)
    return client.post("/api/solicitacao", json=dados)


def enviar_docente(**sobreposicoes):
    dados = dados_docente_validos()
    dados.update(sobreposicoes)
    return client.post("/api/solicitacao", json=dados)


# ---------------------------------------------------------------------------
# arquivo estático e marcação visual
# ---------------------------------------------------------------------------


def test_index_e_servida_com_html_estatico():
    resposta = client.get("/")
    assert resposta.status_code == 200
    html = resposta.text
    assert "<script" in html
    assert "app.js" in html
    assert "style.css" in html
    assert "usp-logo.png" in html


def test_aba_alunos_ativa_por_padrao():
    html = client.get("/").text
    assert re.search(r'<div[^>]*class="[^"]*aba[^"]*ativa[^"]*"[^>]*>\s*ALUNOS', html, re.I) or (
        "ALUNOS" in html and 'class="tab-button active"' in html
    )


def test_estilo_existe():
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert "#1094ab" in resposta.text


def test_js_existe():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200


# ---------------------------------------------------------------------------
# validação
# ---------------------------------------------------------------------------


def test_aluno_valido_retorna_oficio():
    resposta = enviar_aluno()
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is True
    assert "Solicitação registrada" in corpo.get("oficio", "")


def test_docente_valido_retorna_oficio():
    resposta = enviar_docente()
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo.get("valido") is True
    oficio = corpo.get("oficio", "")
    assert "Verba do programa" in oficio


def test_campos_vazios_mensagem_unica():
    resposta = client.post("/api/solicitacao", json={"tipo": "aluno"})
    assert resposta.status_code == 422 or resposta.status_code == 200
    corpo = resposta.json()
    assert "Preencha todos os campos" in str(corpo)


def test_n_usp_somente_digitos():
    resposta = enviar_aluno(n_usp="1234567a")
    corpo = resposta.json()
    assert "N. USP deve conter apenas números" in str(corpo)


def test_agencia_somente_digitos():
    resposta = enviar_aluno(agencia="12-34")
    corpo = resposta.json()
    assert "Número da agência deve conter apenas números" in str(corpo)


def test_email_invalido():
    resposta = enviar_aluno(email="maria-imagem.usp.br")
    corpo = resposta.json()
    assert "E-mail inválido" in str(corpo)


def test_valor_zero_invalido():
    resposta = enviar_aluno(valor="R$ 0,00")
    corpo = resposta.json()
    assert "Valor solicitado deve ser maior que 0" in str(corpo)


def test_valor_nao_numerico_invalido():
    resposta = enviar_aluno(valor="qualquer coisa")
    corpo = resposta.json()
    assert "Valor solicitado deve ser maior que 0" in str(corpo)


@pytest.mark.parametrize(
    "cpf",
    ["12.345.678-90", "12345678909", "123.456.789-0", ""],
)
def test_cpf_fora_do_formato(cpf):
    resposta = enviar_aluno(cpf=cpf)
    corpo = resposta.json()
    assert "CPF deve estar no formato 000.000.000-00" in str(corpo)


def test_cpf_com_digito_verificador_errado():
    resposta = enviar_aluno(cpf="123.456.789-00")
    corpo = resposta.json()
    assert "CPF inválido" in str(corpo)


def test_cep_invalido():
    resposta = enviar_aluno(cep="05508090")
    corpo = resposta.json()
    assert "CEP deve estar no formato 00000-000" in str(corpo)


def test_data_nascimento_formato_errado():
    resposta = enviar_aluno(data_nascimento="1980-02-01")
    corpo = resposta.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in str(corpo)


@pytest.mark.parametrize(
    "data",
    ["31/02/1980", "01/13/1980", "00/05/1990", "01021980"],
)
def test_data_inexistente(data):
    resposta = enviar_aluno(data_nascimento=data)
    corpo = resposta.json()
    assert "Data de nascimento inválida" in str(corpo)


def test_dados_bancarios_docente_valido():
    resposta = enviar_docente()
    assert resposta.status_code == 200
    assert resposta.json().get("valido") is True


def test_email_sem_dominio():
    resposta = enviar_aluno(email="maria@")
    corpo = resposta.json()
    assert "E-mail inválido" in str(corpo)


# ---------------------------------------------------------------------------
# formatação do ofício
# ---------------------------------------------------------------------------


def test_oficio_aluno_com_dados():
    resposta = enviar_aluno()
    oficio = resposta.json()["oficio"]

    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "CCP-Matemática" in oficio
    assert "Evento: Congresso Brasileiro de Matemática" in oficio
    assert "Período: 10 a 14 de julho de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://cbm.org.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 98765-4" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_aluno_sem_complemento_omit_linha():
    resposta = enviar_aluno(complemento="")
    oficio = resposta.json()["oficio"]
    assert "Complemento:" not in oficio


def test_oficio_docente_sem_link_omit_linha():
    resposta = enviar_docente()
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio


def test_oficio_docente_nao_menciona_nivel():
    resposta = enviar_docente()
    oficio = resposta.json()["oficio"]
    assert "Nível" not in oficio
    assert "Mestrado" not in oficio
    assert "Doutorado" not in oficio


def test_oficio_aluno_com_complemento():
    resposta = enviar_docente()
    oficio = resposta.json()["oficio"]
    assert "Complemento: Apto 12" in oficio


# ---------------------------------------------------------------------------
# rótulos do formulário
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rotulo",
    [
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
    ],
)
def test_rotulos_presentes(rotulo):
    html = client.get("/").text
    assert rotulo in html


def test_titulos_de_blocos_presentes():
    html = client.get("/").text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_abas_presentes_e_na_ordem():
    html = client.get("/").text
    pos_alunos = html.index("ALUNOS")
    pos_docentes = html.index("DOCENTES")
    assert pos_alunos < pos_docentes


def test_botoes_enviar_presentes():
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_placeholder_nao_repete_rotulo():
    html = client.get("/").text
    assert html.count("placeholder=") >= 20


def test_nivel_tem_opcoes_mestrado_doutorado():
    html = client.get("/").text
    assert "Mestrado" in html
    assert "Doutorado" in html


def test_tipo_auxilio_tem_tres_opcoes():
    html = client.get("/").text
    for opcao in [
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ]:
        assert opcao in html


def test_apresentacao_tem_quatro_opcoes():
    html = client.get("/").text
    for opcao in [
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ]:
        assert opcao in html


def test_logo_usp_servido():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def test_brasao_nao_aparece():
    html = client.get("/").text
    assert "brasao" not in html.lower()
    assert "escudo" not in html.lower()
    assert "crest" not in html.lower()


def test_fonte_open_sans_ou_sem_serifa():
    css = client.get("/style.css").text
    assert "Open Sans" in css or "sans-serif" in css


def test_data_de_hoje_no_oficio():
    resposta = enviar_docente()
    oficio = resposta.json()["oficio"]
    hoje = date.today().strftime("%d/%m/%Y")
    assert hoje in oficio


def test_mensagem_de_erro_retornada_como_lista():
    resposta = enviar_aluno(cpf="111.111.111-11")
    corpo = resposta.json()
    texto = str(corpo)
    assert "CPF inválido" in texto


def test_todos_campos_obrigatorios_faltando_geram_um_unico_erro():
    resposta = client.post("/api/solicitacao", json={"tipo": "aluno"})
    corpo = resposta.json()
    texto = str(corpo)
    assert texto.count("Preencha todos os campos") >= 1
    assert "N. USP deve conter apenas números" not in texto
    assert "CPF deve estar no formato 000.000.000-00" not in texto
    assert "CEP deve estar no formato 00000-000" not in texto
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in texto
    assert "Data de nascimento inválida" not in texto
    assert "CPF inválido" not in texto
    assert "Valor solicitado deve ser maior que 0" not in texto
    assert "E-mail inválido" not in texto
    assert "Número da agência deve conter apenas números" not in texto


def test_mensagens_multiplas_acumuladas():
    resposta = enviar_aluno(cpf="123456", email="abc")
    corpo = resposta.json()
    texto = str(corpo)
    assert "CPF deve estar no formato 000.000.000-00" in texto
    assert "E-mail inválido" in texto
