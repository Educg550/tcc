---
slug: resultados-nielsen-tdd
title: "Resultados da avaliação Nielsen TDD"
authors: [eduardo]
tags: [tcc, experimento]
---

Rodei o CUA nas duas finalistas do [torneio TDD](/blog/finalistas-nielsen-tdd), run38 e
run19, com o mesmo roteiro, o mesmo modelo e a mesma configuração usados nas
[finalistas baseline](/blog/resultados-nielsen).

<!-- truncate -->

## Quadro geral

Heurísticas: 1 visibilidade do estado do sistema, 2 correspondência com o mundo real,
3 controle e liberdade, 4 consistência e padrões, 5 prevenção de erros, 6 reconhecimento
em vez de memorização, 7 flexibilidade e eficiência, 8 estética e design minimalista,
9 diagnóstico e correção de erros, 10 ajuda e documentação.

| Run | Avaliador | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `glm/run38/tdd` | CUA Opus 5.5 | Regular | Bom | Ruim | Bom | Bom | Bom | Excelente | Bom | Regular | Regular |
| `glm/run19/tdd` | CUA Opus 5.5 | Bom | Regular | Ruim | Bom | Regular | Bom | Excelente | Bom | Regular | Regular |

Pelo CUA, a run38 fica acima nas heurísticas 2 e 5, a run19 fica acima na 1, e as outras
sete empatam.

## Execução

Rodei uma sessão por run, com `anthropic/claude-opus-5.5` via OpenRouter e browser-use
0.13.10, a 1366 × 768 e com escala do dispositivo de 1. Usei o roteiro C1, que reúne
as dez heurísticas e as duas abas. Não rodei o Cypress de novo.

| Medida | `glm/run38/tdd` (campeã) | `glm/run19/tdd` (vice) |
|---|---:|---:|
| Duração total da sessão | 460,93 s (7min41s) | 448,71 s (7min29s) |
| Duração do CUA, incluindo judge | 457,88 s | 448,05 s |
| Passos do agente | 41 de 80 | 39 de 80 |
| Chamadas à API, incluindo judge | 42 | 40 |
| Tokens de entrada | 994.846 | 934.888 |
| Tokens de saída | 20.332 | 21.104 |
| Tokens totais | 1.015.178 | 955.992 |
| Custo confirmado | US$ 4,386024 | US$ 4,161632 |
| Conclusão declarada pelo CUA (`passou`) | `true` | `true` |
| Veredito do judge | `true` | `true` |

**Total: US$ 8,547656, 909,64 s (15min10s) e 1.971.170 tokens.** O custo é a soma de
`usage.cost` das respostas do OpenRouter, incluindo a chamada de judge de cada sessão.

### `glm/run38/tdd`

O judge aceitou a avaliação e considerou as notas sustentadas pelo percurso e pelas
capturas. Registrou três lacunas menores: não houve uso explícito de Shift+Tab, a caixa
de erros de DOCENTES não aparece em nenhuma captura, e os erros foram provocados pela
ferramenta `input`, e não só pelo teclado.

Notas, justificativas e evidências transcritas da saída do CUA:

