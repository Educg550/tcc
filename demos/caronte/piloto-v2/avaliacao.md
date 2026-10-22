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

Materialização em 17/10/2026: `ambiente.py preparar` sobe o projeto
Compose `caronte-piloto-v2` e grava `dados/forms.sql` e `dados/prejanus.sql`;
`ambiente.py restaurar` volta a esse estado antes de cada teste, inclusive os
PDFs dos uploads, gerados a partir das respostas `File`. A base cobre S0, S1
e S3: três editais (mestrado, doutorado, mestrado com PPI mapeado), quatro
candidaturas em duas versões do mestrado e uma de doutorado, três
recomendações (uma com recomendador repetido em outro candidato) e seis
papéis com login pelo provedor OAuth local. S4 a S7 são construídos pelos
testes via API; S2, por inserção no banco do Forms no formato que o Forms
grava. O percurso pelas telas do Forms (V2-INT-01) e pelo Front (V2-INT-03)
está pendente de decisão.

Os formulários completos devem ser exportados do Forms original, incluindo
os campos adicionais de doutorado; não adaptar o de mestrado trocando
somente o título. Mapeamentos de candidatura e recomendação precisam
apontar para campos e versões válidos. O formulário de aceite é associado
administrativamente no estado inicial, pois a API não oferece essa edição.

O pacote inicial deve incluir dados e recursos estáticos declarativos,
inclusive `data/signature.png` e recursos do PDF, sem código Python do
original. Conservar hashes dos bancos exportados, formulários, arquivos,
configuração e imagens. Decisão de 17/10/2026: assuntos e textos
institucionais dos e-mails não são avaliados, pois não fazem parte da
entrada do agente; a suíte confere destinatários, cópias, nome, link,
prazo, semestre, ano e assinatura.

## Tratamento das divergências do original

O requisito completo expressa os percursos a avaliar, mas o original não
é presumido correto. Não corrigir a referência ou trocar a fixture entre
os grupos para produzir uma suíte verde. Cada divergência recebe evidência
HTTP/banco/SMTP, requisito afetado e uma decisão explícita antes de
congelar a suíte. Comportamento desejado e compatibilidade com um bug são
medidas diferentes.

Em 17/10/2026 todos os achados abaixo foram reproduzidos por HTTP no
original, com a fixture v2 (`dados/`) e a suíte em `oraculo/`. Cada teste
segue o requisito, não o original; o mapeamento achado → testes está em
[`oraculo/divergencias.json`](./oraculo/divergencias.json), e o relatório
`.estado/ORACULO.json` acusa falha não registrada ou divergência que passou.

| Achado | Reprodução | Testes que falham no original |
|---|---|---|
| Candidatura finalizada sem Submission local (issue 26) | Listagem 500 `No Submission found for candidate form 20` | `test_candidatura_recem_finalizada_entra_na_listagem` |
| PPI mapeado | Listagem do edital 3 (PPI mapeado, mesmo formulário) responde 500 | `test_listagem_com_ppi_mapeado` |
| Nota do POSCOMP preenchida | Detalhe da inscrição 4 (Diego) responde 500 | `test_resumo_com_nota_do_poscomp` |
| `include_comments` | 200, mas `summary.comments` vazio com comentário gravado | `test_detalhe_com_comentarios` |
| `send-accept` | 500 sempre: indexa por `email` a lista de seções | `test_envia_formulario_de_aceite`, `test_aceite_nao_e_criado_duas_vezes`, `test_da_homologacao_ao_resultado_e_aceite` |
| Aceite pendente como `replied` | Convite sem resposta (montado por SQL) já aparece respondido | `test_estado_do_aceite_pendente` |
| `send-letter` | 500 sempre, mesmo acesso | `test_envia_carta_de_aceite`, `test_carta_nao_e_enviada_duas_vezes` |
| Múltiplos orientadores | `user_ids` vazio ou com dois ids: 200 sem alteração | `test_aprovacao_exige_um_unico_orientador_existente[user_ids1/3]` |
| Cadastro OAuth | Usuário novo gravado com papel `TEACHER` | `test_novo_usuario_autorizado_vira_docente` |
| E-mail de acesso nos relatórios | Anexos de e-mails de candidatos do PDF saem vazios; a listagem nunca lê `form_response.email` | `test_pdf_com_todas_as_secoes` |

