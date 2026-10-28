---
slug: tdd-e-revisao-dos-testes
title: "Se eu corrigir os testes depois de começar a codar, ainda é TDD?"
authors: [eduardo]
tags: [tcc, experimento, referencia]
---

> Atualização em 27/10: a run exploratória foi concluída. Registrei os números e a
> revisão feita pelo coder em [TDD com revisão dos testes: primeira run](/blog/tdd-revisao-primeira-run).

Depois das [runs refeitas](/blog/runs-refeitas-harness), revisei os testes que o
agente escreveu na última run TDD. Achei uma contradição que o coder não tinha como
resolver respeitando os requisitos: um teste exigia criar um edital como docente,
enquanto o requisito e outro teste proibiam essa operação. O harness não deixa o
coder alterar os testes. A dúvida passou a ser se devo manter essa restrição ou
permitir que ele corrija um teste errado durante a implementação. E, nessa segunda
opção, ainda posso chamar o processo de TDD?

<!-- truncate -->

## O que estou chamando de TDD

No [Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd), Kent Beck distingue uma
lista de cenários de uma suíte já implementada. O ciclo começa escolhendo um
cenário, escrevendo seu teste executável, implementando o comportamento e, se
necessário, refatorando. Depois vem o próximo cenário. Beck aponta como erro
transformar a lista inteira em testes executáveis antes de começar a implementar.

A [descrição de Martin Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
também organiza o trabalho em ciclos pequenos e destaca a refatoração. Escrever
testes antes ajuda a pensar na interface que o código deve oferecer. Isso não
garante que a primeira interpretação dessa interface esteja correta.

O meu harness faz uma adaptação: um agente escreve toda a suíte a partir do
requisito; outro implementa e recebe as falhas do pytest. Os testes ficam
congelados na passagem entre os agentes. Essa é a definição operacional do grupo
que chamei de TDD no experimento. Ela combina testes escritos antes do código com
uma separação rígida entre as etapas, e não reproduz o ciclo incremental descrito
por Beck. Preciso manter essa distinção ao discutir os resultados.

## Corrigir um teste ou facilitar a aprovação?

Minha leitura é que corrigir um teste errado durante o desenvolvimento pode ser
compatível com TDD. O critério é o comportamento exigido pelo requisito. Se o teste
usa o usuário errado na preparação, corrigir esse usuário permite verificar o que
se pretendia. Se o código deveria rejeitar uma operação e eu troco a expectativa
de rejeição por sucesso só porque é isso que o código devolve, deixei de verificar
o requisito.

Essa distinção é uma interpretação para orientar a variante do experimento, não
uma autorização irrestrita atribuída às referências. No mesmo texto, Beck critica
apagar asserções para obter aprovação e copiar a saída calculada para o valor
esperado. Uma revisão precisa ter uma razão além de deixar a suíte verde.

Permitir edições também não transforma automaticamente meu pipeline em TDD
canônico: ele ainda começará com uma suíte inteira gerada antes da implementação.
O nome da nova condição será **TDD com revisão dos testes**, preservando o nome do
grupo anterior e explicitando o que mudou.

## O que encontrei na run

A run `05-prejanus-back-piloto-v3-tdd-20261023-223904` terminou por tempo,
com 140/247 no gabarito independente. A baseline fez 186/247. Na revisão:

- O teste de permissão de mapeamentos chama a criação de edital como docente e
  exige 200 antes de verificar a proibição de criar mapeamentos. O docente deveria
  receber 403 já na criação do edital. Essa contradição apareceu nos oito gates em
  que o aplicativo iniciou.
- Os testes de OAuth mandam o retorno do login no corpo JSON. O original recebe os
  parâmetros na URL, e o código gerado implementou a interpretação dos testes.
  Os testes próprios passaram, mas cinco dos sete casos de OAuth do gabarito
  falharam. A entrada também tem uma lacuna: o texto não explicita onde mandar
  esses parâmetros, e o OpenAPI fornecido não os declara.
- Um teste exige encontrar uma versão de candidatura sem mapeamento, sem preparar
  esse cenário. Na fixture, as versões com inscrições já estão mapeadas.
- O helper de e-mail procura as chaves `messages` e `data`, mas a caixa SMTP usa
  `results`. Assim, ele interpreta uma caixa com mensagens como vazia.

Os dois últimos problemas ficaram encobertos por falhas anteriores. Também há
defeitos reais na implementação: uma consulta compara o enum do Postgres com
`VARCHAR` e falha. O helper descarta respostas HTTP de erro e devolve uma lista
vazia. No último gate, 26 das 29 falhas ou erros pararam na busca de inscrições,
antes de avaliar o comportamento pretendido. Em mapeamentos, o gabarito deu 3/27 ao
TDD e 26/27 à baseline.

Portanto, os testes incorretos impediram a convergência para uma implementação
correta e validaram um contrato incompatível, mas não posso atribuir a diferença
inteira entre os grupos ao congelamento dos testes. O próprio OAuth teve resultado
melhor no TDD que na baseline, que falhou nos sete casos.

## Uma variante para investigar

Vou preparar uma run exploratória do zero com a mesma entrada, modelo, provedor,
ambiente e gabarito. O test-writer continua separado. A mudança será permitir ao
coder editar os testes autorais quando identificar um erro, justificando a revisão
pelo requisito ou contrato disponível. Ele continua sem acesso ao gabarito ou ao
código original. Não vou fornecer os consertos encontrados nesta revisão.

O harness guardará a suíte inicial, as versões alteradas e os diffs. A justificativa
do agente será material para análise; uma instrução no prompt não comprova que a
alteração foi correta. Remoções de verificações e testes pulados também precisam
ser examinados. A configuração de execução do pytest permanece protegida, e a
nota vem dos mesmos 247 casos independentes, depois da geração.

As runs anteriores ficam preservadas. A nova condição não conta como repetição do
TDD congelado nem altera o rework: os testes visíveis recebidos pelo rework
continuam fixos. Com uma run por condição e uma nova geração de testes, uma melhora
será uma observação exploratória; não isolará o efeito da permissão de revisão.

## Custo e limites

Não há um terceiro agente. A revisão usa as chamadas do próprio coder e entra no
mesmo orçamento de implementação. As três runs TDD formais já feitas custaram
aproximadamente US$ 0,94, US$ 0,98 e US$ 2,07, com versões diferentes do harness.
Uso esses valores como referência de gasto, sem tratá-los como repetições.

Mantendo os tetos existentes, cada etapa pode gastar US$ 2 e durar até uma hora,
com 40 propostas ao gate. Como há uma etapa de testes e outra de implementação,
o teto nominal da run é US$ 4. A última chamada de cada etapa pode ultrapassar o
limite, pois a conferência acontece entre chamadas. Revisar testes pode consumir
parte desse orçamento ou evitar tentativas improdutivas; ainda não medi qual
efeito prevalece.

O controle das runs formais registrava US$ 9,34 gastos do teto agregado de US$ 12.
Restam cerca de US$ 2,66 nesse teto, o que cobre um gasto parecido com o último TDD,
mas não o pior caso das duas etapas. A execução da variante depende de fechar o
orçamento adicional antes de iniciá-la. Esta nota registra a hipótese e o desenho;
a nova run ainda não foi executada.
