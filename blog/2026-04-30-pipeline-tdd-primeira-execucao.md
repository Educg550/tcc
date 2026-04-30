---
slug: pipeline-tdd-primeira-execucao
title: "Pipeline TDD: primeira execução bem-sucedida via OpenRouter"
authors: [eduardo]
tags: [tcc, experimento]
---

O orquestrador TDD rodou pela primeira vez com sucesso nesta manhã:
35/35 testes gerados e passando, código implementado, tudo em 71 segundos e custou em tokens o equivalente a $0.106043.

<!-- truncate -->

## Contexto

O [post anterior](/blog/orquestrador-hello-world) descrevia o script `orquestrador_claude.py`
e explicava que ele ainda não havia sido executado por falta de uma API key.
A alternativa escolhida foi usar a [OpenRouter](https://openrouter.ai/),
um gateway que unifica o acesso a vários provedores de LLM (Anthropic, OpenAI, Google, etc.)
sob uma única chave de API e permite comparar modelos facilmente.

## O que mudou no script

A principal diferença em relação ao post anterior é o modelo dos subagentes:
para esta demo todos os agentes — orquestrador, `test-writer` e `coder` —
foram configurados como `haiku` (Claude Haiku 4.5), o modelo mais leve da família.
O post anterior previa Sonnet para os subagentes, mas para fins de demonstração
do mecanismo de orquestração o Haiku é suficiente e muito mais barato.

```python
agents = {
    "test-writer": AgentDefinition(..., model="haiku"),
    "coder":       AgentDefinition(..., model="haiku"),
}
options = ClaudeAgentOptions(..., model="haiku")
```

## A execução

O pipeline foi disparado em **30/04/2026 às 11:01:47** (horário de Brasília).
A sequência de eventos registrada em `LOGS.txt`:

| Tempo | Evento |
|-------|--------|
| 0s    | Orquestrador inicia, anuncia a Etapa 1 |
| ~10s  | Chama subagente `test-writer` via tool `Agent` |
| ~26s  | `test-writer` faz `ls` no diretório de trabalho |
| ~45s  | `test-writer` escreve `tests/test_cpf.py` (Write) |
| ~46s  | Orquestrador passa para a Etapa 2, chama `coder` |
| ~48s  | `coder` lê os testes (Read) |
| ~50s  | `coder` faz `ls` |
| ~57s  | `coder` escreve `cpf.py` (Write) |
| ~59s  | `coder` roda `python -m pytest tests/ -v` (Bash) |
| ~62s  | `coder` relê `cpf.py` para confirmação |
| **71s** | **Pipeline concluído — status: `success`** |

O orquestrador nunca escreveu código: seu único trabalho foi despachar
os subagentes na ordem correta usando a tool `Agent`.

## Artefatos gerados

### `tests/test_cpf.py`

| Classe | Cobertura |
|--------|-----------|
| `TestCPFValidos` | 2 CPFs válidos conhecidos |
| `TestCPFComTodosDigitosIguais` | `000…`, `111…`, `222…`, `999…` |
| `TestCPFFormatoIncorreto` | sem pontuação, hífen errado, caracteres especiais, vazio |
| `TestCPFNumeroDigitosIncorreto` | dígitos a mais ou a menos |
| `TestCPFDigitosVerificadoresIncorretos` | 1º errado, 2º errado, ambos errados |
| `TestCPFCasosExtremos` | `None`, espaços, letras, sinal negativo, pontos extras |
| `TestCPFCalculoDosVerificadores` | validação passo-a-passo do módulo 11 com comentários |

### `cpf.py`

Implementação completa da função `validar_cpf(cpf: str) -> bool` com:
- Validação de tipo e `None`
- Verificação do formato exato `XXX.XXX.XXX-YY`
- Rejeição de CPFs com todos os dígitos iguais
- Algoritmo de módulo 11 para os dois dígitos verificadores

Todos os 35 testes passaram na primeira tentativa do `coder` — sem nenhuma iteração de correção.

## Custo

Os dados de billing do OpenRouter ficaram registrados em `orquestrador_claude.csv`:

| Período (UTC) | Requests | Prompt tokens | Completion tokens | Custo (USD) |
|---------------|----------|---------------|-------------------|-------------|
| 14:01         | 9        | 121.600       | 3.823             | $0.054411   |
| 14:02         | 3        | 34.479        | 3.353             | $0.051632   |
| **Total**     | **12**   | **156.079**   | **7.176**         | **$0.106043** |

Os 156 mil tokens de prompt refletem principalmente o contexto acumulado das
múltiplas chamadas encadeadas entre orquestrador e subagentes.

## Próximos passos

- [x] Executar o pipeline pela primeira vez e documentar os resultados
- [ ] Testar com modelos diferentes nos subagentes (Sonnet, outros provedores via OpenRouter)
- [ ] Aumentar a complexidade do requisito (múltiplas funções, módulo com CRUD, CLI)
- [ ] Medir variabilidade: rodar N vezes o mesmo requisito e comparar testes/código gerados
