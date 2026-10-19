# Feira Livre: marketplace entre pessoas

Implemente uma aplicação completa de compra e venda, inspirada em Mercado Livre e
OLX, chamada **Feira Livre**. A mesma conta pode comprar e vender: não existe escolha
de papel nem troca de perfil para acessar essas funções. Entregue frontend e backend
integrados, com dados persistidos em PostgreSQL e navegação real entre telas.

## Stack e execução

Use a stack do Caronte/PreJanus:

- Backend: Python 3.11, FastAPI, SQLAlchemy 2, Pydantic 2, PostgreSQL 17 e psycopg 3.
  O ponto de entrada é `backend.app:app`; todos os endpoints começam com `/api`.
  Pode usar SQLAlchemy síncrono; escolha uma forma consistente para toda a aplicação.
- Frontend em `frontend/`: Next.js **15.5.7**, React e React DOM **19.1.1**,
  TypeScript **5.9.2**, Material UI **7.3.1** e Emotion **11.14.x**. Use App Router.
  Declare essas dependências em `frontend/package.json`, com scripts `dev`, `build`
  e `start`. O executor fornece Node.js e instala os pacotes após a geração.
- O frontend usa URLs relativas `/api/...`. Configure um rewrite do Next para
  `API_INTERNAL_URL`, cujo padrão é `http://127.0.0.1:8000`, preservando `/api`.
  Isso permite cookies na mesma origem. Não fixe outra URL no JavaScript do navegador.
- Leia `DATABASE_URL` do ambiente; o padrão de desenvolvimento é
  `postgresql+psycopg://marketplace:marketplace@127.0.0.1:55432/marketplace`.
  Crie as tabelas no startup. O executor fornece um PostgreSQL vazio e isolado.
- Inclua `README.md` com comandos de instalação e execução, variáveis e credenciais
  de demonstração. Inclua `.env.example`, sem credenciais de serviços reais.
- Não use SQLite, armazenamento local do navegador ou arrays em memória como banco
  da aplicação. Não substitua o backend por mocks ou rotas API do Next.
- Você pode escrever os arquivos, mas não executar comandos. O executor faz instalação,
  build e verificações após a entrega. Estruture em módulos pequenos e funcionais.

## Contrato de dados

JSON usa nomes em inglês. Dinheiro é inteiro em centavos: `price_cents=15990` significa
R$ 159,90. Datas são ISO 8601. IDs são inteiros. Erros usam `{"detail": "mensagem"}`,
com status HTTP adequado. Não devolva hashes de senha nem tokens de sessão no JSON.

Usuário público: `id`, `name`, `email`. Anúncio: `id`, `title`, `description`,
`price_cents`, `stock`, `category`, `condition`, `city`, `image_url`, `status`,
`seller` (ao menos `id` e `name`), `created_at`. Categoria é uma de `eletronicos`,
`casa`, `livros`, `moda`, `outros`; condição é `novo` ou `usado`; status do anúncio
é `active` ou `inactive`. Uma imagem é uma URL opcional; sem URL use um placeholder
local. A aplicação deve continuar utilizável sem baixar nenhuma imagem externa.

## Requisitos funcionais

### R1 — Cadastro, sessão e conta

`POST /api/auth/register` recebe `{name, email, password}` e retorna o usuário com
status 201. Nome não vazio, e-mail válido e único, senha com ao menos 8 caracteres;
e-mail duplicado retorna 409. Guarde senha com Argon2. `POST /api/auth/login` recebe
`{email, password}` e retorna `{"user": ...}` com cookie de sessão HttpOnly.
Credencial incorreta retorna 401. `GET /api/auth/me` retorna o usuário da sessão ou
401. `POST /api/auth/logout` invalida a sessão e retorna 204. A sessão sobrevive a
reinício do backend. Permita editar o nome com `PATCH /api/auth/me`.

### R2 — Catálogo, busca e paginação

`GET /api/listings` é público e lista somente anúncios ativos com estoque positivo.
Aceita `q` (busca sem distinguir maiúsculas no título e descrição), `category`,
`condition`, `city`, `min_price`, `max_price` (centavos), `sort` (`recent`,
`price_asc`, `price_desc`), `page` (começa em 1) e `limit` (padrão 12, máximo 50).
Retorna `{items, total, page, limit}`. Filtros se combinam; página vazia tem
`items: []` e total correto. `GET /api/listings/{id}` mostra o detalhe público de
anúncio ativo; inexistente ou inativo retorna 404. Mostre nome do vendedor e
outros anúncios dele. `GET /api/sellers/{id}` retorna nome, média das avaliações
e quantidade de avaliações. `GET /api/sellers/{id}/listings` retorna lista paginada.

### R3 — Anunciar e gerenciar as próprias vendas

`POST /api/listings` exige sessão e recebe `title`, `description`, `price_cents`,
`stock`, `category`, `condition`, `city` e `image_url` opcional. Título de 3 a 120
caracteres, descrição de 10 a 5000, preço positivo e estoque inteiro de 1 a 999.
O servidor define o vendedor e retorna o anúncio com 201. `PATCH /api/listings/{id}`
permite ao dono editar esses dados e `status`. Outro usuário recebe 403; anônimo,
401. `GET /api/me/listings` inclui anúncios ativos, inativos e sem estoque do dono,
com paginação. Não permita que o payload transfira o anúncio para outra pessoa.

### R4 — Favoritos

