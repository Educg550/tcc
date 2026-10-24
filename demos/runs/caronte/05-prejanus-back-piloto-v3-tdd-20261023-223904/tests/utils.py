import httpx


class Client:
    """Cliente HTTP sincrono que preserva o cookie de sessao manualmente.

    O cookie original e `Secure`; em HTTP local o jar do httpx nao
    reenvia cookies Secure, entao propagamos o header Cookie a mao.
    """

    def __init__(self, base_url):
        self._c = httpx.Client(base_url=base_url, timeout=120.0)
        self.cookie = None

    def request(self, method, url, **kw):
        headers = dict(kw.pop("headers", {}) or {})
        if self.cookie:
            headers["Cookie"] = self.cookie
        r = self._c.request(method, url, headers=headers, **kw)
        sc = r.headers.get("set-cookie")
        if sc:
            self.cookie = sc.split(";", 1)[0]
        return r

    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)

    def put(self, url, **kw):
        return self.request("PUT", url, **kw)

    def patch(self, url, **kw):
        return self.request("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self.request("DELETE", url, **kw)

    def close(self):
        self._c.close()


def edicts(client):
    r = client.get("/edicts")
    assert r.status_code == 200, r.text
    return r.json()


def edicts_with_submissions(client):
    out = []
    for e in edicts(client):
        r = client.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200:
            subs = r.json().get("submissions", [])
            if subs:
                out.append((e["id"], subs))
    return out


def any_submission(client):
    found = edicts_with_submissions(client)
    assert found, "nenhum edital com inscricoes encontrado no ambiente"
    eid, subs = found[0]
    return eid, subs[0]


def smtp_messages(smtp_base):
    r = httpx.get(f"{smtp_base}/api/Messages", timeout=30)
    data = r.json()
    if isinstance(data, dict):
        data = data.get("messages") or data.get("data") or []
    return data


def smtp_raw(smtp_base, message_id):
    return httpx.get(f"{smtp_base}/api/Messages/{message_id}/raw", timeout=30).text


def smtp_find(smtp_base, predicate):
    """Procura mensagem cujo (metadados, raw) satisfaz o predicado."""
    for m in smtp_messages(smtp_base):
        try:
            raw = smtp_raw(smtp_base, m["id"])
        except Exception:
            continue
        if predicate(m, raw):
            return m, raw
    return None


def pdf_items(node, out=None):
    """Coleta (candidatos a label, filename) de valores .pdf no detalhe."""
    if out is None:
        out = []
    if isinstance(node, dict):
        pdfs = [v for v in node.values() if isinstance(v, str) and v.lower().endswith(".pdf")]
        if pdfs:
            labels = []
            for k, v in node.items():
                if isinstance(v, str) and not v.lower().endswith(".pdf"):
                    labels.append(v)
                elif isinstance(v, (int, float)):
                    labels.append(str(v))
                if isinstance(k, str):
                    labels.append(k)
            for p in pdfs:
                out.append((labels, p))
        for v in node.values():
            pdf_items(v, out)
    elif isinstance(node, list):
        for v in node:
            pdf_items(v, out)
    return out
