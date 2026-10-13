---
slug: resultados-nielsen
title: "Resultados da avaliação Nielsen"
authors: [eduardo]
tags: [tcc, experimento]
---

Rodei o CUA nas duas finalistas do torneio cego, run44 e run35, para avaliar
as dez heurísticas de Nielsen. Também dei as minhas notas às duas.
O roteiro, a escala e as heurísticas estão no [post das finalistas](/blog/finalistas-nielsen).

<!-- truncate -->

## Quadro geral

Heurísticas: 1 visibilidade do estado do sistema, 2 correspondência com o mundo real,
3 controle e liberdade, 4 consistência e padrões, 5 prevenção de erros, 6 reconhecimento
em vez de memorização, 7 flexibilidade e eficiência, 8 estética e design minimalista,
9 diagnóstico e correção de erros, 10 ajuda e documentação.

| Run | Avaliador | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `deepseek/run44/baseline` | CUA Opus 5.5 | Bom | Regular | Ruim | Bom | Regular | Bom | Excelente | Bom | Regular | Regular |
| `deepseek/run44/baseline` | Eduardo | Regular | Excelente | Excelente | Excelente | Excelente | Excelente | Excelente | Regular | Ruim | Excelente |
| `deepseek/run35/baseline` | CUA Opus 5.5 | Bom | Bom | Ruim | Excelente | Regular | Bom | Excelente | Excelente | Ruim | Regular |
| `deepseek/run35/baseline` | Eduardo | Regular | Excelente | Regular | Bom | Excelente | Excelente | Excelente | Regular | Ruim | Excelente |

## Finalistas do torneio — Opus 5.5

Rodei uma sessão por run, com `anthropic/claude-opus-5.5` via OpenRouter e browser-use
0.13.10, a 1366 × 768 e com escala do dispositivo de 1. Usei o roteiro C1, que reúne
as dez heurísticas e as duas abas. Não rodei o Cypress de novo.

| Medida | `deepseek/run44/baseline` (campeã) | `deepseek/run35/baseline` (vice) |
|---|---:|---:|
| Duração total da sessão | 433,45 s (7min13s) | 411,00 s (6min51s) |
| Duração do CUA, incluindo judge | 431,66 s | 409,61 s |
| Passos do agente | 37 de 80 | 38 de 80 |
| Chamadas à API, incluindo judge | 38 | 39 |
| Tokens de entrada | 840.420 | 921.207 |
| Tokens de saída | 18.557 | 18.668 |
| Tokens totais | 858.977 | 939.875 |
| Custo confirmado | US$ 3,732820 | US$ 4,058188 |
| Conclusão declarada pelo CUA (`passou`) | `true` | `true` |
| Veredito do judge | `true` | `true` |

**Total: US$ 7,791008, 844,45 s (14min4s) e 1.798.852 tokens.** O custo é a soma de
`usage.cost` das respostas do OpenRouter, incluindo a chamada de judge de cada sessão.
A duração total inclui a consulta ao catálogo e a subida da aplicação; a duração do
CUA mede a chamada `Agent.run`, incluindo o judge e o encerramento do navegador.
Os totais de tempo acima são a soma das duas sessões, sem o início do processo Python.

A tentativa anterior na run44, às 17:40 UTC, parou em 13,55 s (7,72 s de CUA): o SDK
recusou o argumento `usage` antes de enviar qualquer requisição ao modelo. Não houve
cobrança de inferência nem execução da run35 nessa tentativa. Separei esse tempo
das sessões que produziram as notas e corrigi o erro de configuração antes de
rodar as duas finalistas.

O campo `passou` indica que o CUA declarou ter concluído a avaliação, não que o
formulário tem boa usabilidade. O script também grava `completed: true` para as duas
runs, mas esse campo não incorpora o veredito do judge. O judge é outra chamada de
avaliação feita pelo browser-use com o mesmo modelo; seu parecer não substitui
minha conferência das evidências.

### `deepseek/run44/baseline`

O judge aceitou a avaliação e considerou as notas sustentadas pelo percurso e pelas
capturas. Registrou três lacunas: não houve uso de Shift+Tab, os erros foram provocados
pela ferramenta `input` e não só pelo teclado, e não houve rolagem explícita para
procurar ajuda. Seu parecer considerou que essas lacunas não invalidavam a avaliação.

