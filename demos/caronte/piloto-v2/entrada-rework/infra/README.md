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

## Testes do pipeline

O pytest do gate roda em container separado, com o backend já em execução
no ambiente de integração. Testes de rota usam `httpx.Client` síncrono com
a URL de uma variável de ambiente, nunca uma porta fixa:

| Variável | Instância |
|---|---|
| `CARONTE_API` | `APP_ENV=local`, `DEV_USER_ID=2` (docente já cadastrado) |
| `CARONTE_API_SEM_ATALHO` | Fora do ambiente local: sem sessão, rotas protegidas respondem 401 |

A porta 8083 citada no requisito é a publicação no ambiente de integração,
não um endereço disponível dentro do gate.

## Dados e serviços

Os esquemas e funções SQL são os do original congelado. Os bancos
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

**Este pacote ainda não está pronto para executar no harness:** faltam a
fixture v2 materializada, a suíte validada e o alvo com imagens, dependências
e orçamento congelados. Não reutilizar automaticamente o `alvo.toml`, os
bancos ou os limites de execução do piloto de consulta.
