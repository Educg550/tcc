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

Preserve as decisões do recorte: formulário completo de mestrado; fixture
SQL compartilhada e mesmo esquema de banco; candidato envia inscrição;
operador aciona convites; recomendador recebe e abre o link; docente consulta
todas as respostas e abre os anexos de uma inscrição previamente preparada.
São dois cenários independentes na mesma implementação: candidatura e
convites, iniciados sem respostas, e consulta pelo docente, iniciada com
respostas, oito PDFs e registro correspondente em `submission`. A decisão
de 16/10/2026 mantém o commit e exclui a criação/sincronização automática
entre forms e prejanus por causa da issue 26. Restaurar estados separados;
o cenário de consulta não pode reutilizar o banco deixado pela candidatura.
Inclua o fluxo válido de cada cenário e os erros
principais de obrigatório, e-mail, tipo e tamanho de arquivo. Não acrescente
o envio da recomendação nem o fluxo de criação administrativa pela tela.

Cada requisito deve ter id estável e critério observável em HTTP ou tela.
Confira rotas, métodos, payloads, textos visíveis e fronteiras de tamanho no
original, inclusive comportamentos HTTP incomuns. Registre divergências
antes do congelamento; uma validação declarada no código não prova que a
interface de upload propaga o erro corretamente.

## Fontes locais para conferir

| Requisitos | Fontes em `caronte-core/` |
|---|---|
| PIL-AMB-01 | `docker-compose.yml`, `docker/nginx/nginx.conf` |
| PIL-BD-01 | `forms/app/persistence/migrations/`, `prejanus-back/src/infra/database/migrations/`, `prejanus-back/src/infra/database/models/` |
| PIL-AUT-01 | `prejanus-back/src/auth/senhaunica_auth.py`, `prejanus-front/src/middleware.ts`, `prejanus-front/src/lib/getCurrentUser.ts` |
| PIL-ACE-01 | `forms/app/routes/form.py` (`access_shared`), `forms/app/templates/form/shared.html`, `forms/app/services/form_service.py` (`send_url_to_email`) |
| PIL-FOR-01 | `forms/app/commands/insert_application_form.py` (`template_form`), `forms/app/commands/application_submissions/{universities,courses}.csv` |
| PIL-FOR-02, PIL-SUB-01 | `forms/app/routes/form.py` (`form_section`, `form_submit`), `forms/app/templates/form/index.html`, `forms/app/exceptions/error_messages.py` |
| PIL-VAL-01, PIL-VAL-02 | `forms/app/services/response_service.py`, `forms/app/common/validators.py` |
| PIL-ARQ-01, PIL-ARQ-02 | `forms/app/services/file_service.py`, `forms/app/routes/form.py` (`upload_file`, `form_section`, `download_file`) |
| PIL-CON-01, PIL-CON-02 | `forms/app/commands/generate_recommender_list.py`, `forms/app/commands/send_recommenders_email.py`, `forms/app/commands/insert_recommenders_form.py`, `forms/app/commands/__init__.py` |
| PIL-DOC-01 | `prejanus-back/src/routers/edict_routers.py`, `prejanus-back/src/use_cases/submission/get_all_from_edict.py` |
| PIL-DOC-02 | `prejanus-back/src/use_cases/submission/get_by_id.py`, `prejanus-front/src/app/[processId]/submissions/[submissionId]/candidate-details-page.tsx` |
| PIL-DOC-03 | `prejanus-front/src/app/[processId]/submissions/[submissionId]/components/CandidateSubmittedDocs.tsx`, `prejanus-front/src/app/submissions/[submissionId]/api/files/[label]/[filename]/route.ts`, `prejanus-back/src/use_cases/submission/get_file.py` |

O comando de subida e a seleção de usuário estão em
`demos/caronte/caronte.sh`; os usuários iniciais, em `demos/caronte/seed.sql`.

## Estado da revisão de 16/10/2026

O JSON declarativo foi extraído da função `template_form('mestrado', '2026')`,
com os CSVs originais, sem importar a aplicação ou executar serviços.
Foi removido apenas `created_at`. São oito seções, 42 campos, oito campos
de arquivo (quatro obrigatórios) e os rótulos/opções bilíngues originais.

Pontos que a validação em execução deve resolver antes do congelamento:

- Upload: `process_file_field` devolve falha para tipo/tamanho inválido,
  mas `handle_request_files` repassa essa falha como `Result(True, ... )`.
  Em `Result`, qualquer `data` não nulo marca sucesso. Uma reprodução
  isolada com as funções originais confirmou esse sucesso indevido ao
  propagar uma rejeição simulada, sem executar upload real. Reproduzir o
  efeito no endpoint e na tela, tanto em campo obrigatório quanto opcional; não
  presumir que a mensagem específica chega ao usuário. Se o original não
  cumprir PIL-ARQ-02, registrar a divergência para decidir o contrato.
- Frontend: o atalho `DEV_USER_ID` está no backend; o middleware Next ainda
  exige presença do cookie `session` nas páginas internas. Validar a
  preparação desse estado no ambiente local, sem OAuth real nem mudança
  no original.
- Banco: a fixture inicial foi materializada e restaurada em bancos
  temporários com esquema original. Materializar e conferir o estado
  independente de consulta, incluindo respostas, `submission` e oito PDFs.
  Explicitar quais definições de banco são
  infraestrutura compartilhada, inclusive as funções SQL que o backend
  original chama, antes de preparar a entrada das reconstruções.
- HTTP e tela: capturar os payloads efetivos e validar os dois cenários,
  incluindo o HTTP 400 do pedido de link bem-sucedido, a fila de e-mail,
  os dois convites e a leitura dos oito PDFs no prejanus.
- Sincronização: em 16/10/2026, reproduzido por HTTP o erro da issue 26.
  A lista vazia retorna 200; uma resposta sintética finalizada sem linha
  em `submission` faz o mesmo GET retornar 500 com `No Submission found`.
  O estado foi preparado por SQL para diagnóstico, sem alegar execução
  completa do fluxo. A resposta sintética foi removida. Ver `fixture.md`
  para a evidência e os contratos de preparação. O recorte foi revisto por
  decisão de Eduardo: a inscrição antecipada é entrada explícita apenas do
  cenário independente de consulta. Sua leitura não comprova sincronização
  nem permite afirmar que a inscrição enviada no primeiro cenário apareceu
  no prejanus.

Esses pontos são registro de revisão do rascunho, não testes aprovados nem
evidência de que os dois cenários funcionam. As tarefas e decisões pendentes
continuam no beads.
