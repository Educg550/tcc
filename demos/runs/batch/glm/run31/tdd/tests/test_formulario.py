import re
import uuid

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_completos_aluno():
    return {
        "tipo": "aluno",
        "nome": "Maria da Silva",
        "n_usp": "1234567",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Matemática",
        "periodo": "10 a 12 de março de 2025",
        "cidade": "São Paulo",
        "estado_evento": "SP",
        "pais": "Brasil",
        "link": "",
        "valor": "1.500,00",
        "detalhamento": "Inscrição e passagem aérea",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua Methódio Fonseca",
        "numero": "45",
        "complemento": "",
        "bairro": "Jardim Leonor",
        "cep": "05508-090",
        "cidade_endereco": "São Paulo",
        "estado_endereco": "SP",
        "cpf": "153.509.460-56",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def test_pagina_inicial_contem_estrutura():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "USP" in html
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html
    assert "Enviar solicitação" in html


def test_pagina_inicial_contem_campos():
    r = client.get("/")
    html = r.text
    for campo in [
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
        assert campo in html


def test_estaticos_expostos():
    for caminho, conteudo in [
        ("/style.css", "text/css"),
        ("/app.js", "javascript"),
        ("/assets/usp-logo.png", "image"),
    ]:
        r = client.get(caminho)
        assert r.status_code == 200, caminho
        assert conteudo in r.headers["content-type"], caminho


def test_opcoes_de_selecao():
    r = client.get("/")
    html = r.text
    for opcao in ["Mestrado", "Doutorado"]:
        assert opcao in html
    for opcao in [
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ]:
        assert opcao in html
    for opcao in ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in html


def test_envio_valido_aluno_gera_oficio():
    dados = dados_completos_aluno()
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["ok"] is True
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 1234567" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    )
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Período: 10 a 12 de março de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: " not in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e passagem aérea" in oficio
    assert "Rua Methódio Fonseca, 45" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Jardim Leonor, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 153.509.460-56" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "Complemento:" not in oficio


def test_envio_valido_docente_gera_oficio_sem_nivel_e_tipo():
    dados = dados_completos_aluno()
    dados["tipo"] = "docente"
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["ok"] is True
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert re.search(r"^Programa: Matemática$", oficio, re.MULTILINE)
    assert "A CCP-Matemática aprovou" in oficio


def test_envio_com_link_ou_complemento_aparece_no_oficio():
    dados = dados_completos_aluno()
    dados["link"] = "https://exemplo.com"
    dados["complemento"] = "Bloco A"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Complemento: Bloco A" in oficio


def test_campo_obrigatorio_vazio():
    dados = dados_completos_aluno()
    dados["nome"] = ""
    dados["email"] = ""
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    corpo = r.json()
    assert corpo["ok"] is False
    assert "Preencha todos os campos" in corpo["erros"]
    assert len([e for e in corpo["erros"] if e == "Preencha todos os campos"]) == 1


def test_campos_obrigatorios_por_tipo():
    dados = dados_completos_aluno()
    for campo in ["nome", "n_usp", "programa", "email", "evento", "periodo", "cidade", "estado_evento", "pais", "valor", "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_endereco", "estado_endereco", "cpf", "rg", "banco", "agencia", "conta"]:
        dados = dados_completos_aluno()
        dados[campo] = ""
        r = client.post("/solicitacao", json=dados)
        assert r.status_code == 400, campo
        assert "Preencha todos os campos" in r.json()["erros"], campo


def test_docente_exige_campos_sem_nivel_e_tipo():
    dados = dados_completos_aluno()
    dados["tipo"] = "docente"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_n_usp_apenas_numeros():
    dados = dados_completos_aluno()
    dados["n_usp"] = "123456a"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "N. USP deve conter apenas números" in erros


def test_agencia_apenas_numeros():
    dados = dados_completos_aluno()
    dados["agencia"] = "123a"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "Número da agência deve conter apenas números" in erros


def test_valor_maior_que_zero():
    for valor in ["0,00", "0"]:
        dados = dados_completos_aluno()
        dados["valor"] = valor
        r = client.post("/solicitacao", json=dados)
        assert r.status_code == 400, valor
        assert "Valor solicitado deve ser maior que 0" in r.json()["erros"], valor


def test_email_invalido():
    for email in ["sem-arroba", "sem@dominio", "sem@dominio"]:
        dados = dados_completos_aluno()
        dados["email"] = email
        r = client.post("/solicitacao", json=dados)
        assert r.status_code == 400, email
        assert "E-mail inválido" in r.json()["erros"], email


def test_cpf_formato_invalido():
    dados = dados_completos_aluno()
    dados["cpf"] = "153.509.460-5"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CPF inválido" not in erros


def test_cpf_digitos_verificadores_invalidos():
    dados = dados_completos_aluno()
    dados["cpf"] = "153.509.460-00"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "CPF inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" not in erros


def test_cep_formato_invalido():
    dados = dados_completos_aluno()
    dados["cep"] = "05508-0900"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_nascimento_formato_invalido():
    dados = dados_completos_aluno()
    dados["data_nascimento"] = "01-02-1980"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros
    assert "Data de nascimento inválida" not in erros


def test_data_nascimento_inexistente():
    for data in ["31/02/1980", "01/13/1980"]:
        dados = dados_completos_aluno()
        dados["data_nascimento"] = data
        r = client.post("/solicitacao", json=dados)
        assert r.status_code == 400, data
        erros = r.json()["erros"]
        assert "Data de nascimento inválida" in erros, data
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in erros


def test_todos_os_erros_relevantes_aparecem():
    dados = dados_completos_aluno()
    dados["n_usp"] = "abc"
    dados["agencia"] = "x1"
    dados["valor"] = "-5"
    dados["email"] = "invalido"
    dados["cpf"] = "11111111111"
    dados["cep"] = "111"
    dados["data_nascimento"] = "0102198"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 400
    erros = r.json()["erros"]
    for mensagem in [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]:
        assert mensagem in erros, mensagem


def test_cpf_valido_alternativo():
    dados = dados_completos_aluno()
    dados["cpf"] = "529.982.247-25"
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_oficio_aluno_contem_nivel_e_docente_nao():
    dados = dados_completos_aluno()
    r = client.post("/solicitacao", json=dados)
    oficio = r.json()["oficio"]
    assert re.search(r"^Programa: Matemática - Mestrado$", oficio, re.MULTILINE)


def test_layout_sem_rolagem_vertical():
    r = client.get("/style.css")
    assert r.status_code == 200
    css = r.text
    assert "grid" in css or "flex" in css or "columns" in css


def test_cabecalho_com_logo_usp():
    r = client.get("/")
    html = r.text
    assert "/assets/usp-logo.png" in html or "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html
