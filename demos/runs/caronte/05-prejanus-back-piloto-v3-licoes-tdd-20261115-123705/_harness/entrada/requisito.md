# Piloto v3 — PreJanus Back completo

Escopo funcional preservado do piloto v2 de 17/10/2026. Reconstruir todo o backend do PreJanus e suas
integrações, a partir do original Caronte registrado no commit
`46b89c1d5519aeae40c088ee94262e9b739a7d48`. O piloto de consulta anterior
permanece em `02-caronte-consulta`, com suas entradas e resultados preservados.

O produto é uma API FastAPI para acompanhar processos seletivos de mestrado
e doutorado: configurar editais e formulários, consultar candidaturas e
recomendações, registrar avaliações, definir orientadores e comunicar o
resultado. A reconstrução substitui apenas o serviço `prejanus-back`.
Forms e PreJanus Front continuam sendo os clientes e serviços originais.

O contrato declarativo de métodos, caminhos, parâmetros e corpos JSON está
em [`infra/openapi-original.json`](./infra/openapi-original.json), coletado
do original em execução. São **50 operações de aplicação**, incluindo a
raiz; `/docs`, `/redoc` e `/openapi.json` são interfaces auxiliares.
Preservar os nomes das chaves e os caminhos, inclusive `sessions`,
`private_notes` e `reesend_submission`. Onde o OpenAPI não descreve a
resposta, valem os comportamentos e campos explicitados abaixo.

## Organização obrigatória da implementação

Implemente um projeto modular. `app.py` deve apenas criar e configurar a aplicação,
registrar middleware e conectar routers. Separe configuração, conexões dos dois
bancos, autenticação/permissões, routers por domínio e serviços de integração
(Forms, OAuth, e-mail e relatórios). Escolha os nomes e a estrutura de diretórios;
não há um número mínimo artificial de arquivos. Cada módulo deve conter a lógica
da sua responsabilidade, sem depender de um arquivo central com toda a aplicação.

Construa um bloco funcional por vez, escrevendo seus arquivos separadamente pelas
ferramentas e conectando-o aos módulos anteriores. Conclua todos os requisitos
nesta sessão. Não entregue apenas estrutura, stubs ou funcionalidades simuladas.

## Ambiente e persistência

### V2-AMB-01 — Substituir o backend no ambiente original

Executar Python 3.11 e FastAPI em container, ouvindo em `0.0.0.0` na porta
8000, publicada como 8083 no ambiente de integração. `GET /` retorna
`{"message":"Hello World"}`. Expor documentação e contrato OpenAPI.
Aceitar configuração por variáveis do ambiente descritas no README da
infraestrutura. Permitir requisições das origens configuradas em
`BACKEND_CORS_ORIGINS`, com credenciais, para o Front original.

Ler anexos em `/shared/uploads`; gerar relatórios temporários em `/tmp`.
Os arquivos institucionais dos relatórios, a assinatura das cartas e a
whitelist de autenticação são recursos fornecidos na preparação. Os
containers da aplicação não precisam acessar o socket Docker.

### V2-BD-01 — Usar os dois bancos do sistema

Persistir no Postgres do PreJanus os usuários, editais, fases, mapeamentos
por versão, inscrições, orientadores, vagas, comentários, favoritos,
etiquetas, notas privadas e visualizações. Requisições posteriores e
reinícios do backend devem recuperar o estado gravado. Preservar o esquema
original e suas chaves, relações, unicidade e exclusões em cascata.

Consultar o banco do Forms para formulários, seções, campos, respostas,
compartilhamentos e versões, usando a conexão própria. O Forms não é
somente leitura neste piloto: mudanças de fase, reabertura de respostas e
criação de respostas de aceite precisam persistir nesse banco. As funções
SQL do Forms são infraestrutura fornecida; não reimplementá-las nem
substituir os bancos por dados fixos em memória.

## Identidade e permissões

### V2-AUT-01 — Identificar o usuário e permitir o desenvolvimento local

`GET /auth/login` devolve `id`, `name`, `email`, `nusp` e `role`.
Somente com `APP_ENV=local` e `DEV_USER_ID` definido, usar o usuário já
existente com esse id, sem OAuth. Um id local inexistente produz erro de
configuração, sem criar usuário implicitamente. Fora desse ambiente, a
variável não autentica ninguém. Sem sessão válida, as rotas protegidas
respondem 401.

