---
slug: analise-entregas-prejanus-back
title: "O que o código das quatro entregas mostra"
authors: [eduardo]
tags: [tcc, experimento]
---

Li o código das quatro entregas do [resumo de 28/10](/blog/resumo-prejanus-back) e
agrupei as falhas do gabarito por causa raiz. Em todas, poucos defeitos explicam boa
parte das falhas. O TDD ficou em 140 por um erro só: declarou como texto uma coluna que
é enum no esquema, e isso derrubou cerca de 81 casos. Tirando as divergências do
original, o rework empata com a baseline nos reservados. Dos 22 casos que nenhuma
entrega passa, cerca de 19 cobram nomes que a entrada não dá ou são divergências e
instabilidade do ambiente. Os 17 arquivos vêm do prompt, e o TDD é maior quase só por
formatação e pelo ORM.

<!-- truncate -->

## Como fiz a análise

Analisei as quatro entregas válidas: baseline, TDD, rework e a variante exploratória
do TDD com revisão. Para cada uma, li o código de produção, a saída de cada gate e os
logs da aplicação durante o gabarito. Depois agrupei os casos que falham por causa
raiz, com arquivo e linha. Não rodei nenhuma aplicação nem teste de novo. A leitura
foi feita com o Claude Code (Opus 5.5), um agente por entrega. Conferi à mão os
defeitos que mais pesam e as contagens que aparecem aqui.

## Poucos defeitos explicam muitas falhas

| Entrega | Gabarito | Falhas | Divergências do original | Defeito que mais pesa | Casos |
|---|---:|---:|---:|---|---:|
| Baseline | 186 | 61 | 8 | `flatten_mapping` zera os dados mapeados | 15 |
| TDD | 140 | 107 | 12 | `form_type` declarado como texto no ORM | ~81 |
| Rework | 211 | 36 | 8 | URL do OAuth sem barra | 7 |
| TDD com revisão | 194 | 53 | 7 | contrato de `/forms` inventado | 15 |

**Baseline.** A sessão foi única e encerrou por conta própria, usando 13% do tempo e
28% do custo do orçamento. Não faltou nenhuma das 50 operações. Três defeitos somam 26 falhas:

- `routers/auth.py:58` chama `oauth.author_url`, mas a função se chama
  `authorize_url` (`oauth.py:56`). O início do login responde 500 (7 casos).
- `flatten_mapping` (`mapping_utils.py:10`) desce dentro das folhas
  `{section, field}`, que também são dicionários. Todo dado mapeado sai vazio
  (15 casos).
- As datas do edital são validadas na ordem das fases, não na ordem dos campos
  (4 casos).

Os dois primeiros só aparecem executando o código, e a baseline não executa nada.

**TDD.** `prejanus/models.py:81` declara `form_type` como `String`; no esquema
fornecido, a coluna é `form_type_enum`. Toda consulta de mapeamento falha com
`operador não existe: form_type_enum = character varying`. Como o mapeamento está no
caminho da listagem, do detalhe, da atividade, dos e-mails e dos relatórios, o erro se
espalha. Mapeamentos ficou em 3/27 e Relatórios em 1/10. Dos casos atribuídos a esse
defeito, 45 trazem o erro na mensagem. Os outros caem em cascata: o job do PDF morre, a
exceção é engolida (`reports.py:182`) e o download fica em 404.

Os testes próprios acusaram o defeito nas 10 propostas. Mesmo assim, o coder nunca
mexeu na declaração da coluna:

- Em 4 propostas, mudou só o formato do erro.
- Tentou adaptar o driver do psycopg. Nas propostas 6 e 7, chamou APIs que não
  existem e a aplicação não subiu.
- O próprio código já tinha a correção num ponto: `edicts.py:408` faz
  `cast(:ft as form_type_enum)`.

Os testes também ajudaram pouco a localizar a causa. O helper `edicts_with_submissions`
(`tests/utils.py:50`) descarta respostas diferentes de 200, e 26 das 29 falhas finais
diziam só "nenhum edital com inscricoes".

