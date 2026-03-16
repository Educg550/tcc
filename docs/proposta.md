---
sidebar_position: 2
title: Proposta de Pesquisa
---

# Proposta de Pesquisa

## Título

**Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

---

## Contexto

Modelos de linguagem de grande escala (LLMs) têm demonstrado capacidade crescente de gerar código funcional, mas a qualidade desse código em relação aos requisitos originais ainda é variável. A combinação de TDD com LLMs surge como abordagem para aumentar a confiabilidade da geração automática — princípio formalizado pelo orientador Prof. Jorge Melegati no paradigma **Test-Oriented Programming (TOP)** ([paper ICSE 2026](/docs/referencias#test-oriented-programming-top)).

Nesse paradigma, o desenvolvedor só verifica código de testes, não código de produção. A ferramenta **Onion** é uma prova de conceito que implementa TOP: a partir de arquivos de configuração YAML com especificações em linguagem natural, gera código Python automaticamente com base em TDD.

Computer Using Agents (CUAs) — agentes que interagem com interfaces como um usuário humano — adicionam uma camada de validação comportamental de caixa-preta, independente dos testes gerados pelo próprio pipeline.

---

## Os Dois Cenários

### Cenário Baseline — TDD + LLM (sem CUA)

```
Requisito → Agente A (gera testes) → Agente B (implementa) → CI → Loop até passar
```

Baseado na ferramenta Onion / pipeline existente que a Aline está melhorando em paralelo. O desenvolvedor verifica apenas o código de testes, não o código de produção.

### Cenário Experimental — TDD + LLM + CUA como avaliador final

```
Baseline (TDD+LLM+CI) → CUA (recebe requisito original) → Artefato de validação
```

Após o CI passar, o CUA recebe o requisito original em linguagem natural, interage com o sistema como usuário real e verifica se o comportamento observado corresponde ao esperado.

---

## Pergunta de Pesquisa

> **A validação comportamental via CUA detecta falhas que passam despercebidas por pipelines tradicionais baseados em TDD gerados por LLM?**

---

## Por que CUA como Avaliador Final (e não parte central)?

CUAs são problemáticos como parte central do pipeline porque:
- Introduzem não-determinismo adicional (OCR, interpretação visual, múltiplas etapas)
- Dificultam atribuição de erros: LLM geradora? CUA avaliador? OCR?
- São overkill quando há acesso a código-fonte, testes e CI

São adequados como avaliador final porque:
- Simulam comportamento real de usuário (caixa-preta)
- Detectam divergências semânticas que testes gerados pelo próprio pipeline podem não cobrir
- O escopo de frontend torna a interação via interface mais natural

---

## Por que o Baseline é TDD+LLM, não geração direta?

Sugestão do Prof. Jorge Melegati: usar como baseline o pipeline TDD+LLM (Onion) que já existe e está sendo validado em pesquisa paralela. Isso permite:
- Aproveitar infraestrutura existente
- Focar a contribuição do TCC na camada CUA
- Comparar validação estrutural (CI) com validação comportamental (CUA) de forma mais limpa

---

## Benchmarks de Referência — Estado da Arte dos CUAs

| Framework | Precisão | Custo | Tempo |
|-----------|----------|-------|-------|
| Browser Use | 41% | baixo | médio |
| Cua Agent SDK | 79% | altíssimo | muito alto |
| Magnitude | 0.55% | rápido | baixo |
| Gemini CUA | 56% | médio | rápido |

Benchmarks públicos (OS World, REAL, Online Mind2Web, AndroidWorld) mostram que mesmo os melhores modelos têm ~60% de sucesso em ambientes reais, o que torna o CUA uma métrica interessante justamente por sua imperfeição controlada.
