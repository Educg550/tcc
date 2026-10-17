# Consulta do prejanus-back

## Recorte

O piloto mede se reconstruir o caronte com o harness escala, num pedaço
pequeno antes do sistema inteiro. Reconstrói só a consulta do prejanus-back:
o docente encontra uma inscrição preparada, consulta suas respostas e baixa
os anexos.

A reconstrução conversa com o mesmo ambiente do original: o banco do
prejanus, o banco do forms (só leitura), os uploads compartilhados e o login
da Senha Única. Ficam fora o forms, o prejanus-front, Redis, smtp4dev,
ClamAV, nginx e as demais rotas do prejanus-back, inclusive as que enviam
e-mail. A criação da inscrição pelo forms também fica fora, e com ela a
issue 26: a fixture já traz a inscrição com seu registro em `submission`.

## Ambiente e preparação

### PIL-AMB-01 — Stack e acesso

Usar FastAPI e Postgres. A API é acessada em `http://localhost:8083/` e lê
os anexos de `/shared/uploads/`, o volume compartilhado do original. No
original, subir com `bash demos/caronte/caronte.sh subir`, a partir da raiz
do TCC. A reconstrução substitui apenas o serviço `prejanus-back`,
preservando o banco `db`, o volume de uploads, a porta e o contrato de
preparação. O estado de consulta é restaurado por
`bash demos/caronte/caronte.sh consulta`.

### PIL-BD-01 — Compatibilidade com a fixture SQL

O banco do forms é infraestrutura do original, com esquema e funções SQL
(`get_all_submissions`, `get_submissions_by_id`) inalterados. O banco do
prejanus preserva o esquema exigido pela fixture: tabelas, colunas, tipos,
chaves e relações. Ver `infra/README.md`.

A fixture prepara os usuários de ids 1 (administrador) e 2 (docente), um
edital de mestrado, o formulário completo de candidatura
(`infra/formulario-mestrado.json`), os mapeamentos
das versões dos formulários, uma inscrição concluída com respostas
conhecidas, oito PDFs distintos nos uploads e a linha correspondente em
`submission`. Esses dados são entrada da consulta, iguais no original e nas
reconstruções; o sistema avaliado não os cria.

### PIL-AUT-01 — Docente local

Com `APP_ENV=local` e `DEV_USER_ID=2`, o prejanus-back reconhece o docente
preparado no banco, sem depender da Senha Única. `GET /auth/login` retorna
seu `id`, `name`, `email`, `nusp` e `role`. O comando existente
`bash demos/caronte/caronte.sh trocar teacher` seleciona esse usuário;
`trocar admin` seleciona o administrador.

Sem o atalho e sem sessão, `GET /auth/login` e as rotas de consulta
respondem 401. O fluxo OAuth da
Senha Única (`POST /auth/login/senhaunica`) é preservado na interface, mas
fica fora da suíte, porque depende do servidor externo da USP.

## Consulta pelo docente

### PIL-DOC-01 — Encontrar a inscrição

`GET /edicts` lista os editais, `GET /edicts/<edict_id>` consulta o edital e
`GET /edicts/<edict_id>/submissions` retorna a inscrição da fixture no array
`submissions`, identificada pelo nome do candidato. A consulta usa as
respostas do forms e o mapeamento de sua versão. Consultas repetidas não
criam inscrições duplicadas.

### PIL-DOC-02 — Consultar todas as respostas

`GET /submissions/<submission_id>` retorna `summary` e `submission_form`.
Este último organiza os campos por seção, com seus identificadores, nomes,
rótulos, tipos e valores. O e-mail de acesso do candidato aparece nos
detalhes. Campos não preenchidos podem vir sem valor; os preenchidos
correspondem aos valores conhecidos da fixture, incluindo escolhas e textos
opcionais. A nota do POSCOMP fica vazia e `ethnicity-race` fica fora do
mapeamento do edital, para contornar duas falhas do original (ver
`infra/README.md`).

### PIL-DOC-03 — Baixar todos os anexos enviados

`GET /submissions/<submission_id>/files/<field_name>/<filename>` entrega o
PDF daquele campo e daquela inscrição, com
`Content-Disposition: attachment` e o conteúdo preservado. A suíte confere
os oito documentos distintos da fixture.

## Interfaces HTTP incluídas

Rotas relativas a `http://localhost:8083`. Os ids são os valores da
fixture, não constantes do teste.

| Requisito | Interface |
|---|---|
| PIL-AUT-01 | GET `/auth/login` |
| PIL-DOC-01 | GET `/edicts`, `/edicts/<edict_id>`, `/edicts/<edict_id>/submissions` |
| PIL-DOC-02 | GET `/submissions/<submission_id>` |
| PIL-DOC-03 | GET `/submissions/<submission_id>/files/<field_name>/<filename>` |


## Contrato de integração

Leia `infra/README.md` e os esquemas e dados declarativos em `infra/`.
