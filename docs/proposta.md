---
sidebar_position: 2
title: Proposta de Pesquisa
---

# Proposta de Pesquisa

A proposta tem duas partes. A Parte 1 é a proposta inicial, em que o CUA era considerado somente como avaliador final do pipeline baseado em TDD. A Parte 2 estende a proposta depois da mudança de experimento e de escopo do TCC: o alvo passa a ser a reconstrução do PreJanus-back, a comparação inclui a reconstrução guiada por testes e o CUA fica fora da avaliação.

---

## Parte 1 - Proposta Inicial

### Título

**Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents**

---

### Introdução

Modelos de linguagem de grande escala (LLMs) têm demonstrado capacidade crescente de gerar código funcional, mas a qualidade desse código em relação aos requisitos originais ainda é variável. Com as chamadas alucinações, ainda é difícil confiar na geração automática de código sem uma validação, que deve ser especialmente rigorosa em cenários onde o funcionamento do software é crítico.

A combinação de TDD com LLMs surge como abordagem para aumentar a confiabilidade da geração automática. Nesse paradigma, o desenvolvedor fica responsável por verificar especialmente a saúde de código de testes, o código de produção se torna secundário, o que garante uma abordagem mais simples e gerenciável do ponto de vista humano. A ferramenta **Onion** é uma prova de conceito que implementa TOP: a partir de arquivos de configuração YAML com especificações em linguagem natural, gera código Python automaticamente com base em TDD (Test Driven Development).

Outra camada interessante de validação que será introduzida nesse trabalho é o uso de Computer Using Agents (CUAs) - agentes que interagem com interfaces como um usuário humano - que adicionam uma camada de validação comportamental de caixa-preta, independente dos testes gerados pelo próprio pipeline.

---

### Abstrato

Modelos de linguagem de grande escala (LLMs) são cada vez mais utilizados para geração automática de código, mas produzem resultados de qualidade variável e sujeitos a alucinações - implementações que passam por testes superficiais sem satisfazer os requisitos reais. Este trabalho avalia se a adição de validação comportamental via *Computer Using Agents* (CUAs) a um pipeline multiagente baseado em TDD produz código funcionalmente mais correto do que a geração direta com LLM.

O método compara dois cenários controlados: um *baseline* em que o LLM recebe o requisito em linguagem natural e gera código diretamente; e um cenário experimental em que um agente gera testes primeiro, um segundo agente implementa até os testes passarem no CI e, por fim, um CUA interage com a interface do sistema como usuário real, verificando o comportamento observado contra critérios de aceitação escritos fora dos dois pipelines.

O experimento utilizará um conjunto de requisitos de aplicações de software com interface gráfica, permitindo interação natural do CUA, além de softwares sem interface gráfica direta, o que permite também uma validação determinística. A contribuição esperada é evidência empírica sobre a capacidade do CUA de detectar falhas semânticas que escapam ao TDD gerado pelo próprio pipeline, além de uma caracterização dos tipos de erro que cada abordagem captura ou deixa passar.

---

### Os Dois Cenários

#### Cenário Baseline - Geração Direta (sem TDD, sem CUA)

```
Requisito → LLM → Código gerado
```

O LLM recebe o requisito em linguagem natural e implementa diretamente, sem nenhuma
estrutura de testes prévia e sem validação adicional. Representa o uso mais simples e
direto de LLMs para geração de código.

#### Cenário Experimental - TDD + LLM + CUA como avaliador final

```
Requisito → Agente A (gera testes) → Agente B (implementa) → CI → CUA (valida comportamento)
```

Um agente gera testes automatizados para o requisito antes da implementação. Um segundo
agente implementa o código até os testes passarem no CI. Por fim, o CUA recebe os
critérios de aceitação escritos pelo pesquisador fora dos dois pipelines, interage com o
sistema como usuário real e verifica se o comportamento observado corresponde a eles.

---

### Pergunta de Pesquisa

> **O pipeline de geração de código baseado em TDD com validação final via CUA produz código mais correto do que a geração direta de código a partir de requisitos com LLM?**

---

### Por que CUA como Avaliador Final (e não parte central)?

CUAs são problemáticos como parte central do pipeline porque:
- Introduzem não-determinismo adicional (OCR, interpretação visual, múltiplas etapas)
- Dificultam atribuição de erros: LLM geradora? CUA avaliador? OCR?
- São overkill quando há acesso a código-fonte, testes e CI

São adequados como avaliador final porque:
- Simulam comportamento real de usuário (caixa-preta)
- Detectam divergências semânticas que os testes unitários gerados pelo próprio pipeline podem não cobrir
- O CUA julga contra critérios de aceitação escritos por um humano, não contra a especificação produzida pelo próprio pipeline
- O escopo de frontend torna a interação via interface mais natural

---

## Parte 2 - Reconstrução do PreJanus-back

