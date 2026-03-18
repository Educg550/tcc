---
sidebar_position: 1
title: Visão Geral
---

# TCC — Visão Geral

**Aluno:** Eduardo Cruz Guedes · educg550@usp.br
**NUSP:** 13672752
**Curso:** Bacharelado em Ciência da Computação — 5º ano — IME-USP

**Orientadores:**
- Prof. Paulo Meirelles (paulormm@ime.usp.br) — IME-USP
- Prof. Jorge Melegati (jorge@jmelegati.com) — Universidade do Porto

---

## Tema

> **Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

## Pergunta de Pesquisa

> O pipeline de geração de código baseado em TDD com validação final via CUA produz código mais correto do que a geração direta de código a partir de requisitos com LLM?

## Hipótese

O pipeline que gera testes automaticamente e implementa código que passe nessas TDDs, com validação final via CUA, produz código de maior qualidade do que a abordagem de geração direta, na qual o LLM recebe o requisito e implementa sem nenhuma estrutura adicional de testes e sem validação comportamental.

## Resumo

O TCC compara dois pipelines de geração de código com LLM:

| Pipeline | Descrição |
|----------|-----------|
| **Baseline** | LLM recebe requisito → implementa diretamente (sem TDD, sem validação extra) |
| **Experimental** | Agente A gera testes → Agente B implementa → CI → CUA valida comportamento |

O **Computer Using Agent (CUA)** participa da etapa final do pipeline experimental: simula um usuário real interagindo com o sistema gerado e verifica se o comportamento observado corresponde ao requisito original — independentemente do que os testes unitários cobrem.

## Estrutura do Site

- [Proposta de Pesquisa](/docs/proposta) — detalhamento da proposta, pipelines e configuração experimental
- [Metodologia](/docs/metodologia) — métricas, escopo, grupos experimentais
- [Referências](/docs/referencias) — benchmarks, ferramentas e leituras
- [Diário de Pesquisa](/blog) — notas e progressos ao longo do ano
