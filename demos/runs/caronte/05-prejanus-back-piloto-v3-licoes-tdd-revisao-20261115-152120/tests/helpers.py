import os
import time

import httpx
import pytest

# Ordem cronológica exigida pelo requisito:
# date_application (inscricoes) < date_evaluation (homologacao)
# < date_verification (avaliacao) < date_closed (encerrado)
DATES = [
    "2031-01-05T00:00:00",
    "2031-02-05T00:00:00",
    "2031-03-05T00:00:00",
    "2031-04-05T00:00:00",
]


def client(var):
    return httpx.Client(base_url=os.environ[var].rstrip("/"), timeout=120)


def source_edict(cl):
    """Edital existente que possui inscrições, com seu detalhe e inscrições."""
    r = cl.get("/edicts")
    assert r.status_code == 200, r.text
    for e in r.json():
        rs = cl.get(f"/edicts/{e['id']}/submissions")
        assert rs.status_code == 200, rs.text
        subs = rs.json().get("submissions", [])
        if subs:
            d = cl.get(f"/edicts/{e['id']}").json()
            return {"id": e["id"], "detail": d, "submissions": subs}
    pytest.fail("nenhum edital com inscrições foi encontrado nas fixtures")


def edict_body(cl, title):
    src = source_edict(cl)
    d = src["detail"]
    return {
        "title": title,
        "description": "Edital de teste do piloto v2",
        "year": 2031,
        "semester": 1,
        "edict_type": d["type"],
        "is_open": True,
        "candidate_forms": int(d["candidate_form_id"]),
        "recommenders_forms": int(d["recommender_form_id"]),
        "date_application": DATES[0],
        "date_evaluation": DATES[1],
        "date_verification": DATES[2],
        "date_closed": DATES[3],
    }


def mapping_items(data):
    if isinstance(data, list):
        return data
    for key in ("mappings", "data", "items"):
        if isinstance(data, dict) and isinstance(data.get(key), list):
            return data[key]
    return []


def mapping_tree(m):
    for key in ("mapping", "tree", "map"):
        if isinstance(m.get(key), dict):
            return m[key]
    return None


def mapping_version(m):
    for key in ("form_version", "version"):
        if m.get(key) is not None:
            return m[key]
    return None


def copy_mappings(admin, src_id, dst_id, tipo):
    data = admin.get(f"/edicts/{src_id}/{tipo}/mappings").json()
    for m in mapping_items(data):
        tree = mapping_tree(m)
        version = mapping_version(m)
        if tree is not None and version is not None:
            r = admin.post(
                f"/edicts/{dst_id}/{tipo}/mappings/versions/{version}/", json=tree
            )
            assert r.status_code == 200, r.text


def create_edict(admin, title, copy=True):
    body = edict_body(admin, title)
    r = admin.post("/edicts", json=body)
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    if copy:
        src = source_edict(admin)
        for tipo in ("candidates", "recommenders"):
            copy_mappings(admin, src["id"], eid, tipo)
    return eid


def advance(admin, edict_id, phase):
    d = admin.get(f"/edicts/{edict_id}").json()
    for p in d["phases"]:
        if p["phase"] == phase:
            r = admin.post(f"/edicts/{edict_id}/advance-phase", json={"id": p["id"]})
            assert r.status_code == 200, r.text
            return r.json()
    pytest.fail(f"fase {phase} não encontrada no edital {edict_id}")


def submissions_of(cl, edict_id):
    r = cl.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200, r.text
    return r.json()["submissions"]


def first_leaf(admin, form_id):
    secs = admin.get(f"/forms/{form_id}/sections").json()
    ids = [s["id"] if isinstance(s, dict) else s for s in secs]
    for sid in ids:
        fields = admin.get(f"/forms/{form_id}/sessions/{sid}/fields").json()
        if fields:
            f = fields[0]
            return {"section": sid, "field": f["id"]}
    pytest.fail(f"formulário {form_id} sem campos")


def smtp_raw_messages():
    base = os.environ["CARONTE_SMTP_API"].rstrip("/")
    msgs = httpx.get(f"{base}/api/Messages", timeout=60).json()
    out = []
    for m in msgs:
        raw = httpx.get(f"{base}/api/Messages/{m['id']}/raw", timeout=60)
        out.append({"id": m["id"], "raw": raw.content.decode("utf-8", "ignore")})
    return out


def smtp_find(to=None, contains=None, since=None):
    msgs = smtp_raw_messages()
    if since is not None:
        known = {m["id"] for m in since}
        msgs = [m for m in msgs if m["id"] not in known]
    for m in msgs:
        if to and to.lower() not in m["raw"].lower():
            continue
        if contains and contains.lower() not in m["raw"].lower():
            continue
        return m
    return None


def wait_download(cl, path, timeout=90):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = cl.get(path)
        if r.status_code == 200:
            return r
        last = r
        time.sleep(0.5)
    pytest.fail(
        f"download não ficou pronto: {path} (último status "
        f"{last.status_code if last is not None else None})"
    )