Notas, justificativas e evidências transcritas da saída do CUA:

| Heurística | Nota | Justificativa | Evidência (ação e resultado observado) |
|---|---|---|---|
| 1. Visibilidade do estado do sistema | Bom | Aba ativa, formatação e confirmação ficam visíveis. Porém o aviso de erro não se atualiza durante a correção. | A aba ativa aparece em azul escuro e a outra fica clara (igual em ALUNOS e DOCENTES). Ao sair dos campos: 150000→R$ 1.500,00; 01021980→01/02/1980; 05508090→05508-090; 52998224725→529.982.247-25. O envio mostra a tela 'Solicitação registrada'. Depois de restaurar os valores, a caixa rosa de erros continuou no topo até reenviar. |
| 2. Correspondência entre o sistema e o mundo real | Regular | Os formatos brasileiros e os termos institucionais estão corretos, mas há textos contraditórios ou ambíguos. | R$, dd/mm/aaaa, CEP e CPF aparecem no padrão brasileiro. O rótulo do CPF pede 'separados por pontos e traço', mas o exemplo é 12345678909, sem pontuação. O exemplo de período usa formato extenso ('22 a 26 de julho de 2024'). O título diz 'Solicitação registrada', mas o ofício afirma 'A CCP aprovou na data de hoje'. Isso confunde registro com aprovação, nas duas abas. |
| 3. Controle e liberdade do usuário | Ruim | A troca de aba preserva os dados, mas depois do envio não há como voltar para corrigir o pedido. Corrigir exige refazer tudo. | ALUNOS→DOCENTES→ALUNOS preservou todos os dados, e DOCENTES→ALUNOS→DOCENTES também. A confirmação não tem nenhum botão (0 elementos interativos: voltar, editar ou imprimir) e a URL continua '/'. O Voltar do navegador saiu da aplicação para about:blank, nas duas abas. Ao reabrir a URL, o formulário veio vazio e o pedido foi perdido. |
| 4. Consistência e padrões | Bom | Estrutura, validação e confirmação são iguais nas duas abas, com pequenas diferenças de layout. | As duas abas têm os mesmos 3 blocos (Solicitante e Evento, Endereço, Pagamento), a mesma caixa rosa de erros e o mesmo ofício. Diferenças em DOCENTES: não há Nível nem Tipo de auxílio; e-mail e valor ficam na 2ª linha; apresentação ocupa linha própria; a distribuição do endereço é diferente. |
| 5. Prevenção de erros | Regular | Máscaras, selects e exemplos ajudam, mas não há validação antes do envio e os exemplos contradizem os rótulos. | As máscaras de valor, data, CEP e CPF formataram ao sair dos campos. Os selects (Nível, Tipo, Apresentação) evitam digitação livre. O e-mail 'joao' e o valor 0 (que virou R$ 0,00) só foram recusados após clicar em Enviar. O exemplo do CPF sem pontos contradiz o rótulo. O formato do período não corresponde ao exemplo extenso. |
| 6. Reconhecimento em vez de memorização | Bom | Os rótulos ficam visíveis acima dos campos, mas o formato esperado some quando o exemplo desaparece. | Os rótulos em maiúsculas permaneceram visíveis após a digitação, nas duas abas. O formato esperado só aparece como exemplo dentro do campo e desaparece ao digitar. Não há texto de formato fixo. |
| 7. Flexibilidade e eficiência de uso | Excelente | O formulário inteiro pode ser preenchido só com o teclado, sem pontuação manual. | Preenchi as duas abas usando apenas Tab e digitação. A ordem do Tab seguiu a ordem visual. Os selects aceitaram a letra inicial (M=Mestrado, P=Participação/Pôster). Valor, data, CEP e CPF foram digitados só com dígitos e formatados automaticamente. |
| 8. Estética e design minimalista | Bom | O visual é limpo e bem agrupado, sem distrações, mas o envio exige rolagem. | Os 3 blocos têm títulos claros e espaçamento adequado, sem elementos supérfluos. Quase todo o formulário cabe na tela, mas o botão 'Enviar solicitação' exige uma pequena rolagem nas duas abas. |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Regular | As mensagens aparecem, mas são genéricas e não localizam os campos com problema. | Ao enviar com nome vazio, e-mail 'joao' e valor 0, apareceu uma caixa rosa no topo com 'Preencha todos os campos', 'Valor solicitado deve ser maior que 0' e 'E-mail inválido'. Nenhum campo ficou destacado. A mensagem não diz que o campo vazio era o Nome. Foi preciso procurar o campo manualmente. Os demais dados foram preservados. O comportamento foi idêntico em ALUNOS e DOCENTES. |
| 10. Ajuda e documentação | Regular | Não há orientações além dos exemplos dentro dos campos, e o próximo passo após o envio é vago. | Procurei ajuda na página e não encontrei texto, link ou ícone de ajuda. As únicas orientações são os exemplos nos campos, alguns deles contraditórios. O ofício termina com 'Encaminhe-se ao Serviço Financeiro', sem explicar como, e sem opção de imprimir, baixar ou acompanhar o pedido. |

