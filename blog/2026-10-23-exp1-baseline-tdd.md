---
slug: exp1-baseline-tdd
title: "Experimento 1: baseline 191, TDD 209"
authors: [eduardo]
tags: [tcc, experimento]
---

> Atualização em 24/10: o TDD desta nota foi invalidado por um defeito no harness, e as
> runs foram refeitas. Ver [Dois defeitos no harness e as runs refeitas](/blog/runs-refeitas-harness).

Rodei as duas runs do experimento 1 no PreJanus-back, com o escopo, os tetos e o harness
registrados no [post de escopo](/blog/escopo-experimento-prejanus-back). O TDD passou em
209 dos 247 casos do gabarito, e a baseline em 191. Nenhuma run foi invalidada.

<!-- truncate -->

| | Baseline | TDD |
|---|---:|---:|
| Gabarito | 191/247 | 209/247 |
| Visíveis | 131/161 | 135/161 |
| Reservados | 59/85 | 73/85 |
| Erros de preparação | 0 | 0 |
| Custo | US$ 0,33 | US$ 0,94 |
| Tempo de geração | 390 s | 1.874 s |

A baseline entregou numa proposta, com 19 chamadas. No TDD, o test-writer escreveu 47
testes numa proposta, por US$ 0,11, e o coder passou em todos eles na sexta proposta,
com 49 chamadas e US$ 0,83. Nenhuma etapa chegou ao teto. O gate rápido funcionou duas
vezes no TDD: no gate inicial, com o projeto vazio, e na quarta proposta, que quebrou o
import do app. O coder recebeu o traceback e se recuperou na proposta seguinte.

O TDD foi melhor em formulários (23/24 contra 12/24) e em acesso (63/63 contra 55/63),
e pior em mapeamentos (20/27 contra 26/27).

A diferença é de 18 casos. Não a trato como efeito do pipeline: a baseline do piloto v3,
na mesma entrada, modelo e provedor, fez 139/247, 52 casos a menos que esta. Com uma
run por grupo, 18 casos ficam dentro dessa variação.

As runs estão em `demos/runs/caronte/05-prejanus-back-piloto-v3-baseline-20261023-141645/`
e `demos/runs/caronte/05-prejanus-back-piloto-v3-tdd-20261023-144316/`, com `RUN.log`,
chamadas, gates e gabarito em `_harness/`.