`POST /api/favorites/{listing_id}` adiciona um anúncio ativo aos favoritos do usuário;
`DELETE /api/favorites/{listing_id}` remove. Operações são idempotentes. `GET
/api/favorites` retorna os anúncios favoritados, com paginação. Favoritar e retirar
pela interface atualiza o estado imediatamente e persiste após recarregar a página.

### R5 — Conversar com o vendedor

`POST /api/conversations` recebe `{listing_id}` e abre ou recupera a conversa entre
o usuário comprador e o vendedor daquele anúncio. Não abra conversa consigo mesmo.
`GET /api/conversations` lista as conversas do usuário. `GET
/api/conversations/{id}/messages` lista as mensagens em ordem; `POST` na mesma rota
envia `{content}` de 1 a 2000 caracteres e retorna a mensagem com 201. Apenas os dois
participantes podem acessar ou enviar mensagens; outro usuário recebe 403. Mostre
nome da outra pessoa, anúncio associado, remetente e data de cada mensagem. Basta
atualizar ao abrir/enviar ou por polling; não precisa de WebSocket.

### R6 — Comprar e reservar estoque

O botão `Comprar` abre confirmação com quantidade e endereço. `POST /api/orders`
recebe `{listing_id, quantity, address}`; endereço é texto não vazio de até 500
caracteres. O pedido compra um único anúncio, sem carrinho multivendedor. Retorna
201 com `id`, `listing_id`, `buyer_id`, `seller_id`, `quantity`, `unit_price_cents`,
`total_cents`, `address`, `status` e datas. Status inicial é `pending`.

Exija sessão e quantidade inteira positiva; rejeite compra do próprio anúncio com
400. Anúncio inativo ou estoque insuficiente retorna 409. Reserve estoque na mesma
transação da criação: duas compras concorrentes não podem vender a última unidade
duas vezes. Calcule o preço no servidor; mudanças futuras no anúncio não mudam o
preço do pedido. A compra é simulada, sem gateway nem cobrança real.

### R7 — Compras, vendas e andamento

`GET /api/me/orders?role=buyer` lista minhas compras; `role=seller`, minhas vendas,
ambas paginadas. `GET /api/orders/{id}` é visível apenas para comprador e vendedor.
`PATCH /api/orders/{id}/status` recebe `{status}`. O vendedor pode passar de
`pending` para `confirmed` e de `confirmed` para `shipped`; o comprador pode passar
de `shipped` para `delivered`, ou cancelar de `pending` ou `confirmed` para
`cancelled`. Transição inválida retorna 409; pessoa sem permissão, 403. Cancelar
devolve estoque uma única vez. Pedido cancelado ou entregue não muda mais.

### R8 — Avaliar a compra

`POST /api/orders/{id}/review` recebe `{rating, comment}`: nota inteira de 1 a 5,
comentário de até 1000 caracteres. Somente o comprador de pedido entregue pode
avaliar, uma única vez; segunda avaliação retorna 409. `GET
/api/listings/{id}/reviews` retorna as avaliações com nome do comprador e data.
A média no perfil do vendedor reflete essas avaliações.

### R9 — Interface de comprador

Página inicial pública com cabeçalho `Feira Livre`, busca `Buscar produtos`, filtros,
ordenação e cards com imagem, título, preço em reais, cidade, condição e favorito.
Detalhe tem descrição, estoque, vendedor, avaliações, `Comprar` e `Conversar`.
Exiba estados de carregamento, erro e lista vazia; ações que exigem conta encaminham
ao login e permitem voltar ao anúncio. Cadastro, login e logout têm telas/ações
claras. A interface não pode afirmar sucesso quando a API recusa uma operação.

### R10 — Interface de vendedor e navegação

Usuário autenticado acessa no mesmo menu `Favoritos`, `Conversas`, `Minhas compras`,
`Minhas vendas`, `Meus anúncios`, `Anunciar` e `Minha conta`. Formulários mostram
validações; gerenciamento permite editar e desativar anúncio; pedidos mostram
quantidade, preço total, endereço e apenas os botões das transições permitidas para
aquela pessoa. Conversas permitem ler e enviar mensagem. Perfil e detalhe do anúncio
mostram avaliações. Nenhum desses destinos pode ser apenas um placeholder.

### R11 — Persistência, autorização e consistência

Todas as operações de escrita exigem sessão, com validação também no backend.
Separar dados dos usuários não pode depender só de esconder botões no frontend.
Dados persistem após reinício do backend e reload do navegador. Faça consultas
parametrizadas com SQLAlchemy; nunca monte SQL concatenando entrada do usuário.
Senhas nunca são registradas em logs. Não aceite preços negativos, estoque negativo,
IDs de comprador/vendedor fornecidos pelo cliente ou totais calculados no navegador.

### R12 — Apresentação e dados iniciais

Interface em pt-BR, valores com `R$`, datas legíveis, layout responsivo para celular
e desktop, campos com rótulos e botões acessíveis por teclado. Use componentes MUI
com hierarquia visual consistente e um visual próprio de marketplace.

Em banco vazio, semeie uma única vez as contas `ana@example.test`,
`bruno@example.test` e `carla@example.test`, nomes Ana, Bruno e Carla, senha
`Marketplace123!`, e pelo menos 12 anúncios variados distribuídos entre Ana e Bruno.
Inclua `Bicicleta urbana`, `Notebook para estudos` e `Estante de madeira`.
Não duplique seeds a cada startup. Carla pode usar o fluxo completo de compra.
Seeds servem para demonstração; todos os recursos devem funcionar com novas contas
e novos anúncios criados pela interface.
