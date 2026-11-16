---
slug: runs-com-licoes-prejanus-back
title: "Quatro novas runs com lições das entregas anteriores"
authors: [eduardo]
tags: [tcc, experimento]
---

Rodei uma entrega nova de cada condição do PreJanus-back, acrescentando o mesmo
bloco de lições das execuções anteriores à entrada. As quatro ficaram abaixo das
anteriores nos testes reservados. A baseline passou em 51/85, o TDD em 0/85, o
rework em 0/85 e o TDD com revisão em 49/85. A rodada custou US$ 5,80.

<!-- truncate -->

## O que acrescentei à entrada

A rodada segue a sugestão dos orientadores registrada na
[análise das entregas](/blog/analise-entregas-prejanus-back). Cada implementação
começou do zero, sem receber o código das anteriores. Mantive GLM 5.3, provedor
`novita/fp8` sem fallback, contratos, skills, infraestrutura e gabarito. Os limites
continuaram em US$ 2, 3600 segundos e 40 propostas por etapa; uma chamada em
andamento pode ultrapassar o teto de custo ou de tempo.

O bloco foi o mesmo nas quatro condições, inclusive para o test-writer:

> Lições das execuções anteriores:
>
> - Confira se as funções chamadas entre módulos existem e se seus nomes e argumentos correspondem.
> - Respeite os tipos do esquema SQL fornecido, inclusive enums, nas consultas e no ORM.
> - Confira a junção entre host e caminho nas URLs de integração.
> - Preserve informações que permitam identificar a causa das falhas; não transforme erros em resultados vazios ou sucesso.
> - Quando receber falhas, investigue a causa antes de consertar o sintoma do erro. Nos testes que escrever, não descarte respostas inesperadas que expliquem uma falha

As dicas foram limitadas a cuidados derivados dos testes visíveis e dos contratos
de entrada. Os reservados não foram usados para preparar o bloco. No rework, os
161 casos visíveis continuaram disponíveis; nas outras condições, o gabarito
inteiro ficou oculto durante a geração. Executei as condições em sequência,
aplicando o gabarito completo depois de cada uma, sem correção manual nem segunda run.

## Resultados

A medida principal são todos os 85 reservados, incluindo os seis em que o
original falha. O gabarito completo tem 161 visíveis, 85 reservados e um teste
de rastreio dos requisitos, totalizando 247.

| Condição | Reservados antes | Reservados com lições | Visíveis com lições | Gabarito completo com lições | Custo |
|---|---:|---:|---:|---:|---:|
| Baseline | 62/85 | 51/85 | 86/161 | 138/247 | US$ 0,632258 |
| TDD | 49/85 | 0/85 | 1/161 | 2/247 | US$ 2,082051 |
| Rework | 59/85 | 0/85 | 1/161 | 2/247 | US$ 1,334157 |
| TDD com revisão | 63/85 | 49/85 | 81/161 | 131/247 | US$ 1,748713 |
| **Total gasto** | — | — | — | — | **US$ 5,797179** |

Os resultados anteriores são os do [resumo de 28/10](/blog/resumo-prejanus-back).
Nos 79 reservados sem divergência conhecida do original, os resultados desta
rodada foram 49, 0, 0 e 47, respectivamente.

## Duas aplicações não iniciaram

O TDD encerrou a implementação por custo. Ao carregar `app.py`, a aplicação
tentava usar `Depends(get_db)` sem definir `get_db`, provocando `NameError`.

O rework encerrou por tempo. O módulo de editais importava `CANDIDATE_SPEC` de
`src.services.mapping`, mas esse nome não estava disponível, provocando
`ImportError` na inicialização.

Ambos terminaram o gabarito com 93 falhas, 152 erros e dois aprovados. Os aprovados
foram o teste de recusa de origem CORS e o rastreio dos requisitos. Esses dois
acertos não demonstram que a aplicação estivesse funcionando.

A baseline iniciou e terminou com 138 aprovados e 109 falhas, sem erros de
preparação. O TDD com revisão também iniciou: foram 131 aprovados e 116 falhas,
sem erros de preparação. Ele encerrou a implementação por tempo. O snapshot dos
testes autorais ficou apenas na versão inicial, sem revisão registrada pelo coder;
na conferência final dos testes próprios, foram 15 aprovados, 27 falhas e 16 erros.

## Os seis casos em que o original falha

| Comportamento esperado | Baseline | TDD | Rework | TDD com revisão |
|---|---|---|---|---|
| Detalhe inclui os comentários solicitados | Falhou | Erro | Erro | Falhou |
| Aceite sem resposta permanece pendente | Falhou | Erro | Erro | Falhou |
| Envio da carta de aceite | Falhou | Falhou | Falhou | Falhou |
| Aprovação rejeita lista vazia de orientadores | Passou | Erro | Erro | Passou |
| Aprovação rejeita dois orientadores | Passou | Erro | Erro | Passou |
| PDF inclui os anexos de e-mails dos candidatos | Falhou | Falhou | Falhou | Falhou |

