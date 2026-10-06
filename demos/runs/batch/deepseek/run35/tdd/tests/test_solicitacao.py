from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)


CAMINHOS = [
    "/solicitacao",
    "/api/solicitacao",
    "/solicitacoes",
    "/api/solicitacoes",
    "/solicitar",
    "/api/solicitar",
    "/enviar",
    "/api/enviar",
    "/submit",
    "/api/submit",
    "/auxilio",
    "/api/auxilio",
]


def respostas(dados):
    """Envia a solicitação para os endereços plausíveis e devolve o que responderem."""
    recebidas = []
    for caminho in CAMINHOS:
        for kwargs in ({"json": dados}, {"data": dados}):
            resposta = cliente.post(caminho, **kwargs)
            if resposta.status_code != 404:
                recebidas.append(resposta)
    return recebidas


def test_envio_vazio_exige_campos_obrigatorios():
    recebidas = respostas({})
    assert any("Preencha todos os campos" in r.text for r in recebidas)
