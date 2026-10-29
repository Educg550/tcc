import time

import httpx
import pytest

from conftest import BASE, SMTP, banco, corpo, emails, sql

TOKEN_ANA = "c0a5e1f0-0000-4000-8000-000000000001"


def caixa(n, espera=15):
    for _ in range(espera * 2):
        lista = emails()
        if len(lista) >= n:
            return lista
        time.sleep(.5)
    return emails()


def envelope():
    return [m for m in httpx.get(SMTP + "/api/Messages", params={"pageSize": 100}).json()["results"]]


def aprovar(admin, submission_id=1, orientador=3):
    assert admin.post(f"submissions/{submission_id}/select",
                      json={"stats": "approved", "user_ids": [orientador]}).status_code == 200


def convite_pendente(submission_id=1, response_id=50, enviado=False):
    """Estado que send-accept deve deixar, montado sem a rota para avaliar a leitura isoladamente."""
    sql(f"""INSERT INTO form_shared(id,form_id,token,unique_answers,is_public,expiration_at,created_at)
        VALUES({response_id},4,'c0a5e1f0-0000-4000-8000-0000000002{response_id:02d}',true,false,'2030-04-01',now());
        INSERT INTO form_response(id,form_id,shared_id,email,token,metadata,form_version,submitted_at)
        VALUES({response_id},4,{response_id},'candidata.piloto@example.com',
        'c0a5e1f0-0000-4000-8000-0000000003{response_id:02d}','{{}}',1,{"'2026-10-20 10:00:00'" if enviado else "NULL"});""",
        "forms")
    if enviado:
        sql(f"""INSERT INTO responses(response_id,field_id,value) SELECT {response_id},id,
            CASE name WHEN 'accept' THEN 'Aceito a vaga.' ELSE 'Começo em março.' END
            FROM form_field WHERE form_id=4""", "forms")
    sql(f"UPDATE submission SET accept_form_id={response_id} WHERE id={submission_id}")


@pytest.mark.req("V2-MAI-01")
@pytest.mark.integracao("INT-FORMS-DB", "INT-SMTP")
def test_solicita_correcao_reabrindo_e_avisando_o_candidato(admin):
    sql("UPDATE edict SET phase='homologacao' WHERE id=1")
    r = admin.post("submissions/1/reesend_submission", json={"text": "Falta o histórico escolar."})
    assert r.status_code == 200
    assert r.json()["email_sent"] == "candidata.piloto@example.com" and r.json()["message"]
    assert banco("SELECT current_section FROM form_response WHERE id=1", "forms") == [{"current_section": 0}]
    [m] = caixa(1)
    assert m["To"] == "candidata.piloto@example.com" and m["Subject"]
    texto = corpo(m)
    assert "Falta o histórico escolar." in texto
    assert f"https://localhost:8543/form/{TOKEN_ANA}" in texto
    assert "admin.piloto@example.com" not in (m["To"] or "") + (m["Cc"] or "")
    assert any("admin.piloto@example.com" in str(e.get("to")) for e in envelope())


@pytest.mark.req("V2-MAI-01")
@pytest.mark.integracao("INT-FORMS-STACK")
def test_link_de_correcao_abre_a_candidatura_no_forms(admin):
    sql("UPDATE edict SET phase='homologacao' WHERE id=1")
    admin.post("submissions/1/reesend_submission", json={"text": "Corrigir"})
    r = httpx.get(f"{BASE}/form/{TOKEN_ANA}", verify=False, follow_redirects=True)
    assert r.status_code == 200
    assert "Ana Piloto Caronte" in r.text or "Mestrado" in r.text


@pytest.mark.req("V2-MAI-01")
@pytest.mark.parametrize("fase", ["inscricoes", "avaliacao", "encerrado"])
def test_correcao_fora_da_homologacao_responde_400(admin, fase):
    sql(f"UPDATE edict SET phase='{fase}' WHERE id=1")
    antes = banco("SELECT current_section FROM form_response WHERE id=1", "forms")
    assert admin.post("submissions/1/reesend_submission", json={"text": "x"}).status_code == 400
    assert banco("SELECT current_section FROM form_response WHERE id=1", "forms") == antes
    assert caixa(1, espera=2) == []


@pytest.mark.req("V2-MAI-01")
def test_correcao_de_inscricao_inexistente_responde_404(admin):
    assert admin.post("submissions/999/reesend_submission", json={"text": "x"}).status_code == 404


