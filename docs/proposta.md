---
sidebar_position: 2
title: Proposta de Pesquisa
---

# Proposta de Pesquisa

## Título

**Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

---

## Introdução

Modelos de linguagem de grande escala (LLMs) têm demonstrado capacidade crescente de gerar código funcional, mas a qualidade desse código em relação aos requisitos originais ainda é variável. Com as chamadas alucinações, ainda é difícil confiar na geração automática de código sem uma validação, que deve ser especialmente rigorosa em cenários onde o funcionamento do software é crítico.

A combinação de TDD com LLMs surge como abordagem para aumentar a confiabilidade da geração automática. Nesse paradigma, o desenvolvedor fica responsável por verificar especialmente a saúde de código de testes, o código de produção se torna secundário, o que garante uma abordagem mais simples e gerenciável do ponto de vista humano. A ferramenta **Onion** é uma prova de conceito que implementa TOP: a partir de arquivos de configuração YAML com especificações em linguagem natural, gera código Python automaticamente com base em TDD (Test Driven Development).

Outra camada interessante de validação que será introduzida nesse trabalho é o uso de Computer Using Agents (CUAs) — agentes que interagem com interfaces como um usuário humano — que adicionam uma camada de validação comportamental de caixa-preta, independente dos testes gerados pelo próprio pipeline.

---

## Abstrato

Modelos de linguagem de grande escala (LLMs) são cada vez mais utilizados para geração automática de código, mas produzem resultados de qualidade variável e sujeitos a alucinações — implementações que passam por testes superficiais sem satisfazer os requisitos reais. Este trabalho avalia se a adição de validação comportamental via *Computer Using Agents* (CUAs) a um pipeline multiagente baseado em TDD produz código funcionalmente mais correto do que a geração direta com LLM.

O método compara dois cenários controlados: um *baseline* em que o LLM recebe o requisito em linguagem natural e gera código diretamente; e um cenário experimental em que um agente gera testes primeiro, um segundo agente implementa até os testes passarem no CI e, por fim, um CUA interage com a interface do sistema como usuário real, verificando o comportamento observado contra o requisito original.

O experimento utilizará um conjunto de requisitos de aplicações de software com interface gráfica, permitindo interação natural do CUA, além de softwares sem interface gráfica direta, o que permite também uma validação determinística. A contribuição esperada é evidência empírica sobre a capacidade do CUA de detectar falhas semânticas que escapam ao TDD gerado pelo próprio pipeline, além de uma caracterização dos tipos de erro que cada abordagem captura ou deixa passar.

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

> **O pipeline de geração de código baseado em TDD com validação final via CUA produz código mais correto do que a geração direta de código a partir de requisitos com LLM?**

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
