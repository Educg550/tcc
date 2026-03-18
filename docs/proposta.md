---
sidebar_position: 2
title: Proposta de Pesquisa
---

# Proposta de Pesquisa

## Título

**Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

---

## Contexto

Modelos de linguagem de grande escala (LLMs) têm demonstrado capacidade crescente de gerar código funcional, mas a qualidade desse código em relação aos requisitos originais ainda é variável. A combinação de TDD com LLMs surge como abordagem para aumentar a confiabilidade da geração automática.

Nesse paradigma, o desenvolvedor só verifica código de testes, não código de produção. A ferramenta **Onion** é uma prova de conceito que implementa TOP: a partir de arquivos de configuração YAML com especificações em linguagem natural, gera código Python automaticamente com base em TDD.

Computer Using Agents (CUAs) — agentes que interagem com interfaces como um usuário humano — adicionam uma camada de validação comportamental de caixa-preta, independente dos testes gerados pelo próprio pipeline.

---

## Os Dois Cenários

### Cenário Baseline — Geração Direta (sem TDD, sem CUA)

```
Requisito → LLM → Código gerado
```

O LLM recebe o requisito em linguagem natural e implementa diretamente, sem nenhuma
estrutura de testes prévia e sem validação adicional. Representa o uso mais simples e
direto de LLMs para geração de código.

### Cenário Experimental — TDD + LLM + CUA como avaliador final

```
Requisito → Agente A (gera testes) → Agente B (implementa) → CI → CUA (valida comportamento)
```

Um agente gera testes automatizados para o requisito antes da implementação. Um segundo
agente implementa o código até os testes passarem no CI. Por fim, o CUA recebe o
requisito original em linguagem natural, interage com o sistema como usuário real e
verifica se o comportamento observado corresponde ao esperado.

---

## Pergunta de Pesquisa

> **A validação comportamental via CUA detecta falhas que passam despercebidas pela geração direta de código com LLM?**

---

## Por que CUA como Avaliador Final (e não parte central)?

CUAs são problemáticos como parte central do pipeline porque:
- Introduzem não-determinismo adicional (OCR, interpretação visual, múltiplas etapas)
- Dificultam atribuição de erros: LLM geradora? CUA avaliador? OCR?
- São overkill quando há acesso a código-fonte, testes e CI

São adequados como avaliador final porque:
- Simulam comportamento real de usuário (caixa-preta)
- Detectam divergências semânticas que os testes unitários gerados pelo próprio pipeline podem não cobrir
- O escopo de frontend torna a interação via interface mais natural
