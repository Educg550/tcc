---
slug: smoke-marketplace-agno
title: "Smoke do harness: um marketplace em uma sessão GLM"
authors: [eduardo]
tags: [tcc, experimento]
---

Antes de repetir o piloto do PreJanus, testei a nova escrita do harness com outro
projeto: um marketplace com frontend Next/React/MUI e backend FastAPI/SQLAlchemy/
PostgreSQL. A mesma conta pode comprar e vender. O GLM 5.3 gerou o projeto em uma
sessão, com teto de US$ 3, sem executar comandos nem receber resultados de testes.
O backend funcionou nos checks do smoke; o frontend não passou no build.

<!-- truncate -->

## A escrita e o contexto

Retirei o schema que obrigava o modelo a devolver todos os arquivos como strings
em um JSON. Agora ele usa ferramentas do Agno para listar, ler, criar um arquivo e
substituir um trecho. As leituras mostram as alterações da sessão, e as correções
entre propostas mantêm o histórico. Uma edição Python com sintaxe inválida é recusada
antes de substituir a versão anterior.

O caso tem 12 blocos funcionais: cadastro e sessão, catálogo, anúncios, favoritos,
conversas, compra com reserva de estoque, pedidos, avaliações e as telas de comprador
e vendedor. Não dividi esses blocos em sessões distintas. Queria medir o crescimento
do contexto conforme o agente construía o projeto.

| Medida | Resultado |
|---|---:|
| Duração da geração | 421,98 s |
| Custo registrado | US$ 0,298045 |
| Chamadas ao modelo | 46 |
| Sessões | 1 |
| Arquivos gerados | 42 |
| Tokens acumulados | 1.448.210 |
| Entrada da primeira chamada | 5.911 tokens |
| Maior entrada de uma chamada | 48.105 tokens |
| Maior entrada + saída de uma chamada | 49.022 tokens |

Fixei o endpoint `novita/fp8`, sem fallback, com janela de 1.048.576 tokens conforme
o snapshot da API do OpenRouter. O pico de entrada ocupou 4,59% dessa janela, sem
compactação. O total de 1,45 milhão de tokens é a soma das chamadas, incluindo o
histórico reenviado; não significa que a sessão tenha ultrapassado a janela.

O registro por chamada guarda tokens, cache, custo, tamanho da requisição, sessão,
provedor, duração e ferramentas solicitadas. Antes de cada chamada, o harness
reserva um limite conservador para seu custo, usando o teto de preços e a saída
máxima configurada. Essa reserva permite parar antes de enviar uma chamada que
poderia ultrapassar o saldo.

## O que funcionou e o que falhou

O backend subiu em contêiner com PostgreSQL 17.6 e passou em dez checks HTTP que
escrevi fora do contexto do gerador. Eles cobrem catálogo, compra e venda pela mesma
conta, filtros, autorização, favoritos, pedidos, cancelamento, avaliações, conversa
e duas compras concorrentes da última unidade. Reiniciei o backend: a sessão e o
anúncio persistiram, e o seed não foi duplicado. Isso é um smoke, não uma suíte com
cobertura completa dos requisitos.

O frontend original não chegou ao compilador: declarou `@mui/material-nextjs@7.3.1`,
que o npm não encontrou. Fiz uma cópia de diagnóstico e alterei somente essa
dependência para 7.3.0, a versão do Caronte. A instalação passou e o JavaScript
compilou, mas o build TypeScript reprovou: a tela de conversa usa `useRouter` sem
importá-lo. Não corrigi esse código nem considerei a cópia como entrega aprovada.

Também havia um erro na minha entrada: pedi contas de demonstração com domínio
`example.test`, que a validação `EmailStr` recusa no login. Os checks com contas
novas em `example.com` passaram. Corrigi os e-mails e explicitei a versão do pacote
MUI/Next no requisito para futuras execuções. A entrada usada nesta run e a entrega
original ficaram congeladas; não rodei uma segunda geração.

## Comparação com o piloto v2

Dos 42 arquivos, 15 são do backend, 25 do frontend e dois da raiz, README e exemplo
de ambiente. O frontend tem 14 páginas e 21 arquivos de código, com 2.124 linhas.
Para comparar com o recorte do piloto v2, separei o backend:

| Implementação | Arquivos Python de produção | Linhas |
|---|---:|---:|
| Marketplace | 15 | 1.071 |
| PreJanus original | 114 | 7.395 |
| Piloto v2 Agno: baseline | 1 | 2.063 |
| Piloto v2 Agno: TDD | 1 | 1.991 |
| Piloto v2 Agno: rework | 1 | 1.519 |

A contagem inclui `__init__.py` e exclui testes. O original tem ainda 16 arquivos
Python de testes; o TDD antigo gerou sete arquivos de testes. Dependências, build,
caches, infraestrutura fornecida e evidências do harness não entram como código
gerado. As linhas são linhas físicas, não NLOC do lizard.

O marketplace expõe 25 operações HTTP; o contrato do piloto v2 cobre 50. Seu backend
tem 13,2% dos arquivos e 14,5% das linhas do original. O frontend adicional aumenta
o trabalho da sessão, mas não torna os dois escopos equivalentes.

A escrita incremental conseguiu produzir e corrigir vários módulos sem repetir o
colapso de sintaxe Python do piloto anterior. Ainda não posso afirmar que um projeto
completo saiu funcionando, nem que o harness já escala ao Caronte inteiro. O teste
seguinte continua sendo o PreJanus-back nos grupos baseline, TDD e rework dos dois
experimentos, antes de decidir pela execução completa.

Os artefatos estão em
`demos/runs/marketplace/04-marketplace-glm-baseline-20261019-093026/_harness/`:
`RUN.log`, `chamadas_modelo.jsonl`, `ESCALA.json`, `VALIDACAO.json`, o manifesto e
a cópia congelada da entrega, os checks HTTP e os logs dos dois builds.