### V2-AUT-02 — Completar o fluxo Senha Única

`POST /auth/login/senhaunica`, sem `oauth_token`, obtém o request token,
guarda seu segredo na sessão e responde com `redirect_to`. No retorno
com `oauth_token` e `oauth_verifier`, exige o segredo da mesma sessão,
troca pelo access token e consulta os dados do usuário USP. Aplicar a
whitelist de NUSP fornecida em `data/nusp_whitelist.txt`.

Reutilizar o cadastro pelo e-mail, preservando seu papel; para um novo
usuário autorizado, cadastrar nome, e-mail, NUSP e papel de docente
(`teacher`). Guardar `user_id` na sessão para os acessos seguintes.
Sem o segredo de retorno, responder 401; falhas nas trocas de token
respondem 500. A sessão dura oito horas e usa cookie com `SameSite=lax`
e `Secure`, como na interface original.

O provedor do ensaio é um serviço local que reproduz o contrato OAuth da
USP; não substituir essa integração pelo atalho `DEV_USER_ID` nos casos
que avaliam OAuth. Não são necessárias credenciais institucionais.

### V2-AUT-03 — Respeitar papéis e autoria das operações

Os papéis administrativos são `administrator`, `secretary` e
`coordinator`. Eles podem criar e alterar editais, mudar fases, encerrar e
remover editais, manter mapeamentos, selecionar candidaturas, solicitar
correções e gerar relatórios. Um docente (`teacher`) recebe 403 ao tentar
essas operações. O papel `student` também existe no cadastro; não equivale
a um administrador.

Comentários e etiquetas só podem ser excluídos pelo autor, inclusive
quando outro usuário é administrador. Favoritos, notas privadas, vagas e
interesses pertencem ao usuário da operação, conforme os requisitos
seguintes. As consultas e as rotas individuais `send-accept` e `send-letter`
exigem autenticação, sem restrição administrativa adicional no original.
A solicitação de correção continua restrita aos papéis administrativos.
Os downloads de relatórios por `job_id` são públicos no contrato original;
sua criação é restrita.

## Formulários e versões

### V2-FOR-01 — Encontrar formulários para configurar editais

`GET /forms` lista os formulários do Forms. Os filtros opcionais `year` e
`notice` correspondem às tags `Ano` e `Edital` e podem ser combinados.
Retornar os metadados do formulário, incluindo id, título, tags e fase.

### V2-FOR-02 — Consultar estrutura e versões dos formulários

`GET /forms/{form_id}` devolve seções e campos na ordem da estrutura;
`GET /forms/{form_id}/sections`, os ids das seções. Com `version`,
selecionar essa versão; para versão 1, aceitar também seções cuja versão
seja nula. Sem o parâmetro, selecionar seções ativas. Quando a seleção
não encontra seções, preservar o fallback original para todas as seções
do formulário, ordenadas por posição.

`GET /forms/{form_id}/sessions/{section_id}/fields` consulta os campos da
seção, com seus metadados e posições. Preservar o segmento literal
`sessions`. Formulários de candidatura, recomendação e aceite, incluindo
os de doutorado, usam essas mesmas interfaces.

## Editais

### V2-EDI-01 — Listar e consultar editais

`GET /edicts` lista editais por data de encerramento decrescente e aceita
`type` e `is_open`, isolados ou combinados. Cada item contém `id`, `title`,
`year`, `semester`, `edict_type` e `is_open`.

`GET /edicts/{edict_id}` devolve a configuração completa, incluindo
`candidate_form_id`, `recommender_form_id`, descrição, datas, tipo, fase
atual, `phases` e `slots`. As vagas são as do usuário autenticado naquele
edital, como string; na ausência de configuração, `"0"`.

### V2-EDI-02 — Criar e editar o edital e suas datas

`POST /edicts` recebe `title`, `description`, `year`, `semester`,
`edict_type`, `is_open`, `candidate_forms`, `recommenders_forms` e as quatro
datas `date_application`, `date_verification`, `date_evaluation` e
`date_closed`. Criar o edital associado ao autor, com fase inicial
`inscricoes` e quatro registros: `inscricoes`, `homologacao`,
`avaliacao` e `encerrado`. Retornar o id e os dados criados.

