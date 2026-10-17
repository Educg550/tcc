# Avaliação do piloto v2

Este documento pertence à preparação do avaliador, fora da entrada do
agente. O produto está em
[`requisito.md`](../../requisitos/03-caronte-prejanus-completo/requisito.md).
A referência continua sendo o Caronte congelado registrado em
`46b89c1d5519aeae40c088ee94262e9b739a7d48`; o inventário inclui hashes
da árvore local lida e do OpenAPI coletado, sem presumir que a extração
do OpenAPI seja validação comportamental.

## Fronteira da reconstrução

Reconstruir todas as operações alcançáveis dos routers de autenticação,
formulários, editais e inscrições, mais a raiz: 50 pares método/caminho.
A conferência por AST e pelo OpenAPI do original encontrou o mesmo
conjunto. Não adicionar endpoints mencionados apenas no README antigo,
como `/users`, nem transformar funções não expostas em novos requisitos.
Por exemplo, a chamada de envio coletivo no encerramento está comentada;
o fluxo de carta efetivamente exposto é `send-letter`.

Preservar Forms, Front, proxy e serviços compartilhados como dependências.
Seu código não integra o produto gerado nem sua contagem de complexidade.
A comparação usa o mesmo original, imagens, dados iniciais e configuração
nos três grupos. A amplitude nova exige resultados separados do v1.

## Integrações e evidências

Os identificadores desta tabela são usados em `interfaces.json`.

| Integração | Fronteira | Evidência de aceitação |
|---|---|---|
| INT-PREJANUS-DB | Postgres do PreJanus, leitura e escrita | Chaves, relações e estado observados por novas requisições e após reinício; ausência de duplicação |
| INT-FORMS-DB | Segundo banco Postgres, funções SQL e tabelas Forms | Estrutura e respostas lidas; fase, reabertura e resposta de aceite realmente persistidas; permissões verificadas |
| INT-UPLOADS | Volume compartilhado produzido pelo Forms | Bytes e identificação de todos os PDFs; nome e inscrição correspondentes; arquivo alheio não entregue |
| INT-SMTP | SMTP local, mesmo protocolo da aplicação | Mensagem capturada, destinatários, CC/BCC, assunto, corpo, links e assinatura; quantidade por operação |
| INT-OAUTH | Contrato HTTP OAuth da Senha Única | Request/access tokens, assinatura da troca, callback, whitelist e cookie de sessão; credenciais sintéticas |
| INT-RELATORIOS | Background tasks, recursos institucionais e arquivos temporários | Conteúdo PDF/CSV, polling por job, consumo e remoção; não basta receber job_id |
| INT-FRONT | PreJanus Front e proxy originais, cookies e CORS | Cliente consulta e altera o backend substituído; URLs e sessão funcionam via proxy |
| INT-FORMS-STACK | Forms original com Redis, Celery, ClamAV e SMTP | Candidatura e PDFs enviados, convites entregues e links de correção/aceite usados pelo Forms real |

A conta de conexão chamada `forms_reader` precisa escrever no escopo novo:
`change_form_phase`, `update_form_response_section` e criação de
`form_shared`/`form_response`. Conferir os grants reais e exportá-los com
a fixture; não usar superusuário para ocultar a falta de permissão.

O backend não chama Redis, Celery ou ClamAV diretamente. Sua participação
é verificada nos percursos que passam pelo Forms. Não afirmar integração
direta do backend com esses serviços. Falhas de dependências devem ser
atribuídas e registradas separadamente das falhas do código reconstruído.

O script original `docker/init.postgres.sh` já declara SELECT, INSERT,
UPDATE, uso de sequências e execução de funções para `forms_reader`,
inclusive privilégios padrão para objetos futuros. Isso sustenta o contrato
de escrita; os grants dos bancos materializados ainda precisam ser
conferidos na preparação v2.

## Estados reproduzíveis

Usar projeto Compose, rede, bancos, volume de uploads e caixa SMTP
dedicados ao v2. Não restaurar nem apagar os bancos e containers das runs
v1 para preparar o novo piloto. Cada grupo e cenário parte da mesma
cópia, sem herdar o resultado do grupo anterior.

