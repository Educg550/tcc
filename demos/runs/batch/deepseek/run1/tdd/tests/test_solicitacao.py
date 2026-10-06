from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_alunos(**over):
    base = {
        "aba": "alunos",
        "nome_completo": "Maria Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro",
        "periodo": "01/01/2025 a 05/01/2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://exemplo.com",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Passagem e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua das Flores",
        "numero": "100",
        "complemento": "Apto 1",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "111.444.777-35",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    base.update(over)
    return base


def dados_docentes(**over):
    base = dados_alunos(aba="docentes")
    base.pop("nivel")
    base.pop("tipo_auxilio")
    base.update(over)
    return base


def conteudo_servido():
    return client.get("/").text + "\n" + client.get("/app.js").text


# --- Frontend estático ---

def test_pagina_inicial_serve_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_style_e_app_js_servidos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_abas_alunos_e_docentes():
    conteudo = conteudo_servido()
    assert "ALUNOS" in conteudo
    assert "DOCENTES" in conteudo


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in conteudo_servido()


def test_titulos_dos_blocos():
    conteudo = conteudo_servido()
    assert "SOLICITANTE E EVENTO" in conteudo
    assert "ENDEREÇO DO SOLICITANTE" in conteudo
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in conteudo


def test_rotulos_dos_campos():
    conteudo = conteudo_servido()
    for rotulo in [
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
    ]:
        assert rotulo in conteudo, rotulo


def test_placeholders_presentes():
    assert "placeholder" in conteudo_servido()


def test_identidade_visual():
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert "#1094ab" in client.get("/style.css").text


# --- Envio válido ---

def test_envio_valido_alunos_gera_oficio():
    r = client.post("/solicitar", data=dados_alunos())
    assert r.status_code == 200
    body = r.json()
    assert body["erros"] == []
    oficio = body["oficio"]
    assert "Interessada(o): Maria Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação aprovou" in oficio
    assert "Evento: Congresso Brasileiro" in oficio
    assert "Período: 01/01/2025 a 05/01/2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: http://exemplo.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem e hospedagem" in oficio
    assert "Rua das Flores, 100" in oficio
    assert "Complemento: Apto 1" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Centro, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 111.444.777-35" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_preserva_quebras_de_linha():
    oficio = client.post("/solicitar", data=dados_alunos()).json()["oficio"]
    assert "\n" in oficio


def test_oficio_docentes_sem_nivel_e_com_verba():
    r = client.post("/solicitar", data=dados_docentes())
    body = r.json()
    assert body["erros"] == []
    oficio = body["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Programa: Ciência da Computação - Mestrado" not in oficio


def test_link_vazio_sai_do_oficio():
    oficio = client.post("/solicitar", data=dados_alunos(link_evento="")).json()["oficio"]
    assert "Link do evento" not in oficio


def test_complemento_vazio_sai_do_oficio():
    oficio = client.post("/solicitar", data=dados_alunos(complemento="")).json()["oficio"]
    assert "Complemento:" not in oficio


# --- Validação ---

def test_campo_obrigatorio_vazio():
    body = client.post("/solicitar", data=dados_alunos(nome_completo="")).json()
    assert "Preencha todos os campos" in body["erros"]
    assert body["erros"].count("Preencha todos os campos") == 1


def test_n_usp_apenas_numeros():
    body = client.post("/solicitar", data=dados_alunos(n_usp="12a45")).json()
    assert "N. USP deve conter apenas números" in body["erros"]


def test_agencia_apenas_numeros():
    body = client.post("/solicitar", data=dados_alunos(agencia="12a")).json()
    assert "Número da agência deve conter apenas números" in body["erros"]


def test_valor_maior_que_zero():
    body = client.post("/solicitar", data=dados_alunos(valor_solicitado="R$ 0,00")).json()
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_email_invalido():
    body = client.post("/solicitar", data=dados_alunos(email="semarroba")).json()
    assert "E-mail inválido" in body["erros"]


def test_cpf_formato():
    body = client.post("/solicitar", data=dados_alunos(cpf="111.444.777")).json()
    assert "CPF deve estar no formato 000.000.000-00" in body["erros"]


def test_cep_formato():
    body = client.post("/solicitar", data=dados_alunos(cep="0550809")).json()
    assert "CEP deve estar no formato 00000-000" in body["erros"]


def test_data_formato():
    body = client.post("/solicitar", data=dados_alunos(data_nascimento="01/02/80")).json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["erros"]


def test_cpf_invalido():
    body = client.post("/solicitar", data=dados_alunos(cpf="111.444.777-00")).json()
    assert "CPF inválido" in body["erros"]


def test_data_invalida():
    body = client.post("/solicitar", data=dados_alunos(data_nascimento="31/02/1980")).json()
    assert "Data de nascimento inválida" in body["erros"]


def test_multiplos_erros_ao_mesmo_tempo():
    body = client.post("/solicitar", data=dados_alunos(n_usp="abc", agencia="xyz")).json()
    assert "N. USP deve conter apenas números" in body["erros"]
    assert "Número da agência deve conter apenas números" in body["erros"]


def test_erro_nao_gera_oficio():
    body = client.post("/solicitar", data=dados_alunos(email="x")).json()
    assert body["erros"]
    assert not body.get("oficio")
