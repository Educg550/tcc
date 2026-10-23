---
slug: piloto-v3-rework-e-ajustes
title: "Piloto v3: o rework que o gate parou e três ajustes no harness"
authors: [eduardo]
tags: [tcc, experimento]
---

A run de rework do piloto v3 terminou com 2/247 no oráculo. O app gerado não importa,
e o teto de tempo da etapa acabou depois de uma única proposta. Dos 65 minutos da run,
cerca de 45 foram do gate rodando os testes visíveis contra um app fora do ar. Corrigi
isso e mais dois pontos do harness que o piloto mostrou, antes das runs formais.

<!-- truncate -->

## A run de rework

O rework recebe os 161 casos visíveis da suíte-oráculo e os contratos em `infra/`
(OpenAPI, esquemas do banco e variáveis), sem requisito, sem o código original e sem
issues. O gate roda a cópia dos visíveis que fica com o avaliador, então editar os
testes no workspace não muda nada. A run usou o mesmo modelo das outras duas (GLM 5.3,
`novita/fp8`), o teto de US$ 2, 40 propostas e 3.600 s por etapa, e já pegou a fixture
nova do oráculo, com o login pelo atalho `DEV_USER_ID`
([post anterior](/blog/piloto-v3-oraculo-sem-porta-unica)).

| Trecho | Horário | Duração |
|---|---|---:|
| Gate inicial, com o projeto vazio | 15:56–16:19 | 23 min |
| Sessão do coder, 31 chamadas | 16:19–16:38 | 20 min |
| Gate da proposta 1 | 16:38–17:01 | 22 min |

O gate inicial confere que os testes começam vermelhos. Com o projeto vazio, ele rodou
os 161 casos contra o proxy, e cada um esperou o 502 do backend que não subia. O gate da
proposta 1 fez o mesmo, porque o app gerado também não subia. Ao fim dele a etapa já
estava com 3.894 s e parou por tempo.

A sessão custou US$ 0,78 e acumulou 4,3 milhões de tokens de entrada, com contexto
máximo de 185 mil tokens. A segunda chamada levou 763 s sozinha: devolveu 58 mil tokens
de saída, 57,7 mil deles de raciocínio, acima do teto de 32 mil que o harness pede ao
provedor, e criou dois arquivos.

O coder escreveu 17 arquivos Python, com 2.425 linhas, separados em `auth/`, `routers/`
e `services/`. O `app.py` faz `from routers import auth`, mas a rota de autenticação
ficou em `auth/router.py`. O uvicorn para no `ImportError` e nenhuma instância sobe. O
traceback estava no retorno do gate da proposta 1, mas não sobrou tempo para uma
segunda proposta.

No oráculo, a run fez 2/247: 1/161 visíveis e 0/85 reservados. O caso visível aprovado
é o de CORS para origem desconhecida, que passa porque o 502 do proxy não traz cabeçalho
de CORS. O outro é o teste de rastreio da própria suíte. Com isso, o 2/247 mede o defeito do
gate e não serve para comparar o rework com a baseline (139/247) e o TDD (185/247).

## Três ajustes antes das runs formais

**O gate desiste quando o app não sobe.** Antes, o gate esperava cada backend responder,
em até 120 tentativas, e rodava a suíte mesmo sem resposta. Agora ele desiste quando um
dos contêineres do candidato sai e devolve o log de subida sem rodar nenhum teste. Com
o mesmo `ImportError`, o gate leva 42 s. O tempo de gate continua contando no teto da
etapa. Com o app de pé, os 161 visíveis devem levar de 6 a 7 minutos: o oráculo inteiro
levou 9,5 e 10,5 minutos na baseline e no TDD.

**O teto de custo é conferido entre chamadas.** No TDD do piloto, o coder parou com
US$ 1,14 de um teto de US$ 2. Antes de cada chamada, o harness reservava o pior caso:
o pedido contado em bytes como se fossem tokens, a preço máximo e sem cache, mais 100
mil tokens de saída. A reserva chegou a US$ 0,85 por chamada, e a chamada mais cara da
run custou US$ 0,064. Agora a chamada começa se o gasto da etapa ainda está abaixo do
teto, como já acontecia com o tempo. A última chamada pode passar do teto, e o
`RUN.log` registra o valor real.

**O test-writer não grava teste com nome indefinido.** No TDD do piloto, cinco dos sete
arquivos de teste chamavam `pytest.skip` sem `import pytest`. O coder não pode mexer em
`tests/`, então um teste assim reprova até código correto. Agora a ferramenta de escrita
da etapa de testes recusa o arquivo que usa um nome não definido nem importado e devolve
o erro ao test-writer na hora, como já fazia com erro de sintaxe. A checagem é
estática, sem modelo e sem custo. Nos testes do piloto, ela pega exatamente esses cinco
arquivos e nada no oráculo. Ela só vale para a etapa de testes do TDD: o coder e
a baseline continuam sem ela. Ficam de fora os erros que só uma leitura do requisito
pegaria, como hipóteses contraditórias sobre a fase do edital e o login da Senha Única
mandando os parâmetros em JSON em vez de query.

## O que muda daqui em diante

O escopo fechou em 21/10, com o Paulo e o Jorge: o experimento reconstrói só o
PreJanus-back, com as 50 operações do contrato, e o Forms e o front originais ficam
como ambiente. Por enquanto será uma run por grupo. As três runs do piloto v3 foram
medidas com o harness antigo e ficam fora dos resultados.

## Evidências

A run está em `demos/runs/caronte/05-prejanus-back-piloto-v3-rework-20261021-155621/`,
com `RUN.log`, `chamadas_modelo.jsonl`, os três gates (`pytest-1.txt` a `pytest-3.txt`)
e o oráculo em `_harness/ORACULO.json`. Os ajustes estão nos commits `3b4b69f` (gate),
`3d10335` (teto de custo) e `8d3c339` (checagem dos testes).