**Rework.** O módulo de OAuth junta host e recurso sem barra, e o login responde 500.
O traceback com `'8000wsusuario'` já estava na saída do primeiro gate, mas a segunda
proposta não corrigiu. A run parou por custo nessa proposta.

**TDD com revisão.** O teste próprio `test_secoes_versao_inexistente_fallback` compara
o fallback com as seções ativas. O requisito pede todas as seções do formulário. Na
primeira proposta, o código seguia o requisito e falhava nesse teste. Na terceira,
passou a filtrar por `is_active`. O coder podia revisar o teste e não revisou.
Pelo mesmo caminho, os testes próprios mandam os parâmetros do OAuth no corpo, e o
código os lê de lá.

## Rework e baseline empatam nos reservados

| Reservados | Baseline | TDD | Rework | TDD com revisão |
|---|---:|---:|---:|---:|
| Todos (85) | 62 | 49 | 59 | 63 |
| Sem divergência do original (79) | 58 | 47 | 58 | 60 |

A diferença de 59 contra 62 vem das 6 divergências. Fora delas, cada um ganha 8
casos do outro. Os 8 que o rework acerta e a baseline erra são quase cópias de testes
visíveis. Nos 8 que a baseline acerta e o rework erra, a regra está escrita no requisito
completo, que o rework não recebeu. Não encontrei constante nem id da fixture no código
do rework. O sobreajuste que existe é de forma: os títulos do PDF são os trechos que os
testes visíveis procuram.

## O que nenhuma entrega acerta

Vinte e dois casos falham nas quatro entregas:

- 10 cobram nomes que não estão no requisito, no OpenAPI nem no README:
  `summary.user_bidding` (6), `field_id` (3) e títulos exatos do PDF (1). O requisito
  fala em "interesse do usuário" e em "estatísticas de candidaturas".
- 5 são do retorno do OAuth. O gabarito manda `oauth_token` e `oauth_verifier` na query
  string; o OpenAPI não declara parâmetro nenhum nessa operação.
- 3 são divergências registradas do original, e 1 é o link de correção, em que o Forms
  responde 400 (já marcado como instável em 23/10).
- 3 dependem de formato de resposta sem schema: atividade, associação e resumo das
  recomendações.

Com essa entrada, o teto prático de um gerador fica abaixo dos 233 do original.

## Por que 17 arquivos

O número não convergiu exatamente. Nas 12 runs do piloto v3, a quantidade de arquivos
de produção vai de 12 a 18, e 17 aparece em 7 delas. A faixa é estreita por três
motivos:

- A entrada dos três grupos traz a mesma seção "Organização obrigatória da
  implementação". Ela lista as responsabilidades: aplicação, configuração, os dois
  bancos, autenticação, routers por domínio e os serviços de Forms, OAuth, e-mail e
  relatórios.
- O OpenAPI tem quatro tags (`edicts`, `submissions`, `forms` e `auth`), e todas as
  entregas criaram um router por tag.
- O modelo agrupa por domínio. O original tem 84 arquivos porque separa um arquivo por
  caso de uso e um por modelo ORM.

No TDD, os 17 arquivos aparecem já na primeira proposta e não mudam nas outras nove.

## Por que o TDD tem mais linhas

Sem os testes, o TDD tem 833 SLOC a mais que a baseline:

| Origem | SLOC |
|---|---:|
| Expressões quebradas em várias linhas: assinaturas, dicionários, cadeias do ORM | ~569 |
| `models.py` do ORM | 123 |
| Diagnóstico e remendos das correções | 95 a 131 |
| OAuth assinado à mão | 25 |
| Código para satisfazer os testes próprios | ~0 |

Com uma instrução por linha, a diferença cai para 1.549 contra 1.285. O rework e a
variante com revisão têm praticamente o mesmo número de instruções que a baseline
(859 e 854 contra 843). A SLOC maior deles vem só da quebra de linha.

