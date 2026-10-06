# Piloto CUA — DeepSeek run9 baseline

Modelo solicitado e utilizado: `anthropic/claude-sonnet-5.5`, via OpenRouter.
Critério: C1 (dez heurísticas de Nielsen em uma sessão). Viewport: 1366 × 768.
Cypress não foi executado. A aplicação gerada não foi alterada.

**Resultado: avaliação não concluída. Nenhuma tentativa interagiu com a aplicação.**

| Tentativa | Duração medida | Tokens de entrada | Tokens de saída | Tokens totais | Custo registrado (US$) | Resultado |
|---|---:|---:|---:|---:|---:|---|
| Esquema estrito padrão | 39,61 s | 23921 | 1436 | 25357 | 0,062202 | Provedor rejeitou a gramática; encerramento e julgamento consumiram tokens. |
| Esquema no prompt | 141.33 s de atividade | 35655 | 32000 | 67655 | 0,391310 | Duas respostas truncadas em 16000 tokens; tentativa interrompida. |
| Esquema estrito com ferramentas de navegação | 20,66 s | 21075 | 1312 | 22387 | 0,055270 | Recusa do provedor; encerramento e julgamento consumiram tokens. |
| **Total registrado** | — | **80651** | **34748** | **115399** | **0.508782** | **Sem notas de usabilidade.** |

As durações da primeira e terceira tentativas incluem subir e encerrar o servidor.
A segunda registra o intervalo dos dois passos no histórico; não inclui a pausa antes
do encerramento. Esses tempos não estimam uma avaliação Nielsen completa.

O custo vem de `usage.cost` das respostas e foi confirmado por consulta aos registros
`/generation` do OpenRouter. A chamada recusada na terceira tentativa não retornou
uso/custo e seu registro retornou HTTP 404: o total acima soma as cobranças confirmadas,
sem presumir custo zero para dados ausentes. Tokens são os contadores nativos da API,
incluindo respostas de encerramento e o juiz interno do browser-use.

Recusa recebida: “This request was blocked as it seems to violate Anthropic's Terms of
Service restrictions on reverse engineering or duplicating model outputs.” Não houve
nova tentativa após essa recusa.

Artefatos por tentativa:

- [cua-nielsen-sonnet55-20261006T124944Z](cua-nielsen-sonnet55-20261006T124944Z/resultado.json)
- [cua-nielsen-sonnet55-20261006T125043Z](cua-nielsen-sonnet55-20261006T125043Z/interrupcao.json)
- [cua-nielsen-sonnet55-20261006T125352Z](cua-nielsen-sonnet55-20261006T125352Z/resultado.json)

Cada pasta preserva o prompt, o histórico e o uso da API; `generation-accounting.json`
registra a conferência das cobranças. As duas últimas também preservam o script usado.
