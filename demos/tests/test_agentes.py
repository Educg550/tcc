import asyncio
import json
import time
from dataclasses import replace

import httpx
import pytest
from openai import AsyncOpenAI

from harness.models.agentes import Agente
from harness.models.dominio import Projeto, ResultadoPytest
from harness.models.etapas import CODIGO, EtapaTDD
from harness.models.politicas import Batch, Orcamento
from harness.models.tracing import Trace

ORCAMENTO = Orcamento(passos=10, custo_usd=1, tempo_s=60)


@pytest.fixture(autouse=True)
def sem_rede_real(monkeypatch):
    def recusar(*args, **kwargs):
        raise AssertionError("Teste de agente não pode acessar a rede real.")

    monkeypatch.setattr("socket.getaddrinfo", recusar)
    monkeypatch.setattr("socket.socket.connect", recusar)
    monkeypatch.setattr("socket.socket.connect_ex", recusar)


def ferramenta(nome, **argumentos):
    return {"id": "chamada", "type": "function", "function": {
        "name": nome, "arguments": json.dumps(argumentos),
    }}


def configurar(tmp_path, responder, orcamento=ORCAMENTO):
    agente = Agente("teste", "teste")
    agente._agno.telemetry = False
    agente._agno.model.api_key = "teste"
    agente.preparar(Projeto(tmp_path, None), CODIGO, orcamento, time.time())

    async def transportar(request):
        mensagem = responder(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "teste", "object": "chat.completion", "created": 0,
            "model": "teste", "choices": [{
                "index": 0, "finish_reason": "tool_calls" if mensagem.get("tool_calls") else "stop",
                "message": {"role": "assistant", **mensagem},
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2,
                      "total_tokens": 12, "cost": 0.01},
        })

    def cliente_simulado():
        modelo = agente._agno.model
        if modelo.async_client is None or modelo.async_client.is_closed():
            modelo.async_client = AsyncOpenAI(
                api_key="teste", max_retries=0,
                http_client=httpx.AsyncClient(transport=httpx.MockTransport(transportar)),
            )
        return modelo.async_client

    agente._agno.model.get_async_client = cliente_simulado
    return agente, cliente_simulado()


def test_ferramentas_editam_incrementalmente_com_historico_e_metricas(tmp_path):
    async def verificar():
        pedidos = []
        roteiro = [
            {"tool_calls": [ferramenta("criar_arquivo", caminho="app.py", conteudo="x = 1\ny = 2\n")]},
            {"tool_calls": [ferramenta("ler_arquivo", caminho="app.py")]},
            {"tool_calls": [ferramenta("substituir_trecho", caminho="app.py", antigo="x = 1", novo="x = 3")]},
            {"content": "Arquivo criado e corrigido."},
            {"tool_calls": [ferramenta("ler_arquivo", caminho="app.py")]},
            {"tool_calls": [ferramenta("substituir_trecho", caminho="app.py", antigo="x = 3", novo="x = 4")]},
            {"content": "Corrigido após feedback."},
        ]

        def responder(pedido):
            pedidos.append(pedido)
            assert "response_format" not in pedido
            assert pedido["parallel_tool_calls"] is False
            assert {t["function"]["name"] for t in pedido["tools"]} == {
                "listar_arquivos", "ler_arquivo", "criar_arquivo", "substituir_trecho",
            }
            return roteiro.pop(0)

        agente, cliente = configurar(tmp_path, responder, replace(ORCAMENTO, passos=1))
        resposta = await agente.propor("REQUISITO")
        assert cliente.is_closed()
        assert not resposta.erro
        assert resposta.chamadas == 4
        assert resposta.total_tokens == 48
        assert resposta.custo_usd == pytest.approx(0.04)
        assert resposta.mudanca.arquivos[0].conteudo == "x = 3\ny = 2\n"
        assert not (tmp_path / "app.py").exists()
        assert CODIGO.aplicar(resposta.mudanca, agente.arquivos.projeto).arquivos == ["app.py"]
        assert pedidos[2]["messages"][-1]["content"] == "x = 1\ny = 2\n"

        # Um novo cliente é fechado no mesmo loop, sem descartar a sessão do Agno.
        resposta2 = await agente.propor("Corrija somente x.")
        assert agente._agno.model.async_client.is_closed()
        assert resposta2.chamadas == 3 and resposta2.total_tokens == 36
        assert resposta2.custo_usd == pytest.approx(0.03)
        assert resposta2.mudanca.arquivos[0].conteudo == "x = 4\ny = 2\n"
        assert any(m.get("content") == "REQUISITO" for m in pedidos[4]["messages"])
        assert pedidos[5]["messages"][-1]["content"] == "x = 3\ny = 2\n"

    asyncio.run(verificar())