No LLOC, cerca de 200 dos 277 a mais vêm do `models.py`. O Radon conta uma atribuição
anotada, como `x: int = 1`, como duas linhas lógicas. Isso infla o LLOC de modelos ORM,
schemas e configuração. Sem esse arquivo, a diferença fica em 5%.

As outras runs do piloto v3 dão outra perspectiva:

| Grupo | Runs | SLOC | LLOC |
|---|---:|---|---|
| Baseline | 3 | 1.730 a 2.462 | 1.488 a 1.662 |
| TDD | 4 | 2.037 a 2.563 | 1.527 a 1.788 |
| Rework | 4 | 1.765 a 2.110 | 1.345 a 1.501 |

A baseline válida é a menor das 12. O ORM aparece em só 2 delas: a baseline do
piloto de 19/10 e a TDD válida. As outras três runs TDD usam SQL direto. Com uma run
por condição, a diferença da tabela do resumo mistura a escolha da arquitetura,
que muda de run para run, com o efeito do pipeline. As runs anteriores a `7734bea`
servem para comparar tamanho, não nota.

## Padrões que se repetem

1. **Inventar o contrato onde a entrada não diz nada.** Sem schema de resposta, o modelo
   traduz o termo do requisito, usa o nome da coluna ou envolve a lista num objeto. Na
   variante com revisão, 38 das 46 falhas fora das divergências estão em operações sem
   schema. O rework só escapa quando um teste visível mostra o nome.
2. **Defeito pontual vira cascata.** Um nome errado entre módulos, um tipo de coluna ou
   uma barra numa URL derrubam dezenas de casos. A nota mede esses poucos defeitos mais
   do que a cobertura do requisito.
3. **O feedback não vira correção.** O TDD mexeu no formato do erro e no driver, e não
   na causa. No rework, três problemas já diagnosticados no primeiro gate ficaram, e a
   associação das recomendações piorou.
4. **Raciocínio longo sem ação.** No TDD, sete chamadas ocuparam 63% do tempo de
   chamadas; uma levou 670 segundos e 100 mil tokens sem pedir ferramenta. Na
   variante com revisão, duas das seis propostas não editaram nada.
5. **O teste próprio fixa a leitura ambígua.** O canal do OAuth e a ordem das datas
   entraram nos testes do test-writer, e o coder seguiu. Na revisão, o coder trocou
   código certo para passar num teste errado.
6. **Generalizar a partir do exemplo.** O filtro de seções ativas também foi aplicado
   aos campos (baseline e TDD). No rework, o caso visível de vagas vazias virou
   "qualquer texto vira zero".
7. **Texto livre mínimo.** Títulos de PDF sem acento e e-mails em `8bit` que chegam com
   os acentos corrompidos.

## Próximo passo

Os orientadores sugeriram rodar mais uma ou duas vezes, com feedback no input, para ver
se o acerto melhora ou piora. A análise limita o que esse feedback pode conter. As
falhas comuns às quatro entregas só se corrigem dizendo os nomes que o gabarito cobra,
e isso entregaria o gabarito. Os defeitos que a entrada permitiria evitar mudam de run
para run. Por isso, o feedback seria uma lista de cuidados de processo:

- conferir se todo nome chamado entre módulos existe;
- declarar as colunas com os tipos do esquema fornecido;
- não engolir exceções;
- corrigir onde o erro nasce;
- não descartar respostas inesperadas nos helpers de teste.

A nota do TDD já variou de 140 a 209 entre runs. Uma ou duas runs por condição ficam
exploratórias, como a variante com revisão. A medida principal seriam os 79 reservados
sem divergência.

## Artefatos

As entregas, os logs dos gates e os logs da aplicação durante o gabarito estão nas
pastas `demos/runs/caronte/05-prejanus-back-piloto-v3-*` das runs listadas no
[resumo](/blog/resumo-prejanus-back). As linhas citadas aqui se referem aos arquivos
dessas pastas.
