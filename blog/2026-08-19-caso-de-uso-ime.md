---
slug: caso-de-uso-ime
title: "O alvo do pipeline: auxílio financeiro do IME"
authors: [eduardo]
tags: [tcc, planejamento]
---

O v3 gerou uma lista de tarefas em HTML/CSS/JS puro. Isso serviu para provar que o
encanamento funciona — spec-writer, coder, CUA, gate humano, `RUN.log` com custo e tokens —
mas não serve como alvo do experimento.

Uma TODO list é provavelmente o app mais memorizado do pré-treino de qualquer LLM.
Quando o pipeline acerta, eu não sei se ele entendeu o requisito ou se o modelo já sabia a
resposta antes de ler. Preciso de um sistema real e de nicho. Achei um dentro do próprio IME.

<!-- truncate -->

## O fluxo manual de hoje

A Pós-Graduação do IME processa pedidos de auxílio financeiro (participação em evento,
banca de exame ou defesa) mais ou menos assim:

1. O solicitante preenche um Google Form — três seções, cerca de 25 campos
2. Alguém lê as respostas e **copia à mão** para um template
3. O template preenchido vira dois documentos: um ofício à CCP e ao Serviço Financeiro, e
   um recibo CAPES (Anexo XIII.a, Modelo "A")

Existem duas variantes do template, uma para **alunos** e uma para **docentes**.

O passo 2 é o alvo. É trabalho de transcrição, feito por uma pessoa, entre um formulário e
um documento cujos campos têm quase o mesmo nome.

## Por que é um alvo melhor que a TODO list

| | TODO list (v3) | Auxílio financeiro |
|--|--|--|
| Memorizado no pré-treino | quase certamente | improvável |
| Validação de campo | nenhuma | CPF e RG com pontos e traço, CEP, N. USP numérico, valor em real vs. dólar |
| Saída verificável | estado na tela | um documento preenchido, campo por campo |
| Requisitos incrementais | inventados por mim | as duas variantes já existem |

O último ponto é o que mais me interessa: os requisitos não são meus. Eles vêm de um
formulário e de um template que já estavam em uso antes de eu olhar.

## O mapeamento não é 1:1 (e isso é bom)

Eu tinha anotado que os placeholders do template batiam 1:1 com os campos do formulário.
Abri os arquivos e não batem. São três grupos:

**Só no formulário** — `VALOR SOLICITADO`, `DETALHAMENTO DO PEDIDO`,
"Irá apresentar trabalho no evento?", documentos comprobatórios. Nada disso aparece no
documento final: é insumo da decisão, não do texto.

**Nos dois** — identificação e endereço, com o nome praticamente igual dos dois lados:
nome completo, N. USP, e-mail, programa, dados do evento, logradouro, número, complemento,
bairro, CEP, cidade, estado, data de nascimento, CPF, RG/RNM, banco, agência, conta.

**Só no template** — `<<NÚMERO DO PROCESSO>>`, `<<COORDENADOR DO PROGRAMA>>`,
`<<TIPO DE AUXÍLIO>>`, `<<NÍVEL>>`, o valor aprovado (que no recibo é um `R$` em branco) e
a "Descrição da verba aprovada", que no template é uma linha pontilhada.

O terceiro grupo é a descoberta. Entre o formulário e o documento existe uma **etapa de
decisão**: o valor solicitado não é o valor aprovado, e o número do processo só existe
depois que a CCP aprova. Não é falha do fluxo, é o fluxo.

Para o experimento isso melhora o requisito. Ele deixa de ser "renderize um formulário" e
passa a ser "formulário → decisão → documento", com um estado no meio que o sistema precisa
guardar.

## As inconsistências do template são parte do requisito

Comparando as duas variantes, o template de docentes tem coisas que a versão de alunos não tem:

- `[Tipo de Auxílio)` — abre colchete, fecha parêntese
- `CCP-XXX` chumbado no texto, onde a versão de alunos usa `<<PROGRAMA>>`
- `(número do processo)` e `(Coordenador do programa)` entre parênteses, enquanto o resto do
  documento usa `<<MAIÚSCULAS>>`
- o formulário chama o campo de `NOME DO EVENTO / BANCA DE EXAME OU DEFESA`, mas o recibo
  só fala em `<<NOME DO EVENTO>>`

A tentação é normalizar tudo isso antes de escrever o requisito. Não vou. Um LLM tende a
"consertar" essas inconsistências silenciosamente, e consertar sem pedir **é** divergência
semântica quando o requisito fixa o texto visível. Já aprendi no v3 que rótulo exato é
contrato testável: `requisitos.md` fixa o texto, o critério de aceitação repete, e o CUA
procura aquilo na tela. Um template torto é um teste melhor do que um template limpo.

## As duas variantes dão manutenção de graça

O plano é implementar a variante de alunos primeiro e a de docentes depois, como
**manutenção** da primeira — que é exatamente o modo que o harness final precisa ter.

A diferença entre as duas é pequena e concreta: a profissão é fixa e diferente
("Estudante de Pós-Graduação" vs. "Docente"), `<<NÍVEL>>` só aparece na versão de alunos, e
o campo de evento cobre também banca de exame ou defesa na versão de docentes.

Isso dá uma medida de regressão que não precisa ser inventada: implementar docentes não
pode quebrar alunos.

## O que é pytest e o que só o CUA pega

| Camada | O que verifica |
|--------|----------------|
| **pytest** | validação de campo (CPF e RG formatados, CEP, N. USP numérico, obrigatoriedade), substituição de placeholder, campo ausente, os valores fixos de cada variante |
| **CUA** | as três seções na ordem, campo obrigatório barrando o envio, mensagem de erro aparecendo na tela, o documento gerado abrindo com cada valor no lugar certo |

A fronteira é essa: o pytest vê a função de substituição; o CUA vê se dá para chegar até ela
pela tela. Um sistema que monta o documento corretamente mas cujo formulário não deixa
enviar passa no pytest e falha no CUA. É o tipo de divergência que o TCC quer medir.

## Ressalvas

O formulário que tenho em mãos é o de **docentes**. A existência de um campo de nível na
variante de alunos eu inferi do placeholder `<<NÍVEL>>` no template, não do formulário.
Antes de escrever os requisitos preciso do formulário de alunos também.

## Próximos passos

- [ ] Escrever os N requisitos a partir do formulário, começando pela variante de alunos
- [ ] Escrever os critérios de aceitação à mão, fora dos dois pipelines — é a régua nova da
      [metodologia](/docs/metodologia)
- [ ] Decidir o formato do documento gerado: `.docx` ou HTML imprimível
