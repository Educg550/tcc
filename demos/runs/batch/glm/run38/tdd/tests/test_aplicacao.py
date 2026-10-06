import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

RAIZ = Path(__file__).resolve().parent.parent


def dados_aluno_validos():
    return {
        "tipo": "alunos",
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Matemática",
        "periodo": "10 a 12 de março de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição e passagens",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Teste",
        "numero": "100",
        "complemento": "",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def requisicao_alunos(**sobrescritas):
    dados = dados_aluno_validos()
    dados.update(sobrescritas)
    return client.post("/solicitacao", json=dados)


def test_pagina_inicial_e_estaticos():
    for caminho in ("/", "/style.css", "/app.js", "/assets/usp-logo.png"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200
    assert "<!DOCTYPE html>".lower() == client.get("/").text[:15].lower()


def test_pagina_tem_abas_e_blocos():
    pagina = client.get("/").text
    for rotulo in ("ALUNOS", "DOCENTES"):
        assert rotulo in pagina
    for bloco in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert bloco in pagina
    assert pagina.index("ALUNOS") < pagina.index("DOCENTES")


def test_rotulos_dos_campos_na_pagina():
    pagina = client.get("/").text
    for rotulo in (
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
    ):
        assert rotulo in pagina


def test_selects_tem_opcoes():
    pagina = client.get("/").text
    for opcao in ("Mestrado", "Doutorado"):
        assert opcao in pagina
    for opcao in (
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ):
        assert opcao in pagina
    for opcao in ("Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert opcao in pagina
    assert "Enviar solicitação" in pagina


def test_campos_aluno_somente_na_aba_alunos():
    pagina = client.get("/").text
    assert pagina.count("NÍVEL") == 1
    assert pagina.count("TIPO DE AUXÍLIO") == 1


def test_sem_brasao_e_sem_cdn():
    pagina = client.get("/").text
    assert "http://" not in pagina and "https://" not in pagina
    assert "escudo" not in pagina.lower()
    assert "brasão" not in pagina.lower()
    for arquivo in ("/style.css", "/app.js"):
        conteudo = client.get(arquivo).text
        assert "http://" not in conteudo and "https://" not in conteudo


def test_placeholder_nao_repete_rotulo():
    pagina = client.get("/").text
    rotulos = re.findall(r"<label[^>]*>(.*?)</label>", pagina)
    assert len(rotulos) >= 20
    for rotulo in rotulos:
        limpo = re.sub(r"<[^>]+>", "", rotulo).strip()
        assert limpo
        assert pagina.count(limpo) >= 2


def test_oficio_alunos_apos_envio_valido():
    resposta = requisicao_alunos()
    assert resposta.status_code == 200
    corpo = resposta.json()
    oficio = corpo.get("oficio", "")
    assert "Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    )
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Período: 10 a 12 de março de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e passagens" in oficio
    assert "Rua do Teste, 100" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Centro, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro" in oficio
    assert "Complemento:" not in oficio


def test_oficio_docentes_apos_envio_valido():
    dados = dados_aluno_validos()
    dados.update({"tipo": "docentes"})
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resposta = client.post("/solicitacao", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Programa: Matemática - Mestrado" not in oficio


def test_link_e_complemento_vazios_somem_do_oficio():
    resposta = requisicao_alunos(link="", complemento="")
    oficio = resposta.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio


def test_campo_obrigatorio_vazio():
    resposta = requisicao_alunos(nome="")
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo.get("ok") is False
    erros = corpo.get("erros", [])
    assert "Preencha todos os campos" in erros


def test_n_usp_nao_numerico():
    resposta = requisicao_alunos(n_usp="12345a")
    erros = resposta.json()["erros"]
    assert "N. USP deve conter apenas números" in erros


def test_agencia_nao_numerica():
    resposta = requisicao_alunos(agencia="12a4")
    erros = resposta.json()["erros"]
    assert "Número da agência deve conter apenas números" in erros


def test_valor_zero_ou_negativo():
    resposta = requisicao_alunos(valor="R$ 0,00")
    erros = resposta.json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_invalido():
    resposta = requisicao_alunos(email="maria.ime.usp.br")
    erros = resposta.json()["erros"]
    assert "E-mail inválido" in erros
    resposta = requisicao_alunos(email="maria@")
    erros = resposta.json()["erros"]
    assert "E-mail inválido" in erros


def test_cpf_formato_errado():
    resposta = requisicao_alunos(cpf="12345678909")
    erros = resposta.json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cpf_digitos_verificadores_errados():
    resposta = requisicao_alunos(cpf="123.456.789-00")
    erros = resposta.json()["erros"]
    assert "CPF inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" not in erros


def test_cep_formato_errado():
    resposta = requisicao_alunos(cep="05508090")
    erros = resposta.json()["erros"]
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_nascimento_formato_errado():
    resposta = requisicao_alunos(data_nascimento="01021980")
    erros = resposta.json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_data_nascimento_inexistente():
    resposta = requisicao_alunos(data_nascimento="31/02/1980")
    erros = resposta.json()["erros"]
    assert "Data de nascimento inválida" in erros
    resposta = requisicao_alunos(data_nascimento="01/13/1980")
    erros = resposta.json()["erros"]
    assert "Data de nascimento inválida" in erros


def test_varios_erros_de_uma_vez():
    resposta = requisicao_alunos(
        n_usp="12a3",
        agencia="12a3",
        valor="R$ 0,00",
        email="sem-arroba",
        cpf="12345678909",
        cep="05508090",
        data_nascimento="01021980",
    )
    erros = resposta.json()["erros"]
    esperados = [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]
    for mensagem in esperados:
        assert mensagem in erros


def test_link_vazio_e_valido():
    resposta = requisicao_alunos(link="")
    assert resposta.status_code == 200


def test_complemento_vazio_e_valido():
    resposta = requisicao_alunos(complemento="")
    assert resposta.status_code == 200


def test_cep_valido_de_zona():
    resposta = requisicao_alunos(cep="05508-090")
    assert resposta.status_code == 200