Dificuldades na execução: o Voltar do navegador na confirmação saiu para about:blank nas duas abas, impedindo a correção. Por isso foi necessário reabrir a URL para iniciar DOCENTES. Na troca de aba durante o teste de DOCENTES, ALUNOS aparecia vazio porque a sessão havia sido reiniciada. O percurso completo foi concluído nas duas abas.

Artefatos em `demos/runs/batch/deepseek/run44/baseline/_harness/cua-nielsen-opus55-20261011T174407Z/`: `resultado.json`, `relatorio.md`, `api-usage.jsonl`,
`history.json`, `judge.json`, `prompt.md`, `model.json` e `executar.py`.
Copiei as capturas para `screenshots/`; `capturas.json` liga cada passo
ao arquivo preservado, sem alterar o histórico original.

### `deepseek/run35/baseline`

O judge aceitou a avaliação e considerou as notas sustentadas pelo percurso e pelas
capturas. Registrou duas ressalvas: o Excelente na heurística 4 é um pouco generoso, e o
agente disse que o ofício é o mesmo nas duas abas, embora o de DOCENTES traga o assunto
`Verba do programa` e não traga o nível.

Notas, justificativas e evidências transcritas da saída do CUA:

| Heurística | Nota | Justificativa | Evidência (ação e resultado observado) |
|---|---|---|---|
| 1. Visibilidade do estado do sistema | Bom | A aba ativa e as máscaras são claras, mas o erro antigo não acompanha as correções e a confirmação é ambígua. | A aba ativa aparece em azul escuro nas duas abas e o foco é visível no Tab. Ao sair dos campos, valor, data, CEP e CPF são formatados (150000→R$ 1.500,00; 01021980→01/02/1980; 05508090→05508-090; 52998224725→529.982.247-25). Após corrigir os campos, o banner vermelho continua visível até o novo envio. A confirmação 'Solicitação registrada' aparece com o ofício. A URL fica sempre em '/'. Comportamento igual em ALUNOS e DOCENTES. |
| 2. Correspondência com o mundo real | Bom | Os termos e formatos são brasileiros e institucionais, mas o ofício e o exemplo de período confundem. | Os rótulos usam o vocabulário da USP (N. USP, Programa, Banca). Valor em R$ com vírgula, CPF, CEP e data em dd/mm/aaaa. O placeholder do período ('10 a 14 de julho de 2024') difere do formato usado (10/03/2026 a 14/03/2026). O ofício afirma que a 'CCP aprovou na data de hoje' para um pedido recém-enviado e diz 'Encaminhe-se ao Serviço Financeiro'. Igual nas duas abas. |
| 3. Controle e liberdade do usuário | Ruim | Não é possível voltar da confirmação para corrigir o pedido, e os dados se perdem. | A troca de aba preserva os dados (ALUNOS→DOCENTES→ALUNOS e DOCENTES→ALUNOS→DOCENTES). Após um envio com erro, os dados também são preservados. A tela de confirmação não tem nenhum botão ou link (0 elementos interativos). O Voltar do navegador leva a about:blank. Ao reabrir a URL, o formulário vem vazio e na aba ALUNOS, perdendo o pedido inteiro. Igual nas duas abas. |
| 4. Consistência e padrões | Excelente | As duas abas têm a mesma organização, aparência e comportamento. | Ambas têm três blocos, os mesmos rótulos e placeholders, as mesmas máscaras, o mesmo banner de erro e o mesmo ofício. Diferença coerente: DOCENTES não tem Nível nem Tipo de auxílio, e sua primeira linha fica com 8 campos. |
| 5. Prevenção de erros | Regular | Há máscaras, selects e exemplos, mas nada valida antes do envio e o valor é ambíguo. | Os selects (Nível, Tipo, Apresentação) evitam erros de digitação, e as máscaras são aplicadas ao sair dos campos. O placeholder do valor é '1500', mas os dígitos são lidos como centavos (150000→R$ 1.500,00). O e-mail 'joao' e o valor 0 só são acusados após clicar em Enviar. Os rótulos de CPF e RG pedem pontos e traço, mas o CPF aceita só dígitos. Igual nas duas abas. |
| 6. Reconhecimento em vez de memorização | Bom | Os rótulos ficam sempre visíveis, mas o formato esperado some ao digitar. | Os rótulos em caixa alta ficam acima dos campos e continuam visíveis após o preenchimento. O formato esperado existe apenas no placeholder, que desaparece quando se digita. Não há texto de ajuda fixo. Igual nas duas abas. |
| 7. Flexibilidade e eficiência de uso | Excelente | Todo o preenchimento foi possível pelo teclado, sem pontuação manual. | Os dois formulários completos foram preenchidos com Tab e Shift+Tab. A ordem do Tab segue o layout em linhas. Os selects aceitam a letra inicial (M=Mestrado, P=Participação/Pôster). Valor, data, CEP e CPF foram digitados só com dígitos. |
| 8. Estética e design minimalista | Excelente | O formulário cabe inteiro na tela, bem agrupado e sem distrações. | Em 1366x768, os três blocos e o botão Enviar ficam visíveis sem rolagem nas duas abas. Os blocos têm títulos claros e não há elementos supérfluos. Os rótulos são pequenos e alguns textos ficam truncados (nome do evento, logradouro), uma ressalva menor. |
| 9. Ajuda para reconhecer e corrigir erros | Ruim | As mensagens são genéricas e não localizam os campos com problema. | Ao enviar sem nome, com e-mail 'joao' e valor 0, aparece um banner vermelho no topo: 'Preencha todos os campos', 'Valor solicitado deve ser maior que 0', 'E-mail inválido'. A mensagem não diz qual campo está vazio, nenhum campo é destacado (sem borda ou ícone) e não há orientação de como corrigir. O banner persiste após a correção. Igual nas duas abas. |
| 10. Ajuda e documentação | Regular | Só existem placeholders, e nada explica o que acontece após o envio. | Não há link, ícone ou texto de ajuda na página. As orientações se limitam aos placeholders e às instruções nos rótulos (ex.: 'separados por pontos e traço'). Após o envio, a única instrução é 'Encaminhe-se ao Serviço Financeiro', sem dizer como imprimir, salvar ou corrigir o pedido. |

