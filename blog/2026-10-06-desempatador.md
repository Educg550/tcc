---
slug: desempatador
title: "Desempatador: um mata-mata entre as finalistas"
authors: [eduardo]
tags: [tcc, experimento]
---

O Paulo pediu as duas melhores runs do formulário como proposta para substituir o
formulário que o programa usa hoje. As 81 runs que passam em todos os critérios do Cypress
continuam empatadas, e o custo de gerar, que usei como desempate no
[post das finalistas](/blog/finalistas-nielsen), não diz nada sobre qual formulário é
melhor. A escolha fica comigo, olhando as telas, e o desempatador organiza essa escolha.
No fim, nenhuma das duas escolhidas é TDD.

<!-- truncate -->

## A galeria

Cada uma das 81 runs virou três capturas, feitas pelo Cypress a 1280 px de largura: a aba
`ALUNOS` preenchida, a aba `DOCENTES` e o ofício depois do envio. Elas ficam em
`demos/runs/galeria/`, uma pasta por run.

## O torneio

O desempatador (`demos/desempatador/`) é um mata-mata. Cada partida mostra duas runs lado a
lado, com as três telas alinhadas, e a que eu preferir segue na chave. As runs aparecem só
como A e B, com o lado sorteado a cada partida, para eu não saber se estou olhando um
baseline ou um TDD. A ordem da chave também é sorteada, e a semente fica registrada no
`torneio.json` junto com cada escolha.

Num mata-mata simples, a segunda melhor pode cair na metade da chave da campeã e sair
antes da final. Por isso, depois da final, as runs que perderam direto para a campeã
disputam uma repescagem, e a vencedora fica com o segundo lugar. São 85 ou 86 partidas no
total.

## Critérios

Em cada partida, escolho a run que:

- deixa mais fácil saber em qual aba estou, `ALUNOS` ou `DOCENTES`;
- não tem bugs visuais na interface;
- tem o formulário legível;
- separa o formulário em seções;
- é agradável visualmente.

São critérios meus, e eu sou enviesado. O anonimato esconde se a run é baseline ou TDD,
mas o julgamento continua sendo o meu gosto. Mesmo assim, o torneio foi a melhor forma de
desempatar que encontrei, muito melhor do que desempatar pelo custo de gerar.

## Resultado

Joguei as 85 partidas, com a semente `1573452010`:

| Lugar | Run | Grupo | Modelo |
|---|---|---|---|
| 1º | `deepseek/run44/baseline` | Baseline | DeepSeek V4.1 Flash |
| 2º | `deepseek/run35/baseline` | Baseline | DeepSeek V4.1 Flash |
| 3º | `deepseek/run12/baseline` | Baseline | DeepSeek V4.1 Flash |
| 4º | `glm/run31/tdd` | TDD | GLM-5.3 |
| 5º | `deepseek/run28/baseline` | Baseline | DeepSeek V4.1 Flash |
| 6º–9º | `deepseek/run4/baseline` | Baseline | DeepSeek V4.1 Flash |
| 6º–9º | `deepseek/run10/baseline` | Baseline | DeepSeek V4.1 Flash |
| 6º–9º | `deepseek/run18/baseline` | Baseline | DeepSeek V4.1 Flash |
| 6º–9º | `deepseek/run14/tdd` | TDD | DeepSeek V4.1 Flash |

**Nenhuma das duas finalistas é TDD.** A TDD mais bem colocada foi a `glm/run31/tdd`, que
perdeu a final. Com 42 baseline entre as 81, a chance de as duas primeiras serem baseline
por acaso é de cerca de 27%, e o julgamento é de uma pessoa só. Isso não mostra que o
baseline gera formulários melhores, só decide quais duas runs vão para o Paulo.

Do 3º em diante, a ordem segue a fase em que cada run caiu e os jogos da repescagem. As
quatro que caíram nas quartas empatam.

A `run35` perdeu para a campeã na rodada de 32 e voltou pela repescagem. Sem ela, a vice
seria a `glm/run31/tdd`, que perdeu a final e depois perdeu para a `run12` na repescagem.

Quantas runs de cada grupo sobraram em cada fase da chave:

| Fase | Baseline | TDD |
|---|---:|---:|
| Início | 42 | 39 |
| 64 | 36 | 28 |
| 32 | 18 | 14 |
| 16 | 9 | 7 |
| 8 | 6 | 2 |
| 4 | 3 | 1 |
| Final | 1 | 1 |
