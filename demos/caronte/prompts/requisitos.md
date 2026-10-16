# Preparação e revisão dos requisitos do piloto

Este prompt é destinado ao Claude Code ou Codex com acesso ao original
congelado. Não é a entrada dos agentes das runs medidas: essa entrada usa
os requisitos e os dados declarativos congelados, sem acesso ao código
original, a este roteiro de revisão ou à suíte-oráculo escondida.

Leia `demos/caronte/requisitos.md`, `demos/caronte/formulario-mestrado.json`
e `caronte-workitems.md`. Confira o contrato no código de `caronte-core/`,
congelado em `46b89c1d5519aeae40c088ee94262e9b739a7d48`. Work items dão
contexto; só descreva como requisito comportamento que o original implementa.
Não altere o original para fazê-lo cumprir um requisito.

Preserve o recorte: só a consulta do prejanus-back, sobre uma inscrição
preparada pela fixture com respostas, oito PDFs e registro em `submission`.
A reconstrução conversa com o banco do prejanus, o banco do forms (só
leitura), os uploads compartilhados e a Senha Única. Não acrescente forms,
prejanus-front, envio de e-mail nem outras rotas do prejanus-back.

Cada requisito deve ter id estável e critério observável em HTTP. Confira
rotas, métodos, payloads e cabeçalhos no original, inclusive comportamentos
HTTP incomuns. Registre divergências antes do congelamento.

## Fontes locais para conferir

| Requisitos | Fontes em `caronte-core/` |
|---|---|
| PIL-AMB-01 | `docker-compose.yml`, `prejanus-back/src/settings.py` |
| PIL-BD-01 | `forms/app/persistence/migrations/`, `prejanus-back/src/infra/database/migrations/`, `prejanus-back/src/infra/database/models/` |
| PIL-AUT-01 | `prejanus-back/src/auth/senhaunica_auth.py`, `prejanus-back/src/routers/auth_routers.py` |
| PIL-DOC-01 | `prejanus-back/src/routers/edict_routers.py`, `prejanus-back/src/use_cases/submission/get_all_from_edict.py` |
| PIL-DOC-02 | `prejanus-back/src/use_cases/submission/get_by_id.py` |
| PIL-DOC-03 | `prejanus-back/src/routers/submission_routers.py`, `prejanus-back/src/use_cases/submission/get_file.py` |

O comando de subida e a seleção de usuário estão em
`demos/caronte/caronte.sh`; os usuários iniciais, em `demos/caronte/seed.sql`.

## Estado da revisão de 16/10/2026

O JSON declarativo foi extraído da função `template_form('mestrado', '2026')`,
com os CSVs originais, sem importar a aplicação ou executar serviços.
Foi removido apenas `created_at`. São oito seções, 42 campos, oito campos
de arquivo (quatro obrigatórios) e os rótulos/opções bilíngues originais.

Pontos que a validação em execução deve resolver antes do congelamento:

- Banco: a fixture inicial foi materializada e restaurada em bancos
  temporários com esquema original. Falta materializar e conferir o estado
  de consulta, com respostas, `submission` e os oito PDFs. O prejanus-back
  lê o forms pelas funções SQL `get_all_submissions` e
  `get_submissions_by_id`, definidas nas migrações do forms; elas são
  infraestrutura do original, não parte da reconstrução.
- HTTP: capturar os payloads efetivos de PIL-DOC-01..03 e o 401 sem sessão
  de PIL-AUT-01 no original.
- Issue 26: reproduzida por HTTP em 16/10/2026 (ver `fixture.md`). Uma
  resposta finalizada sem linha em `submission` faz a listagem retornar 500.
  O estado de consulta não pode conter resposta assim.

Esses pontos são registro de revisão do rascunho, não testes aprovados. As
tarefas e decisões pendentes continuam no beads.