`POST /edicts/{edict_id}/edit` altera título, descrição, ano, semestre,
tipo e as quatro datas; ano e semestre chegam como strings nessa rota.
`POST /edicts/{edict_id}/edit-date` altera apenas `closed_date` e retorna
seu novo valor. As quatro datas da edição completa e da criação precisam
estar em ordem cronológica estrita. A associação vigente no original é
`date_application` para `inscricoes`, `date_evaluation` para `homologacao`,
`date_verification` para `avaliacao` e `date_closed` para `encerrado`.
Não inverter essa associação implicitamente pelos nomes das variáveis.

### V2-EDI-03 — Mudar fase e propagar ao Forms

`POST /edicts/{edict_id}/advance-phase` recebe o `id` de uma fase do
edital, grava essa fase como atual e responde com `id` e `label`.
Também altera a fase do formulário de candidatura no banco do Forms:

| Fase PreJanus | Fase Forms |
|---|---|
| `inscricoes` | `Registration` |
| `homologacao` | `Approval` |
| `avaliacao` | `Completed` |
| `encerrado` | `Completed` |

A avaliação observa os dois bancos e o comportamento do Forms após a
chamada; um HTTP 200 sem a mudança no Forms não satisfaz este requisito.

### V2-EDI-04 — Encerrar e remover editais

`PATCH /edicts/{edict_id}/close` recebe `confirmation_deadline` e
`send_approval_letter`, fecha o edital (`is_open=false`) e responde 200.
Encerrar novamente responde 409. Essa rota não envia cartas no original;
o envio individual é V2-MAI-03.

`DELETE /edicts/{edict_id}/remove` responde 200 e remove o edital e seus
registros dependentes no PreJanus, preservando os formulários e respostas
do Forms. Consultas posteriores refletem a remoção.

## Mapeamentos dos formulários

### V2-MAP-01 — Criar mapeamentos por tipo e versão

Para `candidates` e `recommenders`,
`POST /edicts/{edict_id}/{tipo}/mappings/versions/{version}/` cria um
mapeamento do formulário correspondente ao edital. O corpo é uma árvore
JSON: nós agrupam propriedades; folhas são `{"section":id,"field":id}`;
um valor nulo indica propriedade não mapeada.

Validar as referências seção/campo na versão solicitada, com o fallback
original quando não há campos nessa versão. Uma referência inválida
responde 422. Registrar autor, formulário, versão e estado ativo; não criar
dois mapeamentos para o mesmo edital, tipo e versão. Devolver id, edital,
tipo, autor, versão, árvore e estado ativo.

### V2-MAP-02 — Consultar, atualizar e excluir mapeamentos

Para os dois tipos, `GET /edicts/{edict_id}/{tipo}/mappings` lista os
mapeamentos existentes. `PUT` e `DELETE` em
`/edicts/{edict_id}/{tipo}/mappings/versions/{version}/{mapping_id}` alteram
a árvore ou excluem a associação identificada pelos quatro componentes.
Combinações inexistentes respondem 404. Excluir responde com
`{"message":"Mapping deleted successfully"}`. A alteração deve aparecer
nas consultas posteriores e preservar as outras versões.

### V2-MAP-03 — Identificar versões ainda sem mapeamento

Para os dois tipos,
`GET /edicts/{edict_id}/{tipo}/forms/versions/unmapped` lista as versões
distintas presentes nas inscrições do edital sem mapeamento daquele tipo.
Criar ou remover o mapeamento altera a lista; uma versão sem inscrições
não aparece apenas por existir no Forms.

## Inscrições e consulta

### V2-INS-01 — Listar candidaturas e integrar recomendações

`GET /edicts/{edict_id}/submissions` retorna `{"submissions":[...]}`.
Usar as respostas de candidatura e recomendação do Forms e o mapeamento
da versão registrada na inscrição. Incluir identidade do candidato,
formação, pesquisa, indicadores, situação, orientador, interesses,
etiquetas, favorito e aceite, com as chaves do OpenAPI fornecido.

