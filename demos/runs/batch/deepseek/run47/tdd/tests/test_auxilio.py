import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------- Página inicial e abas ----------


def test_pagina_inicial_tem_abas(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ALUNOS" in r.text
    assert "DOCENTES" in r.text


def test_cabecalho_institucional(client):
    r = client.get("/")
    assert "Universidade de S\u00e3o Paulo" in r.text
    assert "assets/usp-logo.png" in r.text


def test_cabecalho_sem_brasao(client):
    r = client.get("/")
    assert "brasao" not in r.text.lower()
    assert "escudo" not in r.text.lower()


def test_frontend_e_estatico(client):
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


# ---------- Rótulos dos campos ----------

ROTULOS_COMUNS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "N\u00daMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "NOME DO BANCO",
    "N\u00daMERO DA AG\u00caNCIA",
    "N\u00daMERO DA CONTA",
]


@pytest.mark.parametrize("rotulo", ROTULOS_COMUNS)
def test_rotulos_presentes(client, rotulo):
    r = client.get("/")
    assert rotulo in r.text


@pytest.mark.parametrize(
    "titulo",
    [
        "SOLICITANTE E EVENTO",
        "ENDERE\u00c7O DO SOLICITANTE",
        "INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO",
    ],
)
def test_titulos_blocos(client, titulo):
    r = client.get("/")
    assert titulo in r.text


def test_rotulos_exclusivos_alunos(client):
    r = client.get("/")
    assert "N\u00cdVEL" in r.text
    assert "TIPO DE AUX\u00cdLIO" in r.text
    assert "Mestrado" in r.text
    assert "Doutorado" in r.text


def test_rotulos_apresentacao(client):
    r = client.get("/")
    for op in [
        "P\u00f4ster",
        "Apresenta\u00e7\u00e3o oral",
        "Outra",
        "N\u00e3o ir\u00e1 apresentar trabalho",
    ]:
        assert op in r.text


def test_tipos_de_auxilio(client):
    r = client.get("/")
    for op in [
        "Participa\u00e7\u00e3o em evento",
        "Banca de exame ou defesa",
        "Outro",
    ]:
        assert op in r.text


def test_botao_enviar(client):
    r = client.get("/")
    assert "Enviar solicita\u00e7\u00e3o" in r.text


# ---------- Envio válido de aluno ----------


def dados_aluno(**over):
    d = {
        "nome": "Jo\u00e3o da Silva",
        "n_usp": "12345678",
        "programa": "Ci\u00eancia da Computa\u00e7\u00e3o",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participa\u00e7\u00e3o em evento",
        "email": "joao@usp.br",
        "evento": "Simp\u00f3sio Brasileiro",
        "periodo": "10 a 12 de maio de 2025",
        "cidade_evento": "S\u00e3o Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://exemplo.org",
        "valor": "R$ 1.500,00",
        "detalhamento": "Viagem e hospedagem.",
        "apresentacao": "P\u00f4ster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua das Flores",
        "numero": "100",
        "complemento": "Apto 12",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade": "S\u00e3o Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    d.update(over)
    return d


def test_envio_aluno_gera_oficio(client):
    r = client.post("/api/solicitacao/aluno", json=dados_aluno())
    assert r.status_code == 200
    texto = r.text
    assert "Solicita\u00e7\u00e3o registrada" in texto
    assert "Interessada(o): Jo\u00e3o da Silva - 12345678" in texto
    assert "E-mail: joao@usp.br" in texto
    assert (
        "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Participa\u00e7\u00e3o em evento"
        in texto
    )
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o - Mestrado" in texto
    assert "Evento: Simp\u00f3sio Brasileiro" in texto
    assert "Per\u00edodo: 10 a 12 de maio de 2025" in texto
    assert "Local: S\u00e3o Paulo - SP - Brasil" in texto
    assert "Link do evento: http://exemplo.org" in texto
    assert "Apresenta\u00e7\u00e3o de trabalho: P\u00f4ster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Viagem e hospedagem." in texto
    assert "Rua das Flores, 100" in texto
    assert "Complemento: Apto 12" in texto
    assert "CEP: 05508-090" in texto
    assert "Centro, S\u00e3o Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Ag\u00eancia: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias." in texto


def test_link_e_complemento_vazios_somem(client):
    d = dados_aluno(link_evento="", complemento="")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert r.status_code == 200
    texto = r.text
    assert "Link do evento:" not in texto.replace("Link do evento: ", "")
    assert "Link do evento" not in texto
    assert "Complemento:" not in texto


# ---------- Envio válido de docente ----------


def dados_docente(**over):
    d = dados_aluno()
    d.pop("nivel", None)
    d.pop("tipo_auxilio", None)
    d.update(over)
    return d


def test_envio_docente_gera_oficio(client):
    r = client.post("/api/solicitacao/docente", json=dados_docente())
    assert r.status_code == 200
    texto = r.text
    assert "Solicita\u00e7\u00e3o registrada" in texto
    assert (
        "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        in texto
    )
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o" in texto
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o - " not in texto


# ---------- Validação ----------


def test_campo_obrigatorio_vazio(client):
    d = dados_aluno(nome="")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Preencha todos os campos" in r.text


def test_campo_obrigatorio_vazio_uma_vez(client):
    d = dados_aluno(nome="", email="")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert r.text.count("Preencha todos os campos") == 1


def test_n_usp_nao_numerico(client):
    d = dados_aluno(n_usp="12abc")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "N. USP deve conter apenas n\u00fameros" in r.text


def test_agencia_nao_numerica(client):
    d = dados_aluno(agencia="12ab")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "N\u00famero da ag\u00eancia deve conter apenas n\u00fameros" in r.text


def test_valor_zero(client):
    d = dados_aluno(valor="R$ 0,00")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Valor solicitado deve ser maior que 0" in r.text


def test_email_invalido(client):
    d = dados_aluno(email="joao.usp.br")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "E-mail inv\u00e1lido" in r.text


def test_cpf_formato_invalido(client):
    d = dados_aluno(cpf="12345678909")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "CPF deve estar no formato 000.000.000-00" in r.text


def test_cep_formato_invalido(client):
    d = dados_aluno(cep="05508090")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "CEP deve estar no formato 00000-000" in r.text


def test_data_formato_invalido(client):
    d = dados_aluno(nascimento="1980-02-01")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.text


def test_cpf_digitos_verificadores_invalidos(client):
    d = dados_aluno(cpf="111.111.111-11")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "CPF inv\u00e1lido" in r.text


def test_data_inexistente(client):
    d = dados_aluno(nascimento="31/02/1980")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Data de nascimento inv\u00e1lida" in r.text


def test_data_mes_invalido(client):
    d = dados_aluno(nascimento="01/13/1980")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Data de nascimento inv\u00e1lida" in r.text


def test_multiplos_erros_aparecem(client):
    d = dados_aluno(n_usp="abc", email="invalido")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "N. USP deve conter apenas n\u00fameros" in r.text
    assert "E-mail inv\u00e1lido" in r.text


def test_erro_nao_gera_oficio(client):
    d = dados_aluno(nome="")
    r = client.post("/api/solicitacao/aluno", json=d)
    assert "Encaminhe-se ao Servi\u00e7o Financeiro" not in r.text
