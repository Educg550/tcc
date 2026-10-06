---
slug: resultados-nielsen
title: "Resultados da avaliação Nielsen"
authors: [eduardo]
tags: [tcc, experimento]
---

As notas de cada finalista nas dez heurísticas de Nielsen, com as minhas e as do CUA lado a
lado. O roteiro, a escala e as heurísticas estão no [post das finalistas](/blog/finalistas-nielsen).

<!-- truncate -->

## Quadro geral

Heurísticas: 1 visibilidade do estado do sistema, 2 correspondência com o mundo real,
3 controle e liberdade, 4 consistência e padrões, 5 prevenção de erros, 6 reconhecimento
em vez de memorização, 7 flexibilidade e eficiência, 8 estética e design minimalista,
9 diagnóstico e correção de erros, 10 ajuda e documentação.

| Run | Avaliador | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `deepseek/run9/baseline` | CUA | Bom | Bom | Ruim | Excelente | Bom | Bom | Bom | Excelente | Ruim | Ruim |
| `deepseek/run9/baseline` | Humano | — | — | — | — | — | — | — | — | — | — |

## `deepseek/run9/baseline`

| | |
|---|---|
| Grupo | Baseline |
| Modelo gerador | DeepSeek V4.1 Flash |
| Custo de gerar | US$ 0,0079 |
| Cypress | 12/12 canônicos, 10/10 extras |

### CUA

| | |
|---|---|
| Modelo | `anthropic/claude-sonnet-5.5`, via OpenRouter |
| Data | 06/10/2026 |
| browser-use | 0.13.10 |
| Passos | 42, de no máximo 80 |
| Duração | 300 s |
| Tokens | 1.059.551 |
| Custo | US$ 2,33 |
| Saída | `demos/runs/batch/deepseek/run9/baseline/_harness/cua-nielsen-claude-sonnet-5.5-20261006T102811.json` e `C1.png` |

> Transcritas da saída da sessão, sem edição

