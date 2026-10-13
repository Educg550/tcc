---
slug: finalistas-nielsen-tdd
title: "Finalistas Nielsen TDD"
authors: [eduardo]
tags: [tcc, experimento]
---

As duas finalistas do [torneio geral](/blog/desempatador) são baseline. Para ter também
finalistas TDD, rodei o mesmo desempatador só entre as runs TDD.

<!-- truncate -->

## O torneio

Entraram as 39 runs TDD da galeria, as que passam nos 12 critérios do Cypress e nos 10
extras: 30 do DeepSeek V4.1 Flash e 9 do GLM-5.3. As regras são as mesmas do torneio geral:
mata-mata cego, lado de cada run sorteado a cada partida e repescagem entre as que
perderam direto para a campeã. Como todas são TDD, o anonimato agora só esconde o modelo.

## Resultado

Joguei as 42 partidas, 38 na chave e 4 na repescagem, com a semente `3077434329`:

| Lugar | Run | Modelo |
|---|---|---|
| 1º | `glm/run38/tdd` | GLM-5.3 |
| 2º | `glm/run19/tdd` | GLM-5.3 |
| 3º | `glm/run31/tdd` | GLM-5.3 |

A run19 perdeu a final para a run38 e venceu a repescagem. A run31, que tinha sido a TDD
mais bem colocada no torneio geral, perdeu para a run19 na última partida da repescagem.

Quantas runs de cada modelo sobraram em cada fase da chave:

| Fase | DeepSeek | GLM |
|---|---:|---:|
| Início | 30 | 9 |
| 32 | 25 | 7 |
| 16 | 10 | 6 |
| 8 | 3 | 5 |
| 4 | 2 | 2 |
| Final | 0 | 2 |

O GLM tem 9 das 39 runs e ficou com as três primeiras posições. Ao acaso, a chance de as
duas finalistas serem GLM seria de cerca de 5%.

No torneio geral, a run38 perdeu o primeiro jogo que disputou, contra a
`deepseek/run28/baseline`, que terminou em 5º. A run19 venceu um jogo e perdeu o seguinte,
contra a `deepseek/run43/baseline`.
