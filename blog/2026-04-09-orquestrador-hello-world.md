---
slug: orquestrador-hello-world
title: "Hello World: orquestrador TDD com Agent SDK"
authors: [eduardo]
tags: [tcc, experimento]
---

Primeiro protótipo funcional do pipeline multiagente baseado em TDD,
usando a [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).
O objetivo é demonstrar, da forma mais simples possível,
o conceito central do TCC: **um orquestrador que coordena subagentes
especializados no fluxo Requisito → Testes → Código**.

<!-- truncate -->

## O que o script faz

O requisito de exemplo é trivial, apenas fazer uma função `validar_cpf(cpf) -> bool`:

```
┌──────────────────┐
│  Orquestrador    │  (Haiku — só coordena, não escreve código)
│  "pipeline TDD"  │
└────┬────────┬────┘
     │        │
     ▼        │
┌──────────┐  │
│  Agente  │  │
│  test-   │  │  1. Recebe o requisito
│  writer  │  │  2. Gera testes pytest (tests/test_cpf.py)
│ (Sonnet) │  │  3. NÃO implementa nada
└──────────┘  │
              ▼
        ┌──────────┐
        │  Agente  │
        │  coder   │  1. Lê os testes gerados
        │ (Sonnet) │  2. Implementa cpf.py
        └──────────┘  3. Roda pytest e corrige até passar
```

O orquestrador roda em Haiku (modelo leve e barato) porque ele só precisa
despachar os subagentes na ordem certa.
Os subagentes que fazem o trabalho de escrever testes e código, eles rodam com o Claude Sonnet.

## Como funciona no código

O script usa a função `query()` da Agent SDK com subagentes definidos via `AgentDefinition`:

```python
agents = {
    "test-writer": AgentDefinition(
        description="Gera testes pytest a partir de um requisito...",
        prompt="Escreva APENAS os testes, NÃO implemente...",
        tools=["Write", "Bash", "Read"],
        model="sonnet",
    ),
    "coder": AgentDefinition(
        description="Implementa código que faz os testes passarem...",
        prompt="Leia os testes e implemente a função...",
        tools=["Read", "Write", "Bash"],
        model="sonnet",
    ),
}

# O orquestrador recebe os agentes e coordena a execução
options = ClaudeAgentOptions(
    allowed_tools=["Agent", "Bash", "Read", "Write"],
    agents=agents,
    model="haiku",
)

async for message in query(prompt=PROMPT_ORQUESTRADOR, options=options):
    # streaming dos resultados...
```

O orquestrador recebe um prompt que diz: "chame test-writer primeiro,
depois chame coder". Ele usa a tool `Agent` internamente para despachar cada subagente.

## Status atual: aguardando API key

O script ainda **não foi executado** porque depende de uma chave de API
configurada via variável de ambiente (`ANTHROPIC_API_KEY`).
Atualmente a Agent SDK suporta apenas a API da Anthropic,
mas o plano é utilizar uma chave da [OpenRouter](https://openrouter.ai/)
para testar o pipeline com **múltiplos provedores de LLM** (Claude, GPT, Gemini, etc.)
e comparar os resultados entre modelos.

## Próximos passos

- [ ] Obter API key da OpenRouter para testes multi-provedor
- [ ] Executar o pipeline pela primeira vez e documentar os resultados
- [ ] Avaliar a qualidade dos testes gerados e do código produzido
- [ ] Expandir o requisito para algo mais complexo (múltiplas funções, CRUD, CLI, etc.)
- [ ] Estudar como integrar um CUA como validador comportamental final