Filtrar por `stats` e, com `only_favorites=true`, pelos favoritos do
usuário autenticado. Atualizar a associação das recomendações à inscrição
usando os dados do candidato e recomendador, sem misturar candidatos.
Leituras repetidas não duplicam inscrições, nem apagam decisões ou
orientadores já registrados.

O ciclo de uma candidatura recém-finalizada no Forms também pertence ao
escopo v2. A versão original falha quando ainda não existe sua inscrição
local; o protocolo registra esse caso separadamente. A pré-carga de uma
inscrição para o cenário de consulta não comprova essa integração.

### V2-INS-02 — Consultar resumo e todas as respostas

`GET /submissions/{submission_id}` devolve `summary` e `submission_form`.
O primeiro contém dados pessoais, e-mail de acesso, formação, POSCOMP,
pesquisa, recomendações, situação, favorito, etiquetas, interesse do
usuário, sua nota privada, aceite, semestre e `letter_sent`.

`submission_form` contém todas as seções e campos, com seus ids, nomes,
rótulos, tipos, prefixos e valores, inclusive campos não mapeados no
resumo. Preservar textos, escolhas, números, datas e nomes dos arquivos.
Um campo opcional vazio não pode eliminar os demais campos da seção.
As respostas de versões anteriores devem continuar consultáveis.

Aceitar `include_comments`; a atividade com comentários também possui
a rota específica descrita em V2-AVA-01. Inscrição inexistente responde
404. Não criar uma inscrição durante o acesso ao detalhe.

### V2-INS-03 — Baixar anexos da inscrição

`GET /submissions/{submission_id}/files/{label}/{filename}` devolve o
PDF associado ao campo `label` daquela candidatura, com
`Content-Type: application/pdf`, `Content-Disposition: attachment` e
conteúdo preservado. Conferir o nome solicitado com o valor do campo;
não servir um arquivo pertencente a outra candidatura ou fora dos
uploads. Atender todos os campos de arquivo, inclusive os adicionais dos
formulários de doutorado.

## Avaliação e acompanhamento

### V2-AVA-01 — Comentários e histórico de atividade

`POST /submissions/{submission_id}/comments` recebe `comment` e datas
opcionais, associa o autor e responde com id, usuário, inscrição, texto e
datas. Sem `created_at`, usar o instante da criação. Só criar na fase
`avaliacao`; em outra fase, responder 400.

`GET /submissions/{submission_id}/comments` consulta a atividade:
comentários e eventos de candidatura, recomendações e aceite, com autor,
texto, tipo e data, em ordem cronológica. Não registrar um novo evento só
por ler. `DELETE /submissions/comments/{comment_id}` remove o comentário
do próprio autor com 204; outro autor recebe 403 e um id inexistente, 404.

### V2-AVA-02 — Favoritos por usuário

Na fase `avaliacao`, `POST /submissions/{submission_id}/favorites` marca
o favorito do usuário e responde 201. Uma repetição responde 409;
`DELETE` no mesmo caminho remove com 204, ou 404 se não existir.
Não alterar favoritos de outro usuário. Detalhe e listagem refletem a
marca de quem consulta; o filtro de favoritos respeita essa identidade.

### V2-AVA-03 — Etiquetas e cores por usuário

Na fase `avaliacao`, `POST /submissions/{submission_id}/labels` recebe
`label` e `color`, cria a etiqueta de contexto `candidate` e responde com
id, autor, inscrição e rótulo. Atualizar a cor das etiquetas do mesmo
autor e mesmo rótulo em outras inscrições, preservando os demais autores
e o contexto de interesses (`bidding`).

`GET /submissions/{submission_id}/labels` retorna o catálogo de etiquetas
distintas do usuário, com `id`, `label` e `color`; apesar do caminho, esse
catálogo abrange suas inscrições. As etiquetas mostradas no detalhe
pertencem à inscrição consultada. `DELETE /submissions/label/{label_id}`
remove a etiqueta do próprio autor com 204, com 403 para outro autor e
404 para um id inexistente.

### V2-AVA-04 — Notas privadas

