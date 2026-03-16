---
sidebar_position: 4
title: Referências
---

# Referências e Links

## Test-Oriented Programming (TOP)

Paper do orientador Prof. Jorge Melegati, apresentado no ICSE 2026 (Rio de Janeiro). Fundamento teórico central do TCC.

> **Test-Oriented Programming: rethinking coding for the GenAI era**
> Jorge Melegati — INESC TEC, Faculty of Engineering, University of Porto
> ICSE-Companion '26, April 12–18, 2026, Rio de Janeiro, Brazil
> DOI: [10.5281/17227298](https://doi.org/10.5281/zenodo.17227298)

**Resumo:** Propõe TOP como novo paradigma onde desenvolvedores apenas verificam código de testes, delegando a geração de código de produção para LLMs. Prova de conceito: ferramenta **Onion**, testada com GPT-4o-mini e Gemini 2.5-Flash.

- [Ferramenta Onion (GitHub)](https://github.com/TOProgramming/onion)
- [Dados suplementares (Zenodo)](https://doi.org/10.5281/zenodo.17227298)

---

## Pesquisa Relacionada (referenciada no paper TOP)

- **Assured LLM-Based Software Engineering** — Alshahwan et al. (2024): abordagem onde respostas de LLM vêm com verificação de utilidade; TDD como estratégia de mitigação de não-determinismo
- **LLMs for Software Engineering** — Fan et al. (2023): survey sobre uso de LLMs em engenharia de software
- **LLM-Based Multi-Agent Systems for SE** — He, Treude & Lo (2025): revisão de literatura sobre sistemas multiagente com LLMs
- **GenAI for Test Driven Development** — Mock, Melegati & Russo (2025): resultados preliminares de TDD com IA generativa (XP Workshops)

---

## Orquestração de Agentes

- [Lesson 6 — Agent Skills (DeepLearning.AI)](https://github.com/https-deeplearning-ai/sc-agent-skills-files/tree/main/L6)
- [Prompts — L6 Notes](https://github.com/https-deeplearning-ai/sc-agent-skills-files/blob/main/L6_notes/prompts.md)

## Pipelines Open Source com Skills

- [Superpowers (obra)](https://github.com/obra/superpowers)
- [Everything Claude Code (affaan-m)](https://github.com/affaan-m/everything-claude-code?tab=MIT-1-ov-file)

## CLAUDE.md como Backlog de Orquestrador

- [Exemplo: cozap/CLAUDE.md (freneza)](https://github.com/freneza/cozap/blob/main/CLAUDE.md)

---

## TDD

- [Uncle Bob — The Three Rules of TDD](http://butunclebob.com/ArticleS.UncleBob.TheThreeRulesOfTdd)
- [Uncle Bob — TDD (YouTube)](https://youtu.be/rdLO7pSVrMY?si=iPXT8ftwN4FkK-38)

---

## Computer Using Agents (CUAs)

### Abordagens de CUA

| Abordagem | Descrição |
|-----------|-----------|
| **Imagética** | Tira print da tela, interpreta visualmente e continua o loop |
| **DOM + Playwright** | Inspeciona o DOM e cria código Playwright em tempo real |
| **Textual** | Usa ferramentas para ações predeterminadas no ambiente (print, clique, digitação) |

### Benchmarks Públicos

| Benchmark | Melhor resultado | Observações |
|-----------|-----------------|-------------|
| OS World | ~60% | Ambiente de desktop |
| REAL | ~41% | Ambiente web real |
| Online Mind2Web | ~42% | Navegação web |
| AndroidWorld | Alto, mas controlado | Ambiente mobile |

### Frameworks

- **Browser Use** — 41% precisão, custo baixo
- **Cua Agent SDK** — 79% precisão, custo altíssimo
- **Magnitude** — 0.55% precisão, mais rápido
- **Gemini CUA** — 56% precisão, custo médio