Dificuldades na execução: não houve caminho pela interface para voltar da confirmação. Tentei o Voltar do navegador, que levou a about:blank, e reabri a URL, que trouxe o formulário vazio nas duas abas.

Artefatos em `demos/runs/batch/deepseek/run35/baseline/_harness/cua-nielsen-opus55-20261013T193004Z/`: `resultado.json`, `relatorio.md`, `api-usage.jsonl`,
`history.json`, `judge.json`, `capturas.json`, `screenshots/`, `prompt.md`,
`model.json` e `executar.py`.

## Minha avaliação {#minha-avaliacao}

Avaliei as duas finalistas pela interface, seguindo o roteiro do
[post das finalistas](/blog/finalistas-nielsen). Preenchi com valores digitados na hora,
e não com os dados de `PADRAO`. Nas duas runs, o envio gerou o ofício completo, com
valor, CEP, CPF e data de nascimento formatados. As anotações cruas que fiz enquanto
verificava os critérios, com os ofícios gerados, estão em
[`_resultados.md`](https://github.com/Educg550/tcc/blob/main/blog/2026-10-06-resultados-nielsen/_resultados.md).

### `deepseek/run44/baseline`

| Heurística | Nota | Justificativa |
|---|---|---|
| 1. Visibilidade do estado do sistema | Regular | O formulário separa bem as seções e mostra o erro "Preencha todos os campos" de forma visível, mas não indica qual campo está vazio. A validação de e-mail, CPF, CEP e valor funciona. |
| 2. Correspondência entre o sistema e o mundo real | Excelente | Os valores digitados ganham o formato esperado, conforme o requisito. |
| 3. Controle e liberdade do usuário | Excelente | O progresso se mantém ao trocar de aba. |
| 4. Consistência e padrões | Excelente | As duas abas têm a mesma aparência, com campos consistentes e separados em seções. |
| 5. Prevenção de erros | Excelente | Há placeholders e seleções sempre que possível. |
| 6. Reconhecimento em vez de memorização | Excelente | — |
| 7. Flexibilidade e eficiência de uso | Excelente | — |
| 8. Estética e design minimalista | Regular | É preciso rolar a tela para ver o botão "Enviar solicitação". |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Ruim | A mensagem não indica o campo que causa o erro. |
| 10. Ajuda e documentação | Excelente | As instruções aparecem corretamente no ofício após o envio. |

### `deepseek/run35/baseline`

| Heurística | Nota | Justificativa |
|---|---|---|
| 1. Visibilidade do estado do sistema | Regular | O formulário separa bem as seções e mostra o erro "Preencha todos os campos" de forma visível, mas não indica qual campo está vazio. A validação de e-mail, CPF, CEP e valor funciona. |
| 2. Correspondência entre o sistema e o mundo real | Excelente | Todos os campos com formatação automática funcionam. |
| 3. Controle e liberdade do usuário | Regular | Os dados persistem ao trocar de aba no meio do preenchimento. |
| 4. Consistência e padrões | Bom | O alinhamento dos campos não é consistente. |
| 5. Prevenção de erros | Excelente | Há placeholders e seleções sempre que possível. |
| 6. Reconhecimento em vez de memorização | Excelente | — |
| 7. Flexibilidade e eficiência de uso | Excelente | — |
| 8. Estética e design minimalista | Regular | Algumas caixas de texto ficam desalinhadas sem motivo, mas os campos aparecem em seções separadas nas duas abas. |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Ruim | A mensagem não indica o campo que causa o erro. |
| 10. Ajuda e documentação | Excelente | As instruções aparecem corretamente no ofício após o envio. |

### Comparação com o CUA

Minhas notas coincidem com as do CUA em 1 das 10 heurísticas na run44 e em 2 na run35. A 7
(Excelente) é a única em que todos concordam. Fui mais severo nas heurísticas 1 e 8 e mais
generoso nas 2, 3, 5, 6 e 10, nas duas runs.

- **9.** Vimos a mesma falha: a mensagem genérica que não aponta o campo. Dei Ruim nas duas
  runs; o CUA deu Regular na run44 e Ruim na run35. Também usei essa falha para baixar a heurística 1.
- **8.** Na run44, nós dois registramos a rolagem até o botão de envio. Dei Regular, e o
  CUA deu Bom. Na run35, as caixas desalinhadas que me levaram a Regular não aparecem
  nas justificativas do CUA.
- **10.** Tomei as instruções do ofício como a orientação depois do envio. O CUA procurou
  ajuda na página, não encontrou e achou vago o "Encaminhe-se ao Serviço Financeiro".
- **3.** Testei a troca de abas. O CUA testou voltar da confirmação
  para corrigir o pedido e não achou caminho, o que lhe rendeu Ruim nas duas runs.
  Minhas justificativas não tratam desse caminho.
- **2 e 5.** O CUA apontou problemas de texto que minhas justificativas não citam: o
  ofício diz que a CCP "aprovou" um pedido recém-enviado (nas duas runs), o exemplo de
  CPF não tem a pontuação que o rótulo pede (run44) e o placeholder `1500` fica num campo
  que trata os dígitos como centavos (run35).

Entre as finalistas, minhas notas põem a run44 acima da run35 nas heurísticas 3 e 4 e
as empatam nas demais, o que acompanha o resultado do torneio. As do CUA vão no
sentido oposto: a run35 fica acima nas heurísticas 2, 4 e 8, a run44 fica acima na 9, e as demais
empatam.
