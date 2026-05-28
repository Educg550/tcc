---
slug: orquestrador-v2
title: "Orquestrador v2: etapas separadas e aprovação humana"
authors: [eduardo]
tags: [tcc, experimento]
---

O `orquestrador_v2.py` substitui o `query()` único do v1 por três chamadas independentes, com pausa humana entre cada etapa e realimentação obrigatória em caso de rejeição.

<!-- truncate -->

## Motivação

No v1 o orquestrador despachava `test-writer` e `coder` num único `query()`, sem nenhuma inspeção humana no meio. O contexto acumulava tudo numa janela só, e não havia como intervir se os testes gerados estivessem errados.

O v2 separa as responsabilidades em três `query()` isolados, tornando cada etapa inspecionável antes de avançar.

## As três etapas

| Etapa | Subagente | Modelo | Artefato produzido |
|-------|-----------|--------|--------------------|
| 1 | `test-writer` | Sonnet | `tests/test_acceptance.py` |
| 2 | `structure-writer` | Sonnet | `structure.yml` |
| 3 | `coder` | Haiku | `src/task/*.py` |

O `structure.yml` segue o formato Onion (`!package` na raiz) — lista de pacotes, classes e métodos necessários para fazer os testes passarem, sem nenhum código de produção.

## Aprovação humana

Após cada etapa o orquestrador imprime o artefato gerado e pede `y/n`. Se o usuário digitar `n`, o feedback textual é solicitado e a etapa é re-executada com o feedback alimentado.

## Caso de uso

O requisito de entrada é uma CLI de tarefas em Python com 6 comandos (`add`, `list`, `done`, `edit`, `delete`, `show`), persistência em `tasks.json` e apenas stdlib. Mais complexo por se tratar de um CRUD com flags opcionais e vários edge cases de validação.

## Resultados e métricas obtidos

61/61 testes passando, $1.02, ~24 minutos. Houve 2 rejeições humanas no total (1 no `structure-writer`, 1 no `coder`). O `coder` (Haiku) consumiu mais de 1 milhão de tokens via cache devido às múltiplas iterações internas para fazer os testes passarem.

Output completo:

```json
{
  "started_at": "2026-05-28T10:49:01",
  "ended_at": "2026-05-28T11:13:06",
  "total_duration_s": 1444.6,
  "total_cost_usd": 1.0224989,
  "total_retries": 2,
  "stages": [
    {
      "id": "tests",
      "agent": "test-writer",
      "configured_model": "claude-sonnet-4-6",
      "duration_s": 146.14,
      "duration_api_s": 145.82,
      "num_turns": 2,
      "retries": 0,
      "cost_usd": 0.3591625500000001,
      "usage": {
        "input_tokens": 4,
        "cache_creation_input_tokens": 26576,
        "cache_read_input_tokens": 24752,
        "output_tokens": 1667,
        "server_tool_use": {
          "web_search_requests": 0,
          "web_fetch_requests": 0
        },
        "service_tier": "standard",
        "cache_creation": {
          "ephemeral_1h_input_tokens": 0,
          "ephemeral_5m_input_tokens": 0
        },
        "inference_geo": "",
        "iterations": [],
        "speed": "standard"
      },
      "model_usage": {
        "claude-sonnet-4-6": {
          "inputTokens": 13,
          "outputTokens": 10968,
          "cacheReadInputTokens": 90216,
          "cacheCreationInputTokens": 44677,
          "webSearchRequests": 0,
          "costUSD": 0.3591625500000001,
          "contextWindow": 200000,
          "maxOutputTokens": 32000
        }
      }
    },
    {
      "id": "structure",
      "agent": "structure-writer",
      "configured_model": "claude-sonnet-4-6",
      "duration_s": 116.25,
      "duration_api_s": 116.17,
      "num_turns": 2,
      "retries": 1,
      "cost_usd": 0.33000975,
      "usage": {
        "input_tokens": 4,
        "cache_creation_input_tokens": 14933,
        "cache_read_input_tokens": 36152,
        "output_tokens": 1352,
        "server_tool_use": {
          "web_search_requests": 0,
          "web_fetch_requests": 0
        },
        "service_tier": "standard",
        "cache_creation": {
          "ephemeral_1h_input_tokens": 0,
          "ephemeral_5m_input_tokens": 0
        },
        "inference_geo": "",
        "iterations": [],
        "speed": "standard"
      },
      "model_usage": {
        "claude-sonnet-4-6": {
          "inputTokens": 11,
          "outputTokens": 6872,
          "cacheReadInputTokens": 78785,
          "cacheCreationInputTokens": 54203,
          "webSearchRequests": 0,
          "costUSD": 0.33000975,
          "contextWindow": 200000,
          "maxOutputTokens": 32000
        }
      }
    },
    {
      "id": "code",
      "agent": "coder",
      "configured_model": "claude-haiku-4-5",
      "duration_s": 195.18,
      "duration_api_s": 139.58,
      "num_turns": 2,
      "retries": 1,
      "cost_usd": 0.3333266,
      "usage": {
        "input_tokens": 11,
        "cache_creation_input_tokens": 26441,
        "cache_read_input_tokens": 24514,
        "output_tokens": 1178,
        "server_tool_use": {
          "web_search_requests": 0,
          "web_fetch_requests": 0
        },
        "service_tier": "standard",
        "cache_creation": {
          "ephemeral_1h_input_tokens": 0,
          "ephemeral_5m_input_tokens": 0
        },
        "inference_geo": "",
        "iterations": [],
        "speed": "standard"
      },
      "model_usage": {
        "claude-haiku-4-5": {
          "inputTokens": 130,
          "outputTokens": 10687,
          "cacheReadInputTokens": 1094891,
          "cacheCreationInputTokens": 136218,
          "webSearchRequests": 0,
          "costUSD": 0.3333266,
          "contextWindow": 200000,
          "maxOutputTokens": 32000
        }
      }
    }
  ],
  "pytest_final": {
    "passed": 61,
    "failed": 0,
    "errors": 0,
    "total": 61,
    "summary": "61/61 passed",
    "collection_error": null
  }
}
```
