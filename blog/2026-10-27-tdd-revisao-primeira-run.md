---
slug: tdd-revisao-primeira-run
title: "TDD com revisão dos testes: primeira run, 194/247 no gabarito"
authors: [eduardo]
tags: [tcc, experimento]
---

Rodei uma vez a [variante com revisão dos testes](/blog/tdd-e-revisao-dos-testes).
Ela passou em 194 dos 247 casos do gabarito, contra 140 do TDD com testes
congelados e 186 da baseline nas últimas runs com o harness corrigido. Custou
US$ 2,22 e terminou a implementação pelo teto de custo, com 81 dos 83 testes
próprios passando. O coder revisou um helper dos testes de e-mail e justificou
a alteração. Não repeti a geração.

<!-- truncate -->

## O que ficou igual e o que mudou

A run começou do zero, com a mesma entrada do PreJanus-back, o mesmo GLM 5.3 no
provedor `novita/fp8`, sem fallback, e o mesmo ambiente e gabarito. O test-writer
continuou separado do coder. Mantive os tetos de US$ 2, 40 propostas e uma hora por
etapa; a última chamada pode ultrapassar o custo, como nas runs anteriores.

A variante `tdd-revisao` permite ao coder editar os testes autorais e pede uma
justificativa baseada no requisito ou contrato. O harness preserva a suíte inicial,
as versões posteriores e seus diffs. A configuração do pytest e a medição continuam
protegidas. Nenhum agente recebeu o gabarito, o código original ou os consertos
identificados na revisão anterior.

## Os números

| Medida | Baseline | TDD congelado | TDD com revisão |
|---|---:|---:|---:|
| Gabarito completo | 186/247 | 140/247 | **194/247** |
| Acerto | 75,3% | 56,7% | **78,5%** |
| Recorte visível | 123/161 | 90/161 | 130/161 |
| Recorte reservado | 62/85 | 49/85 | 63/85 |
| Custo | US$ 0,56 | US$ 2,07 | US$ 2,22 |

Os recortes visível e reservado são os do experimento de rework. Para estas três
condições, todos os casos do gabarito ficaram escondidos. O caso adicional aos 246
confere a rastreabilidade dos requisitos.

O test-writer escreveu 82 funções de teste, que resultaram em 83 casos executados,
em uma proposta e 20 chamadas ao modelo. Custou US$ 0,203606 e levou 231 segundos.
O coder fez seis propostas e 57 chamadas, por US$ 2,014733, até atingir o teto de
custo. O gate passou por 75/83, 80/83 e 81/83. Duas propostas não editaram arquivos,
mas consumiram chamadas e orçamento. A avaliação final dos testes próprios manteve
81 aprovados, duas falhas de login OAuth e nenhum erro de preparação.

O `RUN.log` registra 2.925,7 segundos, cerca de 49 minutos, até encerrar a geração e
sua conferência final, com 8.526.253 tokens acumulados. O gabarito levou mais 666
segundos, cerca de 11 minutos, e terminou com 194 aprovados, 53 falhas e nenhum erro
de preparação.

Duas chamadas gastaram os 100 mil tokens de saída somente em raciocínio, sem pedir
nenhuma ferramenta: levaram 466 e 378 segundos. Isso ajuda a explicar o tempo de
geração. O pedido de limitar o raciocínio a 32 mil tokens continuou sem ser
respeitado pelo provedor.

## A revisão feita pelo coder

O helper `_find_message`, em `tests/test_emails.py`, iterava diretamente sobre a
resposta JSON de `GET /api/Messages`, supondo uma lista. A caixa SMTP responde com
um objeto que contém a coleção em `results`. Ao percorrer o objeto, o teste
tentava tratar suas chaves como mensagens e falhava com `AttributeError`.

O coder adicionou um helper que extrai a coleção antes de procurar o e-mail.
Registrou em `tests/REVISOES.md` que esse formato pertence ao smtp4dev, um serviço
fornecido pelo ambiente: mudar a implementação do PreJanus não corrigiria a
interpretação da resposta pelo teste.

Conferi o diff: os seis testes e as 19 asserções desse arquivo foram preservados.
Não houve remoção de asserção ou inclusão de `skip` ou `xfail` na revisão. A mudança
atingiu o helper e acrescentou a justificativa. Foi uma correção da integração do
teste com o ambiente, coerente com o comportamento que ele pretendia verificar.
Nenhum outro arquivo de teste mudou depois da etapa inicial.

O campo `integridade.intacto` ficou `false`, como esperado para uma revisão
permitida nesta condição. O hash inicial continua registrado, e o harness guardou
as duas versões da suíte e o diff. Não alterei esse campo para esconder a mudança.

## O que esse resultado permite dizer

A variante entregou 54 acertos a mais que a última run do TDD congelado e oito a
mais que a baseline. Em mapeamentos, fez 20/27, contra 3/27 do TDD congelado e 26/27
da baseline. Em editais, passou nos 22 casos; em formulários, ficou em 11/24.
Portanto, a melhora no total não significa que tenha sido melhor em todo requisito.

A revisão mostra um caso em que a permissão foi usada para corrigir um teste sem
retirar suas verificações. Ainda não posso atribuir os 54 acertos adicionais a essa
permissão: a suíte foi gerada novamente, tinha 83 casos em vez dos 56 contabilizados
na run anterior, e a implementação também foi uma nova amostra do modelo. Uma run
por condição não isola esses efeitos.

## Artefatos

A run está em
`demos/runs/caronte/05-prejanus-back-piloto-v3-tdd-revisao-20261027-161847/`.
Em `_harness/`, ficaram `RUN.log`, o gabarito em `ORACULO.json`, os logs dos gates,
`execucao.log`, as métricas por chamada e o manifesto da entrega. A suíte inicial
está em `revisoes-testes/000.json`, a revisada em `001.json` e o diff em `001.diff`.
A justificativa está em `tests/REVISOES.md`.

Conferi os hashes da entrega depois do gabarito, os arquivos fornecidos como
infraestrutura e os hashes das fontes do harness usados nesta variante. Os arquivos
do requisito, da fixture e do gabarito permaneceram sem alterações.
