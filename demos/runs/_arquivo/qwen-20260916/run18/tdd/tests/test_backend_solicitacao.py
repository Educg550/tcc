import pytest
from fastapi.testclient import TestClient


CAMPOS_ALUNOS = {
    "nome": "Maria Silva",
    "nusp": "1234567",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "Congresso de Matemática",
    "periodo": "2024-01-10 a 2024-01-15",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://exemplo.com",
    "valor": "R$ 1.500,00",
    "detalhamento": "Auxílio para participação em congresso internacional.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua Exemplo",
    "numero": "100",
    "complemento": "",
    "bairro": "Centro",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "1234567890",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}


def _post(client, aba, payload):
    return client.post("/solicitacao", json={"aba": aba, "dados": payload})


def test_solicitacao_alunos_valida_retorna_oficio(client):
    resp = _post(client, "alunos", CAMPOS_ALUNOS)
    assert resp.status_code == 200
    oficio = resp.text
    assert "Interessada(o): Maria Silva - 1234567" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Complemento:" not in oficio
    assert "Solicitação registrada" in oficio or "oficio" in oficio.lower()


def test_solicitacao_docentes_valida_retorna_oficio(client):
    dados = {k: v for k, v in CAMPOS_ALUNOS.items() if k not in ("nivel", "tipo_auxilio")}
    resp = _post(client, "docentes", dados)
    assert resp.status_code == 200
    oficio = resp.text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática\n" in oficio or oficio.strip().endswith("Programa: Matemática")
    assert "- Mestrado" not in oficio
    assert "TIPO DE AUXÍLIO" not in oficio


def test_solicitacao_omitir_link_evento_remove_linha(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["link_evento"] = ""
    resp = _post(client, "alunos", dados)
    assert resp.status_code == 200
    assert "Link do evento:" not in resp.text


def test_solicitacao_com_complemento_linha_aparece(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["complemento"] = "Apto 12"
    resp = _post(client, "alunos", dados)
    assert resp.status_code == 200
    assert "Complemento: Apto 12" in resp.text



def test_solicitacao_valor_formatado_no_oficio(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["valor"] = "R$ 1.500,00"
    resp = _post(client, "alunos", dados)
    assert "Valor solicitado: R$ 1.500,00" in resp.text



def test_validacao_campos_obrigatorios_vazios(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["nome"] = ""
    resp = _post(client, "alunos", dados)
    assert "Preencha todos os campos" in resp.text


def test_validacao_campo_obrigatorio_faltando_docentes(client):
    dados = {k: v for k, v in CAMPOS_ALUNOS.items() if k not in ("nivel", "tipo_auxilio")}
    dados["nome_evento"] = ""
    resp = _post(client, "docentes", dados)
    assert "Preencha todos os campos" in resp.text


def test_validacao_nusp_letras(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["nusp"] = "12abc34"
    resp = _post(client, "alunos", dados)
    assert "N. USP deve conter apenas números" in resp.text


def test_validacao_agencia_letras(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["agencia"] = "12a45"
    resp = _post(client, "alunos", dados)
    assert "Número da agência deve conter apenas números" in resp.text


def test_validacao_valor_zero(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["valor"] = "0"
    resp = _post(client, "alunos", dados)
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_validacao_valor_negativo(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["valor"] = "-5"
    resp = _post(client, "alunos", dados)
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_validacao_email_sem_arroba(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["email"] = "maria.usp.br"
    resp = _post(client, "alunos", dados)
    assert "E-mail inválido" in resp.text


def test_validacao_email_sem_dominio(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["email"] = "maria@"
    resp = _post(client, "alunos", dados)
    assert "E-mail inválido" in resp.text


def test_validacao_cpf_formato_errado(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["cpf"] = "12345678909"
    resp = _post(client, "alunos", dados)
    assert "CPF deve estar no formato 000.000.000-00" in resp.text


def test_validacao_cep_formato_errado(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["cep"] = "05508090"
    resp = _post(client, "alunos", dados)
    assert "CEP deve estar no formato 00000-000" in resp.text


def test_validacao_data_formato_errado(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["data_nascimento"] = "01021980"
    resp = _post(client, "alunos", dados)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.text


def test_validacao_cpf_digitos_verificadores_errados(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["cpf"] = "111.111.111-11"
    resp = _post(client, "alunos", dados)
    assert "CPF inválido" in resp.text


def test_validacao_data_inexistente(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["data_nascimento"] = "31/02/2000"
    resp = _post(client, "alunos", dados)
    assert "Data de nascimento inválida" in resp.text


def test_validacao_mes_fora_do_intervalo(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["data_nascimento"] = "01/13/2000"
    resp = _post(client, "alunos", dados)
    assert "Data de nascimento inválida" in resp.text


def test_validacao_com_varios_erros_mostra_todas_mensagens(client):
    dados = dict(CAMPOS_ALUNOS)
    dados["nusp"] = "abc"
    dados["email"] = "sem-arroba"
    resp = _post(client, "alunos", dados)
    assert "N. USP deve conter apenas números" in resp.text
    assert "E-mail inválido" in resp.text


def test_oficio_preserva_quebras_de_linha(client):
    resp = _post(client, "alunos", CAMPOS_ALUNOS)
    assert resp.status_code == 200
    assert "\n" in resp.text