| Heurística | Nota | Justificativa | Evidência (ação e resultado observado) |
|---|---|---|---|
| 1. Visibilidade do estado do sistema | Regular | Aba ativa e formatação são claras, mas o retorno do envio com erro fica fora da vista. | A aba ativa fica preenchida em azul (ALUNOS e DOCENTES). Ao sair dos campos, 150000 virou R$ 1.500,00, 01021980 virou 01/02/1980, 05508090 virou 05508-090 e 52998224725 virou 529.982.247-25. Com erros, cliquei em Enviar no fim da página e nada mudou na vista: a caixa vermelha surgiu no topo e precisei rolar até ela. Com dados válidos, a tela 'Solicitação registrada' foi clara. Comportamento igual nas duas abas. |
| 2. Correspondência entre o sistema e o mundo real | Bom | Termos e formatos são os da USP e do Brasil, mas o ofício contradiz o estado real do pedido. | Rótulos como N. USP, PROGRAMA, BANCA DE EXAME OU DEFESA, CPF e RG/RNM; valores em R$ 1.500,00, datas dd/mm/aaaa, CEP 00000-000. O ofício lista os dados corretos, mas afirma 'A CCP aprovou na data de hoje' logo após o pedido ser apenas registrado. O ofício de DOCENTES é idêntico ao de ALUNOS e não indica a categoria. |
| 3. Controle e liberdade do usuário | Ruim | Trocar de aba e corrigir erros funciona; voltar da confirmação para corrigir exige refazer tudo. | Trocar ALUNOS→DOCENTES→ALUNOS (e o inverso) preservou todos os dados. Após o erro, os demais campos ficaram preservados e a correção foi direta. Na confirmação só existe o botão 'Nova solicitação', que abriu o formulário vazio. O Voltar do navegador levou a about:blank, fora da aplicação. Reabrir a URL trouxe o formulário vazio. Não há como editar o pedido enviado. Igual nas duas abas. |
| 4. Consistência e padrões | Bom | As abas têm organização, aparência e comportamento coerentes, com pequenas diferenças. | Mesmos 3 blocos, ordem, máscaras, mensagens de erro e ofício. DOCENTES apenas não tem NÍVEL/TIPO DE AUXÍLIO. Os placeholders mudam entre as abas (João de Oliveira, R$ 2.000,00, Itaú). A confirmação não distingue docente de aluno. |
| 5. Prevenção de erros | Bom | Máscaras, exemplos e selects orientam, mas não há validação antes do envio. | Máscaras em valor, data, CEP e CPF; placeholders com exemplos em todos os campos; selects para NÍVEL, TIPO e apresentação. O e-mail 'joao', o valor 0 e o nome vazio só foram apontados depois do envio, sem aviso ao sair do campo. O período é texto livre, com exemplo '10 a 12 de março de 2025' diferente do formato digitado. |
| 6. Reconhecimento em vez de memorização | Bom | Os rótulos ficam sempre visíveis; o exemplo de formato some ao digitar. | Os rótulos em caixa alta acima dos campos continuam visíveis após o preenchimento. O formato esperado aparece só no placeholder, que desaparece ao digitar. CPF e RG indicam o formato no próprio rótulo. |
| 7. Flexibilidade e eficiência de uso | Excelente | O preenchimento é fluido só pelo teclado. | Preenchi todos os campos das duas abas com Tab, na ordem visual. Os selects aceitaram a letra inicial (M→Mestrado, P→Participação/Pôster). Digitei só os dígitos e a pontuação foi inserida automaticamente. |
| 8. Estética e design minimalista | Bom | Bom agrupamento e sem distrações, mas o formulário inteiro não cabe na tela. | Três blocos com títulos destacados, espaçamento regular e nenhum elemento supérfluo. O botão 'Enviar solicitação' e o fim do bloco de pagamento exigem rolagem (cerca de 0,3 página em 1366x768). |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Regular | As mensagens são parcialmente claras, mas é preciso procurar os campos com erro. | Após enviar, a caixa vermelha no topo (fora da vista) mostrou: 'Preencha todos os campos', 'Valor solicitado deve ser maior que 0' e 'E-mail inválido'. A mensagem genérica não diz qual campo está vazio. Os campos nome, e-mail e valor não receberam destaque visual. As mensagens só sumiram ao reenviar. Idêntico nas duas abas. |
| 10. Ajuda e documentação | Regular | A orientação disponível se resume aos placeholders; não há orientação para depois do envio. | Não encontrei instruções, ajuda ou link na página, só os exemplos nos campos. Após o envio, o ofício termina com 'Encaminhe-se ao Serviço Financeiro', sem explicar ao usuário se deve imprimir, enviar ou aguardar. |

Dificuldades na execução: a caixa de erro ficou fora da vista após o envio e exigiu rolagem manual. O Voltar do navegador saiu para about:blank. 'Nova solicitação' e a reabertura da URL descartaram os dados, então não foi possível corrigir um pedido já enviado. Na reabertura da URL, a troca para ALUNOS mostrou o formulário vazio.

Artefatos em `demos/runs/batch/glm/run38/tdd/_harness/cua-nielsen-opus55-20261013T181944Z/`:
`resultado.json`, `relatorio.md`, `api-usage.jsonl`,
`history.json`, `judge.json`, `capturas.json`, `screenshots/`, `prompt.md`,
`model.json` e `executar.py`.

### `glm/run19/tdd`

O judge aceitou a avaliação e considerou as notas sustentadas pelo percurso e pelas
capturas. Registrou três desvios menores: não houve uso de Shift+Tab, alguns campos foram
preenchidos pela ferramenta `input`, e não só pelo teclado, e a afirmação de que a cor da
aba ativa variou entre azul escuro e turquesa não aparece com clareza nas capturas.

Notas, justificativas e evidências transcritas da saída do CUA:

