# Roteiro 

| # | Heurística | O que observar no formulário |
|---:|---|---|
| 1 | Visibilidade do estado do sistema | Dá para saber em que aba se está, se o envio deu certo e o que cada campo formatado mostra ao sair dele. |
| 2 | Correspondência entre o sistema e o mundo real | Formatos e termos de quem pede auxílio: `R$ 1.500,00`, `dd/mm/aaaa`, CPF pontuado. O ofício se lê como o documento que vai para a CCP. |
| 3 | Controle e liberdade do usuário | Trocar de aba sem perder o que foi digitado, corrigir um erro sem redigitar o resto, voltar da confirmação se algo saiu errado. |
| 4 | Consistência e padrões | As duas abas com o mesmo arranjo e o mesmo comportamento; campos, botões e mensagens com a mesma aparência na página toda. |
| 5 | Prevenção de erros | Máscaras, placeholders com exemplo e seleções nas opções fechadas evitam o erro antes do envio. |
| 6 | Reconhecimento em vez de memorização | O rótulo continua visível depois de digitar, e o formato esperado aparece no próprio campo. |
| 7 | Flexibilidade e eficiência de uso | Dá para preencher tudo pelo teclado: a ordem do Tab segue a leitura e o usuário digita só os dígitos. |
| 8 | Estética e design minimalista | A página cabe em uma tela, os três blocos se distinguem pelo agrupamento e pelo espaçamento, e nada ali deixa de servir ao preenchimento. |
| 9 | Ajuda para reconhecer, diagnosticar e corrigir erros | A mensagem diz o que está errado e permite achar o campo, e aparecem todas as que se aplicam. |
| 10 | Ajuda e documentação | As orientações disponíveis são fáceis de encontrar e suficientes para esclarecer dúvidas sobre o preenchimento e o que fazer após o envio. |

Cada finalista recebe, em cada uma das dez heurísticas, uma nota na escala
**Péssimo / Ruim / Regular / Bom / Excelente**, com justificativa. As minhas notas e as
do CUA ficam separadas, para que as divergências entre as duas avaliações apareçam.

## Roteiro comum — Eduardo e CUA

Aplicar às duas finalistas, em sessões novas. Usar os dados fictícios de `PADRAO` em `demos/avaliacao/campos.js` nas
duas abas. Interagir pela interface e registrar as notas sem consultar as do outro avaliador.

1. **Reconhecer a tela.** Identificar a aba ativa, os três blocos e o botão de envio.
   Observar legibilidade, agrupamento, rótulos, exemplos e orientações disponíveis.
2. **Preencher ALUNOS.** Usar Tab e Shift+Tab para navegar e o teclado para preencher.
   Digitar só os dígitos em valor, CPF, CEP e data; observar a formatação ao sair dos
   campos. Trocar para DOCENTES e voltar: conferir se os dados foram preservados.
3. **Provocar erros.** Apagar o nome, trocar o e-mail por `joao` e o valor por `0`.
   Enviar. Observar se fica visualmente claro o que aconteceu, onde estão os erros e como corrigi-los;
   procurar ajuda na própria página se houver dúvida.
4. **Corrigir e enviar.** Restaurar os três valores e enviar novamente. Conferir a
   preservação dos demais dados, a clareza da confirmação e a leitura do ofício.
   Tentar voltar ao formulário para corrigir o pedido; registrar o caminho e eventuais perdas.
5. **Repetir em DOCENTES.** Na mesma sessão, reabrir a URL inicial para começar um
   preenchimento vazio nessa aba. Repetir o preenchimento, a troca de abas, os erros,
   a correção e o envio. Comparar a organização e o comportamento das abas.
6. **Registrar as dez notas.** Para cada heurística da tabela acima, anotar
   **nota + justificativa curta + evidência** (ação e resultado observado; captura quando útil).

A escala abaixo é a régua comum deste estudo, aplicada ao aspecto observado em cada
heurística; não é uma escala publicada por Nielsen.

