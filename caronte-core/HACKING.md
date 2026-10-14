# HACKING Caronte

## Requirements

* Docker Compose
* Node.js / npm (for building static assets)

## Environment variables

There are three `.env` files to set up before running. Each has an `.env.example` to copy from:

```bash
cp .env.example .env
cp prejanus-back/.env.example prejanus-back/.env
cp forms/.env.example forms/.env
```

### Root `.env`

Controls infrastructure: Postgres admin credentials, database names, users and passwords for each service, and the Docker data volume path.

### `prejanus-back/.env`

App-level config for the FastAPI backend. The `DB_CONNECTION_STRING` and `DB_CONNECTION_STRING_FORMS` values must be assembled from the credentials set in the root `.env`:

```
DB_CONNECTION_STRING=postgresql+psycopg://<PREJANUS_USER>:<PREJANUS_PASSWORD>@db:5432/<PREJANUS_DB>
DB_CONNECTION_STRING_FORMS=postgresql+psycopg://<FORMS_READER>:<FORMS_READER_PASSWORD>@db:5432/<FORMS_DB>
```

### `forms/.env`

App-level config for the Flask forms service. The `POSTGRES_*` variables must match the corresponding credentials in the root `.env`:

```
POSTGRES_HOST=db
POSTGRES_DB=<FORMS_DB>
POSTGRES_USER=<FORMS_USER>
POSTGRES_PASSWORD=<FORMS_PASSWORD>
POSTGRES_PORT=5432
```

> **Note:** `forms/.env` is baked into the Docker image at build time (the Dockerfile copies it to `/src/.env`). Changes to it require a rebuild (`--build`).

## Translations

The forms app uses Flask-Babel. Compiled translation files (`.mo`) are gitignored and must be generated before the UI strings will appear correctly. Run this once from the `forms/` directory (requires `pybabel` from the project's dependencies):

```bash
cd forms
pybabel compile -d translations
```

This also runs automatically when the Docker image is built, so a `docker compose up --build forms` will recompile them too.

## Static assets

CSS, JS bundles, images and JSON schemas are compiled from `static-assets/` using webpack and served by nginx under `/static`. **This is a required step before starting the stack** — nginx will 404 on all `/static` requests until `dist/` exists.

```bash
cd static-assets
npm install   # first time only
npm run build
cd ..
```

The output lands in `static-assets/dist/`, which is bind-mounted into nginx read-only. Because it is a bind mount, subsequent rebuilds are picked up by nginx immediately without a container restart.

## Running the servers for development

```bash
docker compose \
    -f docker-compose.yml \
    -f docker-compose.override.yml \
    up --watch
```

Add `--build` after any change to `forms/.env` or other files copied into images at build time.

### docker-compose.override.yml

The override file layers development-specific behaviour on top of the base `docker-compose.yml`:

- **`prejanus-back`** — enables `docker compose watch` sync so source changes under `src/` are synced and the server restarts automatically; also raises the memory limit for the development workload.
- **`prejanus-front`** — switches to `Dockerfile.develop` and runs `npm run dev` (Next.js dev server with HMR) instead of the production build; watch syncs `src/` and `public/`.
- **`forms`** — sets `FLASK_ENV=development` and enables watch sync+restart on the app source.
- **`smtp`** — activates the `develop` profile, bringing up [smtp4dev](https://github.com/rnwood/smtp4dev) as a local SMTP sink with a web UI at `http://localhost:8080/smtp4dev`.

The base `docker-compose.yml` is production-ready on its own; always pass both files when developing.

### Bypassing Senha Única for local development

Working with the real USP OAuth flow during day-to-day development requires valid institutional credentials and network access to USP servers. Both services support a dev-only bypass that skips the OAuth dance entirely and impersonates a user already present in the database.

#### Prerequisites

You need a user row in each service's database. The easiest way is to run a one-off SQL snippet against the running Postgres container:

**forms** (`caronte_forms` database):
```sql
INSERT INTO users (email, role, created_at)
VALUES ('dev@example.com', 'administrator', NOW())
ON CONFLICT (email) DO NOTHING;
```

**prejanus-back** (`caronte_prejanus` database):
```sql
INSERT INTO "user" (email, name, nusp, role)
VALUES ('dev@example.com', 'Dev User', '0000000', 'administrator')
ON CONFLICT (email) DO NOTHING;
```

You can run these via `docker compose exec db psql`:

```bash
docker compose exec db psql -U caronte_forms   -d caronte_forms   -c "INSERT INTO users (email, role, created_at) VALUES ('dev@example.com', 'administrator', NOW()) ON CONFLICT (email) DO NOTHING;"
docker compose exec db psql -U caronte_prejanus -d caronte_prejanus -c "INSERT INTO \"user\" (email, name, nusp, role) VALUES ('dev@example.com', 'Dev User', '0000000', 'administrator') ON CONFLICT (email) DO NOTHING;"
```

Then note the `id` assigned to the `prejanus-back` user:

```bash
docker compose exec db psql -U caronte_prejanus -d caronte_prejanus -c "SELECT id FROM \"user\" WHERE email = 'dev@example.com';"
```

#### Enabling the bypass

**`forms/.env`** — uncomment and set:
```
DEV_USER_EMAIL=dev@example.com
```

**`prejanus-back/.env`** — uncomment and set (use the id returned above):
```
DEV_USER_ID=1
```

The bypass is only active in `prejanus-back` when `APP_ENV=local` (which is the default in `prejanus-back/.env.example`). Unset or remove either variable to restore normal OAuth authentication.

> **Note:** Because `forms/.env` is baked into the Docker image at build time, adding or changing `DEV_USER_EMAIL` requires a rebuild: `docker compose up --build forms`.

### Accessing the forms admin

The forms admin is at:

```
http://localhost/pt/admin/scripts
```

Access requires the user's DB role to be `administrator`. The seed SQL in the bypass section above already sets `role = 'administrator'`, so with the dev bypass active you can navigate there directly.

### Creating a form

Go to `http://localhost/pt/form/` and click the **create button** in the table header. This opens a popup with a JSON editor — the create page is a fragment intentionally loaded inside that popup, so navigating to `/pt/form/create` directly will render nothing useful.

Paste a valid JSON document into the editor. The expected structure is defined by the JSON Schema served at:

```
http://localhost/static/schema/form.schema.json
```

## End-to-end tests

Browser-level tests live in `e2e/` and are run with [Cypress](https://www.cypress.io/) against a locally running stack.

### Prerequisites

- The full stack must be up and reachable at `http://localhost`.
- The forms service must be running with the `DEV_USER_EMAIL` bypass enabled (see [Bypassing Senha Única](#bypassing-senha-única-for-local-development) above). Cypress does not handle the USP OAuth popup — the bypass makes every request authenticate as the configured dev user automatically.

### Running the tests

```bash
cd e2e
npm install        # first time only
npx cypress run    # headless (CI)
npx cypress open   # interactive runner
```

### DB reset

On the first run, Postgres initialises from scratch. If you need to reset the database, wipe the data directory. Since it is owned by the Postgres container user, use Docker to do it safely:

```bash
docker run --rm \
    -v $(pwd)/docker/postgres_data:/data \
    alpine sh -c "rm -rf /data/*"
```
