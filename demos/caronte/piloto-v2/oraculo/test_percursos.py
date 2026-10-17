import httpx
import pytest

from conftest import BASE, banco, sql
from test_editais import NOVO
from test_mensagens import caixa
from test_relatorios import baixar


@pytest.mark.req("V2-INT-02", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB", "INT-FORMS-DB", "INT-UPLOADS", "INT-SMTP", "INT-RELATORIOS", "INT-FORMS-STACK")
def test_da_homologacao_ao_resultado_e_aceite(clientes):
    admin, docente, outro = clientes("admin"), clientes("docente"), clientes("outro")
    novo = admin.post("edicts", json=dict(NOVO, candidate_forms="3", recommenders_forms="2", edict_type="doutorado"))
    assert novo.status_code == 200
    edital = novo.json()["id"]
    arvore = next(m["mapping"] for m in admin.get("edicts/2/candidates/mappings").json())
    assert admin.post(f"edicts/{edital}/candidates/mappings/versions/1/", json=arvore).status_code == 200
    sql(f"UPDATE edict SET accept_forms='4' WHERE id={edital}")
    sql(f"UPDATE submission SET edict_id={edital} WHERE id=3")

    fases = {p["phase"]: p["id"] for p in admin.get(f"edicts/{edital}").json()["phases"]}
    assert admin.post(f"edicts/{edital}/advance-phase", json={"id": fases["homologacao"]}).status_code == 200
    assert banco("SELECT phase::text FROM form WHERE id=3", "forms") == [{"phase": "Approval"}]
    assert admin.post("submissions/3/reesend_submission", json={"text": "Reenviar plano de pesquisa"}).status_code == 200
    [correcao] = caixa(1)
    assert correcao["To"] == "carla.piloto@example.com"
    link = httpx.get(f"{BASE}/form/c0a5e1f0-0000-4000-8000-000000000003", verify=False)
    assert link.status_code == 200

    assert admin.post(f"edicts/{edital}/advance-phase", json={"id": fases["avaliacao"]}).status_code == 200
    assert docente.post("submissions/3/comments", json={"comment": "Plano consistente"}).status_code == 200
    assert docente.post("submissions/3/favorites").status_code == 201
    assert docente.post("submissions/3/labels", json={"label": "prioridade", "color": "#ff0000"}).status_code == 200
    assert docente.post("submissions/3/private_notes", json={"note": "Conversar"}).status_code == 200
    assert outro.post(f"edicts/{edital}/slots", json={"amount": "1"}).status_code == 200
    assert outro.post("submissions/3/bidding", json={"bidding": "agreed"}).status_code == 200
    plano = next(f["value"] for s in docente.get("submissions/3").json()["submission_form"]
                 for f in s["fields"] if f["name"] == "research-plan")
    assert docente.get(f"submissions/3/files/research-plan/{plano}").status_code == 200

    assert admin.post("submissions/3/select", json={"stats": "approved", "user_ids": [3]}).status_code == 200
    assert admin.post("submissions/3/entry-semester", json={"semester": "primeiro"}).status_code == 200
    assert docente.post("submissions/3/send-accept").status_code == 200
    [sub] = banco("SELECT accept_form_id FROM submission WHERE id=3")
    sql(f"""UPDATE form_response SET submitted_at=now() WHERE id={sub['accept_form_id']};
        INSERT INTO responses(response_id,field_id,value) SELECT {sub['accept_form_id']},id,
        CASE name WHEN 'accept' THEN 'Aceito a vaga.' ELSE 'Até breve.' END FROM form_field WHERE form_id=4""", "forms")
    aceite = docente.get("submissions/3").json()["summary"]["accept"]
    assert (aceite["sent"], aceite["accept"]) == ("replied", "Aceito a vaga.")
    assert docente.post("submissions/3/send-letter").status_code == 200
    assert len(caixa(3)) == 3

    pdf = admin.post(f"edicts/{edital}/interactors_list", params={"mode": "pdf"}, json={"relation": True})
    assert baixar(admin, "pdf", pdf.json()["job_id"]).status_code == 200
    csv = admin.post(f"edicts/{edital}/pairing-biddings")
    assert "agreed" in baixar(admin, "csv", csv.json()["job_id"]).text

    assert admin.patch(f"edicts/{edital}/close", json={"confirmation_deadline": "2031-05-01",
                                                       "send_approval_letter": False}).status_code == 200
    assert admin.post("submissions/3/select", json={"stats": "refused", "user_ids": None}).status_code == 409
    assert banco("SELECT stats, advisor_id, letter_sent FROM submission WHERE id=3") == [
        {"stats": "approved", "advisor_id": 3, "letter_sent": True}]
