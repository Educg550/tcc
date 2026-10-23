---
slug: piloto-v3-oraculo-sem-porta-unica
title: "Piloto v3: o login deixa de ser porta única do oráculo"
authors: [eduardo]
tags: [tcc, experimento]
---

Avaliei a run TDD do piloto v3 e ela empatou com a baseline: 29/247 contra 26/247.
O empate não dizia nada sobre as regras do PreJanus-back. Nas duas runs o login
falhava e derrubava 152 casos ainda na preparação. Mudei a forma como o oráculo
autentica os testes que não avaliam OAuth e reavaliei as duas entregas sem tocar no
código. A baseline foi para 139/247 e o TDD para 185/247.

<!-- truncate -->

## A run TDD

A run TDD usou a mesma entrada, modelo (GLM 5.3, `novita/fp8`) e escrita incremental
da baseline de 19/10, com teto de US$ 2 por etapa. O test-writer escreveu 48 testes
numa proposta, por US$ 0,16. O coder passou por três gates, com 28, 28 e 46 dos 48
testes passando, e parou pelo teto de custo. Gastou US$ 1,14. No total foram
US$ 1,30 e 2.201 s. Dos 48 testes, 2 terminaram falhando: um 500 no login da Senha
Única e um teste inválido do próprio test-writer, que chama `pytest.skip` sem
importar `pytest`.

No oráculo, a run fez 29/247 (16/161 visíveis, 12/85 reservados). A baseline tinha
feito 26/247. Os 152 erros de preparação vieram, nas duas, do login devolvendo 500.

## Por que o login travava tudo

Todo teste que precisa de um usuário logado pedia o cliente à fixture `clientes`, e
ela fazia o fluxo OAuth inteiro contra o login do candidato. Se o login quebrava,
62% dos casos davam erro antes de chegar à regra que deveriam verificar. A baseline
erra a URL do provedor (`oauth:8000wsusuario`) e o TDD devolve 500, mas os dois
viravam o mesmo número.

O requisito já tinha uma saída. O V2-AUT-01 pede um atalho de desenvolvimento: com
`APP_ENV=local` e `DEV_USER_ID`, a aplicação autentica esse usuário sem OAuth. O
próprio requisito só proíbe usar o atalho nos casos que avaliam OAuth. Antes de mudar
a régua, conferi o atalho nas duas runs, e as duas o implementam e passam nos testes
dele. A baseline só o aplica em `GET /auth/login`, que grava a sessão. O TDD e o
original o aplicam na dependência comum de autenticação. Por isso a fixture chama
`GET /auth/login` antes de usar o cliente, como o front faria.

Como o atalho fixa um usuário por instância e o oráculo usa seis perfis, o ambiente
ganhou cinco instâncias `local-<perfil>` além da `local` do docente. Os sete testes
de V2-AUT-02 continuam fazendo o fluxo OAuth real, sem sessão prévia. Um teste mudou
de corpo: o de persistência após reinício passou a reiniciar a instância que o cliente
usa.

## A régua no original

Rodei o oráculo inteiro no PreJanus-back original, sob coverage. O resultado ficou
igual ao de antes da mudança: 233/247, só as 14 divergências registradas falhando,
50/50 operações exercitadas e 2.398/2.565 linhas vivas cobertas (93,5%).

As divergências continuam no denominador. Quando o original falha e o oráculo segue
o requisito, quem está errado é o original, e um candidato pode acertar esses casos.

## Reavaliação

Reavaliei as duas runs com a fixture nova. Conferi pelos hashes que o código era o
mesmo da avaliação anterior.

| Run | Antes | Depois | Visíveis | Reservados | OAuth (V2-AUT-02) |
|---|---:|---:|---:|---:|---:|
| Original | 233/247 | 233/247 | | | 6/7 |
| Baseline v3 | 26/247 | 139/247 | 89/161 | 49/85 | 0/7 |
| TDD v3 | 29/247 | 185/247 | 123/161 | 61/85 | 0/7 |

No original, o caso de OAuth que falha é uma das divergências: usuário novo é
gravado com o papel errado. Nas runs, não sobrou erro de preparação, e as falhas
restantes são de regra. O login quebrado
continua sendo pego: as duas runs reprovam os sete testes de OAuth. O TDD exercitou
as 50 operações; a baseline, 49.

Com o login fora do caminho, o TDD ficou 46 casos à frente. A vantagem é maior nos
casos visíveis (34) que nos reservados (12), mas aparece nas duas partições. Ainda é
uma run por grupo, então não trato a diferença como efeito do pipeline. Ela mostra que
a régua agora separa as duas entregas.

As runs v2 e anteriores foram medidas com a fixture antiga e não são comparáveis a
esses números sem reavaliação.

## Evidências

A decisão e os números estão em `demos/caronte/piloto-v2/avaliacao.md`. Os
resultados novos estão em `_harness/oraculo-atalho/` de cada run:
`demos/runs/caronte/05-prejanus-back-piloto-v3-baseline-20261019-095708/` e
`demos/runs/caronte/05-prejanus-back-piloto-v3-tdd-20261019-103846/`. A avaliação
anterior continua em `_harness/ORACULO.json`. O `MEDIDAS.json` das duas runs ainda
reflete o oráculo antigo.
