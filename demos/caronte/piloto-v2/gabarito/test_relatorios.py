import csv
import io
import time

import pytest
from pypdf import PdfReader

from test_inscricoes import nova_candidatura

TODAS = {"list_of_advisors": True, "relation": True, "approved": True, "refused": True, "underreview": True,
         "general_statistics": True, "show_emails": True}


def interagir(clientes):
    clientes("docente").post("submissions/1/comments", json={"comment": "c"})
    clientes("outro").post("submissions/2/favorites")
    clientes("secretaria").post("submissions/1/labels", json={"label": "l", "color": "#000000"})
    clientes("coordenador").post("submissions/4/private_notes", json={"note": "n"})
    clientes("admin").post("submissions/3/comments", json={"comment": "outro edital"})
    clientes("estudante").post("submissions/1/view")


def baixar(c, tipo, job_id, espera=60):
    for _ in range(espera * 2):
        r = c.get(f"edicts/download_{tipo}/{job_id}")
        if r.status_code != 404:
            return r
        time.sleep(.5)
    return r


def gerar_pdf(admin, opcoes):
    r = admin.post("edicts/1/interactors_list", params={"mode": "pdf"}, json=opcoes)
    assert r.status_code == 200 and r.json()["status"] == "processing"
    pdf = baixar(admin, "pdf", r.json()["job_id"])
    assert pdf.status_code == 200
    return " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)


@pytest.mark.req("V2-REL-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_lista_quem_interagiu_no_edital(clientes):
    interagir(clientes)
    r = clientes("admin").post("edicts/1/interactors_list", json={})
    assert r.status_code == 200
    assert sorted(u["id"] for u in r.json()) == [2, 3, 4, 5]


@pytest.mark.req("V2-REL-01", "V2-REL-03")
@pytest.mark.integracao("INT-RELATORIOS")
def test_pdf_com_todas_as_secoes(clientes):
    interagir(clientes)
    clientes("admin").post("submissions/1/select", json={"stats": "approved", "user_ids": [3]})
    clientes("admin").post("submissions/2/select", json={"stats": "waitlist", "user_ids": None})
    texto = gerar_pdf(clientes("admin"), TODAS)
    for trecho in ("2026", "Estatísticas Gerais", "3 submissões finalizadas", "4 orientadores",
                   "Relação de candidatos e orientadores", "Ana Piloto Caronte", "Outra Docente",
                   "E-mails orientadores", "docente.piloto@example.com", "E-mails candidatos aprovados",
                   "candidata.piloto@example.com", "E-mails candidatos reprovados", "bruno.piloto@example.com",
                   "E-mails candidatos em análise", "diego.piloto@example.com"):
        assert trecho in texto, trecho


@pytest.mark.req("V2-REL-01")
@pytest.mark.integracao("INT-RELATORIOS")
def test_pdf_sem_secoes_opcionais_nem_emails(clientes):
    interagir(clientes)
    texto = gerar_pdf(clientes("admin"), {})
    assert "Observações Finais" in texto
    for ausente in ("Estatísticas Gerais", "Relação de candidatos", "Anexo", "@example.com"):
        assert ausente not in texto, ausente


@pytest.mark.req("V2-REL-01")
@pytest.mark.integracao("INT-RELATORIOS", "INT-FORMS-DB")
def test_pdf_conta_candidaturas_em_preenchimento(clientes):
    nova_candidatura(22, "Gabi Rascunho", submetida=False)
    texto = gerar_pdf(clientes("admin"), {"general_statistics": True})
    assert "3 submissões finalizadas" in texto


@pytest.mark.req("V2-REL-02", "V2-REL-03")
@pytest.mark.integracao("INT-RELATORIOS")
def test_csv_de_interesses_e_vagas(clientes):
    clientes("docente").post("edicts/1/slots", json={"amount": "2"})
    clientes("outro").post("edicts/1/slots", json={"amount": "1"})
    clientes("docente").post("submissions/1/bidding", json={"bidding": "interested"})
    clientes("docente").post("submissions/2/bidding", json={"bidding": "decline"})
    clientes("outro").post("submissions/1/bidding", json={"bidding": "agreed"})
    clientes("docente").post("submissions/4/labels", json={"label": "não é interesse", "color": "#000000"})
    r = clientes("admin").post("edicts/1/pairing-biddings")
    assert r.status_code == 200 and r.json()["status"] == "processing"
    arquivo = baixar(clientes("admin"), "csv", r.json()["job_id"])
    assert arquivo.status_code == 200
    leitor = csv.DictReader(io.StringIO(arquivo.text))
    assert leitor.fieldnames[0] == "#"
    assert sorted(leitor.fieldnames[1:]) == ["docente.piloto@example.com", "outra.piloto@example.com"]
    tabela = {l.pop("#"): l for l in leitor}
    assert tabela["slots"] == {"docente.piloto@example.com": "2", "outra.piloto@example.com": "1"}
    assert tabela["candidata.piloto@example.com"] == {"docente.piloto@example.com": "interested",
                                                      "outra.piloto@example.com": "agreed"}
    assert tabela["bruno.piloto@example.com"] == {"docente.piloto@example.com": "decline", "outra.piloto@example.com": ""}
    assert "não é interesse" not in arquivo.text


@pytest.mark.req("V2-REL-03")
@pytest.mark.parametrize("tipo,mime", [("pdf", "application/pdf"), ("csv", "text/csv")])
def test_download_consumido_uma_unica_vez(admin, tipo, mime):
    r = (admin.post("edicts/1/interactors_list", params={"mode": "pdf"}, json={}) if tipo == "pdf"
         else admin.post("edicts/1/pairing-biddings"))
    job = r.json()["job_id"]
    arquivo = baixar(admin, tipo, job)
    assert arquivo.status_code == 200
    assert arquivo.headers["content-type"].startswith(mime)
    assert arquivo.headers["content-disposition"].startswith("inline")
    assert admin.get(f"edicts/download_{tipo}/{job}").status_code == 404


@pytest.mark.req("V2-REL-03")
def test_jobs_distintos_nao_se_confundem(admin):
    a = admin.post("edicts/1/pairing-biddings").json()["job_id"]
    b = admin.post("edicts/2/pairing-biddings").json()["job_id"]
    assert a != b
    assert baixar(admin, "csv", a).status_code == 200
    assert baixar(admin, "csv", b).status_code == 200


@pytest.mark.req("V2-REL-03")
@pytest.mark.parametrize("tipo", ["pdf", "csv"])
def test_job_inexistente_responde_404(anonimo, tipo):
    assert anonimo.get(f"edicts/download_{tipo}/00000000-0000-0000-0000-000000000000").status_code == 404
