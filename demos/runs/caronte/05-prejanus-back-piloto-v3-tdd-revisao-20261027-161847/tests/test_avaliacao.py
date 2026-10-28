"""V2-AVA-01..05 — comentarios, favoritos, etiquetas, notas e visualizacoes."""
import uuid


def test_comentario_criado_na_fase_avaliacao(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/comments", json={"comment": "Bom candidato"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    assert body["comment"] == "Bom candidato"
    assert body["submission_id"] == sub["id"]
    assert body["user"]["id"] == 1
    assert body["created_at"]


def test_comentario_fora_da_fase_avaliacao(admin, submission_ctx, phase_id):
    edict, sub = submission_ctx
    admin.post(f"/edicts/{edict['id']}/advance-phase", json={"id": phase_id(edict["id"], "homologacao")})
    r = admin.post(f"/submissions/{sub['id']}/comments", json={"comment": "fora de fase"})
    assert r.status_code == 400


def test_atividade_sem_evento_por_leitura(admin, submission_ctx):
    _, sub = submission_ctx
    before = admin.get(f"/submissions/{sub['id']}/comments").json()
    admin.get(f"/submissions/{sub['id']}/comments")
    after = admin.get(f"/submissions/{sub['id']}/comments").json()
    assert len(after) == len(before)


def test_atividade_contem_comentario(admin, submission_ctx):
    _, sub = submission_ctx
    admin.post(f"/submissions/{sub['id']}/comments", json={"comment": "historico"})
    activity = admin.get(f"/submissions/{sub['id']}/comments").json()
    assert any(
        (e.get("comment") == "historico" or e.get("text") == "historico" or e.get("comment") == "historico")
        for e in activity
    )


def test_remover_comentario_autoria(admin, outro, submission_ctx):
    _, sub = submission_ctx
    created = admin.post(f"/submissions/{sub['id']}/comments", json={"comment": "minha"}).json()
    r = outro.delete(f"/submissions/comments/{created['id']}")
    assert r.status_code == 403
    r = admin.delete(f"/submissions/comments/{created['id']}")
    assert r.status_code == 204
    assert admin.delete(f"/submissions/comments/{created['id']}").status_code == 404


def test_favorito_ciclo(admin, submission_ctx):
    _, sub = submission_ctx
    assert admin.post(f"/submissions/{sub['id']}/favorites").status_code == 201
    assert admin.post(f"/submissions/{sub['id']}/favorites").status_code == 409
    detail = admin.get(f"/submissions/{sub['id']}").json()
    assert detail["summary"]["favorite"] is True
    assert admin.delete(f"/submissions/{sub['id']}/favorites").status_code == 204
    assert admin.delete(f"/submissions/{sub['id']}/favorites").status_code == 404


def test_favorito_por_usuario(admin, outro, submission_ctx):
    _, sub = submission_ctx
    admin.post(f"/submissions/{sub['id']}/favorites")
    detail_outro = outro.get(f"/submissions/{sub['id']}").json()
    assert detail_outro["summary"]["favorite"] is False
    admin.delete(f"/submissions/{sub['id']}/favorites")


def test_etiqueta_criacao_e_catalogo(admin, submission_ctx):
    _, sub = submission_ctx
    label = f"etiqueta-{uuid.uuid4().hex[:6]}"
    r = admin.post(f"/submissions/{sub['id']}/labels", json={"label": label, "color": "#ff0000"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    assert body["label"] == label
    assert body["submission_id"] == sub["id"]

    catalog = admin.get(f"/submissions/{sub['id']}/labels").json()
    assert any(l["label"] == label and l["color"] == "#ff0000" for l in catalog["labels"])

    detail = admin.get(f"/submissions/{sub['id']}").json()
    assert any(l["label"] == label for l in detail["summary"]["labels"])


def test_etiqueta_atualiza_cor_do_mesmo_autor(admin, submission_ctx):
    edict, sub = submission_ctx
    label = f"cor-{uuid.uuid4().hex[:6]}"
    admin.post(f"/submissions/{sub['id']}/labels", json={"label": label, "color": "#000000"})
    admin.post(f"/submissions/{sub['id']}/labels", json={"label": label, "color": "#00ff00"})
    catalog = admin.get(f"/submissions/{sub['id']}/labels").json()
    colors = {l["color"] for l in catalog["labels"] if l["label"] == label}
    assert colors == {"#00ff00"}


def test_remover_etiqueta_autoria(admin, outro, submission_ctx):
    _, sub = submission_ctx
    created = admin.post(
        f"/submissions/{sub['id']}/labels", json={"label": "apagar", "color": "#123456"}
    ).json()
    assert outro.delete(f"/submissions/label/{created['id']}").status_code == 403
    assert admin.delete(f"/submissions/label/{created['id']}").status_code == 204
    assert admin.delete(f"/submissions/label/{created['id']}").status_code == 404


def test_nota_privada(admin, outro, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/private_notes", json={"note": "nota secreta"})
    assert r.status_code == 200
    assert r.json()["note"] == "nota secreta"
    detail = admin.get(f"/submissions/{sub['id']}").json()
    assert detail["summary"]["private_note"] == "nota secreta"

    # outro usuario nao ve a nota
    detail_outro = outro.get(f"/submissions/{sub['id']}").json()
    assert detail_outro["summary"]["private_note"] == ""

    # atualizacao nao cria outra nota
    admin.post(f"/submissions/{sub['id']}/private_notes", json={"note": "nota alterada"})
    detail = admin.get(f"/submissions/{sub['id']}").json()
    assert detail["summary"]["private_note"] == "nota alterada"


def test_visualizacoes(admin, outro, submission_ctx):
    _, sub = submission_ctx
    assert admin.post(f"/submissions/{sub['id']}/view").status_code == 200
    first = admin.get(f"/submissions/{sub['id']}/view").json()
    assert first
    admin.post(f"/submissions/{sub['id']}/view")
    second = admin.get(f"/submissions/{sub['id']}/view").json()
    assert len(second) == len(first)  # mesmo usuario, mesmo dia

    outro.post(f"/submissions/{sub['id']}/view")
    third = admin.get(f"/submissions/{sub['id']}/view").json()
    assert len(third) == len(second) + 1