@pytest.mark.req("V2-MAI-02", "V2-BD-01")
@pytest.mark.integracao("INT-FORMS-DB", "INT-SMTP", "INT-PREJANUS-DB")
def test_envia_formulario_de_aceite(clientes):
    aprovar(clientes("admin"))
    r = clientes("docente").post("submissions/1/send-accept")
    assert r.status_code == 200
    assert r.json()["email_sent"] == "candidata.piloto@example.com" and r.json()["message"]
    [sub] = banco("SELECT accept_form_id FROM submission WHERE id=1")
    [resposta] = banco(f"SELECT r.form_id, r.email, r.token::text, r.submitted_at, s.is_public, s.unique_answers, "
                       f"s.expiration_at::date::text AS expira FROM form_response r JOIN form_shared s ON s.id=r.shared_id "
                       f"WHERE r.id={sub['accept_form_id']}", "forms")
    assert {k: resposta[k] for k in ("form_id", "email", "submitted_at", "is_public", "unique_answers", "expira")} == {
        "form_id": 4, "email": "candidata.piloto@example.com", "submitted_at": None, "is_public": False,
        "unique_answers": True, "expira": "2030-04-01"}
    [m] = caixa(1)
    assert m["To"] == "candidata.piloto@example.com" and m["Cc"] == "outra.piloto@example.com"
    texto = corpo(m)
    assert "Ana Piloto Caronte" in texto
    assert f"https://localhost:8543/form/{resposta['token']}" in texto
    assert "1 de abril de 2030" in texto and "April 1, 2030" in texto


@pytest.mark.req("V2-MAI-02")
def test_aceite_nao_e_criado_duas_vezes(clientes):
    aprovar(clientes("admin"))
    clientes("docente").post("submissions/1/send-accept")
    caixa(1)
    antes = banco("SELECT count(*) AS n FROM form_response WHERE form_id=4", "forms")
    assert clientes("docente").post("submissions/1/send-accept").status_code == 400
    assert banco("SELECT count(*) AS n FROM form_response WHERE form_id=4", "forms") == antes
    assert len(caixa(2, espera=3)) == 1


@pytest.mark.req("V2-MAI-02")
def test_aceite_exige_aprovacao(api):
    assert api.post("submissions/1/send-accept").status_code == 400
    assert banco("SELECT id FROM form_response WHERE form_id=4", "forms") == []


@pytest.mark.req("V2-MAI-02")
def test_aceite_sem_formulario_configurado_responde_404(clientes):
    aprovar(clientes("admin"))
    sql("UPDATE edict SET accept_forms=NULL WHERE id=1")
    assert clientes("docente").post("submissions/1/send-accept").status_code == 404


@pytest.mark.req("V2-MAI-02")
@pytest.mark.integracao("INT-FORMS-DB")
def test_estado_do_aceite_sem_convite(api):
    assert api.get("submissions/1").json()["summary"]["accept"]["sent"] == "not_sent"


@pytest.mark.req("V2-MAI-02")
@pytest.mark.integracao("INT-FORMS-DB")
def test_estado_do_aceite_pendente(api):
    convite_pendente()
    assert api.get("submissions/1").json()["summary"]["accept"]["sent"] == "sent"
    ana = {s["id"]: s for s in api.get("edicts/1/submissions").json()["submissions"]}[1]
    assert ana["accept"]["sent"] == "sent"


@pytest.mark.req("V2-MAI-02")
@pytest.mark.integracao("INT-FORMS-DB")
def test_estado_do_aceite_respondido(api):
    convite_pendente(enviado=True)
    aceite = api.get("submissions/1").json()["summary"]["accept"]
    assert (aceite["sent"], aceite["accept"], aceite["comments"]) == ("replied", "Aceito a vaga.", "Começo em março.")
    assert aceite["submitted_at"].startswith("2026-10-20")
    ana = {s["id"]: s for s in api.get("edicts/1/submissions").json()["submissions"]}[1]
    assert (ana["accept"]["sent"], ana["accept"]["accept"]) == ("replied", "Aceito a vaga.")


@pytest.mark.req("V2-MAI-03", "V2-BD-01")
@pytest.mark.integracao("INT-SMTP", "INT-PREJANUS-DB")
def test_envia_carta_de_aceite(clientes):
    aprovar(clientes("admin"))
    clientes("admin").post("submissions/1/entry-semester", json={"semester": "segundo"})
    r = clientes("docente").post("submissions/1/send-letter")
    assert r.status_code == 200
    assert r.json()["email_sent"] == "candidata.piloto@example.com" and r.json()["message"]
    assert banco("SELECT letter_sent FROM submission WHERE id=1") == [{"letter_sent": True}]
    assert clientes("docente").get("submissions/1").json()["summary"]["letter_sent"] is True
    [m] = caixa(1)
    assert m["To"] == "candidata.piloto@example.com" and m["Cc"] == "outra.piloto@example.com"
    html = next(p for p in m.walk() if p.get_content_type() == "text/html").get_content()
    assert "Ana Piloto Caronte" in html and "Outra Docente" in html and "2026" in html and "segundo" in html
    assert 'src="cid:signature"' in html
    [assinatura] = [p for p in m.walk() if p.get_content_maintype() == "image"]
    assert assinatura["Content-ID"] == "<signature>"


@pytest.mark.req("V2-MAI-03")
def test_carta_nao_e_enviada_duas_vezes(clientes):
    aprovar(clientes("admin"))
    clientes("docente").post("submissions/1/send-letter")
    caixa(1)
    assert clientes("docente").post("submissions/1/send-letter").status_code == 400
    assert len(caixa(2, espera=3)) == 1


@pytest.mark.req("V2-MAI-03")
def test_carta_exige_aprovacao(api):
    assert api.post("submissions/1/send-letter").status_code == 400
    assert banco("SELECT letter_sent FROM submission WHERE id=1") == [{"letter_sent": False}]
    assert caixa(1, espera=2) == []
