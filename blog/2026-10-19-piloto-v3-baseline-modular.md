---
slug: piloto-v3-baseline-modular
title: "Piloto v3: baseline do PreJanus com escrita incremental e módulos"
authors: [eduardo]
tags: [tcc, experimento]
---

Repeti a geração baseline do PreJanus-back completo com o harness Agno adaptado
para leitura e escrita incremental. Desta vez, explicitei que separar a aplicação
em módulos era obrigatório. O GLM 5.3 entregou 17 arquivos Python, com 2.865 linhas;
`app.py` ficou com 39 linhas. A API iniciou no ambiente isolado.
O oráculo terminou com 26/247 aprovados; uma falha no OAuth bloqueou grande parte
dos testes autenticados.

<!-- truncate -->

## O que mudou

No piloto v2 medido em Agno, o baseline concentrou a implementação em um `app.py`
de 2.063 linhas. O harness permitia vários arquivos, mas pedia seu conteúdo inteiro
em uma resposta estruturada e não mantinha o histórico das versões anteriores.
A entrega não subiu; interrompi sua avaliação, portanto não há escore completo
desse baseline para comparar com o v3.

Depois da adaptação das ferramentas e do smoke do marketplace, criei uma entrada
v3 preservando as 50 operações, os contratos SQL e OpenAPI, dependências, skills e
orçamento do v2. O texto funcional a partir de “Ambiente e persistência” é idêntico.
Acrescentei a exigência de módulos e retirei os avisos antigos de preparação pendente.

O prompt comum agora exige divisão por responsabilidade, um arquivo por ferramenta
e um ponto de entrada que apenas configure e conecte os módulos. Não fixei número
mínimo de arquivos: arquivos vazios ou reexportações de um monólito não atendem.
A entrada do PreJanus pede configuração, conexões, autenticação, routers e serviços
de integração separados. A divisão continua sendo feita pelo modelo numa sessão.

Esta rodada é só baseline: nenhuma geração de testes, feedback do oráculo, correção
manual da implementação ou CUA. O mesmo avaliador HTTP e a infraestrutura do v2
são usados depois da geração. Não executei TDD nem rework.

## Geração e contexto

| Medida | Resultado |
|---|---:|
| Teto autorizado | US$ 2 |
| Custo registrado | US$ 0,379988 |
| Duração da geração | 550,01 s |
| Duração do harness, incluindo pytest final | 581,96 s |
| Chamadas ao modelo | 24 |
| Sessões | 1 |
| Tokens acumulados | 1.747.468 |
| Entrada da primeira chamada | 42.169 tokens |
| Maior entrada | 93.334 tokens |
| Maior entrada + saída | 96.117 tokens |
| Maior requisição serializada | 438.435 bytes |

Fixei `novita/fp8` no OpenRouter, sem fallback, como no smoke. A janela declarada
é de 1.048.576 tokens: o pico de entrada ocupou 8,90%, sem compactação ou estouro
observado. O total acumulado inclui o histórico reenviado a cada chamada.
O v2 não fixava esse provedor, portanto a comparação não isola exclusivamente a
mudança de escrita: também mudaram o prompt de organização e a seleção do endpoint.

O modelo solicitou 17 criações e 13 substituições de trechos. Uma substituição sem
ocorrência única foi recusada; ele voltou a ler o arquivo e continuou editando.
Esse retorno da ferramenta não é feedback de testes nem retry do gate: houve uma
única proposta, sem repetição da geração. Todas as escritas Python aceitas passaram
pela checagem de sintaxe. Os hashes da entrega foram registrados antes do oráculo.

## A divisão entregue

| Código de produção Python | Arquivos | Linhas físicas |
|---|---:|---:|
| Baseline Agno v2 | 1 | 2.063 |
| Baseline v3 | 17 | 2.865 |
| PreJanus-back original | 114 | 7.395 |

A contagem inclui `__init__.py`: dois vazios no v3. Os demais arquivos contêm a
implementação: configuração, bancos, models, schemas, autenticação, quatro routers
e cinco módulos de serviços. Os maiores são `routers/submissions.py`, com 671 linhas,
e `routers/edicts.py`, com 641. Há divisão real, embora esses routers ainda sejam
grandes. O arquivo principal configura middleware, conecta routers e expõe a raiz.

O OpenAPI gerado contém as 50 operações do contrato e duas operações POST extras
para mapeamentos. Isso mede presença da interface; a correção dos comportamentos
depende do oráculo. A quantidade menor de linhas que no original também não
comprova equivalência funcional.

Os 55 testes locais do harness passaram. O pytest final da aplicação encontrou zero
testes, como esperado nesta baseline; esse campo não é evidência de funcionalidade.
Iniciei uma conferência adicional do oráculo contra o original, interrompida depois
de 26 casos aprovados para evitar disputa das fixtures. A referência histórica do
original continua sendo 233/247, com 14 divergências conhecidas; não a medi novamente
por completo nesta rodada.

## Resultado do oráculo

| Resultado | Casos |
|---|---:|
| Aprovados | 26 |
| Falhas de asserção | 69 |
| Erros de preparação | 152 |
| Total | 247 |
| Parcela visível | 15/161 |
| Parcela reservada | 10/85 |

A suíte levou 703,908 segundos. Um dos 26 aprovados verifica a rastreabilidade
dos requisitos aos testes e não depende da aplicação. O resultado comportamental
é, portanto, 25/246; preservei também o total 26/247 para comparar com os relatórios
anteriores. Nenhum caso foi pulado.

Passaram raiz, documentação, presença das operações no OpenAPI, CORS, atalho local
e recusa de requisições sem sessão. O fluxo OAuth falhou ao compor a URL: o ambiente
fornece `http://oauth:8000` como host e `wsusuario/oauth/request_token` como recurso.
O código concatena os dois sem uma barra, produzindo
`http://oauth:8000wsusuario/oauth/request_token`. A biblioteca rejeita a porta
`8000wsusuario`, e o login responde 500.

Os 152 erros de preparação ocorreram ao autenticar o cliente dos testes. Muitos
casos não chegaram a exercitar sua regra de negócio; esse resultado não permite
afirmar que todos os comportamentos bloqueados têm defeitos próprios. A coleta
HTTP registrou 13 das 50 operações, incluindo respostas de recusa de acesso.
Preservei código, configuração e fixtures do ensaio: não corrigi o OAuth nem
executei outra geração.

Nesta amostra, a escrita incremental entregou módulos reais e uma API que inicia,
com contexto abaixo da janela. A correção funcional continua insuficiente. Ainda
falta medir os grupos TDD e rework com essa escrita e o crescimento do contexto
nas sessões com vários ciclos de correção.

## Evidências

Entrada e runner foram congelados no commit `b53acb2`. A execução está em
`demos/runs/caronte/05-prejanus-back-piloto-v3-baseline-20261019-095708/`.
Em `_harness/`, `RUN.log` mede a geração; `chamadas_modelo.jsonl`, as chamadas;
`MANIFESTO_ENTREGA.json`, os arquivos; `MEDIDAS.json`, a comparação de escala e
contexto. `ORACULO.json`, `oraculo.xml` e `oraculo.txt` preservam a avaliação inteira.
O diagnóstico da URL está em `diagnostico-oauth.json`. Não houve avaliação visual.
