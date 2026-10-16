# Requisitos do piloto Caronte

Rascunho de 16/10/2026, derivado do original congelado em
`46b89c1d5519aeae40c088ee94262e9b739a7d48`. A conferência inclui leitura do
código, restauração da fixture inicial e diagnóstico HTTP da issue 26;
o contrato só será congelado junto com a suíte-oráculo que passar inteira
no original.

## Recorte

O piloto contém dois cenários independentes, na mesma implementação:

1. **Candidatura e convites:** o candidato recebe seu link por e-mail,
   preenche o formulário completo de mestrado e envia a inscrição com os
   documentos. Um operador aciona os convites pelos comandos do original.
   Cada recomendador recebe o convite e abre o formulário com a identificação
   do candidato.
2. **Consulta pelo docente:** a preparação fornece uma inscrição concluída,
   com respostas, oito PDFs e o registro correspondente no prejanus. O docente
   encontra essa inscrição, consulta todas as respostas e abre os documentos.

A decisão de 16/10/2026 mantém o commit congelado e retira do piloto a criação
ou sincronização automática da inscrição entre forms e prejanus, devido à
issue 26 reproduzida no original. O cenário de consulta não usa o resultado
da candidatura: começa em outro estado restaurado, sem respostas novas
sem registro correspondente no prejanus. O piloto não comprova o percurso
contínuo entre enviar a candidatura e encontrá-la no prejanus.

Edital, usuários, formulários, compartilhamento e mapeamentos são preparados
por uma fixture SQL reproduzível, igual no original e nas reconstruções.
A criação administrativa pela interface, o envio da recomendação e as etapas
posteriores de seleção também ficam fora do piloto. A conferência das telas
usa os rótulos em português do original; os dados bilíngues dos formulários
são preservados.

## Ambiente e preparação

### PIL-AMB-01 — Stack e acesso

Usar Flask no forms, FastAPI no prejanus-back, Next no prejanus-front e
Postgres. Postgres, Redis, smtp4dev, ClamAV e nginx compõem o ambiente
compartilhado. O forms é acessado em `http://localhost/`, o prejanus em
`http://localhost/prejanus`, a API FastAPI em `http://localhost:8083/` e o
smtp4dev em `http://localhost:8080/smtp4dev/`.

No original, subir com `bash demos/caronte/caronte.sh subir`, a partir da raiz
do TCC. O comando de subida das reconstruções deve preservar esses serviços,
endereços e o contrato de preparação. Os testes de negócio verificam a
integração com esses serviços; não reimplementam testes internos de Redis,
smtp4dev ou ClamAV.

### PIL-BD-01 — Compatibilidade com a fixture SQL

Preservar os bancos do original e o esquema exigido pela fixture compartilhada:
tabelas, colunas, tipos, chaves e relações. As aplicações devem ler os dados
preparados e gravar as novas respostas nesse esquema. No cenário de candidatura,
a fixture não fornece inscrição concluída, arquivos enviados ou convites
entregues: esses resultados precisam ser produzidos pelo sistema em avaliação.
No cenário de consulta, uma fixture própria fornece a inscrição concluída,
suas respostas e PDFs e a linha correspondente em `submission`. Esses dados
são entrada da consulta, sem atribuir sua criação ao sistema avaliado.

A fixture prepara os usuários de ids 1 (administrador) e 2 (docente), um
edital de mestrado, o formulário completo de candidatura, o formulário de
recomendação, o compartilhamento público e os mapeamentos compatíveis com
as versões dos formulários. Datas e tokens necessários ao teste são dados
de preparação, mantidos iguais entre os grupos de cada avaliação. A fixture
inicial está materializada e teve sua restauração conferida; ver
[`fixture.md`](./fixture.md). O estado de consulta ainda precisa ser
materializado e validado no original. Cada cenário começa de seu próprio
estado conhecido, incluindo os arquivos; não se acrescenta a inscrição
preparada ao banco deixado pelo cenário de candidatura.

### PIL-AUT-01 — Docente local

Com `APP_ENV=local` e `DEV_USER_ID=2`, o prejanus-back reconhece o docente
preparado no banco, sem depender de OAuth externo. `GET /auth/login` retorna
seu `id`, `name`, `email`, `nusp` e `role`. O comando existente
`bash demos/caronte/caronte.sh trocar teacher` seleciona esse usuário;
`trocar admin` seleciona o administrador. O candidato acessa o forms pelo
compartilhamento público, sem usar `DEV_USER_EMAIL`.

O atalho do backend não elimina o middleware do frontend: o estado de sessão
necessário à navegação pelo prejanus deve ser preparado e documentado pela
suíte antes do congelamento, sem alterar o original.

## Candidatura

### PIL-ACE-01 — Receber o link de acesso

`GET /pt/form/shared/<token>` apresenta o formulário de acesso com o campo
`E-mail` e o botão `Receber link de acesso`. Um POST com `__email__` válido
e o `_csrf_token` da página solicita o link individual de preenchimento.
O e-mail entregue ao candidato contém esse link, que permite abrir a
primeira seção sem autenticação institucional.