Baseline e TDD com revisão passaram em dois desses seis casos. Nesses
comportamentos testados, superaram o original, embora tenham acertado menos casos
no conjunto reservado. Isso não significa superioridade da aplicação inteira.

Nesta rodada, o bloco de lições não veio acompanhado de melhora na nota de
nenhuma condição. Uma run por condição, comparada a execuções anteriores, não
isola o efeito das dicas da variação entre gerações. Os erros de inicialização
também mostram que a orientação para conferir nomes entre módulos não garantiu
que isso fosse feito.

## Os padrões de falha continuam, mas a trajetória importa

Depois, comparei o código e os logs das quatro entregas com os padrões da
[análise anterior](/blog/analise-entregas-prejanus-back), sem executar novamente
as aplicações ou os testes. Alguns padrões reaparecem, mas dizer que o feedback
nunca produziu correção seria incorreto.

| Entrega | O que a análise dos artefatos mostra |
|---|---|
| Baseline | Repete a junção do OAuth sem barra e 12 falhas de formato das respostas de Forms. Um novo problema na escrita dos parâmetros das consultas SQL causa falhas em cascata. Também ganha oito casos que a baseline anterior errava, apesar da queda na nota total. |
| TDD | Os gates próprios melhoram de 33/43 para 39/43. O erro de enum da entrega anterior foi evitado. O `get_db` ausente só impede a inicialização depois da proposta final interrompida pelo custo. Os testes próprios de OAuth omitem o callback ao backend, e um helper ainda descarta respostas diferentes de 200. |
| Rework | Os visíveis melhoram de 137/161 para 155/161, e a URL do OAuth está corrigida. A última proposta, interrompida por tempo, deixa o validador de mapeamento incompatível com seus consumidores. A aplicação deixa de iniciar. |
| TDD com revisão | O ORM usa `recommender_form_ids`, mas o esquema declara `recommenders_form_ids`. A consulta falha, e o tratamento da exceção ainda usa `traceback` sem importá-lo. Os três gates completos mantêm 15 aprovados, 27 falhas e 16 erros. |

O padrão mais persistente é um defeito pequeno em caminho compartilhado provocar
muitas falhas. Contratos escolhidos pelos testes próprios também continuam
presentes: no TDD, a autorização no provedor é seguida da cobrança de uma sessão
autenticada sem enviar o callback à aplicação. Na variante com revisão, o teste
envia os parâmetros de OAuth em JSON e o endpoint exige esse corpo, enquanto o
gabarito os envia na query. A ambiguidade de parte da entrada continua relevante.

Há ainda um mecanismo importante no encerramento. O harness recolhe as edições
pendentes mesmo quando a sessão termina com erro, aplica o lote e só depois
verifica esse erro. Nesse caminho, retorna antes do gate da proposta. Assim, TDD
e rework terminaram com alterações incompletas após versões que iniciavam e
tinham passado em mais testes. Os erros finais de importação não foram devolvidos
em outra proposta para correção. Isso envolve a política de encerramento do
harness, além da consistência do código gerado.

Não apliquei o gabarito às versões intermediárias, nem reconstruí essas versões.
Os 155 visíveis do rework não permitem estimar quantos reservados ele acertaria.
A nota final continua sendo a do artefato entregue, mas esconde a melhora anterior
e a regressão no encerramento.

Na variante com revisão, há uma limitação adicional: o papel do coder permite
editar testes com justificativa, mas a mensagem compartilhada após um gate
vermelho ainda manda “Não altere os testes”. Além disso, o corte dos últimos 4000
caracteres da saída do pytest omite o nome da coluna errada que os logs completos
preservam. A estagnação dos gates é observada, mas não prova que o coder recebeu
a causa completa nem explica, sozinha, a ausência de revisão. Mantive o harness
e os resultados como foram executados.

Também não se repetiu literalmente o padrão de chamadas longas sem ação: no TDD,
a maior chamada durou 896 segundos, mas pediu uma edição. Pedir uma ferramenta
não garante que a edição tenha sido aceita; o registro não preserva todos os
argumentos necessários para reconstituir cada alteração.

Encerrei as tentativas de geração. O trabalho restante usa as evidências já
produzidas; não farei novas runs para tentar obter uma nota melhor.

## Artefatos

As quatro pastas estão em `demos/runs/caronte/`:

- `05-prejanus-back-piloto-v3-licoes-baseline-20261115-121042`
- `05-prejanus-back-piloto-v3-licoes-tdd-20261115-123705`
- `05-prejanus-back-piloto-v3-licoes-rework-20261115-134805`
- `05-prejanus-back-piloto-v3-licoes-tdd-revisao-20261115-152120`

Cada uma preserva a entrega, `_harness/RUN.log`, os logs dos gates e da aplicação,
`_harness/GABARITO.json`, `gabarito.xml`, `MANIFESTO_ENTREGA.json` e a entrada,
incluindo `entrada/licoes.md`. Conferi o bloco nas quatro entradas e os hashes das
entregas após o gabarito. Os serviços do ambiente isolado voltaram ao estado
parado anterior, com os volumes preservados. Não iniciei outra rodada.
