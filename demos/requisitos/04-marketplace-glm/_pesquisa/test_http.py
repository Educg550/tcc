"""Checks externos do smoke; esta pasta não entra no contexto do gerador."""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack

import httpx
import pytest

URL = os.environ["MARKETPLACE_API"].rstrip("/")
ANUNCIO = dict(title="Produto do smoke", description="Descrição válida do produto de teste",
               price_cents=15990, stock=3, category="eletronicos", condition="usado",
               city="São Paulo", image_url=None)


@pytest.fixture
def pessoas():
    with ExitStack() as pilha:
        clientes = [pilha.enter_context(httpx.Client(base_url=URL, timeout=20)) for _ in range(3)]
        for i, cliente in enumerate(clientes):
            email = f"smoke-{uuid.uuid4().hex}@example.com"
            r = cliente.post("/api/auth/register", json={"name": f"Pessoa {i}", "email": email,
                                                        "password": "Marketplace123!"})
            assert r.status_code == 201, r.text
            assert "password" not in r.json() and "password_hash" not in r.json()
            r = cliente.post("/api/auth/login", json={"email": email, "password": "Marketplace123!"})
            assert r.status_code == 200, r.text
            assert cliente.get("/api/auth/me").status_code == 200
        yield clientes


@pytest.fixture
def anuncio(pessoas):
    r = pessoas[0].post("/api/listings", json=ANUNCIO)
    assert r.status_code == 201, r.text
    return r.json()


def comprar(cliente, anuncio, quantity=1):
    return cliente.post("/api/orders", json={"listing_id": anuncio["id"], "quantity": quantity,
                                             "address": "Rua do Teste, 123, São Paulo"})


def test_catalogo_publico_tem_seeds_e_paginacao():
    with httpx.Client(base_url=URL) as cliente:
        r = cliente.get("/api/listings", params={"limit": 2})
        assert r.status_code == 200, r.text
        dados = r.json()
        assert dados["total"] >= 12 and len(dados["items"]) == 2
        r = cliente.get("/api/listings", params={"q": "Bicicleta urbana"})
        assert any(a["title"] == "Bicicleta urbana" for a in r.json()["items"])
        assert cliente.post("/api/listings", json=ANUNCIO).status_code == 401


def test_mesma_conta_pode_vender_e_comprar(pessoas, anuncio):
    vendedor, comprador, _ = pessoas
    outro = comprador.post("/api/listings", json={**ANUNCIO, "title": "Também sou vendedor"})
    assert outro.status_code == 201, outro.text
    pedido = comprar(comprador, anuncio, 2)
    assert pedido.status_code == 201, pedido.text
    dados = pedido.json()
    assert dados["status"] == "pending" and dados["total_cents"] == 31980
    assert dados["unit_price_cents"] == 15990 and dados["quantity"] == 2
    assert vendedor.get(f"/api/listings/{anuncio['id']}").json()["stock"] == 1
    assert any(p["id"] == dados["id"] for p in comprador.get("/api/me/orders?role=buyer").json()["items"])
    assert any(p["id"] == dados["id"] for p in vendedor.get("/api/me/orders?role=seller").json()["items"])


def test_filtros_combinam_sem_distinguir_maiusculas(pessoas, anuncio):
    r = pessoas[1].get("/api/listings", params={"q": "PRODUTO DO SMOKE", "category": "eletronicos",
                                                "min_price": 15990, "max_price": 15990})
    assert r.status_code == 200, r.text
    assert any(a["id"] == anuncio["id"] for a in r.json()["items"])


def test_outro_usuario_nao_edita_anuncio(pessoas, anuncio):
    r = pessoas[1].patch(f"/api/listings/{anuncio['id']}", json={"price_cents": 1})
    assert r.status_code == 403, r.text
    assert pessoas[1].get(f"/api/listings/{anuncio['id']}").json()["price_cents"] == 15990


def test_favorito_idempotente_e_persistente(pessoas, anuncio):
    comprador = pessoas[1]
    rota = f"/api/favorites/{anuncio['id']}"
    for _ in range(2):
        assert comprador.post(rota).is_success
    itens = comprador.get("/api/favorites").json()["items"]
    assert sum(a["id"] == anuncio["id"] for a in itens) == 1
    for _ in range(2):
        assert comprador.delete(rota).is_success
    assert not comprador.get("/api/favorites").json()["items"]


def test_compra_propria_e_estoque_insuficiente_sao_recusados(pessoas, anuncio):
    assert comprar(pessoas[0], anuncio).status_code == 400
    assert comprar(pessoas[1], anuncio, 4).status_code == 409
    assert pessoas[1].get(f"/api/listings/{anuncio['id']}").json()["stock"] == 3


def test_cancelamento_restaura_estoque_uma_vez(pessoas, anuncio):
    comprador = pessoas[1]
    r = comprar(comprador, anuncio, 2)
    assert r.status_code == 201, r.text
    rota = f"/api/orders/{r.json()['id']}/status"
    assert comprador.patch(rota, json={"status": "cancelled"}).status_code == 200
    assert comprador.patch(rota, json={"status": "cancelled"}).status_code == 409
    assert comprador.get(f"/api/listings/{anuncio['id']}").json()["stock"] == 3


def test_pedido_privado_e_transicoes_por_participante(pessoas, anuncio):
    vendedor, comprador, estranho = pessoas
    pedido = comprar(comprador, anuncio).json()
    rota = f"/api/orders/{pedido['id']}"
    assert estranho.get(rota).status_code == 403
    assert comprador.patch(rota + "/status", json={"status": "confirmed"}).status_code == 403
    for cliente, estado in ((vendedor, "confirmed"), (vendedor, "shipped"), (comprador, "delivered")):
        r = cliente.patch(rota + "/status", json={"status": estado})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == estado
    assert comprador.patch(rota + "/status", json={"status": "cancelled"}).status_code == 409
    assert comprador.post(rota + "/review", json={"rating": 5, "comment": "Tudo certo"}).status_code == 201
    assert comprador.post(rota + "/review", json={"rating": 5, "comment": "De novo"}).status_code == 409
    perfil = comprador.get(f"/api/sellers/{anuncio['seller']['id']}")
    assert perfil.status_code == 200


def test_conversa_persiste_e_nao_vaza_para_terceiro(pessoas, anuncio):
    vendedor, comprador, estranho = pessoas
    r = comprador.post("/api/conversations", json={"listing_id": anuncio["id"]})
    assert r.status_code in (200, 201), r.text
    rota = f"/api/conversations/{r.json()['id']}/messages"
    assert comprador.post(rota, json={"content": "Ainda está disponível?"}).status_code == 201
    mensagens = vendedor.get(rota)
    assert mensagens.status_code == 200
    dados = mensagens.json()
    itens = dados["items"] if isinstance(dados, dict) else dados
    assert any(m["content"] == "Ainda está disponível?" for m in itens)
    assert estranho.get(rota).status_code == 403


def test_duas_compras_concorrentes_nao_vendem_ultima_unidade_duas_vezes(pessoas):
    r = pessoas[0].post("/api/listings", json={**ANUNCIO, "stock": 1})
    assert r.status_code == 201, r.text
    anuncio = r.json()
    with ThreadPoolExecutor(2) as executor:
        resultados = list(executor.map(lambda cliente: comprar(cliente, anuncio).status_code, pessoas[1:]))
    assert sorted(resultados) == [201, 409]
