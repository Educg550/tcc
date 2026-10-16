# Estados de preparação do piloto

Preparada e conferida em 16/10/2026 no Postgres 17.6 do original congelado
em `46b89c1d5519aeae40c088ee94262e9b739a7d48`.

## Cenário de candidatura: fixture inicial

- `fixture-forms.sql`: exportação de dados pelos comandos originais
  `flask commands create_application_form mestrado 2026` e
  `flask commands create_recommenders_form mestrado 2026`. Contém o formulário
  completo de candidatura (id 1, oito seções, 42 campos), o de recomendação
  (id 2, duas seções, seis campos), 165 opções, um compartilhamento público
  e os valores das sequências correspondentes. Não contém respostas.
- `seed.sql`: os usuários administrador (id 1) e docente (id 2), já usados
  no ambiente local.
- `fixture-prejanus.sql`: um edital de mestrado, quatro fases e dois
  mapeamentos dos campos e versões. Não contém inscrições locais na tabela
  `submission`. As datas das fases vão de janeiro a abril de 2030 para manter
  o edital aberto durante o piloto, sem depender da data de importação.

O esquema deve existir antes da carga: as fixtures são dados SQL, não
migrações. Os ids são fixos e iguais para todas as implementações. O nome
`email` nos mapeamentos é nulo porque o endereço de acesso pertence a
`form_response.email`, não a um campo do formulário. O cenário de candidatura
verifica a gravação no forms; a consulta no prejanus usa outro estado de
preparação, descrito abaixo.

## Cenário de consulta: contrato de preparação

Por decisão de 16/10/2026, o commit original permanece congelado e o piloto
passa a ter dois cenários independentes. A criação/sincronização automática
da inscrição no prejanus fica fora do recorte por causa da issue 26. Essa
decisão não corrige a falha nem comprova a integração entre os cenários.

O estado de consulta deve conter os mesmos usuários, edital, formulários e
mapeamentos da fixture inicial, mais uma inscrição concluída no forms, suas
respostas conhecidas, oito PDFs distintos no armazenamento compartilhado e
a linha correspondente em `prejanus.submission`. Banco e arquivos devem ser
fixos e iguais no original e nas reconstruções. Os testes conferem a leitura
desses dados, sem atribuir sua criação ao sistema avaliado.

Esse estado ainda não foi materializado nem validado. Sua preparação deve
partir de bancos e armazenamento isolados ou restaurados, sem reutilizar o
estado deixado pelo cenário de candidatura: uma resposta nova sem registro
no prejanus ainda provoca o erro 500, mesmo que outra inscrição já esteja
preparada. Não importar dados no ambiente existente para ocultar a falha.

## Carga em bancos recém-migrados e vazios

Os bancos devem estar sem formulários/editais/respostas; não reaplicar as
fixtures no ambiente já preparado. Não há TRUNCATE, DELETE nem sobrescrita
de formulários/editais: colisões de ids fazem a carga falhar. O seed de
usuários existente usa `ON CONFLICT DO NOTHING`.

Na raiz do TCC, com a stack ligada:

```bash
dc() {
    docker compose --project-directory caronte-core -f caronte-core/docker-compose.yml \
        -f demos/caronte/compose.yml --profile develop --profile clamav "$@"
}
dc exec -T db psql -v ON_ERROR_STOP=1 --single-transaction -U caronte_forms -d caronte_forms < demos/caronte/fixture-forms.sql
dc exec -T db psql -v ON_ERROR_STOP=1 --single-transaction -U caronte_prejanus -d caronte_prejanus < demos/caronte/seed.sql
dc exec -T db psql -v ON_ERROR_STOP=1 --single-transaction -U caronte_prejanus -d caronte_prejanus < demos/caronte/fixture-prejanus.sql
bash demos/caronte/caronte.sh trocar teacher
```

Cada importação usa uma transação; a carga nos dois bancos não é uma
transação distribuída. Não alterar os arquivos entre os grupos. O link de
acesso inicial é `/pt/form/shared/<token>`, com o token de `form_shared`
incluído na fixture. O token é dado sintético público de preparação, não
uma credencial institucional.

## Conferência realizada

Foram criados dois bancos temporários separados dos bancos da aplicação.
Seus esquemas foram restaurados de dumps `--schema-only` do original, depois
foram importados os três arquivos de dados, com erro SQL interrompendo a
carga. As contagens verificadas foram:

| Banco | Estado conferido |
|---|---|
| forms | 2 formulários, 10 seções, 48 campos, 1 compartilhamento, 0 respostas |
| prejanus | 1 edital, 4 fases, 2 mapeamentos, 2 usuários, 0 inscrições |

Os dois bancos temporários foram removidos após a conferência. Os bancos
da aplicação mantêm a fixture; o backend está selecionado como docente.
Não houve alteração do código original nem chamada ao OpenRouter.

Essa conferência valida a carga dos dados no esquema original. Ainda não
valida a fixture nas reconstruções, a suíte-oráculo ou o percurso completo
pela interface.

## Falha de sincronização reproduzida

A listagem `GET http://localhost:8083/edicts/1/submissions` retornou HTTP 200
e `{"submissions":[]}` com a fixture inicial. Para diagnóstico, foi criada
diretamente no banco forms uma resposta sintética com `submitted_at`
preenchido e uma resposta de nome, sem a linha correspondente em
`prejanus.submission`. O mesmo GET retornou HTTP 500:

```json
{"detail":"No Submission found for candidate form 1"}
```

A condição já está documentada na issue 26 do projeto, cuja descrição está
em `caronte-workitems.md`. Em
`prejanus-back/src/use_cases/submission/get_all_from_edict.py`, a verificação
de existência de `Submission` ocorre antes do trecho que insere as
inscrições locais. Uma candidatura nova não tem esse registro prévio.

Esta foi uma reprodução direcionada por estado de banco, não uma inscrição
completa pelo navegador. A resposta de diagnóstico e seu valor associado
foram removidos pelo UUID e marcador exclusivos usados na reprodução;
foi conferido que restaram zero respostas. A fixture exportada não contém
esse diagnóstico nem prepara uma inscrição antecipadamente para ocultar
a falha.

O requisito PIL-DOC-01 foi revisto para a consulta de uma inscrição
preparada, em estado independente, e permanece sem validação de aprovação
no original. O código original foi preservado. Os testes HTTP/tela de
rejeição de upload e a validação dos oito documentos pelo docente continuam
por executar. Só a restauração da fixture inicial e o diagnóstico HTTP
descritos acima foram conferidos; não são evidência de aprovação dos dois
cenários completos.
