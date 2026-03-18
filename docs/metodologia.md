---
sidebar_position: 3
title: Metodologia
---

# Metodologia

## Escopo

Para garantir um experimento controlado e reproduzível, o escopo é limitado a:

- **10–20 requisitos fechados** de um sistema com frontend (ex: CRUD web simples — sistema de tarefas ou cadastro de usuários)
- Cada requisito é uma funcionalidade atômica e verificável
- Frontend é necessário para que o CUA possa interagir visualmente com o sistema

---

## Grupos Experimentais

| Grupo | Pipeline | Avaliação |
|-------|----------|-----------|
| **Baseline** | LLM recebe requisito → implementa diretamente | — |
| **Experimental** | Agente A gera testes → Agente B implementa → CI → CUA valida comportamento | CI + CUA |

Ambos os grupos recebem os mesmos requisitos. O baseline é a geração direta sem estrutura de testes. O experimental acrescenta geração automática de testes (TDD) e validação comportamental via CUA.

---

## Métricas

### Métricas Estruturais (CI)
- **Taxa de sucesso CI:** % de requisitos cujo código passa em todos os testes
- **Iterações necessárias:** número de ciclos até o CI passar
- **Complexidade ciclomática:** caminhos de execução do código gerado
- **Testes de mutação:** robustez dos testes gerados

### Métricas Comportamentais (CUA)
- **Taxa de sucesso CUA:** % de requisitos validados com sucesso pelo CUA
- **Falsos positivos CI:** requisitos que passam no CI mas falham no CUA
- **Taxa de divergência semântica:** diferença entre o que o CI e o CUA detectam

### Métricas Operacionais
- **Custo por requisito:** custo em tokens/API para completar cada requisito
- **Taxa de regressão:** novos requisitos que quebram implementações anteriores

---

## Procedimento

1. Definir lista de 10–20 requisitos (sistema com frontend)
2. **Baseline:** LLM recebe cada requisito e implementa diretamente; registrar código gerado
3. **Experimental:** Agente A gera testes → Agente B implementa → CI → CUA recebe o requisito original em linguagem natural e interage com o sistema gerado; registrar resultados de cada etapa
4. Registrar artefatos de falha, logs e resultados do CUA
5. Comparar baseline vs experimental: o pipeline TDD+CUA produz código mais correto que a geração direta?

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
