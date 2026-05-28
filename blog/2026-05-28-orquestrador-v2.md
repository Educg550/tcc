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

## Resultado obtido: métricas coletadas

Ao final, o pipeline grava `output/task-cli-orquestrado/RUN.log` com:

```json
{
  "started_at": "...",
  "ended_at": "...",
  "total_duration_s": 0.0,
  "total_cost_usd": 0.0,
  "total_retries": 0,
  "stages": [...],
  "pytest_final": { "passed": 0, "failed": 0, "total": 0, "summary": "..." }
}
```

Cada entrada em `stages` carrega duração, custo, tokens e `retries` daquela etapa. O `pytest_final` é rodado pelo próprio orquestrador ao final — independente do pytest interno do `coder` — para confirmar o estado real do código entregue.
