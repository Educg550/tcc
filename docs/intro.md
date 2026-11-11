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

> O pipeline de geração de código baseado em TDD produz código mais correto do que a geração direta de código a partir de requisitos com LLM? E um agente que reconstrói o sistema a partir de testes fornecidos, sem os requisitos, acerta os casos que não viu?

## Hipótese

O pipeline que gera testes automaticamente e implementa código que passe nesses testes produz código mais correto do que a abordagem de geração direta, na qual o LLM recebe o requisito e implementa sem nenhuma estrutura adicional de testes.

## Resumo

O TCC tem duas partes. Na primeira, um formulário web gerado em batch comparou geração direta e TDD, com validação final via CUA; o resultado foi inconclusivo. Na segunda, o alvo é o **PreJanus-back**, backend do sistema de inscrições da pós-graduação do IME-USP, e três pipelines são comparados:

| Pipeline | Descrição |
|----------|-----------|
| **Baseline** | LLM recebe requisitos → implementa diretamente (sem testes) |
| **TDD** | Agente A gera testes → Agente B implementa → pytest → correção |
| **Rework** | Agente recebe testes fornecidos, sem requisitos → implementa → pytest → correção |

A avaliação é feita por um gabarito de 247 testes HTTP, escrito fora dos pipelines. Baseline e TDD não veem nenhum caso; o rework recebe 161 e é avaliado nos 85 restantes. O **Computer Using Agent (CUA)**, agente que interage com o sistema como um usuário real, foi o avaliador final na primeira parte e ficou fora da segunda - os motivos estão na [proposta](/docs/proposta).

## Estrutura do Site

- [Proposta de Pesquisa](/docs/proposta) - proposta inicial e extensão para o PreJanus-back
- [Metodologia](/docs/metodologia) - escopo, grupos e avaliação das duas partes
- [Referências](/docs/referencias) - benchmarks, ferramentas e leituras
- [Diário de Pesquisa](/blog) - notas e progressos ao longo do ano
