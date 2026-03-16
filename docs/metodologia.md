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
| **Baseline** | TDD+LLM via Onion (Agente A gera testes → Agente B implementa → CI) | CI |
| **Experimental** | Baseline + CUA como avaliador comportamental final | CI + CUA |

Ambos os grupos recebem os mesmos requisitos. O baseline é o pipeline TDD+LLM já existente (ferramenta Onion / adaptação). O experimental adiciona o CUA como avaliador final após o CI passar.

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
2. Executar pipeline TDD+LLM (Onion) para cada requisito
3. Rodar CI determinístico e registrar resultados do baseline
4. CUA recebe o requisito original e interage com o sistema gerado
5. Registrar artefatos de falha, logs e resultados do CUA
6. Comparar métricas CI vs CUA: o CUA detecta o que o CI não detectou?

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

- [ ] Usar Onion diretamente ou adaptar com Claude Code?
- [ ] Qual CUA usar como avaliador final? (custo vs precisão)
- [ ] Próximo passo: fundamentação teórica ou primeiro experimento/protótipo?
- [ ] O frontend deve ser gerado pelo próprio pipeline ou é parte fixa do escopo?