def test_tdd_corrige_o_arquivo_atual_sem_reescrever_o_projeto(tmp_path):
    async def verificar():
        roteiro = [
            {"tool_calls": [ferramenta("criar_arquivo", caminho="app.py", conteudo="x = 1\ny = 2\n")]},
            {"content": "Implementado."},
            {"tool_calls": [ferramenta("ler_arquivo", caminho="app.py")]},
            {"tool_calls": [ferramenta("substituir_trecho", caminho="app.py", antigo="x = 1", novo="x = 3")]},
            {"content": "Corrigido."},
        ]
        agente, _ = configurar(tmp_path, lambda pedido: roteiro.pop(0))
        projeto = agente.arquivos.projeto
        projeto.preparar()

        def gate():
            app = tmp_path / "app.py"
            passou = app.exists() and "x = 3" in app.read_text()
            return ResultadoPytest(passou, int(passou), int(not passou), 0, "esperava x = 3")

        projeto.rodar_pytest = gate
        etapa = EtapaTDD("code", agente, Batch(), ORCAMENTO, Trace(projeto.saida / "trace.jsonl"))
        resultado = await etapa.executar("REQUISITO", projeto)
        assert resultado["ok"] and resultado["tests_vermelhos"]
        assert (resultado["passos"], resultado["retries"], resultado["chamadas_modelo"]) == (2, 1, 5)
        assert resultado["total_tokens"] == 60
        assert resultado["cost_usd"] == 0.05
        assert [h["passed"] for h in resultado["historico"]] == [0, 1]
        assert (tmp_path / "app.py").read_text() == "x = 3\ny = 2\n"

    asyncio.run(verificar())


def test_sintaxe_invalida_volta_como_erro_da_ferramenta(tmp_path):
    async def verificar():
        pedidos = []

        def responder(pedido):
            pedidos.append(pedido)
            if len(pedidos) <= 2:
                codigo = "x = (" if len(pedidos) == 1 else "x = 1\n"
                return {"tool_calls": [ferramenta("criar_arquivo", caminho="app.py", conteudo=codigo)]}
            return {"content": "Concluído."}

        agente, _ = configurar(tmp_path, responder)
        resposta = await agente.propor("REQUISITO")
        assert not resposta.erro and resposta.chamadas == 3
        assert "never closed" in pedidos[1]["messages"][-1]["content"]
        assert resposta.mudanca.arquivos[0].conteudo == "x = 1\n"

    asyncio.run(verificar())


@pytest.mark.parametrize("limite", ["custo", "tempo"])
def test_orcamento_interrompe_ciclo_antes_de_outra_chamada(tmp_path, limite):
    async def verificar():
        orcamento = replace(ORCAMENTO, custo_usd=0.005) if limite == "custo" else ORCAMENTO
        pedidos = []

        def responder(pedido):
            pedidos.append(pedido)
            if limite == "tempo":
                agente._agno.model.inicio -= 61
            return {"tool_calls": [ferramenta("criar_arquivo", caminho="app.py", conteudo="x = 1\n")]}

        agente, cliente = configurar(tmp_path, responder, orcamento)
        resposta = await agente.propor("REQUISITO")
        assert cliente.is_closed() and len(pedidos) == 1
        assert resposta.limite == limite and resposta.erro
        assert resposta.chamadas == 1 and resposta.total_tokens == 12
        assert resposta.custo_usd == 0.01
        # O orçamento não apaga os arquivos completos já propostos.
        assert resposta.mudanca.arquivos[0].conteudo == "x = 1\n"

    asyncio.run(verificar())


@pytest.mark.parametrize("conteudo", ["Pronto", None, "falha HTTP"])
def test_cliente_fecha_no_mesmo_loop_sem_edicao_ou_com_falha(tmp_path, conteudo):
    async def verificar():
        def responder(pedido):
            if conteudo == "falha HTTP":
                raise httpx.ConnectError("offline")
            return {"content": conteudo}

        agente, cliente = configurar(tmp_path, responder)
        resposta = await agente.propor("teste")
        assert cliente.is_closed()
        assert resposta.mudanca is None and resposta.erro
        assert resposta.chamadas == 1
        if conteudo != "falha HTTP":
            assert resposta.total_tokens == 12 and resposta.custo_usd == 0.01
        else:
            assert resposta.total_tokens == 0 and resposta.custo_usd == 0

    asyncio.run(verificar())
