from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

ENDPOINT = "/api/solicitacao"


def dados_aluno(**mudancas):
    dados = {
        "aba": "ALUNOS",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Simpósio Brasileiro de Computação",
        "periodo_evento": "10 a 15 de outubro de 2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.usp.br",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Passagem aérea",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg_rnm": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "12345-6",
    }
    dados.update(mudancas)
    return dados


def dados_docente(**mudancas):
    dados = dados_aluno()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["aba"] = "DOCENTES"
    dados.update(mudancas)
    return dados


def enviar(dados):
    resposta = client.post(ENDPOINT, json=dados)
    assert resposta.status_code == 200
    return resposta.json()


def test_solicitacao_de_aluno_valida_nao_tem_erros():
    corpo = enviar(dados_aluno())
    assert corpo["erros"] == []


def test_oficio_do_aluno_traz_os_dados_no_lugar_dos_marcadores():
    oficio = enviar(dados_aluno())["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação aprovou na data de hoje" in oficio
    assert "Evento: Simpósio Brasileiro de Computação" in oficio
    assert "Período: 10 a 15 de outubro de 2024" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.usp.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem aérea" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco B" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_do_docente_usa_verba_do_programa_e_nao_tem_nivel():
    oficio = enviar(dados_docente())["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio
    assert "Programa: Ciência da Computação - Mestrado" not in oficio


def test_oficio_preserva_quebras_de_linha():
    oficio = enviar(dados_aluno())["oficio"]
    assert "\n" in oficio


def test_linha_do_link_sai_quando_o_link_fica_vazio():
    oficio = enviar(dados_aluno(link_evento=""))["oficio"]
    assert "Link do evento" not in oficio


def test_linha_do_complemento_sai_quando_o_complemento_fica_vazio():
    oficio = enviar(dados_aluno(complemento=""))["oficio"]
    assert "Complemento" not in oficio


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    corpo = enviar(dados_aluno(nome_completo=""))
    assert corpo["erros"].count("Preencha todos os campos") == 1
    assert len(corpo["erros"]) == 1


def test_n_usp_com_letras():
    corpo = enviar(dados_aluno(n_usp="12a456"))
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_agencia_com_letras():
    corpo = enviar(dados_aluno(numero_agencia="12a4"))
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_valor_zerado():
    corpo = enviar(dados_aluno(valor_solicitado="R$ 0,00"))
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_email_sem_arroba():
    corpo = enviar(dados_aluno(email="maria.ime.usp.br"))
    assert "E-mail inválido" in corpo["erros"]


def test_email_sem_dominio():
    corpo = enviar(dados_aluno(email="maria@"))
    assert "E-mail inválido" in corpo["erros"]


def test_cpf_sem_formatacao():
    corpo = enviar(dados_aluno(cpf="12345678909"))
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]


def test_cep_sem_formatacao():
    corpo = enviar(dados_aluno(cep="05508090"))
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_data_de_nascimento_sem_formatacao():
    corpo = enviar(dados_aluno(data_nascimento="01021980"))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


def test_cpf_com_digitos_verificadores_errados():
    corpo = enviar(dados_aluno(cpf="111.111.111-11"))
    assert "CPF inválido" in corpo["erros"]


def test_data_de_nascimento_inexistente():
    corpo = enviar(dados_aluno(data_nascimento="31/02/1980"))
    assert "Data de nascimento inválida" in corpo["erros"]


def test_mes_fora_de_um_a_doze():
    corpo = enviar(dados_aluno(data_nascimento="13/01/1980"))
    assert "Data de nascimento inválida" in corpo["erros"]


def test_varios_erros_aparecem_juntos():
    corpo = enviar(dados_aluno(email="invalido", cpf="111.111.111-11"))
    assert "E-mail inválido" in corpo["erros"]
    assert "CPF inválido" in corpo["erros"]


def test_com_erro_o_oficio_nao_e_gerado():
    corpo = enviar(dados_aluno(email="invalido"))
    assert not corpo.get("oficio")
