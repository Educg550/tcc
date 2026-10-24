import uuid

from tests.utils import edicts, edicts_with_submissions
from tests.test_edicts import _payload, _form_ids


def _structure(admin, form_id, version=None):
    params = {"version": version} if version else None
    r = admin.get(f"/forms/{form_id}/sections", params=params)
    assert r.status_code == 200, r.text
    data = r.json()
    if data and isinstance(data[0], dict):
        sections = [s["id"] for s in data]
    else:
        sections = list(data)
    assert sections
    fields = []
    for sid in sections:
        fr = admin.get(f"/forms/{form_id}/sessions/{sid}/fields")
        assert fr.status_code == 200, fr.text
        fdata = fr.json()
        if fdata and isinstance(fdata[0], dict):
            fields.extend((sid, f["id"]) for f in fdata)
        else:
            fields.extend((sid, fid) for fid in fdata)
    assert fields
    return fields


def _create_edict(admin):
    payload = _payload(admin)
    r = admin.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"], payload


def _mappings(admin, eid, tipo):
    r = admin.get(f"/edicts/{eid}/{tipo}/mappings")
    assert r.status_code == 200, r.text
    return r.json()


def test_candidate_mapping_crud(admin):
    eid, payload = _create_edict(admin)
    try:
        fields = _structure(admin, payload["candidate_forms"])
        sid, fid = fields[0]
        tree = {"pessoal": {"nome": {"section": sid, "field": fid}, "vazio": None}}
        r = admin.post(
            f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree
        )
        assert r.status_code == 200, r.text
        mapping = r.json()
        mid = mapping["id"]
        assert mapping["form_version"] == 1

        listed = _mappings(admin, eid, "candidates")
        ids = [m["id"] for m in listed]
        assert mid in ids

        # arvore invalida
        bad = {"x": {"section": 999999, "field": 999999}}
        rb = admin.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=bad)
        assert rb.status_code == 422

        # duplicado para mesma versao
        rd = admin.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree)
        assert rd.status_code >= 400

        # atualizar arvore
        sid2, fid2 = fields[-1]
        tree2 = {"pessoal": {"nome": {"section": sid2, "field": fid2}}}
        ru = admin.put(
            f"/edicts/{eid}/candidates/mappings/versions/1/{mid}", json=tree2
        )
        assert ru.status_code == 200, ru.text
        listed = _mappings(admin, eid, "candidates")
        updated = next(m for m in listed if m["id"] == mid)
        assert updated["mapping"] == tree2

        # excluir
        rdel = admin.delete(f"/edicts/{eid}/candidates/mappings/versions/1/{mid}")
        assert rdel.status_code == 200
        assert rdel.json() == {"message": "Mapping deleted successfully"}
        assert mid not in [m["id"] for m in _mappings(admin, eid, "candidates")]

        # combinacoes inexistentes
        assert (
            admin.put(
                f"/edicts/{eid}/candidates/mappings/versions/1/{mid}", json=tree2
            ).status_code
            == 404
        )
        assert (
            admin.delete(
                f"/edicts/{eid}/candidates/mappings/versions/1/{mid}"
            ).status_code
            == 404
        )
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_recommender_mapping_crud(admin):
    eid, payload = _create_edict(admin)
    try:
        fields = _structure(admin, payload["recommenders_forms"])
        sid, fid = fields[0]
        tree = {"carta": {"texto": {"section": sid, "field": fid}}}
        r = admin.post(f"/edicts/{eid}/recommenders/mappings/versions/1/", json=tree)
        assert r.status_code == 200, r.text
        mid = r.json()["id"]
        assert mid in [m["id"] for m in _mappings(admin, eid, "recommenders")]

        rdel = admin.delete(f"/edicts/{eid}/recommenders/mappings/versions/1/{mid}")
        assert rdel.status_code == 200
        assert rdel.json() == {"message": "Mapping deleted successfully"}
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_mapping_requires_admin_role(api):
    eid, payload = _create_edict(api)
    try:
        tree = {"a": None}
        r = api.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree)
        assert r.status_code == 403
    finally:
        api.delete(f"/edicts/{eid}/remove")


def test_unmapped_versions(admin):
    found = edicts_with_submissions(admin)
    assert found, "nenhum edital com inscricoes"
    target = None
    for eid, _subs in found:
        r = admin.get(f"/edicts/{eid}/candidates/forms/versions/unmapped")
        assert r.status_code == 200, r.text
        if r.json():
            target = (eid, r.json())
            break
    assert target, "nenhuma versao sem mapeamento disponivel no ambiente"
    eid, versions = target
    version = versions[0]

    detail = admin.get(f"/edicts/{eid}").json()
    form_id = int(detail["candidate_form_id"])
    fields = _structure(admin, form_id, version=version)
    sid, fid = fields[0]
    tree = {"x": {"y": {"section": sid, "field": fid}}}

    r = admin.post(f"/edicts/{eid}/candidates/mappings/versions/{version}/", json=tree)
    assert r.status_code == 200, r.text
    mid = r.json()["id"]
    try:
        after = admin.get(f"/edicts/{eid}/candidates/forms/versions/unmapped").json()
        assert version not in after
    finally:
        admin.delete(f"/edicts/{eid}/candidates/mappings/versions/{version}/{mid}")
    back = admin.get(f"/edicts/{eid}/candidates/forms/versions/unmapped").json()
    assert version in back