| Heurística | Nota | Justificativa | Evidência (ação e resultado observado) |
|---|---|---|---|
| 1. Visibilidade do estado do sistema | Bom | Aba ativa, formatação e retorno do envio aparecem com clareza, mas o retorno de erro fica desatualizado. | A aba ativa fica destacada em cor forte e a inativa em cinza claro nas duas abas. Ao sair dos campos, valor 150000 virou R$ 1.500,00, data 01021980 virou 01/02/1980, CEP virou 05508-090 e CPF virou 529.982.247-25. O envio válido mostrou o título 'Solicitação registrada'. Depois que corrigi os campos, as mensagens de erro continuaram no topo até o reenvio. Foi igual em ALUNOS e DOCENTES. |
| 2. Correspondência entre o sistema e o mundo real | Regular | Termos e formatos são brasileiros, mas o ofício contradiz o estado real e há rótulos enganosos. | Os formatos R$, dd/mm/aaaa, CEP e CPF seguem o padrão brasileiro, e os termos são institucionais (N. USP, CCP, banca). A tela diz 'Solicitação registrada', mas o ofício afirma 'A CCP-Matemática Aplicada aprovou na data de hoje' e termina com 'Encaminhe-se ao Serviço Financeiro', o que é confuso para quem apenas fez o pedido. O rótulo do CPF pede 'separados por pontos e traço', mas a máscara já insere a pontuação. O exemplo de período é textual ('10 a 15 de julho de 2024'). Foi igual nas duas abas. |
| 3. Controle e liberdade do usuário | Ruim | Trocar de aba preserva os dados, mas não há como voltar da confirmação; corrigir o pedido exige refazer tudo. | Os dados foram preservados nas trocas ALUNOS→DOCENTES→ALUNOS e DOCENTES→ALUNOS→DOCENTES. A confirmação não tem botão voltar ou editar (rolei a tela e não encontrei nenhum elemento interativo), e a URL continua '/'. O voltar do navegador levou a about:blank e saiu da aplicação. Ao reabrir a URL, o formulário veio vazio e os dados se perderam. Aconteceu nas duas abas. |
| 4. Consistência e padrões | Bom | Blocos, máscaras, mensagens e confirmação se repetem entre as abas, com pequenas variações visuais. | As duas abas têm os mesmos três blocos, o botão 'Enviar solicitação', as mesmas três mensagens de erro e o mesmo ofício. Diferenças observadas: DOCENTES não tem NÍVEL/TIPO e o E-MAIL fica ao lado do EVENTO; o exemplo do nome é 'Maria da Silva' em ALUNOS e 'João da Silva' em DOCENTES; a cor da aba ativa variou entre azul escuro e turquesa ao longo da sessão. |
| 5. Prevenção de erros | Regular | Máscaras e selects ajudam, mas não há validação antes do envio e os exemplos se confundem com dados. | As máscaras formataram valor, data, CEP e CPF, e os selects limitam as opções. Não houve aviso ao sair do campo com e-mail 'joao' nem com valor 0; tudo só apareceu depois de enviar. Os placeholders em cinza parecem dados preenchidos; em DOCENTES, o nome vazio mostra 'João da Silva', exatamente o dado digitado, o que dificulta perceber o campo vazio. Foi igual nas duas abas. |
| 6. Reconhecimento em vez de memorização | Bom | Os rótulos ficam sempre visíveis acima dos campos, mas os exemplos de formato somem ao digitar. | Os rótulos em caixa alta continuaram visíveis depois do preenchimento. O formato esperado aparece só no placeholder, que desaparece ao digitar. O exemplo do período não indica o formato numérico. Foi igual nas duas abas. |
| 7. Flexibilidade e eficiência de uso | Excelente | Preenchi tudo pelo teclado, com o Tab em ordem lógica e sem digitar pontuação. | Nas duas abas, o Tab seguiu a ordem visual, linha a linha, e os selects aceitaram a letra inicial ('m' selecionou Mestrado, 'p' selecionou Participação em evento e Pôster). Digitei só dígitos em valor, data, CEP e CPF, e eles foram formatados automaticamente. |
| 8. Estética e design minimalista | Bom | O formulário é compacto e bem agrupado, mas os erros deslocam o botão e os placeholders poluem a leitura. | Em 1366x768 o formulário inteiro coube na tela sem rolagem, nos três blocos titulados e sem distrações. Após o envio com erro, as mensagens empurraram o botão Enviar para baixo da dobra. Os placeholders cinza com aparência de dados atrapalham a leitura. Foi igual nas duas abas. |
| 9. Ajuda para reconhecer, diagnosticar e corrigir erros | Regular | As mensagens dizem que há erro, mas não localizam todos os campos nem indicam como corrigir. | Ao enviar com nome vazio, e-mail 'joao' e valor 0, apareceram no topo, em vermelho: 'Preencha todos os campos', 'Valor solicitado deve ser maior que 0' e 'E-mail inválido'. Não houve borda ou destaque nos campos, e a primeira mensagem não diz qual campo falta. O nome vazio parecia preenchido por causa do placeholder. As mensagens não sumiram ao corrigir. Foi igual nas duas abas. |
| 10. Ajuda e documentação | Regular | Só é possível preencher pelos rótulos e exemplos; não há orientação sobre regras nem sobre o que fazer depois do envio. | Procurei ajuda na página e não encontrei texto de instrução, link ou ícone. A confirmação não explica os próximos passos ao solicitante nem oferece impressão, protocolo ou edição; há apenas o ofício. Foi igual nas duas abas. |

Dificuldades na execução: os placeholders parecidos com dados exigiram atenção para saber se um campo estava vazio. Depois dos erros, o botão Enviar ficou parcialmente fora da tela. Nas duas abas, a tentativa de voltar da confirmação para corrigir o pedido saiu da aplicação; para testar DOCENTES, reabri a URL e comecei um preenchimento vazio. O percurso foi concluído em ALUNOS e DOCENTES na mesma sessão do navegador.

Artefatos em `demos/runs/batch/glm/run19/tdd/_harness/cua-nielsen-opus55-20261013T192131Z/`:
`resultado.json`, `relatorio.md`, `api-usage.jsonl`,
`history.json`, `judge.json`, `capturas.json`, `screenshots/`, `prompt.md`,
`model.json` e `executar.py`.
