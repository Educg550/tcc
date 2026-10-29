---
slug: runs-refeitas-harness
title: "Dois defeitos no harness e as runs refeitas"
authors: [eduardo]
tags: [tcc, experimento]
---

Depois das primeiras runs formais, achei dois defeitos no harness que mudavam o que o
grupo TDD recebia. Invalidei as runs afetadas, corrigi o harness e refiz as três runs
com a mesma entrada. Com o harness corrigido, a baseline passou em 186 dos 247 casos
do gabarito, o TDD em 140, e o rework em 59 dos 85 reservados. A variação entre runs da
mesma condição passou de 50 casos, então uma run por grupo não separa os grupos. Vou
fazer mais runs depois, com o mesmo harness.

<!-- truncate -->

## Os dois defeitos

**O coder não via as falhas do pytest.** Quando o gate falhava, o harness juntava à
saída do pytest os logs dos oito backends, e o coder recebia só os últimos 4.000
caracteres. Esse trecho final era sempre o fim do log de um backend. O resumo do pytest
e a lista dos testes que falharam nunca chegavam. O mesmo trecho confundia a contagem
do harness, que tomava uma linha de traceback pelo resumo. O defeito existia desde o
piloto v2. Agora, com o app de pé, o coder recebe a saída do pytest, e os logs só vão
quando o app não sobe.

**Os testes do TDD não alcançavam o ambiente inteiro.** O container que roda os testes
do test-writer só recebia a URL do docente e a da instância sem atalho. Os testes não
tinham como entrar como administrador, secretaria, coordenador ou estudante, nem falar
com o provedor OAuth local ou com a caixa SMTP, que o gabarito e o rework usam. Numa das
runs, o arquivo de testes de OAuth do test-writer foi pulado inteiro. Agora o gate passa
essas URLs, e o `infra/README.md` da entrada as documenta. Como o README é entrada dos
três grupos, refiz também a baseline e o rework, para que a entrada fosse a mesma.

## O que ficou de fora

| Run | Harness | Gabarito | Situação |
|---|---|---:|---|
| Baseline 23/10 14:16 | `8127059` | 191/247 | Substituída: a entrada mudou |
| TDD 23/10 14:43 | `8127059` | 209/247 | Invalidada: o coder não via as falhas |
| Rework 23/10 18:23 | `e1ee6d1` | 190/247 | Invalidada: o coder não via as falhas |
| TDD 23/10 19:53 | `5e29bf4` | 206/247 | Substituída: gate restrito, entrada mudou |
| Rework 23/10 20:32 | `5e29bf4` | 209/247 | Substituída: a entrada mudou |

A nota anterior, [baseline 191, TDD 209](/blog/exp1-baseline-tdd), usava as duas
primeiras runs da tabela.

## Os resultados com o harness corrigido

As três runs usaram o harness `7734bea`, com os tetos do
[post de escopo](/blog/escopo-experimento-prejanus-back). Nenhuma teve erro do harness,
do ambiente ou de chamada ao modelo.

| | Baseline | TDD | Rework |
|---|---:|---:|---:|
| Gabarito | 186/247 | 140/247 | 211/247 |
| Visíveis | 123/161 | 90/161 | 151/161 |
| Reservados | 62/85 | 49/85 | 59/85 |
| Custo | US$ 0,56 | US$ 2,07 | US$ 2,03 |
| Fim da etapa de código | testes verdes, 1 proposta | tempo, 10 propostas | custo, 2 propostas |

No TDD, o test-writer escreveu 56 testes e usou as variáveis novas do ambiente. Nas propostas
em que o app subiu, o coder ficou entre 25 e 27 testes aprovados, com a lista de falhas
completa no feedback, até parar por tempo na décima. Duas propostas quebraram o app com um uso errado do `psycopg`.
Uma chamada levou 11 minutos e gastou os 100 mil tokens de saída raciocinando, sem
devolver nenhuma ferramenta. O harness pede ao provedor um teto de 32 mil tokens de
raciocínio, que a Novita ignora. Isso já tinha aparecido no rework, com chamadas de 58 a
97 mil tokens. Não é erro de chamada, então a run conta como resultado.

O rework passou em 141 dos 161 visíveis no gate da primeira proposta. A segunda
esgotou o teto de custo e só passou pelo gate final, com 151. Nos reservados, que são a nota do experimento 2, ficou em 59/85.

## Outras conferências

Reavaliei o código da baseline de 23/10 com o gabarito. Deram o mesmo resultado 246 dos
247 casos. O que mudou, `test_link_de_correcao_abre_a_candidatura_no_forms`, depende de
uma página do forms original, que respondeu 400 na segunda vez. Trato esse caso como
instável.

A checagem de que os testes do TDD começam vermelhos não diz nada neste ambiente: com o
projeto vazio o app nunca sobe, então ela sempre dá vermelho.

## O que dá para dizer

Na mesma entrada, com o mesmo modelo e o mesmo provedor, as baselines fizeram 139, 191 e
186, e os TDDs 209, 206 e 140, estes com harness diferentes. A diferença entre os grupos
em qualquer par de runs fica dentro dessa variação. Com uma run por grupo, o resultado
do experimento 1 depende de qual run saiu. As próximas runs usam o harness `7734bea`,
sem mudanças, para que contem como repetições destas.

As runs estão em `demos/runs/caronte/`, nas pastas `05-prejanus-back-piloto-v3-*` de
23 e 24/10. A reavaliação da baseline está em `_harness/oraculo-reavaliacao/` da run de
23/10 14:16.
