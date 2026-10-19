# Feira Livre

Marketplace de compra e venda entre pessoas, inspirado em Mercado Livre e OLX.
A mesma conta pode comprar e vender.

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2 (síncrono), Pydantic 2, PostgreSQL 17 (psycopg 3), Argon2 para senhas.
- **Frontend**: Next.js 15.5.7 (App Router), React 19.1.1, TypeScript 5.9.2, Material UI 7.3.1, Emotion 11.14.

## Execução

### Banco de dados

O backend espera um PostgreSQL acessível pela variável `DATABASE_URL`
(padrão: `postgresql+psycopg://marketplace:marketplace@127.0.0.1:55432/marketplace`).
As tabelas são criadas no startup e o seed de demonstração roda uma única vez em banco vazio.

### Backend

```bash
pip install fastapi uvicorn sqlalchemy "psycopg[binary]" pydantic pydantic-settings argon2-cffi email-validator
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # desenvolvimento
npm run build && npm start   # produção
```

O Next reescreve `/api/*` para `API_INTERNAL_URL` (padrão `http://127.0.0.1:8000`),
mantendo os cookies de sessão na mesma origem.

## Variáveis de ambiente

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://marketplace:marketplace@127.0.0.1:55432/marketplace` | Conexão PostgreSQL |
| `API_INTERNAL_URL` | `http://127.0.0.1:8000` | URL interna da API usada pelo rewrite do Next |

Veja `.env.example`.

## Credenciais de demonstração

Semeadas automaticamente em banco vazio (senha igual para todas):
`Marketplace123!`

- `ana@example.test` — Ana (vendedora)
- `bruno@example.test` — Bruno (vendedor)
- `carla@example.test` — Carla (compradora, sem anúncios)

São criados 14 anúncios variados distribuídos entre Ana e Bruno, incluindo
"Bicicleta urbana", "Notebook para estudos" e "Estante de madeira".

## Testes

```bash
pytest -q --tb=short
```
