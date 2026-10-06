Você é um usuário testando a aplicação web hospedada em http://localhost:46369.

Execute exatamente esta ação:

Abrir a página inicial e avaliar as dez heurísticas de Nielsen em uma única sessão.
Executar todo o percurso abaixo antes de devolver as notas, sem encerrar o navegador
entre as heurísticas ou as abas. Usar área da página de 1366 × 768 e zoom de 100%;
registrar no relatório se não for possível usar essas dimensões.
Interagir pela interface, sem consultar código, testes ou avaliações de outra pessoa.

## Percurso

1. Reconhecer a tela: identificar aba ativa, três blocos e botão de envio. Observar
   legibilidade, agrupamento, rótulos, exemplos e orientações disponíveis.
2. Preencher ALUNOS com os dados abaixo. Usar Tab e Shift+Tab para navegar e o teclado
   para preencher. Digitar só os dígitos em valor, CPF, CEP e data; observar a formatação
   ao sair dos campos. Trocar para DOCENTES e voltar, conferindo a preservação dos dados.
3. Provocar erros: apagar o nome, trocar o e-mail por `joao` e o valor por `0`. Enviar.
   Observar se fica visualmente claro o que aconteceu, onde estão os erros e como
   corrigi-los. Procurar ajuda na própria página se houver dúvida.
4. Restaurar os três valores e enviar. Conferir os demais dados preservados, a clareza
   da confirmação e a leitura do ofício. Tentar voltar ao formulário para corrigir o
   pedido; registrar o caminho e eventuais perdas.
5. Na mesma sessão do navegador, abrir novamente a URL inicial para começar um
   preenchimento vazio em DOCENTES. Repetir os passos 2 a 4 nessa aba, trocando para
   ALUNOS e voltando quando necessário. Comparar a organização e o comportamento das abas.
6. Registrar uma nota por heurística, com justificativa curta e evidência observada
   durante o percurso. Não encerrar após avaliar apenas a primeira aba ou heurística.

## Dados fictícios comuns às duas abas

| Campo | Valor a digitar ou selecionar |
|---|---|
| NOME COMPLETO - SEM ABREVIAR | João da Silva |
| N. USP | 7654321 |
| PROGRAMA | Matemática Aplicada |
| NÍVEL (somente ALUNOS) | Mestrado |
| TIPO DE AUXÍLIO (somente ALUNOS) | Participação em evento |
| E-MAIL | joao.souza@usp.br |
| NOME DO EVENTO / BANCA DE EXAME OU DEFESA | Congresso Brasileiro de Matemática |
| PERÍODO DO EVENTO, EXAME OU DEFESA | 10/03/2026 a 14/03/2026 |
| CIDADE DO EVENTO, EXAME OU DEFESA | Campinas |
| ESTADO DO EVENTO, EXAME OU DEFESA | SP |
| PAÍS DO EVENTO, EXAME OU DEFESA | Brasil |
| LINK DO EVENTO, EXAME OU DEFESA | https://exemplo.usp.br/evento |
| VALOR SOLICITADO (R$) | 150000 |
| DETALHAMENTO DO PEDIDO | Passagem aérea e hospedagem durante o evento. |
| IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO? | Pôster |
| DATA DE NASCIMENTO | 01021980 |
| LOGRADOURO | Rua do Matão |
| NÚMERO | 1010 |
| COMPLEMENTO | Bloco A |
| BAIRRO | Butantã |
| CEP | 05508090 |
| CIDADE | São Paulo |
| ESTADO | SP |
| CPF (SEPARADOS POR PONTOS E TRAÇO) | 52998224725 |
| RG / RNM (SEPARADOS POR PONTOS E TRAÇO) | 12.345.678-9 |
| NOME DO BANCO | Banco do Brasil |
| NÚMERO DA AGÊNCIA | 1234 |
| NÚMERO DA CONTA | 56789-0 |

E verifique se este resultado acontece na tela:

Relatório qualitativo com as dez heurísticas abaixo. As notas tratam da experiência de uso; não repetir a pontuação dos testes Cypress.

| # | Heurística | O que observar |
|---|---|---|
| 1 | Visibilidade do estado do sistema | Aba ativa, retorno do envio e formatação ao sair dos campos. |
| 2 | Correspondência entre o sistema e o mundo real | Termos, formatos brasileiros e compreensão do ofício. |
| 3 | Controle e liberdade do usuário | Trocar de aba, corrigir erros e voltar da confirmação sem perder dados. |
| 4 | Consistência e padrões | Organização, aparência e comportamento coerentes entre as duas abas. |
| 5 | Prevenção de erros | Máscaras, exemplos e seleções que orientam antes do envio. |
| 6 | Reconhecimento em vez de memorização | Rótulos visíveis após digitar e formato esperado disponível na tela. |
| 7 | Flexibilidade e eficiência de uso | Preenchimento pelo teclado, ordem do Tab e digitação sem pontuação manual. |
| 8 | Estética e design minimalista | Formulário inteiro visível sem rolagem, agrupamento, espaçamento e ausência de distrações. |
| 9 | Ajuda para reconhecer, diagnosticar e corrigir erros | Mensagens claras, campos localizáveis e orientação para corrigir os erros. |
| 10 | Ajuda e documentação | Orientações fáceis de encontrar e suficientes para preencher e saber o que fazer após enviar. |

Aplicar esta escala ao aspecto observado em cada heurística:

| Nota | Evidência observável |
|---|---|
| Péssimo | O problema impede concluir a tarefa, sem caminho claro para continuar. |
| Ruim | Só é possível avançar com muita tentativa, confusão ou retrabalho. |
| Regular | É possível concluir, mas é preciso procurar, interpretar ou repetir ações desnecessárias. |
| Bom | O uso é claro e previsível, com pequenas dificuldades que pouco atrapalham. |
| Excelente | O uso é claro e fluido, sem dificuldade observada naquele aspecto durante o percurso. |

Todas as dez heurísticas se aplicam: não usar N/A. Ajuda não exige um manual separado;
julgar se as orientações disponíveis são suficientes. Não inventar evidências ou notas.

No campo `evidencia`, devolver a tabela completa, com dez linhas e as colunas
`Heurística | Nota | Justificativa | Evidência (ação e resultado observado)`.
Cada nota considera as duas abas; identificar na evidência quando elas se comportarem
de forma diferente. Registrar também as dimensões usadas e dificuldades na execução.

Neste critério, `passou` indica exclusivamente se a avaliação foi concluída com as dez
notas fundamentadas, não se a aplicação tem boa usabilidade. Se a sessão não permitir
concluir o percurso, devolver `passou = false` e explicar em `evidencia` o que ficou
pendente, preservando os resultados já observados para retomar o piloto.

Aja como um usuário real: clique, digite, observe. Julgue apenas pelo que observou na
interface durante esta sessão, não pelo que você espera que a aplicação faça.

Devolva `passou` e `evidencia`, seguindo o formato pedido no resultado esperado.
Se não houver formato específico, use uma evidência curta do que viu.
