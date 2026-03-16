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

> A validação comportamental via CUA detecta falhas que passam despercebidas por pipelines tradicionais baseados em TDD gerados por LLM?

## Hipótese

Um pipeline multiagente orientado a TDD produz código com menos defeitos do que a geração direta, e o CUA como avaliador comportamental final é capaz de detectar falhas semânticas que testes unitários automatizados não capturam.

## Resumo

O TCC compara dois pipelines de geração de código com LLM:

| Pipeline | Descrição |
|----------|-----------|
| **Baseline** | LLM recebe requisito → gera código diretamente |
| **TDD Multiagente** | Agente A gera testes → Agente B implementa até passar → CI valida |

Ao final, um **Computer Using Agent (CUA)** age como usuário real e avalia os requisitos originais de forma comportamental (caixa-preta), gerando uma camada de validação independente dos testes unitários.

## Estrutura do Site

- [Proposta de Pesquisa](/docs/proposta) — detalhamento da proposta, pipelines e configuração experimental
- [Metodologia](/docs/metodologia) — métricas, escopo, grupos experimentais
- [Referências](/docs/referencias) — benchmarks, ferramentas e leituras
- [Diário de Pesquisa](/blog) — notas e progressos ao longo do ano
