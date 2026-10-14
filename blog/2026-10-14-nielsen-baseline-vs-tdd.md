---
slug: nielsen-baseline-vs-tdd
title: "Nielsen: campeã baseline contra campeã TDD"
authors: [eduardo]
tags: [tcc, experimento]
---

Pus lado a lado as notas do CUA para as campeãs dos dois torneios: a
`deepseek/run44/baseline`, do [torneio geral](/blog/desempatador), e a `glm/run38/tdd`, do
[torneio TDD](/blog/finalistas-nielsen-tdd).

<!-- truncate -->

## Critérios

1. Visibilidade do estado do sistema
2. Correspondência entre o sistema e o mundo real
3. Controle e liberdade do usuário
4. Consistência e padrões
5. Prevenção de erros
6. Reconhecimento em vez de memorização
7. Flexibilidade e eficiência de uso
8. Estética e design minimalista
9. Ajuda para reconhecer, diagnosticar e corrigir erros
10. Ajuda e documentação

## Escala

A régua não é uma escala publicada, foi a melhor que encontrei para expressar qualidade:

| Nota | Evidência observável |
|---|---|
| Péssimo | O problema impede concluir a tarefa, sem caminho claro para continuar. |
| Ruim | Só é possível avançar com muita tentativa, confusão ou retrabalho. |
| Regular | É possível concluir, mas é preciso procurar, interpretar ou repetir ações desnecessárias. |
| Bom | O uso é claro e previsível, com pequenas dificuldades que pouco atrapalham. |
| Excelente | O uso é claro e fluido, sem dificuldade observada naquele aspecto durante o percurso. |

## Notas

| Heurística | run44 CUA | run44 Eduardo | run38 CUA | run38 Eduardo |
|---|---|---|---|---|
| 1. Visibilidade do estado do sistema | Bom | Regular | Regular | Excelente |
| 2. Correspondência entre o sistema e o mundo real | Regular | Excelente | Bom | Excelente |
| 3. Controle e liberdade do usuário | Ruim | Excelente | Ruim | Regular |
| 4. Consistência e padrões | Bom | Excelente | Bom | Excelente |
| 5. Prevenção de erros | Regular | Excelente | Bom | Excelente |
| 6. Reconhecimento em vez de memorização | Bom | Excelente | Bom | Excelente |
| 7. Flexibilidade e eficiência de uso | Excelente | Excelente | Excelente | Excelente |
| 8. Estética e design minimalista | Bom | Regular | Bom | Bom |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Regular | Ruim | Regular | Excelente |
| 10. Ajuda e documentação | Regular | Excelente | Regular | Excelente |

Pelo CUA, a run38 fica acima nas heurísticas 2 e 5, a run44 na 1, e as outras sete empatam.
Pelas minhas notas, a run38 fica acima nas heurísticas 1, 8 e 9, a run44 na 3, e as outras
seis empatam.

## Minha avaliação da run44

- **1. Visibilidade do estado do sistema.** O formulário separa bem as seções e mostra o
  erro "Preencha todos os campos" de forma visível, mas não indica qual campo está vazio. A
  validação de e-mail, CPF, CEP e valor funciona.
- **2. Correspondência entre o sistema e o mundo real.** Os valores digitados ganham o
  formato esperado, conforme o requisito.
- **3. Controle e liberdade do usuário.** O progresso se mantém ao trocar de aba.
- **4. Consistência e padrões.** As duas abas têm a mesma aparência, com campos consistentes
  e separados em seções.
- **5. Prevenção de erros.** Há placeholders e seleções sempre que possível.
- **8. Estética e design minimalista.** É preciso rolar a tela para ver o botão "Enviar
  solicitação".
- **9. Ajuda para reconhecer, diagnosticar e corrigir erros.** A mensagem não indica o campo
  que causa o erro.
- **10. Ajuda e documentação.** As instruções aparecem corretamente no ofício após o envio.

## Minha avaliação da run38

- **1. Visibilidade do estado do sistema.** A separação e o contraste entre as seções são
  muito bons, e o design dos campos é bom e consistente.
- **3. Controle e liberdade do usuário.** Os dados não se perdem ao trocar de aba, mas um
  valor digitado errado some do campo, e só descubro o erro ao tentar enviar.
- **4. Consistência e padrões.** Os campos são bastante consistentes.
- **5. Prevenção de erros.** Há placeholders e seleções sempre que necessário.
- **8. Estética e design minimalista.** As seções são bem separadas e legíveis, mas é preciso
  rolar a tela para ver o botão "Enviar solicitação".
- **9. Ajuda para reconhecer, diagnosticar e corrigir erros.** As mensagens seguem o
  requisito.
- **10. Ajuda e documentação.** O ofício é exatamente o que o requisito pede.