Decisão de 17/10/2026: os testes continuam exigindo o comportamento do
requisito e contam no denominador; no original, falham. Não há xfail.

V2-INT-01 (candidatura pelas telas do Forms, com ClamAV e Celery) e
V2-INT-03 (Front original) ficam para a etapa final do CUA, separada das
runs, e não entram na suíte HTTP. A suíte cobre o lado do backend desses
percursos: resposta nova gravada no banco do Forms, anexos no volume e o
link de correção abrindo no Forms real.

Os casos que quebram o original ficam isolados em dados próprios (edital 3,
inscrição 4, respostas criadas no teste), para não contaminar o restante:
os demais testes passam no original.

Observações sem teste reprovado, porque o requisito não fixa o comportamento:

- O detalhe de uma inscrição de formulário versionado traz as seções de
  todas as versões, com `null` nos campos da outra versão; o teste só exige
  que todos os campos respondidos estejam presentes.
- NUSP fora da whitelist responde 500, sem sessão nem cadastro; datas fora de
  ordem respondem 500 e vagas não inteiras também; edital inexistente, 400.
  Os testes exigem só a recusa (código ≥ 400) e o estado inalterado.
- A listagem devolve o orientador com `id: -1` fixo, com nome e e-mail certos.
- A associação de datas a fases já está escrita em V2-EDI-02 como o original
  faz; os testes a confirmam.
- O esquema original declara `version NOT NULL DEFAULT 1` em seções e campos.
  O fallback para versão nula de V2-FOR-02 é inalcançável e não é testado.

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

Cobertura viva medida em 19/10/2026 por `ambiente.py cobertura` (os três
backends originais sob coverage, descontado `../codigo-morto.json`):
2398/2565 linhas (93,5%), 50/50 operações exercitadas, 233/247 casos
aprovados e só as 14 divergências registradas falhando. O coverage precisa de
`--concurrency=thread,greenlet`: o SQLAlchemy async retoma em greenlet e,
sem isso, perde as linhas após cada consulta (dava 68,1%; os 52,9% do v1
foram medidos assim e estão subestimados). O que sobra descoberto é sobretudo
o que as divergências impedem de executar (`send-accept`, `send-letter`) e
código sem chamador que o vulture não pegou (`send_approved_emails.py`, a
primeira implementação em `utils/map_candidate.py`).

Decisão de 21/10/2026: o login OAuth deixa de ser porta única. Com a
fixture anterior, todo caso logado passava por `entrar()`, e um defeito no
login do candidato virava erro de preparação em 152/247 casos (62%), sem
exercitar a regra do caso. Agora `clientes(perfil)` usa o atalho
`DEV_USER_ID` do V2-AUT-01, com uma instância `local-<perfil>` por perfil,
e o fluxo OAuth fica nos 7 testes de V2-AUT-02, que entram por `anonimo`.
No original o resultado não mudou: 233/247, só as 14 divergências
registradas falhando, 50/50 operações e 2398/2565 linhas (93,5%).

Reavaliação das runs v3 com a fixture nova (código idêntico, conferido
pelos hashes; resultados em `_harness/oraculo-atalho/`, os anteriores
preservados):

| Run | Antes | Depois | Visíveis | Reservados | V2-AUT-02 |
|---|---|---|---|---|---|
| Baseline v3 | 26/247 | 139/247 | 89/161 | 49/85 | 0/7 |
| TDD v3 | 29/247 | 185/247 | 123/161 | 61/85 | 0/7 |

As runs v2 e anteriores foram medidas com a fixture antiga e não são
comparáveis a esses números sem reavaliação.

Split congelado em 17/10/2026 por `oraculo/split.py` (regra no próprio
arquivo e em `oraculo/split.json`): a unidade é a função de teste, com
todas as parametrizações; estratos são o primeiro requisito. Resultado:
94 funções visíveis e 32 reservadas, 161 e 85 casos. A proporção por caso
passa de 25% porque a matriz de 403 por papel (26 casos) caiu inteira na
reserva.

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
