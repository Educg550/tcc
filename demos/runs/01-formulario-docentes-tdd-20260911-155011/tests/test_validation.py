from fastapi.testclient import TestClient

from app import app
from tests.helpers import build_payload, form_action, get_forms, name_after_label

client = TestClient(app)


def _alunos_form():
    html = client.get("/").text
    alunos, _ = get_forms(html)
    return alunos


def _docentes_form():
    html = client.get("/").text
    _, docentes = get_forms(html)
    return docentes


def test_campo_obrigatorio_vazio_mostra_mensagem_generica():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "NOME COMPLETO - SEM ABREVIAR")] = ""
    resp = client.post(form_action(alunos), data=payload)
    assert resp.status_code == 200
    assert "Preencha todos os campos" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_mensagem_generica_aparece_uma_unica_vez_com_varios_campos_vazios():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "NOME COMPLETO - SEM ABREVIAR")] = ""
    payload[name_after_label(alunos, "PROGRAMA")] = ""
    resp = client.post(form_action(alunos), data=payload)
    assert resp.text.count("Preencha todos os campos") == 1


def test_validacao_generica_vale_tambem_na_aba_docentes():
    docentes = _docentes_form()
    payload = build_payload(docentes, "docentes")
    payload[name_after_label(docentes, "NOME COMPLETO - SEM ABREVIAR")] = ""
    resp = client.post(form_action(docentes), data=payload)
    assert "Preencha todos os campos" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_n_usp_deve_conter_apenas_numeros():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "N. USP")] = "12A34"
    resp = client.post(form_action(alunos), data=payload)
    assert "N. USP deve conter apenas números" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_numero_agencia_deve_conter_apenas_numeros():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "NÚMERO DA AGÊNCIA")] = "12A4"
    resp = client.post(form_action(alunos), data=payload)
    assert "Número da agência deve conter apenas números" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_valor_solicitado_zero_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "VALOR SOLICITADO (R$)")] = "R$ 0,00"
    resp = client.post(form_action(alunos), data=payload)
    assert "Valor solicitado deve ser maior que 0" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_valor_solicitado_nao_numerico_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "VALOR SOLICITADO (R$)")] = "abc"
    resp = client.post(form_action(alunos), data=payload)
    assert "Valor solicitado deve ser maior que 0" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_email_sem_arroba_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "E-MAIL")] = "mariasilva.usp.br"
    resp = client.post(form_action(alunos), data=payload)
    assert "E-mail inválido" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_email_sem_dominio_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "E-MAIL")] = "maria@"
    resp = client.post(form_action(alunos), data=payload)
    assert "E-mail inválido" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_cpf_fora_do_formato_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "CPF (SEPARADOS POR PONTOS E TRAÇO)")] = "12345678901"
    resp = client.post(form_action(alunos), data=payload)
    assert "CPF deve estar no formato 000.000.000-00" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_cep_fora_do_formato_invalido():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "CEP")] = "05508090"
    resp = client.post(form_action(alunos), data=payload)
    assert "CEP deve estar no formato 00000-000" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_data_nascimento_fora_do_formato_invalida():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "DATA DE NASCIMENTO")] = "01021980"
    resp = client.post(form_action(alunos), data=payload)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.text
    assert "Solicitação registrada" not in resp.text


def test_link_do_evento_e_opcional():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "LINK DO EVENTO, EXAME OU DEFESA")] = ""
    resp = client.post(form_action(alunos), data=payload)
    assert "Solicitação registrada" in resp.text
    assert "Preencha todos os campos" not in resp.text


def test_complemento_e_opcional():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "COMPLEMENTO")] = ""
    resp = client.post(form_action(alunos), data=payload)
    assert "Solicitação registrada" in resp.text
    assert "Preencha todos os campos" not in resp.text


def test_valores_preenchidos_sao_preservados_apos_erro():
    alunos = _alunos_form()
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "E-MAIL")] = "invalido-sem-arroba"
    resp = client.post(form_action(alunos), data=payload)
    assert "Maria da Silva Santos" in resp.text
    assert "Solicito auxílio para participação no evento." in resp.text
