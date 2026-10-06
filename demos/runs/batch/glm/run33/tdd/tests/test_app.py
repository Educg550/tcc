import re
from datetime import date
from fastapi.testclient import TestClient

from app import app


def resp_valida(aba):
    """Dados válidos para a aba indicada."""
    dados = {
        "aba": aba,
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "10 a 14 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "",
        "valor_centavos": "150000",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Apresentação oral",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade_res": "São Paulo",
        "estado_res": "SP",
        "cpf": "529.982.247-25",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "567890-1",
    }
    if aba == "alunos":
        dados["nivel"] = "Mestrado"
        dados["tipo_auxilio"] = "Participação em evento"
    return dados


def cliente():
    return TestClient(app)


def test_formulario_alunos_padrao():
    r = cliente().get("/")
    assert r.status_code == 200
    assert "ALUNOS" in r.text
    assert "DOCENTES" in r.text
    assert r.text.index("ALUNOS") < r.text.index("DOCENTES")
    assert "style.css" in r.text
    assert "app.js" in r.text


def test_campos_alunos():
    r = cliente().get("/")
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
        assert rotulo in r.text, rotulo
    for opcao in ["Mestrado", "Doutorado", "Participação em evento",
                  "Banca de exame ou defesa", "Outro", "Pôster",
                  "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in r.text, opcao
    assert "Enviar solicitação" in r.text


def test_estaticos():
    r = cliente().get("/style.css")
    assert r.status_code == 200
    r = cliente().get("/app.js")
    assert r.status_code == 200
    r = cliente().get("/assets/usp-logo.png")
    assert r.status_code == 200


def test_envio_valido_alunos():
    r = cliente().post("/api/validar", json=resp_valida("alunos"))
    assert r.status_code == 200
    corpo = r.json()
    assert corpo.get("ok") is True
    assert "oficio" in corpo
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso Brasileiro de Matemática" in oficio
    assert "Período: 10 a 14 de julho de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento:" not in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento:" not in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 529.982.247-25" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 567890-1" in oficio
    assert "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a" in oficio
    hoje = date.today().strftime("%d/%m/%Y")
    assert f"{hoje}" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_envio_valido_docentes():
    dados = resp_valida("docentes")
    dados["link"] = "https://exemplo.com"
    dados["complemento"] = "Apto 12"
    r = cliente().post("/api/validar", json=dados)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo.get("ok") is True
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert not re.search(r"Programa: Matemática - ", oficio)
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Complemento: Apto 12" in oficio
    assert "Mestrado" not in oficio.split("Dados do evento")[0]


def test_campo_obrigatorio_vazio():
    dados = resp_valida("alunos")
    dados["nome"] = ""
    dados["cidade"] = ""
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert corpo.get("ok") is False
    erros = corpo.get("erros")
    assert "Preencha todos os campos" in erros
    assert erros.count("Preencha todos os campos") == 1
    assert "oficio" not in corpo or not corpo.get("oficio")


def test_campos_opcionais_nao_geram_erro():
    # LINK e COMPLEMENTO vazios não são "campo obrigatório vazio"
    r = cliente().post("/api/validar", json=resp_valida("alunos"))
    assert r.json().get("ok") is True


def test_n_usp_nao_numerico():
    dados = resp_valida("alunos")
    dados["n_usp"] = "12a3456"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert corpo.get("ok") is False
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_agencia_nao_numerica():
    dados = resp_valida("alunos")
    dados["agencia"] = "12-x"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_valor_zero():
    dados = resp_valida("alunos")
    dados["valor_centavos"] = "0"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_email_invalido_sem_arroba():
    dados = resp_valida("alunos")
    dados["email"] = "maria.ime.usp.br"
    r = cliente().post("/api/validar", json=dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_email_invalido_sem_dominio():
    dados = resp_valida("alunos")
    dados["email"] = "maria@"
    r = cliente().post("/api/validar", json=dados)
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_formato_errado():
    dados = resp_valida("alunos")
    dados["cpf"] = "52998224725"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]
    assert "CPF inválido" not in corpo["erros"]


def test_cpf_dv_errado():
    dados = resp_valida("alunos")
    dados["cpf"] = "529.982.247-24"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "CPF inválido" in corpo["erros"]
    assert "CPF deve estar no formato 000.000.000-00" not in corpo["erros"]


def test_cep_formato_errado():
    dados = resp_valida("alunos")
    dados["cep"] = "05508090"
    r = cliente().post("/api/validar", json=dados)
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_formato_errado():
    dados = resp_valida("alunos")
    dados["nascimento"] = "1980-02-01"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]
    assert "Data de nascimento inválida" not in corpo["erros"]


def test_data_inexistente():
    dados = resp_valida("alunos")
    dados["nascimento"] = "31/02/1980"
    r = cliente().post("/api/validar", json=dados)
    corpo = r.json()
    assert "Data de nascimento inválida" in corpo["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in corpo["erros"]


def test_mes_fora_do_intervalo():
    dados = resp_valida("alunos")
    dados["nascimento"] = "01/13/1980"
    r = cliente().post("/api/validar", json=dados)
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_mensagem_cpf_e_data_juntas():
    dados = resp_valida("alunos")
    dados["cpf"] = "111.111.111-11"
    dados["nascimento"] = "31/02/1980"
    r = cliente().post("/api/validar", json=dados)
    erros = r.json()["erros"]
    assert "CPF inválido" in erros
    assert "Data de nascimento inválida" in erros


def test_aba_invalida():
    dados = resp_valida("alunos")
    dados["aba"] = "nao-existe"
    r = cliente().post("/api/validar", json=dados)
    assert r.status_code in (400, 422)


def test_sem_persistencia():
    import os, tempfile, pathlib
    antes = set(pathlib.Path(".").rglob("*.json"))
    cliente().post("/api/validar", json=resp_valida("alunos"))
    depois = set(pathlib.Path(".").rglob("*.json"))
    assert antes == depois


def test_oficio_linhas_completas():
    dados = resp_valida("alunos")
    r = cliente().post("/api/validar", json=dados)
    oficio = r.json()["oficio"]
    linhas = [l for l in oficio.splitlines()]
    esperadas = [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "Dados do evento",
        "Evento: Congresso Brasileiro de Matemática",
        "Período: 10 a 14 de julho de 2025",
        "Local: São Paulo - SP - Brasil",
        "Apresentação de trabalho: Apresentação oral",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e hospedagem",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 529.982.247-25",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 567890-1",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    for l in esperadas:
        assert l in linhas, l
