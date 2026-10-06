---
slug: finalistas-nielsen
title: "Seis finalistas e as heurísticas de Nielsen"
authors: [eduardo]
tags: [tcc, experimento, planejamento]
---

As finalistas do batch serão três do baseline e três do TDD. A próxima etapa
é avaliá-las com o CUA e comigo usando a página. Este post registra como elas foram
escolhidas e os critérios da avaliação, que são as dez heurísticas de usabilidade de
Jakob Nielsen.

<!-- truncate -->

## Selecionando as runs elegíveis

Antes de qualquer avaliação, uma run precisa ter uma aplicação para avaliar. A triagem
olha a estrutura do código e o `RUN.log` e exclui 47 das 200 runs, registrando o motivo
de cada uma:

| Motivo | O que significa | Runs |
|---|---|---:|
| `etapas_sem_sucesso` | o `RUN.log` registra etapa que estourou o orçamento sem terminar | 22 |
| `ausente` | nenhum arquivo Python de implementação | 9 |
| `sem_funcao` | o Python não define nenhuma função ou método | 7 |
| `sem_pagina` | nenhum `index.html` servido | 5 |
| `erro_sintaxe` | o Python não compila | 3 |
| `sem_decisao` | nenhuma função tem sequer um ponto de decisão | 1 |
| **Total** | | **47** |

`sem_funcao` e `sem_decisao` pegam esqueletos, como um `app.py` que contém só `...`. Um
backend que valida CPF, datas e campos obrigatórios sem nenhum desvio condicional não
implementou o requisito. Sem página também não há o que avaliar, porque o requisito é um
formulário web. Os motivos vêm da estrutura, sem limiar de linhas ou de métrica ajustado
para dar o resultado esperado (detalhes no [post anterior](/blog/harness-baseline-tdd)).

Das 47, 46 são do GLM-5.3:

| | Baseline | TDD | Total |
|---|---:|---:|---:|
| DeepSeek V4.1 Flash | 50 / 50 | 49 / 50 | 99 |
| GLM-5.3 | 31 / 50 | 23 / 50 | 54 |
| **Elegíveis** | **81** | **72** | **153** |

## Como estamos decidindo os finalistas

A avaliação determinística empatou. Das 153 runs elegíveis, 94 passam nos doze critérios
da suíte Cypress canônica, e 81 dessas também passam nos dez critérios extras que escrevi
para desempatar (detalhes no [post anterior](/blog/harness-baseline-tdd)). Não sobra
critério determinístico que separe as 81, porque todas fazem o que o requisito pede.

Com tudo empatado, decidi desempatar por meio do **custo de gerar**, em dólares, que o `RUN.log` de
cada run registra. Ele dá ordem total, com 81 valores distintos, e é uma das grandezas que
o TCC compara entre os grupos. Não é nota de qualidade: entre duas aplicações que passam
nos mesmos 22 critérios, fica a que custou menos para gerar.

Esse desempate favorece o baseline, que só gera o código, enquanto o TDD também gera os
testes e itera até o pytest passar. Por isso o corte é por grupo, com as três mais baratas de cada um:

| Grupo | Run | Custo de gerar (US$) |
|---|---|---:|
| Baseline | `deepseek/run9/baseline` | 0,0079 |
| Baseline | `deepseek/run45/baseline` | 0,0080 |
| Baseline | `deepseek/run32/baseline` | 0,0142 |
| TDD | `deepseek/run10/tdd` | 0,0227 |
| TDD | `deepseek/run34/tdd` | 0,0286 |
| TDD | `deepseek/run5/tdd` | 0,0296 |

As seis são do DeepSeek V4.1 Flash. O GLM-5.3 custa mais por run e perde todos os
desempates.

## Critérios de avaliação

O Cypress já verificou o que dava para verificar sem julgamento: o texto exato de cada
mensagem, as máscaras, as abas e o ofício. Os critérios desta etapa são as dez
heurísticas de usabilidade de Nielsen. A primeira lista, de nove, é de Molich e Nielsen
(1990), e o método de avaliação heurística foi descrito no mesmo ano por Nielsen e Molich
(1990). O conjunto atual, de dez, saiu de uma análise fatorial de 249 problemas de
usabilidade reais (Nielsen, 1994a; 1994b). Os nomes seguem a versão atual da Nielsen Norman Group
(Nielsen, 2024), traduzidos por mim, e a coluna da direita aplica cada heurística ao
formulário de auxílio financeiro:

| # | Heurística | O que observar no formulário |
|---:|---|---|
| 1 | Visibilidade do estado do sistema | Dá para saber em que aba se está, se o envio deu certo e o que cada campo formatado mostra ao sair dele. |
| 2 | Correspondência entre o sistema e o mundo real | Formatos e termos de quem pede auxílio: `R$ 1.500,00`, `dd/mm/aaaa`, CPF pontuado. O ofício se lê como o documento que vai para a CCP. |
| 3 | Controle e liberdade do usuário | Trocar de aba sem perder o que foi digitado, corrigir um erro sem redigitar o resto, voltar da confirmação se algo saiu errado. |
| 4 | Consistência e padrões | As duas abas com o mesmo arranjo e o mesmo comportamento; campos, botões e mensagens com a mesma aparência na página toda. |
| 5 | Prevenção de erros | Máscaras, placeholders com exemplo e seleções nas opções fechadas evitam o erro antes do envio. |
| 6 | Reconhecimento em vez de memorização | O rótulo continua visível depois de digitar, e o formato esperado aparece no próprio campo. |
| 7 | Flexibilidade e eficiência de uso | Dá para preencher tudo pelo teclado: a ordem do Tab segue a leitura e o usuário digita só os dígitos. |
| 8 | Estética e design minimalista | A página cabe em uma tela, os três blocos se distinguem pelo agrupamento e pelo espaçamento, e nada ali deixa de servir ao preenchimento. |
| 9 | Ajuda para reconhecer, diagnosticar e corrigir erros | A mensagem diz o que está errado e permite achar o campo, e aparecem todas as que se aplicam. |
| 10 | Ajuda e documentação | O requisito não pede ajuda; conta o que a página oferece além dos placeholders. |

A identidade visual da USP fica como critério à parte, porque Nielsen não trata de marca:
logotipo com margem livre, nenhum brasão, azul `#1094ab` dominante e Open Sans ou outra
fonte sem serifa.

Cada finalista recebe, em cada critério, uma nota na escala
**Péssimo / Ruim / Regular / Bom / Excelente**, com justificativa. As minhas notas e as
do CUA ficam separadas, para que as divergências entre as duas avaliações apareçam.

Ainda falta fixar as âncoras de cada nota em cada heurística e decidir o que fazer com
item que não se aplica. Depois disso, eu e o CUA avaliamos as seis, e as duas melhores vão
para os orientadores.

## Referências

- MOLICH, R.; NIELSEN, J. Improving a human-computer dialogue. *Communications of the
  ACM*, v. 33, n. 3, p. 338–348, mar. 1990. DOI:
  [10.1145/77481.77486](https://doi.org/10.1145/77481.77486).
- NIELSEN, J.; MOLICH, R. Heuristic evaluation of user interfaces. In: *Proceedings of
  the SIGCHI Conference on Human Factors in Computing Systems (CHI '90)*. Seattle: ACM,
  1990. p. 249–256. DOI: [10.1145/97243.97281](https://doi.org/10.1145/97243.97281).
- NIELSEN, J. Enhancing the explanatory power of usability heuristics. In: *Proceedings
  of the SIGCHI Conference on Human Factors in Computing Systems (CHI '94)*. Boston: ACM,
  1994a. p. 152–158. DOI: [10.1145/191666.191729](https://doi.org/10.1145/191666.191729).
- NIELSEN, J. Heuristic evaluation. In: NIELSEN, J.; MACK, R. L. (ed.). *Usability
  Inspection Methods*. Nova York: John Wiley & Sons, 1994b.
- NIELSEN, J. 10 usability heuristics for user interface design. *Nielsen Norman Group*,
  30 jan. 2024. Publicado originalmente em 1994. Disponível em:
  [https://www.nngroup.com/articles/ten-usability-heuristics/](https://www.nngroup.com/articles/ten-usability-heuristics/).
  Acesso em: 6 out. 2026.
