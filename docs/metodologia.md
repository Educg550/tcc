---
sidebar_position: 3
title: Metodologia
---

# Metodologia

## Escopo

Para garantir um experimento controlado e reproduzível, o escopo é limitado a:

- **N requisitos fechados** de um sistema com frontend (ex: CRUD web simples - sistema de tarefas ou cadastro de usuários)
- Cada requisito é uma funcionalidade atômica e verificável
- Frontend é necessário para que o CUA possa interagir visualmente com o sistema

---

## Grupos Experimentais

| Grupo | Pipeline |
|-------|----------|
| **Baseline** | requisito → LLM → código |
| **Experimental** | requisito → Agente A gera testes → Agente B implementa → CI → CUA valida comportamento |

Ambos os grupos recebem os mesmos requisitos. O baseline é a geração direta sem estrutura de testes. O experimental acrescenta geração automática de testes (TDD) e validação comportamental via CUA.

Os dois grupos são avaliados pela mesma régua externa, descrita a seguir.

---

## Critérios de Aceitação

Para cada requisito, o pesquisador escreve **à mão** um arquivo de critérios de aceitação, fora dos dois pipelines. O CUA julga o sistema gerado contra esse arquivo, com o mesmo protocolo para baseline e experimental.

Por que os critérios não podem sair do próprio pipeline:

- O CUA existe para detectar divergências que os testes gerados pelo próprio pipeline podem não cobrir (ver [Proposta](/docs/proposta)). Se os critérios viessem do agente de especificação, o CUA estaria validando a interpretação do próprio pipeline, e a divergência ficaria invisível por construção.
- O grupo baseline não tem agente de especificação. Sem critérios externos, não existe régua equivalente para os dois grupos.

---

## Modos de Execução

O orquestrador roda em dois modos:

| Modo | Comportamento | Uso |
|------|---------------|-----|
| **Interativo** (padrão) | aprovação binária `y/n` por etapa, com feedback textual obrigatório na rejeição | desenvolvimento e debug/demonstração |
| **Batch** (`--yes`) | sem stdin e sem intervenção humana; quem fecha o loop é o CI | **único modo permitido** nas execuções que produzem a comparação entre grupos |

O batch é obrigatório no experimento porque o feedback humano é uma ajuda externa que só o grupo experimental receberia.

---

## Métricas

### Métricas Estruturais (CI)
- **Taxa de sucesso CI:** % de requisitos cujo código passa em todos os testes
- **Iterações necessárias:** número de ciclos até o CI passar
- **Complexidade ciclomática:** caminhos de execução do código gerado
- **Testes de mutação:** robustez dos testes gerados

### Métricas Comportamentais (CUA)
- **Taxa de sucesso CUA:** % de requisitos aprovados pelo CUA contra os critérios de aceitação, por grupo
- **Falsos positivos CI:** requisitos que passam no CI mas falham no CUA
- **Taxa de divergência semântica:** diferença entre o que o CI e o CUA detectam

### Métricas Operacionais
- **Custo por requisito:** custo em tokens/API para completar cada requisito
- **Retries e feedback (modo interativo):** número de rejeições por etapa e o texto que as motivou

---

## Contagem de Falhas

O campo `etapas_ok` do `RUN.log` (todas as etapas terminaram com sucesso) não significa a mesma coisa nos dois grupos, e por isso não serve como critério de elegibilidade na comparação:

- **Baseline:** uma etapa só e nenhum portão que possa reprovar. `etapas_ok` é verdadeiro sempre que o modelo escreve algum arquivo.
- **Experimental:** o pytest é portão. `etapas_ok` é falso quando o pipeline esgota as tentativas sem passar nos testes.

No lote de 200 runs isso apareceu como zero runs baseline descartadas por `etapas_ok` contra 22 runs TDD. Descartar essas runs e comparar só as elegíveis esconde a falha do TDD no portão e mantém todas as falhas do baseline, que só aparecem depois, na avaliação. O viés favorece o grupo experimental: entre elegíveis, o TDD vence em tudo; contando as inelegíveis como reprovação, o baseline fica à frente com o DeepSeek (82% contra 76%) e atrás com o GLM (6% contra 24%).

Decisão: **o denominador de toda taxa é o número de tentativas por célula (modelo × grupo), não o de runs elegíveis.** Uma run que não chega à avaliação, por falhar no portão ou não produzir sistema executável, conta como reprovada no grupo em que ocorreu.

---

## Procedimento

1. Definir a lista de N requisitos (sistema com frontend)
2. Escrever, para cada requisito, o arquivo de critérios de aceitação - fora dos dois pipelines
3. **Baseline:** LLM recebe cada requisito e implementa diretamente; registrar código gerado
4. **Experimental:** Agente A gera testes → Agente B implementa → CI; registrar resultados de cada etapa
5. **Avaliação:** o CUA interage com o sistema produzido por cada grupo e julga contra os critérios de aceitação, com o mesmo protocolo nos dois casos
6. Registrar artefatos de falha, logs e resultados do CUA
7. Comparar baseline vs experimental: o pipeline TDD+CUA produz código mais correto que a geração direta?

Os passos 3 a 5 rodam sempre em **modo batch**.

---

## Ferramentas Previstas

| Papel | Ferramenta |
|-------|-----------|
| Pipeline TDD+LLM | [Onion](https://github.com/TOProgramming/onion) ou adaptação com Claude |
| LLM | GPT-4o-mini, Gemini 2.5-Flash e/ou Claude (para comparação) |
| CI | pytest, executado deterministicamente |
| CUA (avaliador) | A definir: Browser Use, Cua Agent SDK ou Gemini CUA |

---

## Questões em Aberto

- [ ] Como definir um bom requisito de software?
- [ ] Como avaliar de forma precisa o resultado de ambos pipelines?
- [ ] O frontend deve ser gerado pelo próprio pipeline ou é parte fixa do escopo?
- [ ] Qual o valor de N e quantas repetições por requisito?
- [ ] Que protocolo os dados do modo interativo precisam para entrar nas conclusões: o que se registra, como o feedback é classificado, quantas execuções?