| Estado | Dados e preparação exigidos | Comportamento observado |
|---|---|---|
| S0 — infraestrutura e identidade | Dois esquemas originais; usuários de todos os papéis, dois docentes distintos, whitelist, provedor OAuth e HTTPS local | Raiz, documentação, CORS, 401, bypass exclusivamente local, login OAuth existente/novo/negado |
| S1 — catálogo e configuração | Formulários completos de mestrado, doutorado, recomendação e aceite; tags, seções ativas/inativas e versões 1, nula e 2 | Filtros Forms, estrutura, criação e edição de editais, datas e mapeamentos |
| S2 — candidatura nova | Forms sem respostas e PreJanus sem inscrições; criação de resposta exclusivamente pelo Forms | Cadastro e finalização, uploads, convites, sincronização da inscrição e recomendações |
| S3 — consulta preparada | Candidaturas finalizadas e registros locais correspondentes; duas versões; respostas recomendadas e não recomendadas; PDFs de conteúdo distinto | Listagem, detalhe, todos os campos e anexos; versões não mapeadas; filtros sem mistura de candidatos |
| S4 — homologação | Inscrição consistente e fase homologacao; caixa SMTP vazia | Solicitar correção, examinar estado e mensagem, abrir o link, corrigir e reenviar pelo Forms |
| S5 — avaliação | Edital aberto em avaliacao; múltiplas inscrições e docentes, sem marcas pessoais | Comentários, favoritos, etiquetas e propagação de cores, notas privadas, visualizações por dia, vagas e interesses |
| S6 — decisão e aceite | Aprovado com orientador e aceite configurado; também não aprovado e sem formulário | Criar convite uma vez, mensagem SMTP, resposta única, aceite/recusa pelo Forms, estados pendente/respondido, carta e repetição |
| S7 — relatórios e encerramento | Decisões, vagas, interesses, interações e candidaturas incompletas conhecidos | Conteúdo do PDF e CSV, jobs distintos, remoção após download, encerramento e cascata da remoção |

S2 e S3 são independentes: carregar `submission` em S3 não resolve nem
aprova o percurso de candidatura nova. Cobrir múltiplos candidatos e
docentes com dados distintos para detectar hardcoding e vazamento de
estado. Respostas reservadas usam outros valores dentro do mesmo contrato.

Os formulários completos devem ser exportados do Forms original, incluindo
os campos adicionais de doutorado; não adaptar o de mestrado trocando
somente o título. Mapeamentos de candidatura e recomendação precisam
apontar para campos e versões válidos. O formulário de aceite é associado
administrativamente no estado inicial, pois a API não oferece essa edição.

O pacote inicial deve incluir dados e recursos estáticos declarativos,
inclusive `data/signature.png` e recursos do PDF, sem código Python do
original. Conservar hashes dos bancos exportados, formulários, arquivos,
configuração e imagens. Os assuntos e corpos de e-mail são contratos a
congelar; as referências a 2026 e a mestrado existentes no original não
podem ser generalizadas silenciosamente ao avaliar doutorado.

## Tratamento das divergências do original

O requisito completo expressa os percursos a avaliar, mas o original não
é presumido correto. Não corrigir a referência ou trocar a fixture entre
os grupos para produzir uma suíte verde. Cada divergência recebe evidência
HTTP/banco/SMTP, requisito afetado e uma decisão explícita antes de
congelar a suíte. Comportamento desejado e compatibilidade com um bug são
medidas diferentes.

| Achado | Evidência disponível | Consequência para o v2 |
|---|---|---|
| Candidatura finalizada sem Submission local retorna 500 (issue 26) | Reproduzido por HTTP no v1; get_all_from_edict verifica a linha antes do upsert | S2 permanece no escopo; S3 pré-carregado não é substituto. Resolver tratamento antes de validar V2-INT-01 |
| PPI mapeado quebra a listagem; POSCOMP preenchido quebra detalhe | Reproduzidos no v1; conversão duplicada de checkbox e score numérico versus schema string | O v2 inclui esses valores. Não repetir as exclusões por dados do v1 para declarar cobertura completa |
| send-accept e send-letter tratam seções como objeto com email/responses | Indício por leitura: get_submissions_forms_by_id devolve lista de seções, os dois consumidores usam chaves de objeto | Reproduzir S6; não declarar envio funcionando só pela existência das rotas |
| Aceite pendente pode aparecer como replied | Indício por leitura: a presença de seções torna get_accept_info verdadeiro antes de submitted_at | Verificar os três estados, com a mesma resposta antes e depois do envio |
| Cadastro OAuth usa enum de papel onde a coluna é string | Indício por leitura em get_or_register_user | Conferir cadastro de novo usuário no provedor local; não testar só usuário existente |
| Múltiplos orientadores retornam objeto de exceção em vez de levantar erro | Indício por leitura em select_stats_submission | Conferir status HTTP e persistência; não presumir 409 pela classe da exceção |
| Edição/criação associam date_verification a avaliacao e date_evaluation a homologacao | Leitura de insert_edict e edit_edict | Registrar associação observada e expectativa antes de congelar; não corrigir os nomes por intuição |
| Inclusão de comentários no detalhe carrega relações, mas summary.comments permanece vazio | Indício por leitura em get_submission_by_id | Validar separadamente include_comments e GET comments; não inferir histórico correto a partir do OpenAPI |