Na fase `avaliacao`, `POST /submissions/{submission_id}/private_notes`
recebe `note`, cria ou atualiza a nota do par usuário/inscrição e devolve
o texto. Uma atualização não cria outra nota. O detalhe devolve apenas a
nota privada do usuário autenticado, ou string vazia quando não existe;
trocar de usuário não expõe o texto do anterior.

### V2-AVA-05 — Registrar visualizações

`POST /submissions/{submission_id}/view` responde 200 e registra uma
visualização por usuário, inscrição e dia em `America/Sao_Paulo`.
Repetições no mesmo dia não criam outra linha; outro usuário ou outro dia
pode criar. `GET` no mesmo caminho lista as visualizações com usuário e
datas. Reiniciar o backend não apaga o histórico.

## Orientação e resultado

### V2-SEL-01 — Vagas e manifestação de interesse

`POST /edicts/{edict_id}/slots` recebe `amount` como string e atualiza as
vagas do usuário naquele edital. Valor vazio ou negativo vira `"0"`;
texto que não representa inteiro é rejeitado. Repetir atualiza o registro.

`POST /submissions/{submission_id}/bidding` recebe `bidding` e `user_id`
opcional. Valores aceitos: `decline`, `available`, `interested`, `agreed`,
`interested_scholarship` e string vazia. Um usuário administrativo pode
indicar outro usuário; para os demais, usar sempre o próprio id. Manter
um interesse corrente por par usuário/inscrição, separado das etiquetas
de candidato, e refletir a alteração no detalhe e na listagem.

### V2-SEL-02 — Selecionar candidatura e orientador

`POST /submissions/{submission_id}/select` recebe `stats` (`approved`,
`refused`, `underreview` ou `waitlist`) e `user_ids`, lista ou nulo.
Somente papéis administrativos alteram a decisão. Aprovar exige um único
orientador existente; registrar sua associação e o estado aprovado.
As outras situações atualizam o estado. Uma inscrição inexistente
responde 404 e um edital fechado impede alterações, com 409.

`POST /submissions/{submission_id}/entry-semester` recebe `semester` e
grava a escolha. Normalizar referências a primeiro/first e segundo/second
para `Primeiro semestre.` e `Segundo semestre.`; os outros textos são
preservados. O detalhe usa a escolha gravada antes do valor do Forms.

## Comunicação e efeitos no Forms

### V2-MAI-01 — Solicitar correção da candidatura

Na fase `homologacao`, um usuário administrativo usa
`POST /submissions/{submission_id}/reesend_submission` com `text`.
Reabrir a resposta de candidatura no Forms com seção atual zero e enviar
ao e-mail de acesso do candidato a solicitação, o motivo e o link
`{BASE_URL}/form/{token}` da própria resposta. Colocar o solicitante em
cópia oculta. Responder com `message` e `email_sent`.

O link precisa abrir a candidatura existente no Forms, permitindo sua
correção e reenvio. Verificar estado antes e depois no Forms e mensagem
recebida pelo servidor SMTP local.

### V2-MAI-02 — Criar e enviar formulário de aceite

`POST /submissions/{submission_id}/send-accept` exige candidatura aprovada
e formulário de aceite configurado no edital. Criar no Forms um
compartilhamento privado de resposta única, com expiração na data de
encerramento do edital, e uma resposta vinculada ao e-mail do candidato.
Gravar o id dessa resposta em `submission.accept_form_id`.

Enviar ao candidato mensagem em português e inglês, com nome, prazo e
link `{BASE_URL}/form/{token}`, copiando o orientador. Responder com
`message` e `email_sent`. Formulário de aceite não configurado responde
404; candidato não aprovado ou aceite já criado responde 400. Repetir
não cria outro compartilhamento, outra resposta ou outro envio.

A resposta preenchida no Forms deve aparecer no detalhe e na listagem,
com decisão, observações e data. Distinguir ausência de convite, convite
pendente e resposta enviada (`not_sent`, `sent`, `replied`). O formulário
de aceite e sua associação inicial ao edital são dados administrativos
da preparação, pois a API original não oferece um setter próprio.

### V2-MAI-03 — Enviar carta de aceite

