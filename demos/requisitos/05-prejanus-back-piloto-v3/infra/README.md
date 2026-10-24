# Infraestrutura declarada do piloto v2

O produto a reconstruir está em `../requisito.md`. Este diretório reúne
contratos de integração fornecidos ao agente, sem o código original.

`openapi-original.json` foi obtido por `GET /openapi.json` da instância
original em `http://localhost:8093`, em 17/10/2026. Seus 50 pares
método/caminho foram conferidos com os decoradores dos quatro routers e
de `main.py`. O documento descreve interfaces; não comprova que os
comportamentos ou integrações funcionem. Algumas respostas não têm schema
e são detalhadas no requisito em linguagem natural.

## Configuração da aplicação

| Variáveis ou recurso | Contrato |
|---|---|
| `APP_NAME`, `APP_ENV`, `APP_VERSION` | Identificação e ambiente; atalho de autenticação somente em `local` |
| `DB_CONNECTION_STRING` | Conexão do banco PreJanus |
| `DB_CONNECTION_STRING_FORMS` | Conexão do banco Forms; necessita das permissões de escrita das integrações |
| `BASE_URL` | URL pública usada nos links do Forms enviados por e-mail |
| `BACKEND_CORS_ORIGINS` | Origens do cliente separadas por vírgula, com credenciais |
| `SECRET_KEY` | Assinatura da sessão; igual entre instâncias que compartilham sessões |
| `DEV_USER_ID` | Id previamente existente; não habilita acesso fora de `local` |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL`, `SMTP_USE_TLS` | SMTP do ensaio; sem senha, sem autenticação; TLS conforme configuração |
| `SENHAUNICA_OAUTH_HOST` | Endereço do provedor OAuth local do ensaio |
| `SENHAUNICA_REQUEST_TOKEN_RESOURCE`, `SENHAUNICA_AUTHORIZE_URL`, `SENHAUNICA_ACCESS_TOKEN_RESOURCE`, `SENHAUNICA_CALLBACK_ID` | Request token, autorização, access token e callback |
| `SENHAUNICA_CONSUMER_KEY`, `SENHAUNICA_CONSUMER_SECRET` | Credenciais sintéticas do provedor local |
| `data/nusp_whitelist.txt` | NUSP autorizados, separados por linhas e/ou vírgulas |
| `/shared/uploads/` | Arquivos produzidos pelo Forms, legíveis pelo backend |
| `/tmp/` | Escrita e leitura de PDF e CSV temporários |
| `assets/logo.png`, `assets/usp.png`, `data/signature.png` | Recursos estáticos dos relatórios e mensagens |

Nenhuma credencial real é parte deste pacote. O cenário de sessão precisa
de HTTPS local para que o cliente respeite o cookie `Secure`; não alterar
o contrato do cookie apenas para o ensaio passar.

## Contrato da Senha Única

OAuth 1.0a com assinatura HMAC-SHA1, chave e segredo de `SENHAUNICA_CONSUMER_*`,
todas as rotas relativas a `SENHAUNICA_OAUTH_HOST`:

| Passo | Requisição | Resposta |
|---|---|---|
| Request token | `POST {SENHAUNICA_REQUEST_TOKEN_RESOURCE}`, assinado só com a chave do consumidor | `application/x-www-form-urlencoded` com `oauth_token` e `oauth_token_secret` |
| Autorização | O usuário abre `{SENHAUNICA_AUTHORIZE_URL}?oauth_token=...&callback_id={SENHAUNICA_CALLBACK_ID}` | O provedor devolve `oauth_token` e `oauth_verifier` ao callback |
| Access token | `POST {SENHAUNICA_ACCESS_TOKEN_RESOURCE}`, assinado com o request token, seu segredo e o verifier | `application/x-www-form-urlencoded` com `oauth_token` e `oauth_token_secret` |
| Dados do usuário | `POST wsusuario/oauth/usuariousp`, assinado com o access token e seu segredo | JSON com `loginUsuario` (NUSP), `nomeUsuario`, `emailPrincipalUsuario` e `vinculo` |

O pacote `senhaunicapy` listado no alvo implementa esse cliente; usá-lo é opcional.

## Testes do pipeline

O pytest do gate roda em container separado, com o backend já em execução
no ambiente de integração. Testes de rota usam `httpx.Client` síncrono com
a URL de uma variável de ambiente, nunca uma porta fixa:

| Variável | Instância |
|---|---|
| `CARONTE_API` | `APP_ENV=local`, `DEV_USER_ID=2` (docente `teacher` já cadastrado) |
| `CARONTE_API_ADMIN` | `APP_ENV=local`, `DEV_USER_ID=1` (`administrator`) |
| `CARONTE_API_OUTRO` | `APP_ENV=local`, `DEV_USER_ID=3` (outra docente, `teacher`) |
| `CARONTE_API_SECRETARIA` | `APP_ENV=local`, `DEV_USER_ID=4` (`secretary`) |
| `CARONTE_API_COORDENADOR` | `APP_ENV=local`, `DEV_USER_ID=5` (`coordinator`) |
| `CARONTE_API_ESTUDANTE` | `APP_ENV=local`, `DEV_USER_ID=6` (`student`) |
| `CARONTE_API_SENHAUNICA` | Sem atalho, com login pela Senha Única no provedor local |
| `CARONTE_API_SEM_ATALHO` | Fora do ambiente local: sem sessão, rotas protegidas respondem 401 |
| `SENHAUNICA_PROVEDOR` | Provedor OAuth local |
| `CARONTE_SMTP_API` | API HTTP da caixa SMTP local (smtp4dev) |

O provedor local autoriza sem tela. Com o `oauth_token` do request token,
`GET {SENHAUNICA_PROVEDOR}/wsusuario/oauth/authorize?oauth_token=...&perfil=...`
responde em JSON com `oauth_token` e `oauth_verifier`, que seguem para o
callback. Os perfis são `admin`, `docente`, `outro`, `secretaria`,
`coordenador` e `estudante`, já cadastrados; `novo`, na whitelist e ainda
sem cadastro; e `negado`, fora da whitelist.

Na caixa SMTP, `GET /api/Messages` lista as mensagens e
`GET /api/Messages/{id}/raw` devolve a mensagem completa. Os bancos e a
caixa voltam ao estado inicial antes de cada execução do gate, não entre
testes.

A porta 8083 citada no requisito é a publicação no ambiente de integração,
não um endereço disponível dentro do gate.

## Dados e serviços

Os esquemas e funções SQL são os do original congelado, em `esquema-prejanus.sql`
e `esquema-forms.sql`, já aplicados nos bancos do ambiente. Os bancos
PreJanus e Forms são conexões distintas. A preparação deve fornecer
concessões explícitas para leitura e escrita necessárias; o nome histórico
do usuário `forms_reader` não comprova essas concessões.

O conjunto de dados v2 deve conter formulários completos de mestrado,
doutorado, recomendação e aceite, com versões, árvores de mapeamento,
respostas sintéticas e anexos identificáveis. A fixture de consulta v1
serve de referência, mas é insuficiente para o novo escopo.

Forms, Front, Postgres, proxy, SMTP local, Redis, Celery e ClamAV continuam
fornecidos pelo ambiente. O backend se integra com Forms principalmente
pelo banco e pelos arquivos compartilhados, sem uma nova API HTTP entre
os serviços. O provedor OAuth local substitui apenas o servidor externo
USP, preservando o protocolo de comunicação.

O ambiente isolado, os bancos, as fixtures e os recursos do piloto v2 já estão
preparados pelo harness. Use os contratos acima e o alvo declarado nesta entrada.