Issue 26, falha do PPI e falha do POSCOMP foram reproduzidos no v1 e
continuam registrados em `../fixture.md`; os demais achados ainda não
foram reproduzidos nesta preparação.
Nada aqui constitui resultado de uma execução v2. Se houver correção da
referência, ela exige nova identificação e um conjunto de dados/suíte
congelados para todos os grupos; não misturar esse caso com o original v1.

Não converter limitações em xfail ou remover operações sem registrar o
denominador e o escopo resultantes. Se o objetivo escolhido exigir um
comportamento que o original não consegue executar, esse caso precisa de
um critério independente e identificação própria, em vez da afirmação de
que a suíte inteira passou na referência.

## Régua e separação de informação

Cada operação do inventário precisa de teste externo de comportamento,
além dos testes de fluxo entre operações. Cada requisito deve estar
rastreado; presença de rota no OpenAPI sozinha não vale como aprovação.
Cobrir caminhos válidos e erros relevantes, identidades distintas,
persistência e efeitos nas dependências. Usar HTTP, SQL de inspeção,
captura SMTP, leitura de arquivos e cliente original, sem importar as
funções Python das implementações avaliadas.

Preservar a política de divisão do piloto: aproximadamente 75% visíveis
e 25% reservados, com regra de arredondamento e estratificação registradas
antes das runs. Aplicar a estratificação também às integrações e aos
fluxos, não apenas às rotas. Variantes do mesmo cenário compartilham a
partição quando revelarem sua resposta esperada. Não copiar parametrizações
reservadas para o workspace e apenas marcá-las como skip.

Baseline e TDD recebem requisito e infraestrutura declarativa comum; a
suíte externa inteira permanece oculta. O TDD escreve seus próprios testes
e recebe somente o feedback deles. Rework começa do zero, com os testes
visíveis e contratos operacionais, sem implementação anterior ou código
original; os reservados são sua nota principal. A infraestrutura pública
precisa ser a mesma entre os grupos e registrada nas entradas de cada run.

Os testes do pipeline devem ter um contrato único com o gate antes do v2:
o desacordo entre httpx com servidor externo e TestClient do v1 está em
`tcc-hqt.12`. Não repetir sessões pagas para contornar essa falha de
infraestrutura. Ensaiar previamente o gate sem modelo, em container,
com uma implementação conhecida e uma entrega propositalmente quebrada.

CUA continua sendo avaliador final e está parado; o pedido atual não
autoriza retomá-lo. O piloto v2 deve primeiro obter evidência HTTP e de
integração. Qualquer validação posterior pelo Front/CUA é etapa final
separada, não ferramenta de feedback ao coder durante essas runs.

## Condição de congelamento e medição

O pacote estará pronto para execução quando requisitos, contratos de
e-mail/erros, fixtures e serviços externos locais estiverem identificados,
a régua estiver validada no original com as divergências resolvidas e o
split estiver congelado. Registrar cobertura viva do backend completo e
resultados por rota, requisito e integração, sem usar a cobertura parcial
v1 como medida do novo escopo.

Congelar modelo, imagem OpenCode, inventário de skills, runtime e imagens
das dependências. Manter temperatura 0.1 e top-p 0.9 comuns aos grupos.
O orçamento v1 não se transfere automaticamente para este escopo; o alvo
v2 deve registrar limites antes de qualquer chamada paga. Não iniciar
execuções apenas porque o texto dos requisitos existe.

RUN.log continua registrando duração, tokens, custo, retries, motivo da
parada e integridade dos testes. Separar custo registrado pelo executor de
cobrança final, inclusive chamadas interrompidas. Registrar cada falha do
pipeline, comportamento externo, integridade, skills disponibilizadas e
carregadas, hashes e versões. Avaliar até as entregas cujo gate não concluiu,
preservando o motivo; não confundir timeout do TDD com reprovação de toda
a API.

Para complexidade e cobertura, comparar o backend completo com o backend
completo, delimitando o mesmo conjunto de operações; não incluir Forms,
Front e serviços originais no código gerado. Uma execução por grupo
continua sendo exploração de viabilidade, sem inferência estatística.