`POST /submissions/{submission_id}/send-letter` envia ao candidato
aprovado uma carta HTML com sua identificação, orientador, semestre e
ano de ingresso, copiando o orientador e incluindo a assinatura fornecida.
Responder com `message` e `email_sent` e persistir `letter_sent=true`.
Uma candidatura não aprovada ou carta já enviada responde 400; repetir
não envia outra carta. Assuntos e textos institucionais ficam a critério
da implementação; os valores personalizados citados acima são obrigatórios.

Todos os e-mails do ensaio são entregues ao SMTP local; o estado no banco
e a recepção da mensagem são evidências distintas. Um retorno 200 ou uma
flag gravada isoladamente não comprovam entrega.

## Relatórios

### V2-REL-01 — Consultar participantes e gerar relatório PDF

`POST /edicts/{edict_id}/interactors_list` recebe as opções
`list_of_advisors`, `relation`, `approved`, `refused`, `underreview`,
`general_statistics` e `show_emails`, todas inicialmente falsas.
No modo padrão `plain_text`, devolver os usuários que interagiram no
edital por comentários, favoritos, etiquetas ou notas privadas.

Com `mode=pdf`, responder `{"job_id":"...","status":"processing"}`
e gerar o relatório em segundo plano. Incluir as seções selecionadas,
estatísticas de candidaturas finalizadas e em preenchimento, relação de
aprovados e orientadores, listas de e-mails quando solicitadas, ano do
edital e recursos institucionais. Conferir conteúdo e números do PDF,
permitindo variação de metadados binários e data de geração.

### V2-REL-02 — Exportar interesses e vagas em CSV

`POST /edicts/{edict_id}/pairing-biddings` responde com `job_id` e
`status=processing` e gera um CSV. A primeira coluna é `#`; as demais
são e-mails dos docentes com manifestações de interesse. A linha
`slots` informa as vagas de cada docente naquele edital. Cada linha
seguinte identifica uma candidatura pelo e-mail e contém os interesses
dos docentes, preservando campos vazios e o formato CSV.

### V2-REL-03 — Recuperar arquivos de relatórios

`GET /edicts/download_pdf/{job_id}` e
`GET /edicts/download_csv/{job_id}` entregam os arquivos gerados com os
tipos `application/pdf` e `text/csv` e disposição `inline`. Antes de
estar pronto, ou para um job inexistente, responder 404. O arquivo é
removido após o consumo completo; nova tentativa recebe 404. Os jobs
usam ids distintos para não confundir downloads entre relatórios.

## Percursos completos de integração

### V2-INT-01 — Da candidatura à consulta e recomendação

Com o Forms original, preencher e finalizar uma candidatura com anexos.
Acessar a API como docente, encontrar o candidato, consultar todas as
respostas, baixar os documentos e consultar as recomendações recebidas.
Cobrir mestrado e doutorado com seus formulários completos, além de
versões distintas. A criação e entrega dos convites de recomendação é
responsabilidade do Forms; o backend consome as respostas e as associa
à candidatura. Não usar o estado pré-carregado da consulta para declarar
que o percurso de criação passou.

### V2-INT-02 — Da homologação ao resultado e aceite

Configurar edital e mapeamentos, avançar para homologação, solicitar
correção, corrigir e reenviar pelo Forms. Avançar para avaliação, registrar
comentários, favoritos, etiquetas, notas, vagas e interesses; aprovar com
orientador e semestre. Enviar formulário de aceite, responder pelo Forms,
consultar resultado, enviar carta e gerar PDF e CSV. Conferir efeitos nos
dois bancos, anexos e cada e-mail no SMTP local. Encerrar o edital e
verificar a restrição a novas decisões.

### V2-INT-03 — Compatibilidade com o Front e serviços compartilhados

O PreJanus Front original deve continuar consumindo as mesmas URLs,
corpos, cookies e arquivos do backend substituído, inclusive através do
proxy original. O Forms mantém suas integrações com Redis, Celery,
ClamAV, SMTP e uploads. Exercitar envio de PDF e links das mensagens
com essa infraestrutura real; não reconstruir esses serviços dentro da
API nem atribuir seu código ao modelo avaliado.

Os percursos são critérios de aceitação do escopo completo. Casos em que
o original falha precisam de tratamento registrado antes do congelamento
e das novas execuções; não reduzir silenciosamente o v2 à consulta.
