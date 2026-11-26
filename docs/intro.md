---
sidebar_position: 1
title: Visão Geral
---

# TCC - Visão Geral

**Aluno:** Eduardo Cruz Guedes · educg550@usp.br
**NUSP:** 13672752
**Curso:** Bacharelado em Ciência da Computação - 5º ano - IME-USP

**Orientadores:**
- Prof. Paulo Meirelles (paulormm@ime.usp.br) - IME-USP
- Prof. Jorge Melegati (jorge@jmelegati.com) - Universidade do Porto

---

## Tema

> **Avaliação de pipelines multiagente de geração de código: geração direta, TDD e reconstrução guiada por testes**

## Pergunta de Pesquisa

> A geração com TDD produz código com maior corretude funcional do que a geração direta?

Nos casos avaliados, comparamos também o consumo em tokens e o custo
de cada pipeline. Avaliamos a reconstrução guiada pelo gabarito público
com os casos do gabarito privado, aos quais o agente não tem acesso.

## Resumo

No primeiro estudo, os pipelines geraram repetidas vezes um formulário web de
solicitação de auxílio financeiro com dois modelos. Uma suíte comum de Cypress
verificou os comportamentos especificados no requisito. Usamos o Computer-Using
Agent (CUA) na avaliação de usabilidade das finalistas.

O segundo estudo reconstruiu o backend do PreJanus e avaliou as variantes em
testes de caixa preta reservados. Comparamos geração direta, TDD com testes
congelados, TDD com revisão e reconstrução guiada por testes visíveis (*rework*).
Avaliamos as entregas pela interface HTTP. O gabarito público tem 161 casos,
fornecidos apenas ao *rework*, e o gabarito privado reserva 85 casos para a
avaliação das quatro variantes.

Nos casos avaliados, não encontramos evidência de que a geração com TDD produza
consistentemente maior corretude funcional do que a geração direta. No
formulário, o pipeline com mais aprovações dependeu do modelo. No
PreJanus-back, o resultado dependeu da variante de TDD e da rodada, com uma
execução por variante.

## Estrutura do Site

- [Monografia (PDF)](pathname:///monografia.pdf) - versão entregue (v1)
- [Proposta de Pesquisa](/docs/proposta) - proposta inicial e extensão para o PreJanus-back
- [Metodologia](/docs/metodologia) - escopo, grupos e avaliação das duas partes
- [Referências](/docs/referencias) - benchmarks, ferramentas e leituras