### Título

**Avaliação de pipelines multiagente de geração de código: geração direta, TDD e reconstrução guiada por testes**

---

### Introdução

O experimento da Parte 1, com o formulário de auxílio financeiro do IME-USP, foi encerrado como inconclusivo. O requisito se mostrou simples demais para os modelos: muitas implementações dos dois grupos passaram em todos os critérios funcionais, e não houve critério sem viés para desempatá-las. O CUA, que deveria dar a palavra final, mudou de nota entre sessões da mesma aplicação.

O TCC passou então para um sistema real e maior: o Caronte, sistema de inscrições em editais da pós-graduação do IME-USP. Em acordo com os orientadores, o escopo foi fechado no **PreJanus-back**, o backend FastAPI do sistema, com 50 operações HTTP, dois bancos Postgres, autenticação via Senha Única, envio de e-mails e relatórios. O frontend, o Forms e os serviços externos permanecem os originais.

A mudança de alvo trouxe uma terceira forma de gerar código. Além de partir dos requisitos, um agente pode reconstruir o sistema a partir de testes fornecidos, sem o documento de requisitos. Nesse caso, os testes passam a ser a especificação, e a avaliação usa casos que o agente não viu.

---

### Abstrato

Este trabalho avalia três pipelines multiagente de geração de código na reconstrução do PreJanus-back. No primeiro experimento, a geração direta e o pipeline baseado em TDD partem dos mesmos requisitos e contratos (OpenAPI, esquemas dos bancos e infraestrutura). No segundo, um agente reconstrói o sistema a partir de 161 testes fornecidos, sem o documento de requisitos.

As entregas são avaliadas por um gabarito externo de 247 casos, aplicado via HTTP como caixa-preta e oculto dos agentes; no segundo experimento, a nota vem dos 85 casos que ficaram fora dos testes fornecidos. O mesmo modelo é usado em todas as etapas, com tetos de custo, tempo e propostas por etapa. A contribuição esperada é uma comparação, no nível de requisito, de onde cada pipeline acerta e falha, e uma caracterização dos tipos de erro que a geração direta, os testes gerados pelo próprio pipeline e os testes fornecidos deixam passar.

---

### Os Três Cenários

#### Cenário Baseline - Geração Direta

```
Requisitos e contratos → LLM → Código gerado
```

O LLM recebe os requisitos e os contratos e implementa diretamente, sem testes prévios e sem nenhum resultado de testes durante a geração.

#### Cenário TDD - Testes Próprios antes do Código

```
Requisitos e contratos → Agente A (gera testes) → Agente B (implementa) → pytest → correção
```

Um agente gera testes a partir dos requisitos. Um segundo agente implementa e corrige o código até os testes passarem ou até atingir o teto da etapa.

#### Cenário de Reconstrução Guiada por Testes (rework)

```
Testes fornecidos e contratos → Agente (implementa) → pytest dos testes fornecidos → correção
```

O agente recebe 161 casos do gabarito e os contratos, sem código original, documento de requisitos ou issues, e implementa até os testes passarem ou até atingir o teto da etapa.

---

### Perguntas de Pesquisa

> **Experimento 1: o pipeline de geração de código baseado em TDD produz código mais correto do que a geração direta a partir dos requisitos?**

> **Experimento 2: um agente que reconstrói o sistema a partir de testes fornecidos, sem o documento de requisitos, acerta os casos que não viu?**

---

### Por que o CUA Fica Fora da Parte 2?

Até a Parte 1, o CUA era considerado somente como avaliador final. Na Parte 2, ele fica fora da avaliação porque:
- O experimento e o escopo mudaram: o que é reconstruído é uma API, sem interface própria, e o frontend continua o original. O gabarito HTTP faz a avaliação caixa-preta diretamente na interface reconstruída, como a Parte 1 já previa para softwares sem interface gráfica direta
- O andamento do TCC: com o tempo até a entrega, o esforço ficou concentrado no gabarito e nas runs dos três cenários
- O CUA tem um viés diferente do gabarito: julga pela própria leitura da tela e do critério. Na Parte 1, pulou o percurso pedido e mesmo assim deu nota a ele, inventou diferenças inexistentes, e o modelo que conferia as sessões aceitou num caso o erro que reprovou em outro. Uma falha apontada pelo CUA não se atribui com segurança ao pipeline ou ao avaliador
- O CUA introduz não-determinismo forte: seis das dez heurísticas avaliadas mudaram de nota entre sessões da mesma aplicação, a ponto de inverter a comparação entre as finalistas. O gabarito, reaplicado à mesma entrega, repetiu 246 dos 247 resultados

Os resultados do CUA na Parte 1 continuam como evidência do trabalho e estão nas [observações sobre o CUA](/blog/observacoes-cua). O desenho completo da Parte 2 está na [metodologia](/docs/metodologia).