1. **Visibilidade do estado do sistema: Bom.** A aba ativa tem destaque visual, a formatação aparece ao sair dos campos e a confirmação é clara. O banner de erro antigo continua na tela após a correção. *Evidência:* Ao clicar em DOCENTES/ALUNOS o formulário mudou (DOCENTES sem NÍVEL e TIPO DE AUXÍLIO). Ao dar Tab, valor virou 'R$ 1.500,00', data 01/02/1980, CEP 05508-090, CPF 529.982.247-25. Após enviar apareceu 'Solicitação registrada' com o ofício. Depois de restaurar os campos, o banner amarelo anterior seguia visível (ALUNOS e DOCENTES).
2. **Correspondência entre o sistema e o mundo real: Bom.** Termos e formatos brasileiros (R$, CPF, CEP, dd/mm/aaaa, ofício) são familiares. O texto do ofício tem estranhezas. *Evidência:* Valor, CPF, CEP e data foram exibidos em formato brasileiro, e o ofício trouxe os dados corretos nas duas abas. O ofício diz 'aprovou na data de hoje' para um pedido recém-enviado, tem cabeçalho USP duplicado e Assunto 'Verba do programa' em DOCENTES, o que confunde um pouco.
3. **Controle e liberdade do usuário: Ruim.** Alternar abas preserva os dados, mas a confirmação não tem caminho de volta e o botão Voltar do navegador descarta tudo. *Evidência:* ALUNOS→DOCENTES→ALUNOS manteve todos os dados (a outra aba aparece vazia, sem aviso). Corrigir erros foi possível sem perda. Na confirmação não há botões nem links interativos; o Voltar do navegador levou a about:blank e os dados foram perdidos (ALUNOS e DOCENTES).
4. **Consistência e padrões: Excelente.** As duas abas têm mesmo layout, blocos, máscaras, banner de erro e confirmação. A única diferença são os campos NÍVEL e TIPO DE AUXÍLIO só em ALUNOS, o que é esperado. *Evidência:* Ordem dos campos e Tab iguais; mesmas máscaras (valor, data, CEP, CPF); mesmo banner de erros e mesma confirmação em ambas.
5. **Prevenção de erros: Bom.** Máscaras, selects e placeholders com exemplo ajudam. Não há validação antes do envio. *Evidência:* NÍVEL, TIPO DE AUXÍLIO e apresentação são seleções fechadas; valor, data, CEP e CPF aceitam só dígitos e se formatam. O valor '0' virou 'R$ 0,00' e o e-mail 'joao' foi aceito sem aviso até o envio.
6. **Reconhecimento em vez de memorização: Bom.** Os rótulos permanecem visíveis depois de digitar. Os exemplos em placeholder somem ao digitar. *Evidência:* Os rótulos ficaram visíveis com os campos preenchidos nas duas abas e os placeholders mostravam exemplos de formato antes de digitar. Um campo apagado (nome) voltou a mostrar só o placeholder, sem indicação de que era obrigatório.
7. **Flexibilidade e eficiência de uso: Bom.** Todo o preenchimento foi possível só pelo teclado, com Tab em ordem lógica e sem digitar pontuação em valor, data, CEP e CPF. Período, RG e conta exigem pontuação manual. *Evidência:* Preenchi ALUNOS por Tab/Shift+Tab e DOCENTES por Tab. Selects aceitaram digitação ('Mestrado', 'Participação em evento', 'Pôster'). Digitei 150000, 01021980, 05508090 e 52998224725 e a pontuação veio automaticamente; período, RG ('12.345.678-9') e conta ('56789-0') foram digitados com pontuação.
8. **Estética e design minimalista: Excelente.** O formulário inteiro cabe sem rolagem, com três blocos bem agrupados e sem distrações. *Evidência:* Em ~1400×850 vi os três blocos (SOLICITANTE E EVENTO, ENDEREÇO DO SOLICITANTE, INFORMAÇÕES PARA PAGAMENTO) e o botão 'Enviar solicitação' sem rolar, nas duas abas. Só o cabeçalho duplicado do ofício destoa.
9. **Ajuda para reconhecer, diagnosticar e corrigir erros: Ruim.** O banner único no topo não localiza os campos e o aviso de campo vazio é genérico. *Evidência:* Com nome apagado, e-mail 'joao' e valor 0, o banner listou 'Preencha todos os campos', 'Valor solicitado deve ser maior que 0' e 'E-mail inválido'. Nenhum campo foi destacado, e 'Preencher todos os campos' não indica qual está vazio (o nome só mostrava o placeholder). O resultado foi idêntico em ALUNOS e DOCENTES.
10. **Ajuda e documentação: Ruim.** Não encontrei ajuda na página, nem para preencher nem para saber o que fazer após o envio. *Evidência:* Em todo o percurso só vi placeholders de exemplo. Não havia link de ajuda, instrução, legenda de campos obrigatórios ou orientação na página. A confirmação não explica o próximo passo nem como corrigir o pedido enviado.

Dificuldades que o CUA relatou na execução:

- A digitação teve ruído: o nome ficou como 'J' e foi completado depois, e ao restaurar o
  e-mail o 'joao' ficou anexado ('joaojoao.souza@usp.br'), corrigido com Ctrl+A.
- Na aba DOCENTES, os primeiros campos foram preenchidos por clique e digitação direta, e
  o restante por Tab.
- Ao reabrir a URL numa aba nova, a página abriu em ALUNOS, vazia, e foi preciso clicar em
  DOCENTES.
- O atributo `selected` das abas aparece como `false` no DOM, embora a aba ativa tenha
  destaque visual claro.

### Humano

| | |
|---|---|
| Avaliador | Eduardo |
| Data | — |
| Duração | — |
| Navegador | — |

1. **Visibilidade do estado do sistema:** —
2. **Correspondência entre o sistema e o mundo real:** —
3. **Controle e liberdade do usuário:** —
4. **Consistência e padrões:** —
5. **Prevenção de erros:** —
6. **Reconhecimento em vez de memorização:** —
7. **Flexibilidade e eficiência de uso:** —
8. **Estética e design minimalista:** —
9. **Ajuda para reconhecer, diagnosticar e corrigir erros:** —
10. **Ajuda e documentação:** —
