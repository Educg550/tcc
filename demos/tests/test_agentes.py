import asyncio

import httpx
import pytest
from openai import AsyncOpenAI

from harness.models.agentes import Agente


@pytest.mark.parametrize("conteudo", ['{"arquivos": []}', None, "falha HTTP"])
def test_cliente_fecha_no_mesmo_loop_e_resposta_preserva_metricas(conteudo):
    async def verificar():
        def responder(request):
            if conteudo == "falha HTTP":
                raise httpx.ConnectError("offline", request=request)
            return httpx.Response(200, json={
                "id": "teste", "object": "chat.completion", "created": 0,
                "model": "teste", "choices": [{
                    "index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": conteudo},
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2,
                          "total_tokens": 12, "cost": 0.01},
            })

        agente = Agente("teste", "teste")
        agente._agno.telemetry = False
        cliente = AsyncOpenAI(
            api_key="teste", max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(responder)),
        )
        agente._agno.model.async_client = cliente
        try:
            resposta = await agente.propor("teste")
            if conteudo == "falha HTTP":
                assert resposta.mudanca is None
                assert resposta.erro
            else:
                assert resposta.total_tokens == 12
                assert resposta.custo_usd == 0.01
                if conteudo is None:
                    assert resposta.mudanca is None
                    assert "resposta vazia" in resposta.erro
                else:
                    assert resposta.mudanca.arquivos == []
        finally:
            assert cliente.is_closed()

    asyncio.run(verificar())