O original apresenta `Verifique seu e-mail para obter o link de acesso.` e
`Acesso liberado com sucesso`. Essa resposta usa HTTP **400 mesmo no caminho
de sucesso**; esse status não deve ser confundido com falha de entrega.
O assunto do e-mail começa com `Acesso ao formulário:`.

### PIL-FOR-01 — Formulário completo

Apresentar as oito seções e os 42 campos do anexo
[`formulario-mestrado.json`](./formulario-mestrado.json), na mesma ordem,
com os nomes, tipos, rótulos, opções, obrigatoriedade e regras declaradas.
O anexo é dado declarativo extraído do formulário original de mestrado de
2026; somente o horário de criação foi removido para torná-lo estável.

Os campos `Text` com opções, como curso e instituição, oferecem sugestões;
as sugestões não transformam o campo em uma escolha fechada. Não criar
obrigatoriedade condicional apenas porque uma descrição recomenda um
documento: vale a regra efetivamente implementada no original.

### PIL-FOR-02 — Navegação e persistência

`GET /pt/form/<response_token>` apresenta a seção atual. `Próximo` avança,
`Voltar` retorna e `Enviar` aparece na última seção. Os valores salvos
continuam associados ao mesmo candidato ao navegar e recarregar a página.

O POST dessa rota usa os nomes dos campos do anexo e `_csrf_token`, com
`next` para avançar ou `back` para voltar. Checkbox usa os nomes indexados
do original, como `acknowledgment[1]`. A resposta JSON contém
`url_redirect`, que a interface segue. Voltar durante o preenchimento não
obriga a completar todos os campos da seção atual.

### PIL-VAL-01 — Obrigatórios

Não permitir avançar normalmente nem concluir uma seção deixando um campo
obrigatório sem resposta. Isso inclui a confirmação de ciência, as escolhas
obrigatórias e os documentos obrigatórios do anexo. A avaliação inclui uma
tentativa inválida e a correção posterior, seguida da continuação do fluxo.

### PIL-VAL-02 — E-mail do recomendador

O primeiro e-mail de recomendador é obrigatório; o segundo é opcional.
Quando informado, cada um deve passar pela validação de e-mail declarada
no anexo. Uma entrada inequivocamente inválida, como `sem-arroba`, não
permite avançar. Corrigir a entrada permite continuar. O piloto verifica
a regra do original, sem acrescentar validação de domínio institucional.

### PIL-ARQ-01 — Enviar documentos

Cada campo `File` preenchido aceita PDF com extensão e MIME compatíveis e
tamanho **menor que 1.048.576 bytes**. Um arquivo exatamente nesse limite
já é rejeitado pelo original. O upload passa pelo ClamAV do ambiente;
arquivo limpo aceito fica disponível à inscrição no forms.

O formulário contém oito campos de arquivo: quatro obrigatórios
(`official-document-file`, `lattes-cv-file`, `studies-transcripts`,
`motivation-letter`) e quatro opcionais (`disabilities-file`,
`ethnicity-race-file`, `poscomp-file`, `graduate-courses-file`). O fluxo
válido da suíte deve enviar PDFs distintos nos oito, para conferir sua
persistência e a correspondência entre campo e documento pelo forms.
A consulta pelo docente usa os oito PDFs da fixture independente.

### PIL-ARQ-02 — Tipo e tamanho inválidos

Uma tentativa de upload com tipo proibido ou tamanho no limite/superior a
1 MiB não deve registrar esse conteúdo como documento válido da inscrição.
A suíte inclui um caso de tipo proibido e um de tamanho proibido, além da
correção com PDF válido. O comportamento de erro das rotas de upload ainda
precisa ser reproduzido no original antes do congelamento; ver o registro
de revisão em `prompts/requisitos.md`.

### PIL-SUB-01 — Concluir a inscrição

Depois das oito seções completas, `Enviar` conduz a
`/pt/form/submit/<response_token>` e apresenta `Sua resposta foi registrada`.
A inscrição finalizada mantém o e-mail de acesso, as respostas e os anexos
do candidato no forms. A criação do registro no prejanus fica fora desse
critério.

## Convite ao recomendador

### PIL-CON-01 — Disparar os convites

Após a candidatura, o operador usa a interface administrativa de comandos
existente no forms, com os ids fornecidos pela preparação:

```text
flask commands generate_recommender_list <application_form_id> <recommender_form_id> <expiration_at>
flask commands send_recommenders_email
```

O primeiro comando prepara os links e o CSV `tmp/tmp_recommenders.csv`; o
segundo enfileira os convites desse CSV. Executá-los faz parte do roteiro de
avaliação, entre as ações dos usuários. O contrato não exige que clicar
`Enviar` na inscrição dispare os convites automaticamente.

### PIL-CON-02 — Entrega e abertura

Cada recomendador indicado com e-mail preenchido recebe no smtp4dev um
convite destinado ao endereço informado, com o assunto
`Solicitação de recomendação para candidatura`, o nome do candidato e o
link `Link para o formulário de recomendação`.

