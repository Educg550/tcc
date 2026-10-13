---
slug: observacoes-cua
title: "Observações sobre o CUA nas finalistas"
authors: [eduardo]
tags: [tcc, experimento]
---

Rodei nove sessões do CUA de Nielsen nas quatro finalistas, duas baseline e duas TDD.
Anoto aqui o que deu errado nelas, porque sustenta um ponto do TCC: o CUA sozinho não é um
avaliador confiável e custa caro para o que entrega. Nos posts de resultados ficaram
as sessões aceitas pelo judge: 17:44 na run44, 19:30 na run35, 18:19 na run38 e 19:21 na
run19.

<!-- truncate -->

## As nove sessões

Todas usaram o mesmo roteiro C1, `anthropic/claude-opus-5.5` via OpenRouter, browser-use
0.13.10 e tela de 1366 × 768. O roteiro pede o preenchimento das duas abas por Tab e
teclado. A contagem de Tab e de ações `input`, que preenchem o campo direto pelo índice,
vem do histórico de cada sessão. Horários em UTC.

| Run | Sessão | Tab | `input` | Judge | Custo (US$) | Duração | O que deu errado |
|---|---|---:|---:|---|---:|---:|---|
| `deepseek/run44/baseline` | 11/10 17:44 | 56 | 12 | aceitou | 3,73 | 7min13s | — |
| `deepseek/run35/baseline` | 11/10 17:51 | 52 | 12 | contestou | 3,79 | 6min59s | erro do judge |
| `deepseek/run35/baseline` | 11/10 18:07 | 6 | 62 | contestou | 2,74 | 5min20s | CUA pulou o teclado; disse que os ofícios eram iguais |
| `glm/run38/tdd` | 13/10 18:19 | 58 | 12 | aceitou | 4,39 | 7min41s | — |
| `glm/run19/tdd` | 13/10 18:27 | — | — | contestou | 3,99 | 7min14s | CUA inventou diferenças entre as abas |
| `glm/run19/tdd` | 13/10 18:43 | 0 | 62 | contestou | 2,67 | 5min25s | CUA pulou o teclado; disse que os ofícios eram iguais |
| `deepseek/run35/baseline` | 13/10 19:15 | 7 | 62 | contestou | 2,87 | 5min49s | CUA pulou o teclado |
| `glm/run19/tdd` | 13/10 19:21 | 58 | 15 | aceitou | 4,16 | 7min29s | — |
| `deepseek/run35/baseline` | 13/10 19:30 | 54 | 13 | aceitou | 4,06 | 6min51s | disse que os ofícios eram iguais; o judge aceitou |

O histórico da sessão das 18:27 na run19 não foi preservado, então não tenho a contagem;
segundo o judge, ela preencheu ALUNOS por Tab. O judge contestou cinco das nove sessões.

A run35 é o exemplo principal: precisou de quatro sessões. Na primeira, o agente fez o
percurso e o judge errou; nas duas seguintes, o agente pulou o teclado; só a quarta passou
sem contestação.

## O judge erra

Na sessão das 17:51, a run35 foi preenchida por Tab, como pede o roteiro. O judge
contestou dizendo que ALUNOS nunca foi preenchido e que a primeira passagem tinha
acontecido em DOCENTES. As capturas dizem o contrário: as dos passos 4 e 13 mostram a aba
ALUNOS ativa, com NÍVEL = Mestrado e TIPO DE AUXÍLIO = Participação em evento, e a do
passo 18 mostra o ofício de ALUNOS com `Matemática Aplicada - Mestrado`. O agente fez o
trabalho; quem errou foi o judge.

## O CUA pula o percurso

Em três sessões, o agente preencheu os campos direto pelo índice, com 62 ações `input` e
no máximo sete Tab. Mesmo assim deu nota à heurística 7, que avalia justamente o
preenchimento pelo teclado: Excelente na run35 às 18:07, Bom na run19 às 18:43 e Bom na
run35 às 19:15. Na run35 às 19:15, a justificativa fala em preenchimento fluido e ordem de
Tab igual à ordem visual, coisa que o agente não testou. O roteiro pedia o teclado nas três
sessões; o agente escolheu o caminho mais curto e não avisou.

## O CUA inventa evidência

Na run19 às 18:27, o agente justificou a heurística 4 com diferenças entre as abas que não
existem: disse que o placeholder do período era diferente em DOCENTES e que o rótulo do RG
quebrava em duas linhas só lá. No `index.html`, o placeholder é `10 a 15 de julho de 2024`
nas duas abas.

Em três sessões, o agente afirmou que o ofício é igual nas duas abas. O requisito manda o
ofício de DOCENTES ter o assunto `Verba do programa`, e as capturas mostram isso.

## O judge não é consistente

A afirmação de que os ofícios são iguais pesou contra o agente na run35 às 18:07 e na run19
às 18:43. Na run35 às 19:30, o judge registrou o mesmo erro e o chamou de "nuance de
julgamento", não de invenção, e aceitou a sessão. O mesmo erro reprova uma sessão e passa
em outra.

## Mesma run, notas diferentes

As quatro sessões da run35 deram estas notas:

| Sessão | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 11/10 17:51 | Bom | Regular | Ruim | Excelente | Regular | Bom | Excelente | Bom | Regular | Regular |
| 11/10 18:07 | Bom | Bom | Ruim | Bom | Bom | Bom | Excelente | Bom | Regular | Regular |
| 13/10 19:15 | Bom | Regular | Ruim | Bom | Bom | Bom | Bom | Bom | Regular | Regular |
| 13/10 19:30 | Bom | Bom | Ruim | Excelente | Regular | Bom | Excelente | Excelente | Ruim | Regular |

Seis das dez heurísticas mudam de nota entre sessões da mesma página. Mesmo entre as duas
que fizeram o percurso por teclado, 17:51 e 19:30, mudam três: a 2, a 8 e a 9. Na run19,
as três sessões discordam em três heurísticas: a 2, a 7 e a 9.

Isso muda a comparação entre as finalistas. Contra a única sessão da run44, a run35 fica
acima em uma heurística com a sessão das 17:51, em duas com a das 18:07, empata com a das
19:15 e fica acima em três (contra uma) com a das 19:30. A conclusão depende de qual sessão
eu escolher.

## Custo

As nove sessões custaram **US$ 32,39** e somaram 60 minutos: em média, US$ 3,60 e 6,7
minutos por sessão, para avaliar uma run. Só a run35 consumiu US$ 13,45 em quatro sessões.
A suíte Cypress avaliou as 153 runs elegíveis com custo zero e cerca de 68 segundos por run
([post do harness](/blog/harness-baseline-tdd)).

## O que isso diz

Em nove sessões, o agente pulou o percurso pedido três vezes e inventou ou errou evidência
em quatro. O judge, que é o mesmo modelo relendo o rastro, errou uma vez contra o agente e
foi indulgente com o mesmo erro que condenou em outra sessão. As notas de uma mesma página
mudam de uma sessão para outra o bastante para inverter uma comparação. E cada sessão
custa dólares, enquanto os testes determinísticos custam zero.

O CUA sozinho é um canhão para matar mosquito: caro, lento e pouco confiável para dar a
palavra final. Ele acha coisas que os testes não acham, como a confirmação sem caminho de
volta e o ofício que diz "aprovou" para um pedido recém-enviado. Mas só faz sentido no fim
do pipeline, depois dos testes, e com alguém conferindo o que ele diz. São quatro runs, um
modelo e um requisito; não dá para generalizar a taxa de falhas, só registrar que elas
aparecem e de que tipo são.
