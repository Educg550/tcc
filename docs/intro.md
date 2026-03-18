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
- Prof. Jorge Melegati (jorge@jmelegati.com) — INESC TEC / Universidade do Porto

---

## Tema

> **Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

## Pergunta de Pesquisa

> A validação comportamental via CUA detecta falhas que passam despercebidas pela geração direta de código com LLM?

## Hipótese

Um pipeline multiagente que combina geração automática de testes (TDD) com validação comportamental via CUA detecta mais falhas do que a abordagem de geração direta — na qual o LLM recebe o requisito e implementa sem nenhuma estrutura adicional.

## Resumo

O TCC compara dois pipelines de geração de código com LLM:

| Pipeline | Descrição |
|----------|-----------|
| **Baseline** | LLM recebe requisito → implementa diretamente (sem TDD, sem validação extra) |
| **Experimental** | Agente A gera testes → Agente B implementa → CI → CUA valida comportamento |

O **Computer Using Agent (CUA)** atua como avaliador de caixa-preta na etapa final do pipeline experimental, simulando um usuário real e verificando se o comportamento observado corresponde ao requisito original — independentemente do que os testes unitários cobrem.

## Estrutura do Site

- [Proposta de Pesquisa](/docs/proposta) — detalhamento da proposta, pipelines e configuração experimental
- [Metodologia](/docs/metodologia) — métricas, escopo, grupos experimentais
- [Referências](/docs/referencias) — benchmarks, ferramentas e leituras
- [Diário de Pesquisa](/blog) — notas e progressos ao longo do ano
