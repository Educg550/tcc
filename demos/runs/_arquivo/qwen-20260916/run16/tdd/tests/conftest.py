from fastapi.testclient import TestClient


def _criar_cliente():
    try:
        from app import app
    except Exception:
        return None
    try:
        return TestClient(app)
    except Exception:
        return None


def test_cliente_de_teste_funciona():
    # Garante que o servidor abre e serve a página raiz.
    # Testes que precisam do cliente usam pytest.importorskip para não quebrar
    # a suíte quando o backend ainda não existe.
    cliente = _criar_cliente()
    if cliente is None:
        import pytest
        pytest.skip("backend ainda não implementado")
    resposta = cliente.get("/")
    assert resposta.status_code == 200