Ao seguir o link, o recomendador encontra o campo
`Nome completo do candidato a ser recomendado`, preenchido com o candidato
correto e desabilitado para edição, e seu próprio `Nome completo` já
preenchido. A avaliação termina na abertura; não preenche nem envia a carta.
O roteiro usa os dois recomendadores do formulário e verifica a entrega e
a associação de cada convite.

## Consulta pelo docente

### PIL-DOC-01 — Encontrar a inscrição

Com o docente local e o estado independente de consulta, abrir o prejanus
e o edital preparado permite encontrar a inscrição fornecida pela fixture,
identificada pelo nome do candidato. O e-mail de acesso é conferido nos
detalhes da inscrição.
`GET /edicts` lista os editais, `GET /edicts/<edict_id>` consulta o edital e
`GET /edicts/<edict_id>/submissions` retorna a inscrição no array
`submissions`. A consulta usa as respostas do forms e o mapeamento de sua
versão. Consultas repetidas não criam inscrições duplicadas.

### PIL-DOC-02 — Consultar todas as respostas

Abrir a inscrição pela lista, ou pela página
`/prejanus/<edict_id>/submissions/<submission_id>`, mostra os dados do
candidato e as respostas de todas as seções. Campos não preenchidos podem
aparecer sem valor; as respostas preenchidas devem corresponder aos valores
conhecidos da fixture de consulta, incluindo escolhas e textos opcionais.

`GET /submissions/<submission_id>` no backend retorna `summary` e
`submission_form`; este último organiza os campos por seção, com seus
identificadores, nomes, rótulos, tipos e valores. O frontend consulta
`/prejanus/<edict_id>/submissions/api` para a lista e
`/prejanus/submissions/<submission_id>/api` para os detalhes, expondo
respectivamente `candidates` e o par `summary`/`submissionForm`.

### PIL-DOC-03 — Abrir todos os anexos enviados

Na seção `Documentos`, cada campo de arquivo preenchido apresenta seu rótulo
e o botão `Visualizar`. O botão abre o PDF correspondente àquele campo e
àquela inscrição, preservando seu conteúdo. A suíte verifica os oito
documentos distintos fornecidos pela fixture de consulta, conferindo o
conteúdo de cada um.

A rota do frontend é
`/prejanus/submissions/<submission_id>/api/files/<field_name>/<filename>`;
a rota do backend é
`/submissions/<submission_id>/files/<field_name>/<filename>`. Ambas usam
GET. O backend entrega o PDF com `Content-Disposition: attachment`.

## Interfaces HTTP incluídas

`<token>` e `<response_token>` são UUIDs; os ids das demais rotas são os
valores produzidos pela fixture ou pela aplicação, não constantes do teste.
As rotas do backend FastAPI abaixo são relativas a `http://localhost:8083`.

| Requisito | Interface |
|---|---|
| PIL-ACE-01 | GET/POST `/pt/form/shared/<token>` |
| PIL-FOR-02, PIL-VAL-01, PIL-VAL-02 | GET/POST `/pt/form/<response_token>` |
| PIL-ARQ-01, PIL-ARQ-02 | POST `/pt/form/<response_token>/upload`, multipart com o nome do campo |
| PIL-ARQ-01 | GET `/pt/form/<response_token>/download/<filename>` |
| PIL-SUB-01 | GET/POST `/pt/form/submit/<response_token>` |
| PIL-AUT-01 | GET `/auth/login` |
| PIL-DOC-01 | GET `/edicts`, `/edicts/<edict_id>`, `/edicts/<edict_id>/submissions` |
| PIL-DOC-02 | GET `/submissions/<submission_id>` |
| PIL-DOC-03 | GET `/submissions/<submission_id>/files/<field_name>/<filename>` |

## Critério para congelamento

Cada requisito tem pelo menos um teste que verifica seu comportamento,
incluindo as seções e campos de PIL-FOR-01, as respostas de PIL-DOC-02 e
os anexos de PIL-DOC-03. Toda rota e tela incluída na fatia é exercitada.
Todos os testes citam os ids correspondentes e passam no original. Registrar
a cobertura de linhas vivas, sem percentual mínimo no piloto.

Congelar requisitos, os estados de banco e arquivos dos dois cenários e a
suíte juntos. Identificar o cenário de cada teste; nenhum teste pressupõe
que o envio no forms produz uma inscrição consultável no prejanus.
Dividir a suíte em 75% visíveis e 25% held-out, estratificados por rota e
tela nos dois cenários, registrando a regra de
arredondamento para grupos pequenos antes das runs. No experimento de
reconstrução por requisitos, a suíte inteira fica escondida; no rework,
o agente recebe a parte visível e é avaliado na reservada.

O piloto não compõe os resultados finais. A preparação ocorre fora do
OpenRouter; as chamadas medidas de baseline, TDD e rework somadas têm teto
de US$ 10; os dois cenários integram cada uma dessas runs. A escolha do
escopo e dos tetos finais depende dessa medição, que não inclui a integração
automática retirada do piloto.