| Nota | Evidência observável |
|---|---|
| Péssimo | O problema impede concluir a tarefa, sem caminho claro para continuar. |
| Ruim | Só é possível avançar com muita tentativa, confusão ou retrabalho. |
| Regular | É possível concluir, mas é preciso procurar, interpretar ou repetir ações desnecessárias. |
| Bom | O uso é claro e previsível, com pequenas dificuldades que pouco atrapalham. |
| Excelente | O uso é claro e fluido, sem dificuldade observada naquele aspecto durante o percurso. |

## Run 35 baseline:

### Heurísticas

1. Regular. o formulário separa corretamente as secoes e mostra um erro "Preencha todos os campos" de forma visível. Porém, não é trivial saber qual campo está vazio quando o erro aparece, pois ele não é explicitamente indicado. No entanto, a validação de email, CPF, CEP e valor funcionam ok
2. Excelente, todos os campos autoformatantes funcionam adequadamente.
3. Regular, o estado persiste ao trocar de aba no meio do preenchimento, mas reiniciar a página reseta o progresso (requisito não funcional).
4. Bom, mas o layout não é consistente no alinhamento de inputs
5. Excelente, tem placeholders e choices sempre que possível
6. Excelente
7. Excelente
8. Regular. A página tem algumas inconsistências entre alinhamento de inputs (caixas de texto desalinhadas sem motivo), mas mostra adequadamente os inputs em seções separadas em ambas abas (Alunos/Docentes)
9. Ruim. Como dito antes, a mensagem não mostra o campo que está causando o erro explicitamente.
10. Excelente. As instruções são passadas corretamente no ofício após enviar o formulário

Meu output:

```
Interessada(o): eawfwe - 12312
E-mail: fewafwe@gmail.com
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: fewaf - Doutorado

A CCP-fewaf aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: 1fewaf
Período: fawevaew
Local: ewavwev - avewve - wavewva
Link do evento: ewvewvew
Apresentação de trabalho: Apresentação oral
Valor solicitado: R$ 123,12
Detalhamento: wevaewvewveaw

Endereço da(o) interessada(o)
aawef, 12
Complemento: ewfaawef
CEP: 05609-102
waefaew, safs - dfasfdsf

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 529.982.247-25
RG / RNM: 423432524234
Banco: fewaf
Agência: 233412
Conta: 3242342

Encaminhe-se ao Serviço Financeiro para providências.
```

## Run 44 baseline:

### Heurísticas

1. Regular, mesma questão do outro, o formulário separa corretamente as secoes e mostra um erro "Preencha todos os campos" de forma visível. Porém, não é trivial saber qual campo está vazio quando o erro aparece, pois ele não é explicitamente indicado. No entanto, a validação de email, CPF, CEP e valor funcionam ok
2. Excelente, tudo se traduz ao digitar conforme requisito
3. Excelente, o progresso se mantém entre abas do formulario e ao recarregar a página também
4. Excelente, ambos formulários tem a mesma aparência, inputs consistentes e separados em seções
5. Excelente, há placeholders e choices sempre que possível
6. Excelente
7. Excelente
8. Regular, é necessário scrollar a tela pra baixo pra ver o botão de "Enviar solicitação"
9. Ruim, Como dito antes, a mensagem não mostra o campo que está causando o erro explicitamente.
10. Excelente. Instruções são passadas corretamente após o envio do formulário

Output:

```
Interessada(o): wfwef - 123214
E-mail: fewafaewfewaf@gmail.com
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: fewafwe - Mestrado

A CCP-fewafwe aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: fewaf
Período: f3fwef
Local: ewafewf - fewfwaefwef - fwefwe
Link do evento: fewfwae
Apresentação de trabalho: Apresentação oral
Valor solicitado: R$ 1.500,00
Detalhamento: ewfaawefewfew

Endereço da(o) interessada(o)
fewafe, f3wfaw
Complemento: ewfafe
CEP: 01501-323
fewafwf, fewfwe - fewfwe

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 529.982.247-25
RG / RNM: 59834598342
Banco: eafaewfewa
Agência: 123
Conta: 123123

Encaminhe-se ao Serviço Financeiro para providências.
```